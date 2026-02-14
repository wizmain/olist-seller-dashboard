"""대시보드 설정 및 경로 상수."""

from pathlib import Path

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# 원본 데이터 경로
RAW_DATA_DIR = PROJECT_ROOT / "olist-ecommerce" / "data"
ORDER_ITEMS_PATH = RAW_DATA_DIR / "olist_order_items_dataset.csv"
ORDERS_PATH = RAW_DATA_DIR / "olist_orders_dataset.csv"
REVIEWS_PATH = RAW_DATA_DIR / "olist_order_reviews_dataset.csv"
SELLERS_PATH = RAW_DATA_DIR / "olist_sellers_dataset.csv"
PRODUCTS_PATH = RAW_DATA_DIR / "olist_products_dataset.csv"
CUSTOMERS_PATH = RAW_DATA_DIR / "olist_customers_dataset.csv"
PAYMENTS_PATH = RAW_DATA_DIR / "olist_order_payments_dataset.csv"
CATEGORY_TRANSLATION_PATH = RAW_DATA_DIR / "product_category_name_translation.csv"

# 클러스터 분석 결과 경로
CLUSTER_DIR = PROJECT_ROOT / "claude_eda"
SELLER_CLUSTER_DATA_PATH = CLUSTER_DIR / "seller_cluster_analysis_data.csv"
SELLER_CLUSTER_STATS_PATH = CLUSTER_DIR / "seller_cluster_analysis_stats.csv"
PRODUCT_CLUSTER_DATA_PATH = CLUSTER_DIR / "product_cluster_analysis_data.csv"
PRODUCT_CLUSTER_STATS_PATH = CLUSTER_DIR / "product_cluster_analysis_stats.csv"
CUSTOMER_CLUSTER_DATA_PATH = CLUSTER_DIR / "customer_cluster_analysis_data.csv"

# 앱 설정
APP_TITLE = "Olist 셀러 컨설팅 대시보드"
APP_ICON = "📊"
APP_LAYOUT = "wide"

# 건강 점수 가중치
HEALTH_WEIGHTS = {
    "revenue": 0.20,
    "orders": 0.15,
    "review": 0.25,
    "delivery": 0.20,
    "product": 0.10,
    "reach": 0.10,
}

# 색상 팔레트
COLORS = {
    "primary": "#1f77b4",
    "success": "#2ca02c",
    "warning": "#ff7f0e",
    "danger": "#d62728",
    "info": "#17becf",
    "muted": "#7f7f7f",
    "cluster_0": "#2ca02c",  # Top Performer - 녹색
    "cluster_1": "#d62728",  # Low Review - 빨강
    "cluster_2": "#ff7f0e",  # Delivery Risk - 주황
    "cluster_3": "#1f77b4",  # Standard - 파랑
}

PRIORITY_COLORS = {
    "critical": "#d62728",
    "high": "#ff7f0e",
    "medium": "#1f77b4",
    "low": "#2ca02c",
}
