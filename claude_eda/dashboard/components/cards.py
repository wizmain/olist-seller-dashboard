"""KPI 카드, 컨설팅 어드바이스 카드 컴포넌트."""

from __future__ import annotations

import streamlit as st

from claude_eda.dashboard.config import PRIORITY_COLORS
from claude_eda.dashboard.engine.rule_engine import ConsultingAdvice
from claude_eda.dashboard.utils.formatting import (
    fmt_currency,
    fmt_days,
    fmt_number,
    fmt_pct_value,
    fmt_score,
)
from claude_eda.dashboard.utils.korean import PRIORITY_LABELS


def kpi_card_row(metrics) -> None:
    """8개 KPI 카드를 2행 4열로 표시."""
    row1 = st.columns(4)
    with row1[0]:
        st.metric("총 매출", fmt_currency(metrics.total_revenue))
    with row1[1]:
        st.metric("총 주문수", fmt_number(metrics.total_orders))
    with row1[2]:
        st.metric("고유 고객수", fmt_number(metrics.unique_customers))
    with row1[3]:
        st.metric(
            "평균 리뷰",
            fmt_score(metrics.avg_review),
            delta=f"{metrics.avg_review - 3.89:.2f}" if metrics.avg_review > 0 else None,
            delta_color="normal",
        )

    row2 = st.columns(4)
    with row2[0]:
        st.metric("평균 배송일", fmt_days(metrics.avg_delivery_days))
    with row2[1]:
        st.metric(
            "배송 지연율",
            fmt_pct_value(metrics.late_delivery_pct * 100),
            delta=f"{(metrics.late_delivery_pct - 0.07) * 100:.1f}%p" if metrics.late_delivery_pct > 0 else None,
            delta_color="inverse",
        )
    with row2[2]:
        st.metric("상품 종류", fmt_number(metrics.product_variety))
    with row2[3]:
        st.metric("평균 단가", fmt_currency(metrics.avg_price))


def advice_card(advice: ConsultingAdvice) -> None:
    """우선순위별 색상 코딩 컨설팅 카드."""
    color = PRIORITY_COLORS.get(advice.priority, "#1f77b4")
    priority_label = PRIORITY_LABELS.get(advice.priority, advice.priority)

    st.markdown(
        f"""
        <div style="border-left: 4px solid {color}; padding: 12px 16px;
             margin-bottom: 12px; background-color: #f8f9fa; border-radius: 4px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h4 style="margin: 0; color: #333;">{advice.title}</h4>
                <span style="background-color: {color}; color: white; padding: 2px 8px;
                      border-radius: 12px; font-size: 0.8em;">{priority_label}</span>
            </div>
            <div style="margin-top: 8px; font-size: 0.9em; color: #555;">
                현재: <strong>{advice.current_value}</strong> →
                목표: <strong>{advice.target_value}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("상세 분석 및 액션 플랜", expanded=False):
        st.write(advice.description)
        if advice.actions:
            st.markdown("**실행 방안:**")
            for action in advice.actions:
                st.markdown(f"- {action}")
        if advice.expected_effect:
            st.info(f"기대 효과: {advice.expected_effect}")


def roadmap_timeline(roadmap: list[dict]) -> None:
    """3단계 성장 로드맵 타임라인."""
    phase_colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]
    phase_icons = ["1️⃣", "2️⃣", "3️⃣"]

    for i, phase in enumerate(roadmap):
        color = phase_colors[i] if i < len(phase_colors) else "#333"
        icon = phase_icons[i] if i < len(phase_icons) else "📌"

        st.markdown(
            f"""
            <div style="border-left: 3px solid {color}; padding: 10px 16px;
                 margin-bottom: 8px; background-color: #fafafa; border-radius: 4px;">
                <h4 style="margin: 0;">{icon} {phase['phase']}: {phase['label']}</h4>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for goal in phase["goals"]:
            st.markdown(f"  - {goal}")
        st.write("")


def strength_weakness_card(
    strengths: list[tuple[str, float, float]],
    weaknesses: list[tuple[str, float, float]],
    metric_labels: dict[str, str],
) -> None:
    """강점/약점 카드 표시."""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 💪 강점 (Top 3)")
        for name, seller_val, top_val in strengths:
            label = metric_labels.get(name, name)
            if top_val > 0:
                ratio = seller_val / top_val * 100
            else:
                ratio = 0
            st.markdown(
                f"- **{label}**: {seller_val:,.1f} "
                f"(Top Performer의 {ratio:.0f}%)"
            )

    with col2:
        st.markdown("### ⚠️ 약점 (Top 3)")
        for name, seller_val, top_val in weaknesses:
            label = metric_labels.get(name, name)
            if top_val > 0:
                ratio = seller_val / top_val * 100
            else:
                ratio = 0
            st.markdown(
                f"- **{label}**: {seller_val:,.1f} "
                f"(Top Performer의 {ratio:.0f}%)"
            )
