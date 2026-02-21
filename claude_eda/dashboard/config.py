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
GEOLOCATION_PATH = RAW_DATA_DIR / "olist_geolocation_dataset.csv"
CATEGORY_TRANSLATION_PATH = RAW_DATA_DIR / "product_category_name_translation.csv"

# 클러스터 분석 결과 경로
CLUSTER_DIR = PROJECT_ROOT / "claude_eda"
SELLER_CLUSTER_DATA_PATH = CLUSTER_DIR / "seller_cluster_analysis_data.csv"
SELLER_CLUSTER_STATS_PATH = CLUSTER_DIR / "seller_cluster_analysis_stats.csv"
PRODUCT_CLUSTER_DATA_PATH = CLUSTER_DIR / "product_cluster_analysis_data.csv"
PRODUCT_CLUSTER_STATS_PATH = CLUSTER_DIR / "product_cluster_analysis_stats.csv"
CUSTOMER_CLUSTER_DATA_PATH = CLUSTER_DIR / "customer_cluster_analysis_data.csv"

# 셀러 회사명 매핑
SELLER_NAME_MAPPING_PATH = PROJECT_ROOT / "olist-ecommerce" / "output" / "seller_id_company_name_mapping.csv"

# 상품명 매핑
PRODUCT_NAME_MAPPING_PATH = PROJECT_ROOT / "olist-ecommerce" / "output" / "product_id_name_mapping.csv"

# 물류 창고 분석 결과 경로
WAREHOUSE_RECOMMENDATIONS_PATH = CLUSTER_DIR / "warehouse_recommendations.csv"
WAREHOUSE_SCENARIO_PATH = CLUSTER_DIR / "warehouse_scenario_comparison.csv"
WAREHOUSE_STATE_GAP_PATH = CLUSTER_DIR / "warehouse_state_gap_analysis.csv"

# 재고 관리 데이터 경로
INVENTORY_DATA_DIR = RAW_DATA_DIR / "inventory"

# 브라질 권역 매핑
REGION_MAP = {
    "SP": "Southeast", "RJ": "Southeast", "MG": "Southeast", "ES": "Southeast",
    "RS": "South", "SC": "South", "PR": "South",
    "BA": "Northeast", "PE": "Northeast", "CE": "Northeast", "MA": "Northeast",
    "PB": "Northeast", "PI": "Northeast", "RN": "Northeast", "AL": "Northeast",
    "SE": "Northeast",
    "AM": "North", "PA": "North", "AP": "North", "RR": "North",
    "RO": "North", "AC": "North", "TO": "North",
    "GO": "Central-West", "DF": "Central-West", "MT": "Central-West", "MS": "Central-West",
}

# 권역별 우기 월
RAINY_MONTHS = {
    "Southeast": {10, 11, 12, 1, 2, 3},
    "South": {9, 10, 11, 12, 1, 2},
    "Northeast": {3, 4, 5, 6, 7},
    "North": {12, 1, 2, 3, 4, 5},
    "Central-West": {10, 11, 12, 1, 2, 3},
}

RAINY_MONTHS_DISPLAY = {
    "Southeast": "10~3월",
    "South": "9~2월",
    "Northeast": "3~7월",
    "North": "12~5월",
    "Central-West": "10~3월",
}

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

# 브라질 27개 주 대략적 중심 좌표 (지도 라벨 위치용)
STATE_CENTER_COORDS: dict[str, tuple[float, float]] = {
    "AC": (-9.02, -70.81),
    "AL": (-9.57, -36.78),
    "AM": (-3.47, -62.22),
    "AP": (1.41, -51.77),
    "BA": (-12.58, -41.70),
    "CE": (-5.20, -39.53),
    "DF": (-15.83, -47.86),
    "ES": (-19.57, -40.51),
    "GO": (-15.83, -49.84),
    "MA": (-5.42, -45.44),
    "MG": (-18.51, -44.56),
    "MS": (-20.51, -54.54),
    "MT": (-12.68, -56.92),
    "PA": (-3.79, -52.48),
    "PB": (-7.28, -36.72),
    "PE": (-8.38, -37.86),
    "PI": (-7.72, -42.73),
    "PR": (-24.89, -51.55),
    "RJ": (-22.25, -42.66),
    "RN": (-5.81, -36.59),
    "RO": (-10.83, -63.34),
    "RR": (1.99, -61.33),
    "RS": (-29.75, -53.25),
    "SC": (-27.45, -50.95),
    "SE": (-10.57, -37.45),
    "SP": (-22.19, -48.79),
    "TO": (-10.18, -48.33),
}
