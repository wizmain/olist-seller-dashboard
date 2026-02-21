"""셀러별 배송 지연 & 계절 분석 모듈."""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from claude_eda.dashboard.config import RAINY_MONTHS, REGION_MAP
from claude_eda.dashboard.data.loader import (
    load_customers,
    load_order_items,
    load_orders,
    load_reviews,
)


@st.cache_data
def _build_delivery_base() -> pd.DataFrame:
    """전체 배송 분석용 기본 테이블을 구축한다 (캐싱)."""
    orders = load_orders()
    items = load_order_items()
    reviews = load_reviews()
    customers = load_customers()

    # delivered만
    delivered = orders[orders["order_status"] == "delivered"].copy()
    delivered = delivered.dropna(
        subset=["order_delivered_carrier_date", "order_delivered_customer_date"]
    )

    # shipping_limit 병합
    shipping_limits = (
        items.groupby("order_id")["shipping_limit_date"]
        .min().reset_index()
        .rename(columns={"shipping_limit_date": "shipping_limit"})
    )
    shipping_limits["shipping_limit"] = pd.to_datetime(shipping_limits["shipping_limit"])

    df = delivered.merge(shipping_limits, on="order_id", how="left")
    df = df.dropna(subset=["shipping_limit"])

    # seller_id 병합 (order_items에서)
    seller_map = items.drop_duplicates("order_id")[["order_id", "seller_id"]]
    df = df.merge(seller_map, on="order_id", how="left")

    # 고객 주 병합
    df = df.merge(customers[["customer_id", "customer_state"]], on="customer_id", how="left")

    # 지연 지표
    df["dispatch_delay_days"] = (
        df["order_delivered_carrier_date"] - df["shipping_limit"]
    ).dt.total_seconds() / 86400

    df["delivery_delay_days"] = (
        df["order_delivered_customer_date"] - df["order_estimated_delivery_date"]
    ).dt.total_seconds() / 86400

    df["total_delivery_days"] = (
        df["order_delivered_customer_date"] - df["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400

    df["dispatch_days"] = (
        df["order_delivered_carrier_date"] - df["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400

    df["transit_days"] = (
        df["order_delivered_customer_date"] - df["order_delivered_carrier_date"]
    ).dt.total_seconds() / 86400

    df["is_dispatch_delayed"] = df["dispatch_delay_days"] > 0
    df["is_delivery_delayed"] = df["delivery_delay_days"] > 0

    # 월/계절
    df["order_month"] = df["order_purchase_timestamp"].dt.month
    df["order_ym"] = df["order_purchase_timestamp"].dt.to_period("M").astype(str)

    # 고객 권역
    df["customer_region"] = df["customer_state"].map(REGION_MAP).fillna("Other")

    # 계절 할당 (고객 소재 기준)
    def _season(row):
        region = row["customer_region"]
        month = row["order_month"]
        rainy = RAINY_MONTHS.get(region, {10, 11, 12, 1, 2, 3})
        return "우기" if month in rainy else "건기"

    df["season"] = df.apply(_season, axis=1)

    # 리뷰 병합
    review_scores = reviews.groupby("order_id")["review_score"].mean().reset_index()
    df = df.merge(review_scores, on="order_id", how="left")

    return df


def compute_seller_delivery(seller_id: str) -> dict:
    """셀러의 배송 성과를 분석한다."""
    base = _build_delivery_base()
    seller_df = base[base["seller_id"] == seller_id].copy()
    all_df = base.copy()

    result: dict = {
        "has_data": len(seller_df) > 0,
        "seller_orders": len(seller_df),
    }

    if not result["has_data"]:
        return result

    # ── 1. 셀러 배송 KPI ───────────────────────────────────
    result["dispatch_delay_rate"] = seller_df["is_dispatch_delayed"].mean()
    result["delivery_delay_rate"] = seller_df["is_delivery_delayed"].mean()
    result["avg_dispatch_delay"] = seller_df["dispatch_delay_days"].mean()
    result["avg_delivery_delay"] = seller_df["delivery_delay_days"].mean()
    result["avg_total_delivery"] = seller_df["total_delivery_days"].mean()
    result["avg_dispatch_days"] = seller_df["dispatch_days"].mean()
    result["avg_transit_days"] = seller_df["transit_days"].mean()

    # 전체 평균 (비교용)
    result["platform_dispatch_delay_rate"] = all_df["is_dispatch_delayed"].mean()
    result["platform_delivery_delay_rate"] = all_df["is_delivery_delayed"].mean()
    result["platform_avg_total_delivery"] = all_df["total_delivery_days"].mean()
    result["platform_avg_dispatch_days"] = all_df["dispatch_days"].mean()
    result["platform_avg_transit_days"] = all_df["transit_days"].mean()

    # ── 2. 발송 지연 구간별 분포 ───────────────────────────
    bins = [-np.inf, 0, 3, 7, np.inf]
    labels = ["정시/조기", "1~3일", "4~7일", "7일+"]
    seller_df["dispatch_group"] = pd.cut(
        seller_df["dispatch_delay_days"], bins=bins, labels=labels
    )
    result["dispatch_group_dist"] = (
        seller_df["dispatch_group"].value_counts().reindex(labels, fill_value=0).to_dict()
    )

    # ── 3. 월별 배송 지연율 추이 ───────────────────────────
    seller_monthly = seller_df.groupby("order_ym").agg(
        delivery_delay_rate=("is_delivery_delayed", "mean"),
        dispatch_delay_rate=("is_dispatch_delayed", "mean"),
        order_count=("order_id", "count"),
    ).reset_index()
    seller_monthly = seller_monthly[seller_monthly["order_count"] >= 1]

    platform_monthly = all_df.groupby("order_ym").agg(
        delivery_delay_rate=("is_delivery_delayed", "mean"),
    ).reset_index()

    result["seller_monthly"] = seller_monthly
    result["platform_monthly"] = platform_monthly

    # ── 4. 계절별 분석 ─────────────────────────────────────
    # 셀러 소재 권역 (고객 기반 최빈 권역)
    if not seller_df["customer_region"].empty:
        result["primary_region"] = seller_df["customer_region"].mode().iloc[0]
    else:
        result["primary_region"] = "Southeast"

    season_stats = seller_df.groupby("season").agg(
        orders=("order_id", "count"),
        dispatch_delay_rate=("is_dispatch_delayed", "mean"),
        delivery_delay_rate=("is_delivery_delayed", "mean"),
        avg_dispatch_days=("dispatch_days", "mean"),
        avg_transit_days=("transit_days", "mean"),
        avg_total=("total_delivery_days", "mean"),
        avg_review=("review_score", "mean"),
    ).to_dict(orient="index")
    result["season_stats"] = season_stats

    # 플랫폼 계절 평균
    platform_season = all_df.groupby("season").agg(
        delivery_delay_rate=("is_delivery_delayed", "mean"),
        avg_transit_days=("transit_days", "mean"),
    ).to_dict(orient="index")
    result["platform_season"] = platform_season

    # 셀러의 월별 운송 소요일
    seller_monthly_transit = seller_df.groupby("order_month")["transit_days"].mean()
    result["monthly_transit"] = seller_monthly_transit.to_dict()

    # 플랫폼 월별 운송 소요일
    platform_monthly_transit = all_df.groupby("order_month")["transit_days"].mean()
    result["platform_monthly_transit"] = platform_monthly_transit.to_dict()

    # ── 5. 발송 지연 → 리뷰 영향 ──────────────────────────
    if seller_df["review_score"].notna().sum() > 0:
        delayed = seller_df[seller_df["is_dispatch_delayed"]]
        on_time = seller_df[~seller_df["is_dispatch_delayed"]]
        result["review_on_time"] = on_time["review_score"].mean() if len(on_time) > 0 else None
        result["review_delayed"] = delayed["review_score"].mean() if len(delayed) > 0 else None
    else:
        result["review_on_time"] = None
        result["review_delayed"] = None

    return result


def compute_regional_delivery_days(seller_id: str) -> dict[str, float]:
    """셀러의 배송 완료 주문에서 고객 state별 평균 배송 소요일을 집계한다."""
    base = _build_delivery_base()
    seller_df = base[base["seller_id"] == seller_id].copy()

    if seller_df.empty:
        return {}

    valid = seller_df.dropna(subset=["customer_state", "total_delivery_days"])
    if valid.empty:
        return {}

    by_state = valid.groupby("customer_state")["total_delivery_days"].mean()
    return by_state.to_dict()
