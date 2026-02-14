"""규칙 기반 컨설팅 조언 생성기 (10+ 규칙)."""

from __future__ import annotations

from dataclasses import dataclass, field

from claude_eda.dashboard.data.preprocessor import SellerMetrics
from claude_eda.dashboard.engine.benchmarks import (
    CATEGORY_OPPORTUNITY,
    CLUSTER_BENCHMARKS,
    DELIVERY_REPURCHASE,
    GROWTH_TARGETS,
    PHOTO_EFFECT,
    REGION_DEMAND_SUPPLY,
    REVIEW_REVENUE_MAP,
)


@dataclass
class ConsultingAdvice:
    """컨설팅 조언 단위."""

    title: str
    category: str  # review, delivery, product, pricing, reach, growth
    priority: str  # critical, high, medium, low
    current_value: str = ""
    target_value: str = ""
    description: str = ""
    actions: list[str] = field(default_factory=list)
    expected_effect: str = ""


def generate_all_advice(metrics: SellerMetrics) -> list[ConsultingAdvice]:
    """전체 규칙 실행, 우선순위별 정렬."""
    advices: list[ConsultingAdvice] = []

    advices.extend(_rule_review_critical(metrics))
    advices.extend(_rule_delivery_delay(metrics))
    advices.extend(_rule_product_variety(metrics))
    advices.extend(_rule_photo_shortage(metrics))
    advices.extend(_rule_region_concentration(metrics))
    advices.extend(_rule_review_sweet_spot(metrics))
    advices.extend(_rule_category_expansion(metrics))
    advices.extend(_rule_price_optimization(metrics))
    advices.extend(_rule_delivery_warning(metrics))
    advices.extend(_rule_low_review_diagnosis(metrics))
    advices.extend(_rule_cancel_rate(metrics))
    advices.extend(_rule_repeat_customer(metrics))
    advices.extend(_rule_review_keyword_insight(metrics))

    # 우선순위 정렬
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    advices.sort(key=lambda a: priority_order.get(a.priority, 99))
    return advices


def _rule_review_critical(m: SellerMetrics) -> list[ConsultingAdvice]:
    """규칙 1: 리뷰 긴급 (<3.5) → 매출 악순환 경고."""
    if m.avg_review <= 0 or m.avg_review >= 3.5:
        return []
    return [
        ConsultingAdvice(
            title="리뷰 점수 긴급 개선 필요",
            category="review",
            priority="critical",
            current_value=f"{m.avg_review:.1f}점",
            target_value="3.5점 이상",
            description=(
                f"현재 평균 리뷰 {m.avg_review:.1f}점은 플랫폼 평균(3.89점) 대비 "
                f"심각하게 낮습니다. 저평가 비율이 {m.low_review_pct:.0%}로, "
                "리뷰 3.5 미만 셀러는 매출이 급격히 하락하는 악순환에 빠질 수 있습니다. "
                f"리뷰 3.5-4.0 구간 셀러 평균 매출은 R$4,200이지만, "
                f"현재 구간(~3.0)은 R$1,800 수준입니다."
            ),
            actions=[
                "저평가 리뷰의 주요 불만 사항 분석 (배송 지연 vs 상품 품질)",
                "배송 관련 불만이 높다면 예상 배송일을 보수적으로 재설정",
                "상품 관련 불만이면 상품 설명 및 사진 보강으로 기대치 관리",
                "고객 문의에 24시간 내 응답 체계 구축",
            ],
            expected_effect="리뷰 0.5점 개선 시 매출 약 2배 이상 증가 가능",
        )
    ]


def _rule_delivery_delay(m: SellerMetrics) -> list[ConsultingAdvice]:
    """규칙 2: 배송 지연율 (>10%)."""
    if m.late_delivery_pct <= 0.10:
        return []
    return [
        ConsultingAdvice(
            title="배송 지연율 개선 시급",
            category="delivery",
            priority="critical" if m.late_delivery_pct > 0.20 else "high",
            current_value=f"{m.late_delivery_pct:.1%}",
            target_value="6% 이하 (Top Performer 수준)",
            description=(
                f"배송 지연율 {m.late_delivery_pct:.1%}는 "
                f"Top Performer 평균(6%) 대비 "
                f"{m.late_delivery_pct / 0.06:.1f}배 높습니다. "
                "배송 지연은 저평가 리뷰의 주된 원인이며, "
                "재구매율을 크게 낮춥니다."
            ),
            actions=[
                "예상 배송일을 현재 평균 배송일 + 3일 여유로 보수적 설정",
                "물류 파트너 변경 또는 지역 거점 물류 활용 검토",
                "주문 접수 → 발송까지 리드타임 1일 단축 목표",
                "지연 발생 시 고객에게 선제적 안내 메시지 발송",
            ],
            expected_effect=(
                "지연율 10%p 감소 시 리뷰 약 0.3점 개선, "
                "재구매율 약 40% 향상 기대"
            ),
        )
    ]


def _rule_product_variety(m: SellerMetrics) -> list[ConsultingAdvice]:
    """규칙 3: 상품 다양성 부족 (<10종)."""
    if m.product_variety >= 10:
        return []
    top_variety = CLUSTER_BENCHMARKS[0]["product_variety"]
    return [
        ConsultingAdvice(
            title="상품 라인업 확대 필요",
            category="product",
            priority="high",
            current_value=f"{m.product_variety}종",
            target_value=f"{top_variety:.0f}종 (Top Performer 평균)",
            description=(
                f"현재 {m.product_variety}종의 상품으로는 "
                "고객 유입과 교차판매 기회가 제한적입니다. "
                f"Top Performer 셀러는 평균 {top_variety:.0f}종을 운영하며, "
                "상품 다양성은 매출과 강한 양의 상관관계를 보입니다."
            ),
            actions=[
                "현재 베스트셀러 카테고리의 연관 상품 추가",
                "높은 기회지수 카테고리 진출 검토 (watches_gifts, computers_accessories 등)",
                "월 2-3종 신상품 등록 목표 설정",
                "시즌 상품 및 번들 상품 기획",
            ],
            expected_effect=(
                f"상품 10종 → {top_variety:.0f}종 확대 시 "
                "매출 3-5배 성장 잠재력"
            ),
        )
    ]


def _rule_photo_shortage(m: SellerMetrics) -> list[ConsultingAdvice]:
    """규칙 4: 사진 부족 (<2장 평균)."""
    if m.avg_photos >= 2:
        return []
    return [
        ConsultingAdvice(
            title="상품 사진 보강 필요",
            category="product",
            priority="high",
            current_value=f"평균 {m.avg_photos:.1f}장",
            target_value="4장 이상",
            description=(
                f"현재 상품당 평균 사진 {m.avg_photos:.1f}장은 부족합니다. "
                "사진 4장 이상 등록 시 매출이 평균 +27.3% 증가하는 것으로 "
                "분석되었습니다. 사진은 가장 빠르고 비용 효과적인 개선 방법입니다."
            ),
            actions=[
                "모든 상품에 최소 3-4장의 고품질 사진 등록",
                "다각도 촬영 (정면, 측면, 상세, 사용 장면)",
                "사이즈 비교 사진 포함 (반품/불만 예방)",
                "자연광 활용, 깨끗한 배경으로 촬영",
            ],
            expected_effect="사진 4장 이상 시 매출 +27.3% 효과",
        )
    ]


def _rule_region_concentration(m: SellerMetrics) -> list[ConsultingAdvice]:
    """규칙 5: 고객 지역 편중 (SP 비율 > 50%)."""
    if m.customer_state_dist.empty:
        return []
    total = m.customer_state_dist["customers"].sum()
    sp_row = m.customer_state_dist[m.customer_state_dist["state"] == "SP"]
    sp_share = sp_row["customers"].iloc[0] / total if not sp_row.empty else 0

    if sp_share <= 0.50:
        return []

    # 높은 수요/공급 비율 지역 추천
    opportunity_regions = sorted(
        REGION_DEMAND_SUPPLY.items(), key=lambda x: x[1], reverse=True
    )[:3]
    region_text = ", ".join(
        [f"{r}(수급비율 {v:.0f})" for r, v in opportunity_regions]
    )

    return [
        ConsultingAdvice(
            title="시장 다변화 필요 (SP 편중)",
            category="reach",
            priority="medium",
            current_value=f"SP 비중 {sp_share:.0%}",
            target_value="SP 40% 이하로 분산",
            description=(
                f"고객의 {sp_share:.0%}가 상파울루에 집중되어 있습니다. "
                "SP는 셀러 공급이 과잉 상태(수급비율 35)이며, "
                f"공급 부족 지역에 기회가 있습니다: {region_text}."
            ),
            actions=[
                "RJ, MG, BA 등 수요 대비 공급 부족 지역 타겟 마케팅",
                "배송비를 상품 가격에 내재화하여 전국 무료배송 제공",
                "지역별 인기 카테고리 분석 후 맞춤 상품 추천",
            ],
            expected_effect="신규 지역 진출 시 경쟁 감소로 노출 확대, 매출 20-30% 성장 가능",
        )
    ]


def _rule_review_sweet_spot(m: SellerMetrics) -> list[ConsultingAdvice]:
    """규칙 6: 리뷰 스위트스팟 (3.5-4.0) → 0.5점 개선으로 매출 점프."""
    if not (3.5 <= m.avg_review < 4.0):
        return []
    return [
        ConsultingAdvice(
            title="리뷰 스위트스팟 — 매출 점프 기회",
            category="review",
            priority="high",
            current_value=f"{m.avg_review:.1f}점",
            target_value="4.0-4.5점 (최고 매출 구간)",
            description=(
                f"현재 리뷰 {m.avg_review:.1f}점은 3.5-4.0 구간으로, "
                f"평균 매출 R${REVIEW_REVENUE_MAP['3.5-4.0']:,}입니다. "
                f"4.0-4.5 구간으로 0.5점만 개선하면 "
                f"평균 매출이 R${REVIEW_REVENUE_MAP['4.0-4.5']:,}로 "
                "약 81% 급증합니다. 이것이 가장 효율적인 성장 레버입니다."
            ),
            actions=[
                "리뷰 1-2점 주문의 공통 원인 파악 및 근본 해결",
                "배송 예상일을 실제 배송일보다 2-3일 여유있게 설정",
                "포장 품질 개선 (파손 방지, 브랜딩)",
                "배송 완료 후 감사 메시지 발송",
            ],
            expected_effect="0.5점 개선 시 매출 약 +81% (R$3,400 → R$7,600)",
        )
    ]


def _rule_category_expansion(m: SellerMetrics) -> list[ConsultingAdvice]:
    """규칙 7: 고기회 카테고리 미진출."""
    if m.category_revenue.empty:
        return []
    current_cats = set(m.category_revenue["category"].dropna().tolist())
    opportunities = []
    for cat, score in CATEGORY_OPPORTUNITY.items():
        if cat not in current_cats:
            opportunities.append((cat, score))

    if not opportunities:
        return []

    top3 = sorted(opportunities, key=lambda x: x[1], reverse=True)[:3]
    cat_text = ", ".join([f"{c}(기회지수 {s:,})" for c, s in top3])

    return [
        ConsultingAdvice(
            title="고기회 카테고리 진출 추천",
            category="product",
            priority="medium",
            current_value=f"현재 {len(current_cats)}개 카테고리",
            target_value=f"+{min(3, len(top3))}개 카테고리 확장",
            description=(
                f"미진출 고기회 카테고리가 있습니다: {cat_text}. "
                "이 카테고리들은 높은 수요와 매출 잠재력을 가지고 있어 "
                "효과적인 매출 확대 수단이 될 수 있습니다."
            ),
            actions=[
                f"{top3[0][0]} 카테고리 3-5종 시범 등록",
                "소량 재고로 시작하여 수요 검증 후 확대",
                "기존 베스트셀러와 번들 상품 구성",
            ],
            expected_effect="신규 카테고리 1개 추가 시 매출 10-25% 증가 기대",
        )
    ]


def _rule_price_optimization(m: SellerMetrics) -> list[ConsultingAdvice]:
    """규칙 8: 가격 최적화 — 볼륨존 분석."""
    if m.avg_price <= 0:
        return []
    # 볼륨존: R$30-100
    if 30 <= m.avg_price <= 100:
        return []  # 이미 볼륨존

    if m.avg_price < 30:
        return [
            ConsultingAdvice(
                title="가격대 상향 검토",
                category="pricing",
                priority="low",
                current_value=f"R${m.avg_price:.0f}",
                target_value="R$30-100 (메인 볼륨존)",
                description=(
                    f"현재 평균 단가 R${m.avg_price:.0f}는 "
                    "저가 구간에 위치합니다. 메인 볼륨존(R$30-100)은 "
                    "전체 거래의 45%를 차지하며, 수익성과 볼륨을 동시에 "
                    "확보할 수 있는 최적 구간입니다."
                ),
                actions=[
                    "번들 상품 구성으로 객단가 상향",
                    "프리미엄 옵션 추가 (세트, 기프트 포장 등)",
                    "R$30-100 구간 상품 라인업 추가",
                ],
                expected_effect="객단가 2배 향상 시 동일 주문 수로 매출 2배",
            )
        ]
    else:
        return [
            ConsultingAdvice(
                title="중저가 라인 추가로 볼륨 확대",
                category="pricing",
                priority="low",
                current_value=f"R${m.avg_price:.0f}",
                target_value="R$30-100 라인 추가",
                description=(
                    f"현재 평균 단가 R${m.avg_price:.0f}는 고가 구간입니다. "
                    "메인 볼륨존(R$30-100) 상품을 추가하면 "
                    "고객 유입을 늘리고 교차판매로 전체 매출을 높일 수 있습니다."
                ),
                actions=[
                    "R$30-100 구간 엔트리 상품 기획",
                    "기존 고가 상품의 소용량/분할 버전 출시",
                    "번들 할인으로 고가 + 중저가 교차판매",
                ],
                expected_effect="볼륨존 진입 시 주문수 2-3배 증가 가능",
            )
        ]


def _rule_delivery_warning(m: SellerMetrics) -> list[ConsultingAdvice]:
    """규칙 9: 배송일 경고 (>20일)."""
    if m.avg_delivery_days <= 20 or m.avg_delivery_days == 0:
        return []
    return [
        ConsultingAdvice(
            title="배송일 과다 — 재구매율 급락 위험",
            category="delivery",
            priority="high",
            current_value=f"{m.avg_delivery_days:.1f}일",
            target_value="14일 이내",
            description=(
                f"평균 배송 {m.avg_delivery_days:.1f}일은 매우 긴 수준입니다. "
                f"21일 초과 시 재구매율이 {DELIVERY_REPURCHASE['over_21']:.1%}로 "
                f"급락하며, 이는 7일 이내 배송({DELIVERY_REPURCHASE['under_7']:.1%}) "
                "대비 1/4 수준입니다."
            ),
            actions=[
                "주요 고객 밀집 지역 근처 물류 거점 확보",
                "소형 경량 상품 위주로 빠른 배송 가능 라인업 구성",
                "물류 파트너 재검토 (2-3곳 비교 견적)",
                "같은 지역(SP, RJ) 고객 우선 타겟으로 배송 시간 단축",
            ],
            expected_effect=(
                "배송일 20일→14일 단축 시 재구매율 2배 향상, "
                "리뷰 점수 0.3-0.5점 개선"
            ),
        )
    ]


def _rule_low_review_diagnosis(m: SellerMetrics) -> list[ConsultingAdvice]:
    """규칙 10: 저평가 원인 분석 (배송 vs 상품 품질 구분)."""
    if m.avg_review >= 3.5 or m.avg_review <= 0:
        return []
    if m.low_review_pct < 0.20:
        return []

    # 배송 문제인지 상품 문제인지 진단
    is_delivery_issue = m.late_delivery_pct > 0.15 or m.avg_delivery_days > 18
    if is_delivery_issue:
        cause = "배송"
        desc = (
            f"저평가의 주요 원인은 배송 문제로 추정됩니다. "
            f"지연율 {m.late_delivery_pct:.1%}, 평균 배송일 {m.avg_delivery_days:.1f}일이 "
            "리뷰 하락의 핵심 요인입니다."
        )
        actions = [
            "예상 배송일을 현재보다 3-5일 여유있게 재설정 (기대치 관리)",
            "지연 주문 발생 시 고객에게 사전 안내",
            "물류 파트너 변경 또는 다중 물류 체계 구축",
        ]
    else:
        cause = "상품 품질/기대치"
        desc = (
            f"배송은 양호하나 저평가 비율이 {m.low_review_pct:.0%}로 높습니다. "
            "상품 품질 또는 고객 기대치 불일치가 원인으로 추정됩니다."
        )
        actions = [
            "상품 설명을 정확하고 상세하게 개선 (과장 금지)",
            "사진에 실제 크기, 소재, 색상을 명확히 표시",
            "포장 품질 개선 (파손 방지, 깔끔한 포장)",
            "반품/교환 정책 명시로 고객 신뢰 확보",
        ]

    return [
        ConsultingAdvice(
            title=f"저평가 원인 진단: {cause} 문제",
            category="review",
            priority="critical",
            current_value=f"저평가 비율 {m.low_review_pct:.0%}",
            target_value="10% 이하",
            description=desc,
            actions=actions,
            expected_effect="저평가 비율 절반 감소 시 평균 리뷰 0.5-1.0점 개선",
        )
    ]


def _rule_cancel_rate(m: SellerMetrics) -> list[ConsultingAdvice]:
    """규칙 11: 취소율 높음 (>2%)."""
    if m.cancel_rate <= 0.02:
        return []
    return [
        ConsultingAdvice(
            title="주문 취소율 관리 필요",
            category="delivery",
            priority="high" if m.cancel_rate > 0.05 else "medium",
            current_value=f"{m.cancel_rate:.1%} ({m.cancel_count}건)",
            target_value="2% 이하",
            description=(
                f"주문 취소/미배송 비율이 {m.cancel_rate:.1%}로 높습니다. "
                "취소율이 높으면 플랫폼 내 셀러 평판에 부정적 영향을 미치고, "
                "노출 순위 하락으로 이어질 수 있습니다."
            ),
            actions=[
                "재고 관리 시스템 점검 — 품절 상품 즉시 비활성화",
                "주문 접수 후 24시간 내 발송 프로세스 확립",
                "취소 사유 분석 (재고 부족 vs 고객 변심 vs 배송 문제)",
                "자동 재고 알림 설정으로 품절 방지",
            ],
            expected_effect="취소율 절반 감소 시 플랫폼 노출도 향상, 전환율 개선",
        )
    ]


def _rule_repeat_customer(m: SellerMetrics) -> list[ConsultingAdvice]:
    """규칙 12: 재구매율 낮음."""
    if m.unique_customers < 10 or m.repeat_customer_rate >= 0.03:
        return []
    return [
        ConsultingAdvice(
            title="재구매 고객 확보 전략 필요",
            category="growth",
            priority="medium",
            current_value=f"{m.repeat_customer_rate:.1%} ({m.repeat_customer_count}명)",
            target_value="3% 이상",
            description=(
                f"재구매 고객 비율이 {m.repeat_customer_rate:.1%}로 낮습니다. "
                "신규 고객 획득 비용은 기존 고객 유지 비용의 5-7배입니다. "
                "재구매율 향상은 안정적 매출 성장의 핵심입니다."
            ),
            actions=[
                "포장에 브랜드 카드/쿠폰 동봉으로 재구매 유도",
                "상품 번들/세트 구성으로 추가 구매 촉진",
                "베스트셀러 상품군 확대로 고객 재방문 유도",
                "배송 품질 개선으로 고객 만족도 향상",
            ],
            expected_effect="재구매율 1%p 향상 시 매출 안정성 대폭 개선",
        )
    ]


def _rule_review_keyword_insight(m: SellerMetrics) -> list[ConsultingAdvice]:
    """규칙 13: 리뷰 키워드 기반 구체적 개선 조언."""
    rka = m.review_keyword_analysis
    if not rka or not rka.get("issue_counts"):
        return []

    primary = rka.get("primary_issue")
    if not primary:
        return []

    analyzed = rka.get("analyzed_count", 0)
    if analyzed == 0:
        return []

    issue_count = rka["issue_counts"].get(primary, 0)
    pct = issue_count / analyzed

    # 주요 이슈가 리뷰의 20% 이상일 때만
    if pct < 0.20:
        return []

    actions_map = {
        "배송 지연": [
            "예상 배송일을 보수적으로 재설정 (실제 배송일 + 3일)",
            "발송 지연 시 고객에게 선제적 메시지 발송",
            "고객 밀집 지역 근처 물류 거점 활용",
        ],
        "상품 품질": [
            "반복 불만 상품 품질 검수 강화",
            "공급처 변경 또는 품질 기준 재협의",
            "불량률 높은 상품 리스트업 및 개선/제거",
        ],
        "포장 문제": [
            "파손 방지 포장재 업그레이드 (에어캡, 완충재)",
            "깨지기 쉬운 상품 별도 포장 프로세스 도입",
            "포장 가이드라인 수립 및 준수",
        ],
        "기대 불일치": [
            "상품 설명/사이즈/색상 정보 정확도 재점검",
            "실제 사진 위주로 상품 이미지 교체",
            "상품 상세페이지에 실측 사진 및 비교 이미지 추가",
        ],
    }

    return [
        ConsultingAdvice(
            title=f"리뷰 분석: '{primary}' 이슈 집중 개선",
            category="review",
            priority="high",
            current_value=f"텍스트 리뷰 {analyzed}건 중 {issue_count}건 ({pct:.0%})",
            target_value=f"{primary} 관련 불만 50% 감소",
            description=(
                f"리뷰 텍스트 분석 결과, **{primary}**이 가장 빈번한 "
                f"이슈로 나타났습니다 ({issue_count}건, {pct:.0%}). "
                "이 이슈를 집중 개선하면 리뷰 점수와 고객 만족도를 "
                "효과적으로 높일 수 있습니다."
            ),
            actions=actions_map.get(primary, ["해당 이슈의 근본 원인 분석 및 개선"]),
            expected_effect=f"{primary} 이슈 절반 감소 시 리뷰 0.3-0.5점 개선 기대",
        )
    ]


def identify_strengths_weaknesses(
    metrics: SellerMetrics,
) -> tuple[list[tuple[str, float, float]], list[tuple[str, float, float]]]:
    """Top Performer 대비 상위 3 / 하위 3 지표 식별.

    Returns:
        (strengths, weaknesses) 각각 (metric_name, seller_value, top_value) 튜플 리스트
    """
    top = CLUSTER_BENCHMARKS[0]
    comparisons = {
        "total_orders": (metrics.total_orders, top["total_orders"]),
        "total_revenue": (metrics.total_revenue, top["total_revenue"]),
        "avg_price": (metrics.avg_price, top["avg_price"]),
        "product_variety": (metrics.product_variety, top["product_variety"]),
        "avg_review": (metrics.avg_review, top["avg_review"]),
        "unique_customers": (metrics.unique_customers, top["unique_customers"]),
    }

    # 비율 계산 (셀러/Top Performer)
    ratios = []
    for name, (seller_val, top_val) in comparisons.items():
        if top_val > 0:
            ratio = seller_val / top_val
        else:
            ratio = 0
        ratios.append((name, seller_val, top_val, ratio))

    # 높을수록 강점
    ratios.sort(key=lambda x: x[3], reverse=True)
    strengths = [(r[0], r[1], r[2]) for r in ratios[:3]]
    weaknesses = [(r[0], r[1], r[2]) for r in ratios[-3:]]

    # 낮을수록 좋은 지표 추가 확인
    lower_better = {
        "avg_delivery_days": (
            metrics.avg_delivery_days,
            top["avg_delivery_days"],
        ),
        "late_delivery_pct": (
            metrics.late_delivery_pct,
            top["late_delivery_pct"],
        ),
        "low_review_pct": (metrics.low_review_pct, top["low_review_pct"]),
    }
    for name, (seller_val, top_val) in lower_better.items():
        if top_val > 0 and seller_val > 0:
            ratio = top_val / seller_val  # 역수 (낮을수록 좋으니)
            if ratio > 1.2:  # Top Performer보다 20% 이상 좋으면 강점
                strengths.append((name, seller_val, top_val))
            elif ratio < 0.5:  # Top Performer보다 2배 이상 나쁘면 약점
                weaknesses.append((name, seller_val, top_val))

    return strengths[:3], weaknesses[:3]


def generate_growth_roadmap(
    metrics: SellerMetrics,
) -> list[dict]:
    """단기/중기/장기 성장 로드맵 생성."""
    roadmap = []

    # 단기 (1-3개월)
    phase1 = GROWTH_TARGETS["phase1"]
    short_goals = []
    if metrics.avg_review < phase1["avg_review"] and metrics.avg_review > 0:
        short_goals.append(
            f"리뷰 점수 {metrics.avg_review:.1f} → {phase1['avg_review']}점 개선"
        )
    if metrics.late_delivery_pct > phase1["late_delivery_pct"]:
        short_goals.append(
            f"배송 지연율 {metrics.late_delivery_pct:.0%} → "
            f"{phase1['late_delivery_pct']:.0%} 이하로 감소"
        )
    if metrics.product_variety < phase1["product_variety"]:
        short_goals.append(
            f"상품 수 {metrics.product_variety} → {phase1['product_variety']}종으로 확대"
        )
    if metrics.avg_photos < phase1["avg_photos"]:
        short_goals.append(f"상품 사진 평균 {phase1['avg_photos']}장 이상 등록")
    if not short_goals:
        short_goals.append("현재 성과 유지 및 안정화")
    roadmap.append({
        "phase": "단기 (1-3개월)",
        "label": phase1["label"],
        "goals": short_goals,
    })

    # 중기 (3-6개월)
    phase2 = GROWTH_TARGETS["phase2"]
    mid_goals = []
    if metrics.total_orders < phase2["total_orders"]:
        mid_goals.append(
            f"월 주문수 {phase2['total_orders']}건 달성"
        )
    if metrics.avg_review < phase2["avg_review"] and metrics.avg_review > 0:
        mid_goals.append(f"리뷰 {phase2['avg_review']}점 이상 달성")
    if metrics.product_variety < phase2["product_variety"]:
        mid_goals.append(f"상품 라인업 {phase2['product_variety']}종 확대")
    mid_goals.append(f"매출 R${phase2['total_revenue']:,} 목표")
    roadmap.append({
        "phase": "중기 (3-6개월)",
        "label": phase2["label"],
        "goals": mid_goals,
    })

    # 장기 (6-12개월)
    phase3 = GROWTH_TARGETS["phase3"]
    long_goals = [
        f"총 주문수 {phase3['total_orders']}건 (Top Performer 수준)",
        f"리뷰 {phase3['avg_review']}점 이상 유지",
        f"상품 {phase3['product_variety']}종 운영",
        f"매출 R${phase3['total_revenue']:,} 달성",
        f"지연율 {phase3['late_delivery_pct']:.0%} 이하 유지",
    ]
    roadmap.append({
        "phase": "장기 (6-12개월)",
        "label": phase3["label"],
        "goals": long_goals,
    })

    return roadmap
