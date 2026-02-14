"""건강 점수 (0-100) 6차원 가중 합산."""

from __future__ import annotations

import numpy as np

from claude_eda.dashboard.config import HEALTH_WEIGHTS
from claude_eda.dashboard.engine.benchmarks import CLUSTER_BENCHMARKS


def _clamp(val: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, val))


def compute_dimension_scores(
    total_revenue: float,
    total_orders: int,
    avg_review: float,
    low_review_pct: float,
    avg_delivery_days: float,
    late_delivery_pct: float,
    product_variety: int,
    unique_customers: int,
) -> dict[str, float]:
    """6차원 개별 점수 (0-100) 산출."""
    top = CLUSTER_BENCHMARKS[0]  # Top Performer 기준

    # 매출 (0-100): Top Performer 매출 대비 비율 (로그 스케일)
    if total_revenue > 0:
        rev_score = _clamp(
            np.log1p(total_revenue) / np.log1p(top["total_revenue"]) * 100
        )
    else:
        rev_score = 0.0

    # 주문량 (0-100): Top Performer 주문수 대비
    if total_orders > 0:
        ord_score = _clamp(
            np.log1p(total_orders) / np.log1p(top["total_orders"]) * 100
        )
    else:
        ord_score = 0.0

    # 리뷰 (0-100): 평균 리뷰 (1-5) → 0-100 + 저평가 패널티
    if avg_review > 0:
        base_review = _clamp((avg_review - 1) / 4 * 100)
        penalty = low_review_pct * 50  # 저평가 비율에 따른 패널티
        rev_score_dim = _clamp(base_review - penalty)
    else:
        rev_score_dim = 0.0

    # 배송 (0-100): 배송일 짧을수록 + 지연율 낮을수록 좋음
    if avg_delivery_days > 0:
        # 7일=100, 30일=0 선형 스케일
        day_score = _clamp((30 - avg_delivery_days) / 23 * 100)
        late_score = _clamp((1 - late_delivery_pct) * 100)
        del_score = day_score * 0.6 + late_score * 0.4
    else:
        del_score = 50.0  # 데이터 없음

    # 상품 (0-100): 다양성 기준 (Top Performer 36.3 기준)
    prod_score = _clamp(product_variety / top["product_variety"] * 100)

    # 고객도달 (0-100): 고유 고객수 (로그 스케일)
    if unique_customers > 0:
        reach_score = _clamp(
            np.log1p(unique_customers) / np.log1p(top["unique_customers"]) * 100
        )
    else:
        reach_score = 0.0

    return {
        "revenue": round(rev_score, 1),
        "orders": round(ord_score, 1),
        "review": round(rev_score_dim, 1),
        "delivery": round(del_score, 1),
        "product": round(prod_score, 1),
        "reach": round(reach_score, 1),
    }


def compute_health_score(dimension_scores: dict[str, float]) -> float:
    """6차원 가중 합산 건강 점수 (0-100)."""
    total = 0.0
    for dim, weight in HEALTH_WEIGHTS.items():
        total += dimension_scores.get(dim, 0.0) * weight
    return round(_clamp(total), 1)


def compute_full_health(
    total_revenue: float,
    total_orders: int,
    avg_review: float,
    low_review_pct: float,
    avg_delivery_days: float,
    late_delivery_pct: float,
    product_variety: int,
    unique_customers: int,
) -> tuple[float, dict[str, float]]:
    """건강 점수 + 차원별 점수 반환."""
    dims = compute_dimension_scores(
        total_revenue=total_revenue,
        total_orders=total_orders,
        avg_review=avg_review,
        low_review_pct=low_review_pct,
        avg_delivery_days=avg_delivery_days,
        late_delivery_pct=late_delivery_pct,
        product_variety=product_variety,
        unique_customers=unique_customers,
    )
    score = compute_health_score(dims)
    return score, dims
