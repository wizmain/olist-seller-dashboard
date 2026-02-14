"""한국어 라벨 및 번역 매핑."""

# 셀러 클러스터 라벨
SELLER_CLUSTER_LABELS = {
    0: "우수 판매자 (Top Performer)",
    1: "저평가 판매자 (Low Review)",
    2: "배송 위험 (Delivery Risk)",
    3: "일반 판매자 (Standard)",
}

SELLER_CLUSTER_SHORT = {
    0: "우수",
    1: "저평가",
    2: "배송위험",
    3: "일반",
}

# 고객 클러스터 라벨
CUSTOMER_CLUSTER_LABELS = {
    0: "고액 소비자",
    1: "일반 고객",
    2: "이탈 위험",
    3: "재구매 고객",
}

# 상품 클러스터 라벨
PRODUCT_CLUSTER_LABELS = {
    0: "프리미엄 (고가)",
    1: "베스트셀러 (인기)",
    2: "가성비 상품",
    3: "저평가 상품",
    4: "대형/중량 상품",
}

# 메트릭 이름 한국어
METRIC_LABELS = {
    "total_orders": "총 주문수",
    "total_revenue": "총 매출",
    "avg_price": "평균 단가",
    "product_variety": "상품 다양성",
    "avg_review": "평균 리뷰",
    "low_review_pct": "저평가 비율",
    "avg_delivery_days": "평균 배송일",
    "late_delivery_pct": "배송 지연율",
    "unique_customers": "고유 고객수",
    "items_per_order": "주문당 상품수",
}

# 레이더 차트용 축 라벨 (짧게)
RADAR_LABELS = {
    "total_orders": "주문수",
    "total_revenue": "매출",
    "avg_price": "단가",
    "product_variety": "상품수",
    "avg_review": "리뷰",
    "unique_customers": "고객수",
}

# 브라질 주 이름 한국어
STATE_NAMES_KR = {
    "SP": "상파울루",
    "RJ": "리우데자네이루",
    "MG": "미나스제라이스",
    "RS": "히우그란지두술",
    "PR": "파라나",
    "SC": "산타카타리나",
    "BA": "바이아",
    "DF": "브라질리아 연방구",
    "ES": "에스피리투산투",
    "GO": "고이아스",
    "PE": "페르남부쿠",
    "CE": "세아라",
    "PA": "파라",
    "MT": "마투그로수",
    "MA": "마라냥",
    "MS": "마투그로수두술",
    "PB": "파라이바",
    "PI": "피아우이",
    "RN": "히우그란지두노르치",
    "AL": "알라고아스",
    "SE": "세르지피",
    "TO": "토칸칭스",
    "RO": "혼도니아",
    "AM": "아마조나스",
    "AC": "아크리",
    "AP": "아마파",
    "RR": "호라이마",
}

# 건강 점수 차원 이름
HEALTH_DIMENSIONS = {
    "revenue": "매출",
    "orders": "주문량",
    "review": "리뷰",
    "delivery": "배송",
    "product": "상품",
    "reach": "고객도달",
}

# 컨설팅 카테고리
ADVICE_CATEGORIES = {
    "review": "리뷰 관리",
    "delivery": "배송 개선",
    "product": "상품 전략",
    "pricing": "가격 최적화",
    "reach": "시장 확장",
    "growth": "성장 전략",
}

# 우선순위 라벨
PRIORITY_LABELS = {
    "critical": "긴급",
    "high": "높음",
    "medium": "보통",
    "low": "참고",
}

# 로드맵 단계
ROADMAP_PHASES = {
    "short": "단기 (1-3개월)",
    "mid": "중기 (3-6개월)",
    "long": "장기 (6-12개월)",
}
