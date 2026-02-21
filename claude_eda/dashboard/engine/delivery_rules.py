"""배송·재고 컨설팅 규칙 엔진."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DeliveryAdvice:
    """배송·재고 컨설팅 조언 단위."""

    title: str
    category: str  # dispatch, delivery, seasonal, inventory
    priority: str  # critical, high, medium, low
    current_value: str = ""
    target_value: str = ""
    description: str = ""
    actions: list[str] = field(default_factory=list)
    expected_effect: str = ""


def generate_delivery_advice(
    delivery: dict, inventory: dict
) -> list[DeliveryAdvice]:
    """배송·재고 분석 결과를 바탕으로 맞춤형 조언을 생성한다."""
    advices: list[DeliveryAdvice] = []

    if delivery.get("has_data"):
        advices.extend(_rule_dispatch_delay(delivery))
        advices.extend(_rule_delivery_delay(delivery))
        advices.extend(_rule_seasonal_risk(delivery))
        advices.extend(_rule_transit_slow(delivery))
        advices.extend(_rule_review_impact(delivery))

    if inventory.get("has_data"):
        advices.extend(_rule_reorder_alert(inventory))
        advices.extend(_rule_inventory_utilization(inventory))

    # 우선순위 정렬
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    advices.sort(key=lambda a: priority_order.get(a.priority, 99))
    return advices


def generate_delivery_roadmap(
    delivery: dict, inventory: dict
) -> list[dict]:
    """90일 로드맵을 생성한다."""
    phases = []

    # Phase 1: 즉시 (0~30일)
    immediate_actions = []
    if delivery.get("has_data"):
        if delivery.get("dispatch_delay_rate", 0) > 0.1:
            immediate_actions.append("발송 프로세스 점검 — 주문 접수 후 24시간 내 발송 체계 구축")
        if delivery.get("delivery_delay_rate", 0) > 0.1:
            immediate_actions.append("배송 지연 주문 원인 분석 — 발송 지연 vs 운송 지연 구분")

    if inventory.get("has_data"):
        alerts = inventory.get("reorder_alerts")
        if alerts is not None and len(alerts) > 0:
            critical = alerts[alerts["urgency"] == "critical"] if "urgency" in alerts.columns else alerts
            immediate_actions.append(
                f"재고 긴급 보충 — 발주점 이하 상품 {len(alerts)}개 중 "
                f"안전재고 이하 {len(critical)}개 즉시 발주"
            )

    if not immediate_actions:
        immediate_actions.append("현재 배송 성과 모니터링 체계 수립")

    phases.append({
        "phase": "Phase 1: 즉시 개선 (0~30일)",
        "icon": "🔴",
        "actions": immediate_actions,
    })

    # Phase 2: 중기 (30~60일)
    mid_actions = []
    if delivery.get("has_data"):
        season_stats = delivery.get("season_stats", {})
        rainy = season_stats.get("우기", {})
        if rainy.get("delivery_delay_rate", 0) > 0.1:
            mid_actions.append("우기 대비 전략 — 우기 시작 2주 전 주요 상품 재고 30% 증량")
            mid_actions.append("운송 경로 다변화 — 보조 창고 활용으로 우기 운송 리스크 분산")

    if inventory.get("has_data") and inventory.get("primary_info"):
        mid_actions.append(
            f"창고 활용 최적화 — {inventory['primary_info'].get('warehouse_name', '')} "
            f"기반 입출고 효율화"
        )

    if not mid_actions:
        mid_actions.append("배송 데이터 기반 예측 모델 구축")

    phases.append({
        "phase": "Phase 2: 계절 대비 (30~60일)",
        "icon": "🟡",
        "actions": mid_actions,
    })

    # Phase 3: 장기 (60~90일)
    long_actions = []
    if inventory.get("has_data"):
        long_actions.append("자동 발주 시스템 운영 — 발주점 기반 자동 재발주 프로세스 가동")
        if inventory.get("secondary_warehouse"):
            long_actions.append(
                f"보조 창고({inventory['secondary_warehouse']}) 활용 확대 — "
                "이원화 재고 관리로 배송 안정성 확보"
            )

    if delivery.get("has_data"):
        long_actions.append("분기별 배송 성과 리뷰 — 계절별 KPI 목표 재설정")

    if not long_actions:
        long_actions.append("장기 물류 파트너십 및 재고 전략 수립")

    phases.append({
        "phase": "Phase 3: 장기 최적화 (60~90일)",
        "icon": "🟢",
        "actions": long_actions,
    })

    return phases


# ─── 개별 규칙 ────────────────────────────────────────────────

def _rule_dispatch_delay(d: dict) -> list[DeliveryAdvice]:
    rate = d.get("dispatch_delay_rate", 0)
    platform = d.get("platform_dispatch_delay_rate", 0.09)
    if rate <= platform:
        return []

    if rate > 0.2:
        priority = "critical"
    elif rate > 0.1:
        priority = "high"
    else:
        priority = "medium"

    return [DeliveryAdvice(
        title="발송 지연율 개선 필요",
        category="dispatch",
        priority=priority,
        current_value=f"{rate:.1%}",
        target_value=f"{platform:.1%} (플랫폼 평균) 이하",
        description=(
            f"셀러의 발송 지연율({rate:.1%})이 플랫폼 평균({platform:.1%})보다 높습니다. "
            f"발송 지연은 배송 지연의 핵심 원인이며, 7일+ 지연 시 배송 지연 확률이 64.4%로 급등합니다."
        ),
        actions=[
            "주문 접수 후 24시간 내 발송 목표 설정",
            "재고 부족으로 인한 발송 지연이라면 안전재고 수준 상향",
            "주문 집중 시간대 파악 후 발송 작업 스케줄 최적화",
        ],
        expected_effect=f"발송 지연율 {rate:.1%} → {platform:.1%} 달성 시 배송 지연 약 50% 감소 기대",
    )]


def _rule_delivery_delay(d: dict) -> list[DeliveryAdvice]:
    rate = d.get("delivery_delay_rate", 0)
    platform = d.get("platform_delivery_delay_rate", 0.08)
    if rate <= platform * 1.2:
        return []

    priority = "critical" if rate > 0.2 else "high" if rate > 0.12 else "medium"

    return [DeliveryAdvice(
        title="배송 지연율 경고",
        category="delivery",
        priority=priority,
        current_value=f"{rate:.1%}",
        target_value=f"{platform:.1%} 이하",
        description=(
            f"배송 지연율({rate:.1%})이 플랫폼 평균({platform:.1%})보다 높습니다. "
            "배송 8일+ 지연 시 평균 리뷰가 1.75점으로 급락하며, "
            "고객 만족도에 치명적 영향을 미칩니다."
        ),
        actions=[
            "발송 단계 vs 운송 단계 지연 원인 구분 분석",
            "운송 지연이 원인이면 Olist 추천 창고 활용 검토",
            "예상 배송일을 보수적으로 설정하여 고객 기대치 관리",
        ],
        expected_effect="배송 지연율 50% 감소 시 리뷰 점수 +0.2~0.3점 상승 기대",
    )]


def _rule_seasonal_risk(d: dict) -> list[DeliveryAdvice]:
    season_stats = d.get("season_stats", {})
    rainy = season_stats.get("우기", {})
    dry = season_stats.get("건기", {})

    if not rainy or not dry:
        return []

    rainy_rate = rainy.get("delivery_delay_rate", 0)
    dry_rate = dry.get("delivery_delay_rate", 0)
    diff = rainy_rate - dry_rate

    if diff < 0.03:
        return []

    rainy_transit = rainy.get("avg_transit_days", 0)
    dry_transit = dry.get("avg_transit_days", 0)
    transit_diff = rainy_transit - dry_transit

    priority = "high" if diff > 0.1 else "medium"
    region = d.get("primary_region", "Southeast")

    return [DeliveryAdvice(
        title="우기 배송 지연 리스크",
        category="seasonal",
        priority=priority,
        current_value=f"우기 지연율 {rainy_rate:.1%} (건기 {dry_rate:.1%})",
        target_value=f"우기-건기 격차 {diff:.1%} → 3%p 이내",
        description=(
            f"주 배송 권역({region})에서 우기 배송 지연율({rainy_rate:.1%})이 "
            f"건기({dry_rate:.1%}) 대비 {diff:.1%}p 높습니다. "
            f"운송 소요도 우기 {rainy_transit:.1f}일 vs 건기 {dry_transit:.1f}일로 "
            f"{transit_diff:+.1f}일 차이가 납니다."
        ),
        actions=[
            "우기 시작 2주 전 주요 상품 재고를 근접 창고에 선배치",
            "우기(10~3월) 중 예상 배송일에 3~4일 여유분 추가",
            "보조 창고 활용으로 운송 거리 단축 및 리스크 분산",
        ],
        expected_effect=f"우기 운송 소요 {transit_diff:.1f}일 단축 시 지연율 절반 감소 가능",
    )]


def _rule_transit_slow(d: dict) -> list[DeliveryAdvice]:
    seller_transit = d.get("avg_transit_days", 0)
    platform_transit = d.get("platform_avg_transit_days", 9.0)

    if seller_transit <= platform_transit * 1.3:
        return []

    return [DeliveryAdvice(
        title="운송 소요 시간 과다",
        category="delivery",
        priority="medium",
        current_value=f"{seller_transit:.1f}일",
        target_value=f"{platform_transit:.1f}일 (플랫폼 평균)",
        description=(
            f"평균 운송 소요({seller_transit:.1f}일)가 플랫폼 평균({platform_transit:.1f}일)보다 "
            f"{seller_transit - platform_transit:.1f}일 길며, 배송 권역이 멀거나 "
            "물류 경로가 비효율적일 수 있습니다."
        ),
        actions=[
            "고객 분포 분석 후 가장 가까운 Olist 추천 창고 활용",
            "주요 배송 권역에 분산 재고 배치 검토",
            "물류 최적화 페이지에서 창고 시뮬레이션 확인",
        ],
        expected_effect="창고 활용 시 운송 소요 30~50% 단축 기대",
    )]


def _rule_review_impact(d: dict) -> list[DeliveryAdvice]:
    on_time = d.get("review_on_time")
    delayed = d.get("review_delayed")

    if on_time is None or delayed is None:
        return []

    gap = on_time - delayed
    if gap < 0.3:
        return []

    return [DeliveryAdvice(
        title="발송 지연이 리뷰 점수를 낮추고 있음",
        category="dispatch",
        priority="high" if gap > 0.8 else "medium",
        current_value=f"정시 발송 리뷰 {on_time:.2f}점 vs 지연 발송 리뷰 {delayed:.2f}점",
        target_value=f"격차 {gap:.2f}점 → 0.3점 이내",
        description=(
            f"정시 발송 시 평균 리뷰 {on_time:.2f}점, 지연 발송 시 {delayed:.2f}점으로 "
            f"{gap:.2f}점 차이가 납니다. 발송 지연이 고객 불만의 직접적 원인입니다."
        ),
        actions=[
            "발송 지연 주문의 고객 응대 강화 (배송 안내 메시지 발송)",
            "지연 원인별 대응: 재고 부족 → 안전재고 확보, 작업 지연 → 자동화",
            "정시 발송 인센티브 목표 설정",
        ],
        expected_effect=f"발송 지연 제로화 시 평균 리뷰 +{gap * d.get('dispatch_delay_rate', 0.1):.2f}점 상승 기대",
    )]


def _rule_reorder_alert(inv: dict) -> list[DeliveryAdvice]:
    alerts = inv.get("reorder_alerts")
    if alerts is None or alerts.empty:
        return []

    critical_count = len(alerts[alerts["urgency"] == "critical"]) if "urgency" in alerts.columns else 0
    total_count = len(alerts)

    priority = "critical" if critical_count > 0 else "high"

    return [DeliveryAdvice(
        title="재고 부족 경고 — 즉시 발주 필요",
        category="inventory",
        priority=priority,
        current_value=f"발주점 이하 {total_count}개 상품 (안전재고 이하 {critical_count}개)",
        target_value="모든 상품 발주점 이상 유지",
        description=(
            f"주 이용 창고({inv.get('primary_warehouse', '')})에서 "
            f"{total_count}개 상품이 발주점 이하입니다. "
            f"그 중 {critical_count}개는 안전재고마저 부족하여 "
            "품절 위험이 높습니다."
        ),
        actions=[
            f"안전재고 이하 {critical_count}개 상품 긴급 발주",
            f"발주점 이하 나머지 {total_count - critical_count}개 상품 정기 발주",
            "자동 발주 규칙 활성화로 재고 부족 사전 방지",
        ],
        expected_effect="품절 방지 → 발송 지연 감소 → 배송 지연 감소 → 리뷰 개선",
    )]


def _rule_inventory_utilization(inv: dict) -> list[DeliveryAdvice]:
    items = inv.get("inventory_items")
    if items is None or items.empty:
        return []

    total_on_hand = items["quantity_on_hand"].sum()
    total_reserved = items["quantity_reserved"].sum()
    utilization = total_reserved / total_on_hand if total_on_hand > 0 else 0

    if utilization < 0.5:
        return [DeliveryAdvice(
            title="재고 활용률 점검 필요",
            category="inventory",
            priority="low",
            current_value=f"예약율 {utilization:.1%} ({total_reserved:,}/{total_on_hand:,})",
            target_value="적정 예약율 30~60%",
            description=(
                f"현재 재고 {total_on_hand:,}개 중 출고 예약 {total_reserved:,}개로 "
                f"예약율이 {utilization:.1%}입니다. 과잉 재고가 있을 수 있으며, "
                "보관 비용 최적화를 검토해 보세요."
            ),
            actions=[
                "저회전 상품 식별 후 재고 수준 하향 조정",
                "시즌별 수요 예측 기반 발주량 최적화",
            ],
            expected_effect="과잉 재고 20% 감축 시 보관 비용 절감",
        )]

    return []
