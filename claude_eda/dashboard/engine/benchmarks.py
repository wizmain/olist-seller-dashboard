"""Expert Research에서 추출한 벤치마크 상수."""

# =============================================================================
# 클러스터별 평균값 (seller_cluster_analysis_stats 기반)
# =============================================================================
CLUSTER_BENCHMARKS = {
    0: {  # Top Performer
        "label": "우수 판매자",
        "total_orders": 98.5,
        "total_revenue": 12161.0,
        "avg_price": 136.0,
        "product_variety": 36.3,
        "avg_review": 4.06,
        "low_review_pct": 0.10,
        "avg_delivery_days": 12.1,
        "late_delivery_pct": 0.06,
        "unique_customers": 87.4,
        "items_per_order": 1.24,
    },
    1: {  # Low Review
        "label": "저평가 판매자",
        "total_orders": 6.1,
        "total_revenue": 607.0,
        "avg_price": 107.3,
        "product_variety": 4.5,
        "avg_review": 2.58,
        "low_review_pct": 0.48,
        "avg_delivery_days": 13.5,
        "late_delivery_pct": 0.11,
        "unique_customers": 5.9,
        "items_per_order": 1.07,
    },
    2: {  # Delivery Risk
        "label": "배송 위험",
        "total_orders": 7.7,
        "total_revenue": 774.0,
        "avg_price": 116.5,
        "product_variety": 5.4,
        "avg_review": 3.14,
        "low_review_pct": 0.30,
        "avg_delivery_days": 28.9,
        "late_delivery_pct": 0.42,
        "unique_customers": 7.2,
        "items_per_order": 1.10,
    },
    3: {  # Standard
        "label": "일반 판매자",
        "total_orders": 13.0,
        "total_revenue": 1294.0,
        "avg_price": 115.7,
        "product_variety": 7.8,
        "avg_review": 4.11,
        "low_review_pct": 0.08,
        "avg_delivery_days": 11.0,
        "late_delivery_pct": 0.04,
        "unique_customers": 12.3,
        "items_per_order": 1.11,
    },
}

# =============================================================================
# 리뷰 구간별 평균 매출 (Expert Research)
# =============================================================================
REVIEW_REVENUE_MAP = {
    "1.0-2.0": 250,
    "2.0-3.0": 520,
    "3.0-3.5": 1800,
    "3.5-4.0": 4200,
    "4.0-4.5": 7603,    # 최고 매출 구간
    "4.5-5.0": 5100,
}

# =============================================================================
# 카테고리 기회지수 (평균 매출 × 수요)
# =============================================================================
CATEGORY_OPPORTUNITY = {
    "watches_gifts": 7100,
    "computers_accessories": 5200,
    "health_beauty": 4800,
    "bed_bath_table": 2657,
    "sports_leisure": 2400,
    "furniture_decor": 2200,
    "housewares": 1900,
    "auto": 1800,
    "garden_tools": 1600,
    "cool_stuff": 1500,
}

# =============================================================================
# 지역 수급비율 (공급 대비 수요 — 높을수록 공급 부족 = 기회)
# =============================================================================
REGION_DEMAND_SUPPLY = {
    "RJ": 72.4,
    "MG": 85.3,
    "BA": 172.5,
    "RS": 90.1,
    "PE": 178.8,
    "CE": 195.0,
    "PA": 210.0,
    "PR": 68.5,
    "SC": 55.2,
    "SP": 35.0,  # 공급 과잉
}

# =============================================================================
# 사진 수 → 매출 효과
# =============================================================================
PHOTO_EFFECT = {
    "base": 1.0,        # 1장
    "2_photos": 1.12,   # +12%
    "3_photos": 1.20,   # +20%
    "4plus": 1.273,     # +27.3%
}

# =============================================================================
# 배송일 → 재구매율 관계
# =============================================================================
DELIVERY_REPURCHASE = {
    "under_7": 0.045,    # 7일 이내: 4.5% 재구매
    "7_14": 0.035,       # 7-14일: 3.5%
    "14_21": 0.025,      # 14-21일: 2.5%
    "over_21": 0.012,    # 21일 초과: 1.2% (급락)
}

# =============================================================================
# 가격대 분포 (볼륨존)
# =============================================================================
PRICE_VOLUME_ZONES = {
    "budget": {"range": (0, 30), "share": 0.25},
    "volume": {"range": (30, 100), "share": 0.45},    # 메인 볼륨존
    "mid": {"range": (100, 300), "share": 0.22},
    "premium": {"range": (300, 10000), "share": 0.08},
}

# =============================================================================
# KPI 로드맵 타겟값 (Phase 1/2/3)
# =============================================================================
GROWTH_TARGETS = {
    "phase1": {  # 단기 1-3개월
        "label": "기반 다지기",
        "total_orders": 15,
        "avg_review": 3.8,
        "late_delivery_pct": 0.08,
        "product_variety": 10,
        "avg_photos": 3,
    },
    "phase2": {  # 중기 3-6개월
        "label": "성장 가속",
        "total_orders": 40,
        "avg_review": 4.0,
        "late_delivery_pct": 0.05,
        "product_variety": 20,
        "total_revenue": 5000,
    },
    "phase3": {  # 장기 6-12개월
        "label": "Top Performer 진입",
        "total_orders": 98,
        "avg_review": 4.1,
        "late_delivery_pct": 0.04,
        "product_variety": 36,
        "total_revenue": 12000,
    },
}

# =============================================================================
# 전체 평균 (벤치마크 기준선)
# =============================================================================
PLATFORM_AVERAGES = {
    "total_orders": 24.0,
    "total_revenue": 2558.0,
    "avg_price": 120.7,
    "product_variety": 11.4,
    "avg_review": 3.89,
    "low_review_pct": 0.12,
    "avg_delivery_days": 12.5,
    "late_delivery_pct": 0.07,
    "unique_customers": 22.0,
    "items_per_order": 1.15,
}
