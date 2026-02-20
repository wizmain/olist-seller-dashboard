"""시장 기회 분석 모듈 — 지역 수급, 카테고리 가격, 기회 점수."""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from claude_eda.dashboard.data.loader import (
    build_merged_table,
    load_customers,
    load_seller_clusters,
    load_sellers,
)


@st.cache_data
def compute_regional_supply_demand() -> pd.DataFrame:
    """주(State)별 고객 수, 셀러 수, 수급 비율 계산."""
    customers = load_customers()
    sellers = load_sellers()

    cust_by_state = (
        customers.groupby("customer_state")["customer_unique_id"]
        .nunique()
        .reset_index()
    )
    cust_by_state.columns = ["state", "customers"]

    seller_by_state = (
        sellers.groupby("seller_state")["seller_id"]
        .nunique()
        .reset_index()
    )
    seller_by_state.columns = ["state", "sellers"]

    df = cust_by_state.merge(seller_by_state, on="state", how="outer").fillna(0)
    df["sellers"] = df["sellers"].astype(int)
    df["customers"] = df["customers"].astype(int)
    df["ratio"] = df.apply(
        lambda r: r["customers"] / r["sellers"] if r["sellers"] > 0 else r["customers"] * 10,
        axis=1,
    )

    # 기회 등급
    def grade(ratio, sellers):
        if sellers == 0:
            return "진출 가능"
        if ratio >= 200:
            return "긴급 공급 부족"
        if ratio >= 100:
            return "높은 기회"
        if ratio >= 50:
            return "중간 기회"
        return "포화"

    df["opportunity_grade"] = df.apply(lambda r: grade(r["ratio"], r["sellers"]), axis=1)
    return df.sort_values("ratio", ascending=False).reset_index(drop=True)


@st.cache_data
def compute_category_state_matrix() -> pd.DataFrame:
    """카테고리 × 주(State) 매출/주문/셀러수/평균가격 매트릭스."""
    merged = build_merged_table()
    delivered = merged[merged["order_status"] == "delivered"]

    matrix = (
        delivered.groupby(["product_category_name_english", "seller_state"])
        .agg(
            revenue=("price", "sum"),
            orders=("order_id", "nunique"),
            sellers=("seller_id", "nunique"),
            avg_price=("price", "mean"),
            median_price=("price", "median"),
        )
        .reset_index()
    )
    matrix.columns = ["category", "state", "revenue", "orders", "sellers", "avg_price", "median_price"]
    matrix["orders_per_seller"] = matrix.apply(
        lambda r: r["orders"] / r["sellers"] if r["sellers"] > 0 else 0, axis=1
    )
    return matrix


@st.cache_data
def compute_category_price_stats() -> pd.DataFrame:
    """카테고리별 가격 통계 (전체 시장 기준)."""
    merged = build_merged_table()
    delivered = merged[merged["order_status"] == "delivered"]

    stats = (
        delivered.groupby("product_category_name_english")["price"]
        .agg(["mean", "median", "std", "min", "max", "count"])
        .reset_index()
    )
    stats.columns = ["category", "mean_price", "median_price", "std_price", "min_price", "max_price", "order_count"]

    # 사분위수 추가
    q25 = delivered.groupby("product_category_name_english")["price"].quantile(0.25).reset_index()
    q25.columns = ["category", "p25"]
    q75 = delivered.groupby("product_category_name_english")["price"].quantile(0.75).reset_index()
    q75.columns = ["category", "p75"]

    stats = stats.merge(q25, on="category").merge(q75, on="category")
    return stats.sort_values("order_count", ascending=False).reset_index(drop=True)


@st.cache_data
def compute_category_price_by_state(category: str) -> pd.DataFrame:
    """특정 카테고리의 주(State)별 가격 통계."""
    merged = build_merged_table()
    cat_data = merged[
        (merged["product_category_name_english"] == category)
        & (merged["order_status"] == "delivered")
    ]
    if cat_data.empty:
        return pd.DataFrame()

    stats = (
        cat_data.groupby("customer_state")["price"]
        .agg(["mean", "median", "count"])
        .reset_index()
    )
    stats.columns = ["state", "avg_price", "median_price", "orders"]
    return stats.sort_values("orders", ascending=False).reset_index(drop=True)


def compute_seller_growth_regions(
    seller_id: str,
    seller_categories: list[str],
    seller_state: str,
) -> list[dict]:
    """셀러 맞춤 성장 가능 지역 Top 5 추천.

    Returns:
        list of dicts with keys:
            state, opportunity_score, market_revenue, market_orders,
            competitors, orders_per_seller, avg_price, avg_delivery_risk,
            reason
    """
    regional_sd = compute_regional_supply_demand()
    cat_state = compute_category_state_matrix()

    # 셀러의 카테고리에 해당하는 지역별 데이터
    if not seller_categories:
        return []

    cat_filtered = cat_state[cat_state["category"].isin(seller_categories)]
    if cat_filtered.empty:
        return []

    # 지역별 집계 (셀러의 카테고리 기준)
    region_agg = (
        cat_filtered.groupby("state")
        .agg(
            market_revenue=("revenue", "sum"),
            market_orders=("orders", "sum"),
            competitors=("sellers", "sum"),
            avg_price=("avg_price", "mean"),
        )
        .reset_index()
    )

    # 수급 비율 조인
    region_agg = region_agg.merge(
        regional_sd[["state", "customers", "ratio", "opportunity_grade"]],
        on="state",
        how="left",
    )

    # 기회 점수 계산
    # = (수급비율 정규화 × 0.4) + (시장매출 정규화 × 0.3) + (셀러당 주문 정규화 × 0.3)
    region_agg["orders_per_seller"] = region_agg.apply(
        lambda r: r["market_orders"] / r["competitors"] if r["competitors"] > 0 else r["market_orders"],
        axis=1,
    )

    def _normalize(series):
        mn, mx = series.min(), series.max()
        if mx == mn:
            return pd.Series([50.0] * len(series), index=series.index)
        return (series - mn) / (mx - mn) * 100

    region_agg["score_ratio"] = _normalize(region_agg["ratio"].fillna(0))
    region_agg["score_revenue"] = _normalize(region_agg["market_revenue"])
    region_agg["score_ops"] = _normalize(region_agg["orders_per_seller"])

    region_agg["opportunity_score"] = (
        region_agg["score_ratio"] * 0.4
        + region_agg["score_revenue"] * 0.3
        + region_agg["score_ops"] * 0.3
    ).round(1)

    # 셀러 자기 주(State) 제외 + 상위 5개
    region_agg = region_agg[region_agg["state"] != seller_state]
    top5 = region_agg.sort_values("opportunity_score", ascending=False).head(5)

    results = []
    for _, r in top5.iterrows():
        # 추천 이유 생성
        reasons = []
        if r["ratio"] >= 100:
            reasons.append(f"고객/셀러 비율 {r['ratio']:.0f}:1 (공급 부족)")
        if r["orders_per_seller"] >= 30:
            reasons.append(f"셀러당 주문 {r['orders_per_seller']:.0f}건 (높은 수요)")
        if r["market_revenue"] >= 50000:
            reasons.append(f"시장 규모 R${r['market_revenue']:,.0f}")
        if not reasons:
            reasons.append("성장 잠재력 있음")

        results.append({
            "state": r["state"],
            "opportunity_score": r["opportunity_score"],
            "opportunity_grade": r.get("opportunity_grade", ""),
            "market_revenue": r["market_revenue"],
            "market_orders": int(r["market_orders"]),
            "competitors": int(r["competitors"]),
            "orders_per_seller": r["orders_per_seller"],
            "avg_price": r["avg_price"],
            "customers": int(r.get("customers", 0)),
            "reason": " / ".join(reasons),
        })

    return results


def compute_price_simulation(category: str, state: str) -> list[dict]:
    """특정 카테고리+지역에서 가격대별 매출 시뮬레이션.

    Returns:
        list of dicts with keys:
            price_range, label, order_share, avg_price,
            estimated_monthly_orders, estimated_monthly_revenue
    """
    merged = build_merged_table()
    cat_data = merged[
        (merged["product_category_name_english"] == category)
        & (merged["order_status"] == "delivered")
    ]

    if cat_data.empty:
        return []

    # 전체 카테고리 데이터에서 가격대별 분포
    total_orders = cat_data["order_id"].nunique()

    # 데이터 기간 (월 수)
    dates = cat_data["order_purchase_timestamp"].dropna()
    if dates.empty:
        return []
    months = max(1, (dates.max() - dates.min()).days / 30)

    # 해당 지역 데이터
    state_data = cat_data[cat_data["customer_state"] == state] if state else cat_data
    state_orders = state_data["order_id"].nunique()
    monthly_orders = state_orders / months if months > 0 else 0

    bins = [
        (0, 30, "저가 (R$0-30)"),
        (30, 100, "볼륨존 (R$30-100)"),
        (100, 200, "프리미엄 (R$100-200)"),
        (200, 50000, "고가 (R$200+)"),
    ]

    results = []
    for low, high, label in bins:
        segment = state_data[(state_data["price"] >= low) & (state_data["price"] < high)]
        seg_orders = segment["order_id"].nunique()
        share = seg_orders / state_orders if state_orders > 0 else 0
        avg_p = float(segment["price"].mean()) if not segment.empty else (low + high) / 2

        est_monthly = monthly_orders * share
        est_revenue = est_monthly * avg_p

        results.append({
            "price_range": f"R${low}-{high}" if high < 50000 else f"R${low}+",
            "label": label,
            "order_share": share,
            "avg_price": avg_p,
            "estimated_monthly_orders": round(est_monthly, 1),
            "estimated_monthly_revenue": round(est_revenue, 0),
        })

    return results


def compute_cross_sell_categories(seller_categories: list[str]) -> pd.DataFrame:
    """셀러의 카테고리와 함께 판매되는 다른 카테고리 추천."""
    merged = build_merged_table()
    cluster_df = load_seller_clusters()

    # 같은 카테고리를 판매하는 다른 셀러들
    sellers_in_cat = merged[
        merged["product_category_name_english"].isin(seller_categories)
    ]["seller_id"].unique()

    # 그 셀러들이 판매하는 다른 카테고리
    other_cats = merged[
        (merged["seller_id"].isin(sellers_in_cat))
        & (~merged["product_category_name_english"].isin(seller_categories))
    ]

    if other_cats.empty:
        return pd.DataFrame()

    cross = (
        other_cats.groupby("product_category_name_english")
        .agg(
            sellers=("seller_id", "nunique"),
            revenue=("price", "sum"),
            avg_price=("price", "mean"),
            orders=("order_id", "nunique"),
        )
        .reset_index()
    )
    cross.columns = ["category", "sellers", "revenue", "avg_price", "orders"]
    cross["adoption_rate"] = cross["sellers"] / len(sellers_in_cat)
    cross = cross[cross["adoption_rate"] >= 0.05]  # 5% 이상 채택된 카테고리만

    return cross.sort_values("adoption_rate", ascending=False).head(10).reset_index(drop=True)


@st.cache_data
def compute_category_opportunity_for_seller(
    seller_id: str,
    seller_categories: list[str],
    seller_state: str,
) -> pd.DataFrame:
    """셀러 미진출 카테고리 중 기회 높은 것 추천."""
    cat_state = compute_category_state_matrix()

    # 셀러 지역 또는 인접 지역에서 수요 높은 카테고리
    # 셀러 미진출 카테고리만
    untapped = cat_state[
        ~cat_state["category"].isin(seller_categories)
    ]

    # 지역별 집계
    opp = (
        untapped.groupby("category")
        .agg(
            total_revenue=("revenue", "sum"),
            total_orders=("orders", "sum"),
            total_sellers=("sellers", "sum"),
            avg_price=("avg_price", "mean"),
        )
        .reset_index()
    )

    opp["orders_per_seller"] = opp.apply(
        lambda r: r["total_orders"] / r["total_sellers"] if r["total_sellers"] > 0 else r["total_orders"],
        axis=1,
    )
    opp["opportunity_score"] = (opp["orders_per_seller"] * opp["avg_price"] / 100).round(1)

    return opp.sort_values("opportunity_score", ascending=False).head(10).reset_index(drop=True)
