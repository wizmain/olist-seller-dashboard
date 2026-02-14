"""셀러별 메트릭 계산 파이프라인."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import streamlit as st

from claude_eda.dashboard.data.loader import (
    build_merged_table,
    load_customer_clusters,
    load_product_clusters,
    load_seller_cluster_stats,
    load_seller_clusters,
    load_sellers,
)


@dataclass
class SellerMetrics:
    """특정 셀러의 전체 메트릭."""

    seller_id: str

    # 프로필
    seller_state: str = ""
    seller_city: str = ""
    cluster: int = -1
    first_order: str = ""
    last_order: str = ""
    active_months: int = 0

    # KPI
    total_revenue: float = 0.0
    total_orders: int = 0
    unique_customers: int = 0
    avg_order_value: float = 0.0
    avg_review: float = 0.0
    low_review_pct: float = 0.0
    avg_delivery_days: float = 0.0
    late_delivery_pct: float = 0.0
    product_variety: int = 0
    avg_price: float = 0.0
    items_per_order: float = 0.0
    total_items: int = 0

    # 월별 추이
    monthly_orders: pd.DataFrame = field(default_factory=pd.DataFrame)
    monthly_revenue: pd.DataFrame = field(default_factory=pd.DataFrame)
    monthly_review: pd.DataFrame = field(default_factory=pd.DataFrame)

    # 상품 분석
    category_revenue: pd.DataFrame = field(default_factory=pd.DataFrame)
    product_cluster_dist: pd.DataFrame = field(default_factory=pd.DataFrame)

    # 고객 분석
    customer_state_dist: pd.DataFrame = field(default_factory=pd.DataFrame)
    customer_cluster_dist: pd.DataFrame = field(default_factory=pd.DataFrame)

    # 배송 분석
    delivery_days_list: list = field(default_factory=list)

    # 리뷰 분석
    review_distribution: pd.DataFrame = field(default_factory=pd.DataFrame)

    # 퍼센타일
    percentiles: dict = field(default_factory=dict)

    # 상품 사진 정보
    avg_photos: float = 0.0


@st.cache_data
def compute_seller_metrics(seller_id: str) -> SellerMetrics | None:
    """특정 셀러의 전체 메트릭 계산."""
    merged = build_merged_table()
    seller_data = merged[merged["seller_id"] == seller_id]

    if seller_data.empty:
        return None

    m = SellerMetrics(seller_id=seller_id)

    # --- 프로필 ---
    sellers_df = load_sellers()
    seller_info = sellers_df[sellers_df["seller_id"] == seller_id]
    if not seller_info.empty:
        m.seller_state = seller_info.iloc[0]["seller_state"]
        m.seller_city = seller_info.iloc[0]["seller_city"]

    cluster_df = load_seller_clusters()
    cluster_row = cluster_df[cluster_df["seller_id"] == seller_id]
    if not cluster_row.empty:
        m.cluster = int(cluster_row.iloc[0]["cluster"])

    # delivered 주문만 필터 (KPI 계산용)
    delivered = seller_data[seller_data["order_status"] == "delivered"]

    timestamps = seller_data["order_purchase_timestamp"].dropna()
    if not timestamps.empty:
        m.first_order = timestamps.min().strftime("%Y-%m-%d")
        m.last_order = timestamps.max().strftime("%Y-%m-%d")
        span = (timestamps.max() - timestamps.min()).days
        m.active_months = max(1, span // 30)

    # --- KPI ---
    m.total_revenue = float(seller_data["price"].sum())
    m.total_orders = seller_data["order_id"].nunique()
    m.unique_customers = seller_data["customer_unique_id"].nunique()
    m.avg_order_value = (
        m.total_revenue / m.total_orders if m.total_orders > 0 else 0.0
    )
    m.total_items = len(seller_data)
    m.items_per_order = m.total_items / m.total_orders if m.total_orders > 0 else 0.0
    m.product_variety = seller_data["product_id"].nunique()
    m.avg_price = float(seller_data["price"].mean()) if not seller_data.empty else 0.0

    reviews = seller_data["review_score"].dropna()
    if not reviews.empty:
        m.avg_review = float(reviews.mean())
        m.low_review_pct = float((reviews <= 2).mean())
    else:
        m.avg_review = 0.0
        m.low_review_pct = 0.0

    delivery = delivered["delivery_days"].dropna()
    if not delivery.empty:
        m.avg_delivery_days = float(delivery.mean())
        m.delivery_days_list = delivery.tolist()
    else:
        m.avg_delivery_days = 0.0
        m.delivery_days_list = []

    late = delivered["is_late"].dropna()
    m.late_delivery_pct = float(late.mean()) if not late.empty else 0.0

    # 사진 정보
    photos = seller_data["product_photos_qty"].dropna()
    m.avg_photos = float(photos.mean()) if not photos.empty else 0.0

    # --- 월별 추이 ---
    monthly = seller_data.dropna(subset=["order_month"]).copy()
    if not monthly.empty:
        mo = monthly.groupby("order_month").agg(
            orders=("order_id", "nunique"),
            revenue=("price", "sum"),
        )
        mo.index = mo.index.astype(str)
        m.monthly_orders = mo[["orders"]].reset_index()
        m.monthly_revenue = mo[["revenue"]].reset_index()

        mr = monthly.dropna(subset=["review_score"]).groupby("order_month").agg(
            avg_review=("review_score", "mean"),
            count=("review_score", "count"),
        )
        mr.index = mr.index.astype(str)
        m.monthly_review = mr.reset_index()

    # --- 상품 분석 ---
    cat_rev = (
        seller_data.groupby("product_category_name_english")["price"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )
    cat_rev.columns = ["category", "revenue"]
    m.category_revenue = cat_rev

    # 상품 클러스터 분포
    prod_clusters = load_product_clusters()
    seller_products = seller_data["product_id"].unique()
    matched = prod_clusters[prod_clusters["product_id"].isin(seller_products)]
    if not matched.empty:
        pc_dist = matched["cluster"].value_counts().reset_index()
        pc_dist.columns = ["cluster", "count"]
        m.product_cluster_dist = pc_dist

    # --- 고객 분석 ---
    cust_states = (
        seller_data.groupby("customer_state")["customer_unique_id"]
        .nunique()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )
    cust_states.columns = ["state", "customers"]
    m.customer_state_dist = cust_states

    # 고객 클러스터 분포
    cust_clusters = load_customer_clusters()
    seller_customers = seller_data["customer_unique_id"].unique()
    cust_matched = cust_clusters[
        cust_clusters["customer_unique_id"].isin(seller_customers)
    ]
    if not cust_matched.empty:
        cc_dist = cust_matched["cluster"].value_counts().reset_index()
        cc_dist.columns = ["cluster", "count"]
        m.customer_cluster_dist = cc_dist

    # --- 리뷰 분포 ---
    if not reviews.empty:
        rev_dist = reviews.value_counts().sort_index().reset_index()
        rev_dist.columns = ["score", "count"]
        m.review_distribution = rev_dist

    # --- 퍼센타일 ---
    m.percentiles = compute_percentile_ranks(seller_id)

    return m


@st.cache_data
def compute_percentile_ranks(seller_id: str) -> dict:
    """전체 셀러 대비 퍼센타일 (상위 X%) 계산."""
    cluster_df = load_seller_clusters()
    seller_row = cluster_df[cluster_df["seller_id"] == seller_id]
    if seller_row.empty:
        return {}

    seller_row = seller_row.iloc[0]
    metrics = [
        "total_orders",
        "total_revenue",
        "avg_price",
        "product_variety",
        "avg_review",
        "unique_customers",
        "items_per_order",
    ]
    # 낮을수록 좋은 지표
    lower_better = ["low_review_pct", "avg_delivery_days", "late_delivery_pct"]

    percentiles = {}
    for col in metrics:
        if col in cluster_df.columns:
            val = seller_row[col]
            rank = (cluster_df[col] >= val).mean() * 100
            percentiles[col] = round(rank, 1)

    for col in lower_better:
        if col in cluster_df.columns:
            val = seller_row[col]
            rank = (cluster_df[col] <= val).mean() * 100
            percentiles[col] = round(rank, 1)

    return percentiles


@st.cache_data
def get_cluster_averages() -> dict:
    """클러스터별 평균값 딕셔너리 반환."""
    stats = load_seller_cluster_stats()
    result = {}
    for _, row in stats.iterrows():
        cluster_id = int(row["cluster"])
        result[cluster_id] = {
            "total_orders": row["total_orders"],
            "total_revenue": row["total_revenue"],
            "avg_price": row["avg_price"],
            "product_variety": row["product_variety"],
            "avg_review": row["avg_review"],
            "low_review_pct": row["low_review_pct"],
            "avg_delivery_days": row["avg_delivery_days"],
            "late_delivery_pct": row["late_delivery_pct"],
            "unique_customers": row["unique_customers"],
            "items_per_order": row["items_per_order"],
            "count": int(row["count"]),
        }
    return result
