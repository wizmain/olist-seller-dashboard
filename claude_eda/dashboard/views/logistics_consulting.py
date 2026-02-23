"""Page 5: 물류 최적화 컨설팅."""

from __future__ import annotations

import streamlit as st

from claude_eda.dashboard.components.charts import (
    logistics_map,
    logistics_savings_bar,
    logistics_scenario_bar,
    region_effect_bar,
    warehouse_ranking_bar,
)
from claude_eda.dashboard.config import COLORS
from claude_eda.dashboard.data.logistics_analyzer import compute_seller_logistics
from claude_eda.dashboard.data.preprocessor import SellerMetrics
from claude_eda.dashboard.utils.formatting import fmt_currency, fmt_days, fmt_pct_value
from claude_eda.dashboard.utils.korean import STATE_NAMES_KR


def render_logistics_consulting(metrics: SellerMetrics) -> None:
    """물류 최적화 컨설팅 페이지 렌더."""
    # 헤더
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #1565C0 0%, #0D47A1 50%, #01579B 100%);
             padding: 20px 24px; border-radius: 8px; margin-bottom: 16px;">
            <h2 style="color: white; margin: 0 0 8px 0;">물류 최적화 컨설팅</h2>
            <span style="color: rgba(255,255,255,0.85); font-size: 0.95em;">
                셀러 <code style="background: rgba(255,255,255,0.2); color: white;
                padding: 2px 6px; border-radius: 4px;">{metrics.company_name or metrics.seller_id[:12]}</code>
                &nbsp;&nbsp;|&nbsp;&nbsp;
                지역: <b>{STATE_NAMES_KR.get(metrics.seller_state, metrics.seller_state)}</b>
                &nbsp;&nbsp;|&nbsp;&nbsp;
                Olist 물류 거점을 활용한 배송 효율화 전략
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.spinner("물류 데이터 분석 중..."):
        logi = compute_seller_logistics(metrics.seller_id)

    if logi["seller_lat"] is None:
        st.warning("이 셀러의 위치 데이터(geolocation)를 찾을 수 없어 물류 분석이 불가합니다.")
        return

    if logi["customer_points"].empty:
        st.warning("이 셀러의 배송 완료 주문이 없어 물류 분석이 불가합니다.")
        return

    # === 섹션 1: 물류 현황 진단 ===
    _render_logistics_status(metrics, logi)

    st.write("")

    # === 섹션 2: Olist 추천 창고 & 지도 ===
    _render_warehouse_recommendation(logi)

    st.write("")

    # === 섹션 3: 비용-효과 시뮬레이션 ===
    _render_simulation(logi)

    st.write("")

    # === 섹션 4: 맞춤 액션 플랜 ===
    _render_action_plan(metrics, logi)


def _section_header(title: str, icon: str, description: str) -> None:
    st.markdown(
        f"""
        <div style="border-bottom: 2px solid #e0e0e0; padding-bottom: 8px; margin: 24px 0 16px 0;">
            <h3 style="margin: 0; color: #333;">{icon} {title}</h3>
            <span style="color: #777; font-size: 0.85em;">{description}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ================================================================
# 섹션 1: 물류 현황 진단
# ================================================================

def _render_logistics_status(metrics: SellerMetrics, logi: dict) -> None:
    _section_header(
        "셀러 물류 현황 진단",
        "📦",
        "현재 배송 거리, 운임, 배송일을 플랫폼 평균과 비교합니다",
    )

    # KPI 카드 — 셀러 vs 플랫폼 평균
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        delta_dist = logi["avg_distance"] - logi["platform_avg_distance"]
        st.metric(
            "평균 배송 거리",
            f"{logi['avg_distance']:.0f}km",
            delta=f"{delta_dist:+.0f}km (vs 평균)",
            delta_color="inverse",
        )
    with c2:
        delta_freight = logi["avg_freight"] - logi["platform_avg_freight"]
        st.metric(
            "평균 운임",
            fmt_currency(logi["avg_freight"]),
            delta=f"R${delta_freight:+.1f} (vs 평균)",
            delta_color="inverse",
        )
    with c3:
        delta_days = logi["avg_delivery_days"] - logi["platform_avg_delivery_days"]
        st.metric(
            "평균 배송일",
            fmt_days(logi["avg_delivery_days"]),
            delta=f"{delta_days:+.1f}일 (vs 평균)",
            delta_color="inverse",
        )
    with c4:
        st.metric(
            "배송 지연율",
            fmt_pct_value(logi["late_pct"] * 100),
            delta=f"{(logi['late_pct'] - 0.079) * 100:+.1f}%p (vs 평균)",
            delta_color="inverse",
        )

    # 진단 메시지
    if logi["avg_distance"] > logi["platform_avg_distance"] * 1.3:
        st.error(
            f"이 셀러의 평균 배송 거리({logi['avg_distance']:.0f}km)는 "
            f"플랫폼 평균({logi['platform_avg_distance']:.0f}km) 대비 "
            f"**{logi['avg_distance']/logi['platform_avg_distance']:.1f}배**로, "
            f"물류 거점 활용이 강력히 권장됩니다."
        )
    elif logi["avg_distance"] > logi["platform_avg_distance"]:
        st.warning(
            f"평균 배송 거리({logi['avg_distance']:.0f}km)가 "
            f"플랫폼 평균({logi['platform_avg_distance']:.0f}km)보다 높습니다. "
            f"창고 활용 시 배송 효율 개선이 가능합니다."
        )
    else:
        st.success(
            f"평균 배송 거리({logi['avg_distance']:.0f}km)가 "
            f"플랫폼 평균({logi['platform_avg_distance']:.0f}km) 이하입니다. "
            f"물류 효율이 양호하나, 원거리 고객 확대 시 창고 활용을 검토하세요."
        )


# ================================================================
# 섹션 2: Olist 추천 창고 & 지도
# ================================================================

def _render_warehouse_recommendation(logi: dict) -> None:
    _section_header(
        "Olist 추천 물류 거점",
        "🏭",
        "Olist가 데이터 기반으로 도출한 5개 최적 창고 위치와 셀러에게 유리한 순위를 보여줍니다",
    )

    col_l, col_r = st.columns([3, 2])

    with col_l:
        fig = logistics_map(
            logi["seller_lat"], logi["seller_lng"], logi["seller_state"],
            logi["customer_points"], logi["warehouse_recs"],
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        fig = warehouse_ranking_bar(logi["warehouse_recs"])
        st.plotly_chart(fig, use_container_width=True)

    # 최적 창고 하이라이트
    best = logi["best_warehouse"]
    if best:
        state_kr = STATE_NAMES_KR.get(best["state"], best["state"])
        st.markdown(
            f"""
            <div style="border-left: 4px solid {COLORS['success']}; padding: 14px 18px;
                 background: #f0faf0; border-radius: 4px; margin: 8px 0 16px 0;">
                <h4 style="margin: 0 0 8px 0; color: #2e7d32;">
                    최적 추천: WH{best['id']} — {best['city'].title()}, {state_kr} ({best['state']})
                </h4>
                <div style="display: flex; gap: 32px; font-size: 0.95em; color: #333;">
                    <div>
                        <span style="color: #777;">셀러→창고</span><br>
                        <b>{best['seller_to_wh_km']:.0f}km</b>
                    </div>
                    <div>
                        <span style="color: #777;">고객→창고 평균</span><br>
                        <b>{best['customer_to_wh_km']:.0f}km</b>
                    </div>
                    <div>
                        <span style="color: #777;">거리 감소</span><br>
                        <b style="color: #2e7d32;">{best['reduction_km']:.0f}km (↓{best['reduction_pct']:.0f}%)</b>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 창고 상세 테이블
    wh = logi["warehouse_recs"]
    if not wh.empty:
        with st.expander("전체 창고 상세 정보", expanded=False):
            display_df = wh[["warehouse_id", "nearest_city", "state", "region", "priority",
                             "seller_to_wh_km", "customer_to_wh_km",
                             "distance_reduction_km", "reduction_pct"]].copy()
            display_df.columns = [
                "창고 ID", "도시", "주", "권역", "우선순위",
                "셀러→창고(km)", "고객→창고(km)", "거리 감소(km)", "감소율(%)",
            ]
            display_df["셀러→창고(km)"] = display_df["셀러→창고(km)"].round(0).astype(int)
            display_df["고객→창고(km)"] = display_df["고객→창고(km)"].round(0).astype(int)
            display_df["거리 감소(km)"] = display_df["거리 감소(km)"].round(0).astype(int)
            st.dataframe(display_df, use_container_width=True, hide_index=True)


# ================================================================
# 섹션 3: 비용-효과 시뮬레이션
# ================================================================

def _render_simulation(logi: dict) -> None:
    _section_header(
        "비용-효과 시뮬레이션",
        "📊",
        "현재 직배 대비 창고 활용 시 거리/운임/배송일 절감 효과를 시뮬레이션합니다",
    )

    sim = logi["simulation"]

    col_l, col_r = st.columns(2)
    with col_l:
        fig = logistics_scenario_bar(sim)
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        fig = logistics_savings_bar(sim)
        st.plotly_chart(fig, use_container_width=True)

    # 권역별 효과
    col_l2, col_r2 = st.columns(2)
    with col_l2:
        fig = region_effect_bar(logi["region_effect"])
        st.plotly_chart(fig, use_container_width=True)

    with col_r2:
        # 시나리오 요약 테이블
        if sim:
            st.markdown("**시나리오별 상세 비교**")
            rows = []
            current = sim[0]
            for s in sim:
                dist_pct = (1 - s["avg_distance"] / current["avg_distance"]) * 100 if current["avg_distance"] > 0 else 0
                rows.append({
                    "시나리오": s["scenario"].replace("\n", " "),
                    "평균 거리": f'{s["avg_distance"]:.0f}km',
                    "감소율": f'{dist_pct:.0f}%' if dist_pct > 0 else "-",
                    "예상 운임": f'R${s["est_freight"]:.1f}',
                    "예상 배송일": f'{s["est_days"]:.1f}일',
                })
            import pandas as pd
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ================================================================
# 섹션 4: 맞춤 액션 플랜
# ================================================================

def _render_action_plan(metrics: SellerMetrics, logi: dict) -> None:
    _section_header(
        "맞춤 물류 액션 플랜",
        "🎯",
        "셀러의 현재 상황에 맞는 물류 최적화 전략을 제안합니다",
    )

    best = logi["best_warehouse"]
    sim = logi["simulation"]

    if not best or not sim:
        st.info("물류 데이터가 부족하여 액션 플랜을 생성할 수 없습니다.")
        return

    current = sim[0]
    best_sim = sim[-1]  # 5개 창고
    freight_save = current["est_freight"] - best_sim["est_freight"]
    days_save = current["est_days"] - best_sim["est_days"]

    # 긴급도 판단
    if logi["avg_distance"] > 800:
        urgency = "high"
        urgency_label = "높음"
        urgency_color = COLORS["danger"]
    elif logi["avg_distance"] > 500:
        urgency = "medium"
        urgency_label = "보통"
        urgency_color = COLORS["warning"]
    else:
        urgency = "low"
        urgency_label = "낮음"
        urgency_color = COLORS["success"]

    state_kr = STATE_NAMES_KR.get(best["state"], best["state"])

    # 액션 플랜 카드
    st.markdown(
        f"""
        <div style="border: 2px solid {urgency_color}; border-radius: 8px; padding: 20px;
             background: white; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center;
                 margin-bottom: 16px;">
                <h4 style="margin: 0; color: #333;">물류 최적화 긴급도</h4>
                <span style="background: {urgency_color}; color: white; padding: 4px 12px;
                      border-radius: 12px; font-weight: 600;">{urgency_label}</span>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px;">
                <div style="text-align: center; padding: 12px; background: #f8f9fa; border-radius: 6px;">
                    <div style="font-size: 0.8em; color: #777;">현재 평균 거리</div>
                    <div style="font-size: 1.5em; font-weight: 700; color: #333;">
                        {logi['avg_distance']:.0f}km</div>
                </div>
                <div style="text-align: center; padding: 12px; background: #e8f5e9; border-radius: 6px;">
                    <div style="font-size: 0.8em; color: #777;">창고 활용 시</div>
                    <div style="font-size: 1.5em; font-weight: 700; color: #2e7d32;">
                        {best_sim['avg_distance']:.0f}km</div>
                </div>
                <div style="text-align: center; padding: 12px; background: #e3f2fd; border-radius: 6px;">
                    <div style="font-size: 0.8em; color: #777;">예상 절감</div>
                    <div style="font-size: 1.5em; font-weight: 700; color: #1565c0;">
                        ↓{(1 - best_sim['avg_distance']/logi['avg_distance'])*100:.0f}%</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 단계별 액션
    actions = []

    # Phase 1: 즉시 실행
    phase1_actions = [
        f"**{best['city'].title()}, {state_kr}** 창고(WH{best['id']}) 입고 신청",
        f"고객→창고 평균 거리 {best['customer_to_wh_km']:.0f}km — "
        f"현재 대비 **{best['reduction_pct']:.0f}% 거리 감소**",
    ]
    if logi["late_pct"] > 0.10:
        phase1_actions.append(
            f"배송 지연율 {logi['late_pct']*100:.1f}% → 창고 활용으로 지연 감소 기대"
        )

    actions.append({
        "phase": "Phase 1: 즉시 실행",
        "label": "최근접 창고 활용 시작",
        "color": "#1f77b4",
        "icon": "1️⃣",
        "goals": phase1_actions,
    })

    # Phase 2: 확장
    re = logi["region_effect"]
    if len(re) > 1:
        top_region = re.iloc[0]
        phase2_actions = [
            f"주요 고객 권역({top_region['region']})에 가까운 추가 창고 활용 검토",
            f"3개 창고 활용 시 평균 거리 {sim[2]['avg_distance']:.0f}km — "
            f"건당 운임 R${current['est_freight'] - sim[2]['est_freight']:.1f} 절감",
        ]
    else:
        phase2_actions = ["고객 분포 확대에 따라 추가 창고 활용 검토"]

    if metrics.total_orders >= 50:
        monthly_savings = freight_save * (metrics.total_orders / max(metrics.active_months, 1))
        phase2_actions.append(
            f"월간 운임 절감 추정: **R${monthly_savings:.0f}** "
            f"(주문 {metrics.total_orders / max(metrics.active_months, 1):.0f}건/월 기준)"
        )

    actions.append({
        "phase": "Phase 2: 3개월 후",
        "label": "다중 창고 네트워크 최적화",
        "color": "#ff7f0e",
        "icon": "2️⃣",
        "goals": phase2_actions,
    })

    # Phase 3: 고도화
    phase3_actions = [
        f"5개 창고 전체 활용 시 평균 거리 {best_sim['avg_distance']:.0f}km, "
        f"배송일 {best_sim['est_days']:.1f}일 달성",
        "리뷰 점수 개선 → 거리 감소에 따른 배송 만족도 상승 기대",
        "원거리 지역(North, Northeast) 고객 확대 기회 확보",
    ]
    actions.append({
        "phase": "Phase 3: 6개월 후",
        "label": "전국 커버리지 완성",
        "color": "#2ca02c",
        "icon": "3️⃣",
        "goals": phase3_actions,
    })

    # 로드맵 렌더링
    for action in actions:
        st.markdown(
            f"""
            <div style="border-left: 3px solid {action['color']}; padding: 10px 16px;
                 margin-bottom: 8px; background-color: #fafafa; border-radius: 4px;">
                <h4 style="margin: 0;">{action['icon']} {action['phase']}: {action['label']}</h4>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for goal in action["goals"]:
            st.markdown(f"  - {goal}")
        st.write("")

    # 참고 사항
    st.markdown(
        """
        <div style="background: #fff3e0; border-radius: 6px; padding: 12px 16px;
             margin-top: 8px; font-size: 0.85em; color: #e65100;">
            <b>참고:</b> 운임/배송일 절감은 거리-운임(R$0.0104/km), 거리-배송일(0.006일/km)
            선형 회귀 모델 기반 추정치입니다. 실제 효과는 상품 무게/부피, 운송사, 계절 등에 따라 달라질 수 있습니다.
        </div>
        """,
        unsafe_allow_html=True,
    )
