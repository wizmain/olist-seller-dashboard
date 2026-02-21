"""데이터 로딩 모듈. @st.cache_data로 전체 CSV 캐싱."""

import pandas as pd
import streamlit as st

from claude_eda.dashboard.config import (
    CATEGORY_TRANSLATION_PATH,
    CUSTOMER_CLUSTER_DATA_PATH,
    CUSTOMERS_PATH,
    GEOLOCATION_PATH,
    ORDER_ITEMS_PATH,
    ORDERS_PATH,
    PAYMENTS_PATH,
    PRODUCT_CLUSTER_DATA_PATH,
    PRODUCT_CLUSTER_STATS_PATH,
    PRODUCTS_PATH,
    REVIEWS_PATH,
    SELLER_CLUSTER_DATA_PATH,
    SELLER_CLUSTER_STATS_PATH,
    SELLERS_PATH,
    WAREHOUSE_RECOMMENDATIONS_PATH,
    WAREHOUSE_SCENARIO_PATH,
    WAREHOUSE_STATE_GAP_PATH,
)


@st.cache_data
def load_order_items() -> pd.DataFrame:
    return pd.read_csv(ORDER_ITEMS_PATH)


@st.cache_data
def load_orders() -> pd.DataFrame:
    df = pd.read_csv(ORDERS_PATH)
    date_cols = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


@st.cache_data
def load_reviews() -> pd.DataFrame:
    return pd.read_csv(REVIEWS_PATH)


@st.cache_data
def load_sellers() -> pd.DataFrame:
    return pd.read_csv(SELLERS_PATH)


@st.cache_data
def load_products() -> pd.DataFrame:
    return pd.read_csv(PRODUCTS_PATH)


@st.cache_data
def load_customers() -> pd.DataFrame:
    return pd.read_csv(CUSTOMERS_PATH)


@st.cache_data
def load_payments() -> pd.DataFrame:
    return pd.read_csv(PAYMENTS_PATH)


@st.cache_data
def load_category_translation() -> pd.DataFrame:
    return pd.read_csv(CATEGORY_TRANSLATION_PATH)


@st.cache_data
def load_geolocation() -> pd.DataFrame:
    """zip_code_prefix별 대표 위경도 (중복 제거, 첫 번째 값 사용)."""
    df = pd.read_csv(GEOLOCATION_PATH)
    return (
        df.groupby("geolocation_zip_code_prefix")
        .agg({"geolocation_lat": "first", "geolocation_lng": "first"})
        .reset_index()
    )


@st.cache_data
def load_seller_clusters() -> pd.DataFrame:
    return pd.read_csv(SELLER_CLUSTER_DATA_PATH)


@st.cache_data
def load_seller_cluster_stats() -> pd.DataFrame:
    return pd.read_csv(SELLER_CLUSTER_STATS_PATH)


@st.cache_data
def load_product_clusters() -> pd.DataFrame:
    return pd.read_csv(PRODUCT_CLUSTER_DATA_PATH)


@st.cache_data
def load_product_cluster_stats() -> pd.DataFrame:
    return pd.read_csv(PRODUCT_CLUSTER_STATS_PATH)


@st.cache_data
def load_customer_clusters() -> pd.DataFrame:
    return pd.read_csv(CUSTOMER_CLUSTER_DATA_PATH)


@st.cache_data
def build_merged_table() -> pd.DataFrame:
    """order_items + orders + reviews + customers + products + sellers 조인."""
    items = load_order_items()
    orders = load_orders()
    reviews = load_reviews()
    customers = load_customers()
    products = load_products()
    sellers = load_sellers()
    cat_trans = load_category_translation()

    # products에 영문 카테고리 추가
    products = products.merge(cat_trans, on="product_category_name", how="left")

    # 조인
    merged = items.merge(orders, on="order_id", how="left")
    review_cols = ["order_id", "review_score", "review_comment_message"]
    merged = merged.merge(
        reviews[review_cols].drop_duplicates("order_id"),
        on="order_id",
        how="left",
    )
    merged = merged.merge(customers, on="customer_id", how="left")
    merged = merged.merge(products, on="product_id", how="left")
    merged = merged.merge(sellers, on="seller_id", how="left")

    # 배송일 계산
    merged["delivery_days"] = (
        merged["order_delivered_customer_date"]
        - merged["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400
    merged["is_late"] = (
        merged["order_delivered_customer_date"]
        > merged["order_estimated_delivery_date"]
    )

    # 월 컬럼
    merged["order_month"] = merged["order_purchase_timestamp"].dt.to_period("M")

    return merged


@st.cache_data
def load_warehouse_recommendations() -> pd.DataFrame:
    return pd.read_csv(WAREHOUSE_RECOMMENDATIONS_PATH)


@st.cache_data
def load_warehouse_scenarios() -> pd.DataFrame:
    return pd.read_csv(WAREHOUSE_SCENARIO_PATH)


@st.cache_data
def load_warehouse_state_gap() -> pd.DataFrame:
    return pd.read_csv(WAREHOUSE_STATE_GAP_PATH)


@st.cache_data
def get_seller_list() -> pd.DataFrame:
    """셀러 ID + 매출 순위 리스트 반환 (검색/선택용)."""
    seller_clusters = load_seller_clusters()
    seller_list = (
        seller_clusters[["seller_id", "total_revenue", "total_orders", "cluster"]]
        .sort_values("total_revenue", ascending=False)
        .reset_index(drop=True)
    )
    seller_list["rank"] = range(1, len(seller_list) + 1)
    return seller_list
