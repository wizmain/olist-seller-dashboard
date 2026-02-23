"""Page 3: 시장 기회 분석."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from claude_eda.dashboard.components.charts import (
    category_opportunity_table,
    price_boxplot,
    regional_price_table,
    revenue_simulation_chart,
    supply_demand_chart,
)
from claude_eda.dashboard.config import COLORS
from claude_eda.dashboard.data.market_analyzer import (
    compute_category_opportunity_for_seller,
    compute_category_price_by_state,
    compute_category_price_stats,
    compute_cross_sell_categories,
    compute_price_simulation,
    compute_regional_supply_demand,
    compute_seller_growth_regions,
)
from claude_eda.dashboard.data.preprocessor import SellerMetrics
from claude_eda.dashboard.utils.korean import STATE_NAMES_KR


def render_market_opportunity(metrics: SellerMetrics) -> None:
    """시장 기회 분석 페이지 렌더."""
    # 헤더
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #1f77b4 0%, #17becf 100%);
             padding: 20px 24px; border-radius: 8px; margin-bottom: 16px;">
            <h2 style="color: white; margin: 0 0 8px 0;">시장 기회 분석</h2>
            <span style="color: rgba(255,255,255,0.85); font-size: 0.95em;">
                셀러 <code style="background: rgba(255,255,255,0.2); color: white;
                padding: 2px 6px; border-radius: 4px;">{metrics.company_name or metrics.seller_id[:12]}</code>
                &nbsp;&nbsp;|&nbsp;&nbsp;
                지역: <b>{STATE_NAMES_KR.get(metrics.seller_state, metrics.seller_state)}</b>
                &nbsp;&nbsp;|&nbsp;&nbsp;
                카테고리: <b>{_get_seller_categories_str(metrics)}</b>
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # === 섹션 1: 성장 가능 지역 분석 ===
    _render_growth_regions(metrics)

    st.write("")

    # === 섹션 2: 카테고리별 가격 스위트스팟 ===
    _render_price_sweet_spot(metrics)

    st.write("")

    # === 섹션 3: 카테고리 확장 기회 ===
    _render_category_expansion(metrics)


def _get_seller_categories(metrics: SellerMetrics) -> list[str]:
    if metrics.category_revenue is not None and not metrics.category_revenue.empty:
        return metrics.category_revenue["category"].dropna().tolist()
    return []


def _get_seller_categories_str(metrics: SellerMetrics) -> str:
    cats = _get_seller_categories(metrics)
    if not cats:
        return "미분류"
    if len(cats) <= 3:
        return ", ".join(cats)
    return f"{', '.join(cats[:3])} 외 {len(cats) - 3}개"


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


def _customer_state_chart(metrics: SellerMetrics) -> go.Figure:
    """현재 고객 지역 분포 수평 바 차트."""
    dist = metrics.customer_state_dist
    if dist is None or dist.empty:
        fig = go.Figure()
        fig.add_annotation(text="고객 지역 데이터 없음", x=0.5, y=0.5,
                           xref="paper", yref="paper", showarrow=False,
                           font=dict(size=14, color="gray"))
        fig.update_layout(height=420, xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig

    d = dist.copy().sort_values("customers", ascending=True)
    total = d["customers"].sum()
    labels = [
        f"{STATE_NAMES_KR.get(s, s)} ({s})" for s in d["state"]
    ]

    fig = go.Figure(go.Bar(
        x=d["customers"],
        y=labels,
        orientation="h",
        marker_color=COLORS["primary"],
        text=[f"{c}명 ({c / total:.0%})" for c in d["customers"]],
        textposition="outside",
    ))
    fig.update_layout(
        title="현재 고객 지역 분포",
        xaxis=dict(title="고객 수"),
        height=420,
        margin=dict(t=50, b=30, l=100, r=80),
    )
    return fig


# ================================================================
# 섹션 1: 성장 가능 지역 분석
# ================================================================

def _render_growth_regions(metrics: SellerMetrics) -> None:
    _section_header(
        "성장 가능 지역 분석",
        "📍",
        "현재 고객 분포와 전체 시장 수급을 비교하여 진출 가능성이 높은 지역을 제안합니다",
    )

    seller_cats = _get_seller_categories(metrics)

    # 좌: 현재 고객 분포 차트 / 우: 전체 수급 차트 — 동일 높이
    col_l, col_r = st.columns(2)

    with col_l:
        fig = _customer_state_chart(metrics)
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        sd_df = compute_regional_supply_demand()
        fig = supply_demand_chart(sd_df, metrics.seller_state)
        st.plotly_chart(fig, use_container_width=True)

    # 추천 진출 지역 카드
    if not seller_cats:
        st.info("카테고리 정보가 없어 지역 추천이 불가합니다.")
        return

    growth_regions = compute_seller_growth_regions(
        metrics.seller_id, seller_cats, metrics.seller_state
    )
    if not growth_regions:
        st.info("추천 가능한 지역이 없습니다.")
        return

    st.markdown(
        '<p style="font-weight:600; font-size:1.05em; color:#333; margin: 16px 0 12px 0;">'
        '맞춤 추천 진출 지역</p>',
        unsafe_allow_html=True,
    )

    grade_color = {
        "긴급 공급 부족": COLORS["danger"],
        "진출 가능": COLORS["danger"],
        "높은 기회": COLORS["warning"],
        "중간 기회": COLORS["info"],
        "포화": COLORS["muted"],
    }

    cols = st.columns(min(len(growth_regions), 5))
    for i, region in enumerate(growth_regions[:5]):
        with cols[i]:
            color = grade_color.get(region["opportunity_grade"], COLORS["primary"])
            state_kr = STATE_NAMES_KR.get(region["state"], region["state"])
            st.markdown(
                f"""
                <div style="border-top: 4px solid {color}; border-radius: 6px;
                     padding: 14px; background: #f8f9fa; min-height: 220px;">
                    <div style="font-size: 0.75em; color: {color}; font-weight: 600;
                         text-transform: uppercase; letter-spacing: 0.5px;">
                        {region['opportunity_grade']}</div>
                    <div style="font-size: 1.3em; font-weight: 700; margin: 4px 0;">
                        {state_kr} ({region['state']})</div>
                    <div style="font-size: 1.8em; font-weight: 800; color: {color};
                         margin: 4px 0;">{region['opportunity_score']:.0f}<span
                         style="font-size: 0.4em; color: #999;">점</span></div>
                    <div style="font-size: 0.8em; color: #555; line-height: 1.6;">
                        시장 R${region['market_revenue']:,.0f}<br>
                        주문 {region['market_orders']:,}건 · 경쟁 {region['competitors']}명<br>
                        셀러당 {region['orders_per_seller']:.0f}건 · 평균가 R${region['avg_price']:,.0f}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ================================================================
# 섹션 2: 카테고리별 가격 스위트스팟
# ================================================================

def _render_price_sweet_spot(metrics: SellerMetrics) -> None:
    _section_header(
        "카테고리 가격 스위트스팟",
        "💰",
        "시장 가격 분포에서 셀러의 현재 포지션을 확인하고, 지역별 최적 가격대를 시뮬레이션합니다",
    )

    seller_cats = _get_seller_categories(metrics)
    price_stats = compute_category_price_stats()

    if seller_cats:
        my_stats = price_stats[price_stats["category"].isin(seller_cats)]
    else:
        my_stats = price_stats.head(10)

    # 셀러 가격 딕셔너리
    seller_prices = {}
    if metrics.category_revenue is not None and not metrics.category_revenue.empty:
        try:
            from claude_eda.dashboard.data.loader import build_merged_table
            merged_data = build_merged_table()
            sd = merged_data[merged_data["seller_id"] == metrics.seller_id]
            seller_prices = sd.groupby("product_category_name_english")["price"].mean().to_dict()
        except Exception:
            pass

    # 좌: 박스플롯 / 우: 가격 포지셔닝 테이블 — 동일 높이
    col_l, col_r = st.columns(2)

    with col_l:
        stats_to_show = my_stats if not my_stats.empty else price_stats.head(10)
        fig = price_boxplot(stats_to_show, seller_prices)
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        # 테이블 형태로 깔끔하게 표시
        fig = _price_position_table(my_stats, seller_prices)
        st.plotly_chart(fig, use_container_width=True)

    # 지역별 가격 + 매출 시뮬레이션 (선택형)
    st.markdown(
        '<p style="font-weight:600; font-size:1.05em; color:#333; margin: 16px 0 12px 0;">'
        '지역별 가격 분석 & 매출 시뮬레이션</p>',
        unsafe_allow_html=True,
    )

    all_cats = seller_cats if seller_cats else price_stats["category"].head(20).tolist()
    sd_df = compute_regional_supply_demand()
    states = sd_df["state"].tolist()
    state_labels = [f"{s} ({STATE_NAMES_KR.get(s, s)})" for s in states]

    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        selected_cat = st.selectbox("카테고리 선택", all_cats, key="market_cat_select")
    with col_sel2:
        selected_state_label = st.selectbox("지역 선택", state_labels, key="market_state_select")
        selected_state = selected_state_label.split(" (")[0] if selected_state_label else ""

    col_l2, col_r2 = st.columns(2)

    with col_l2:
        if selected_cat:
            price_by_state = compute_category_price_by_state(selected_cat)
            fig = regional_price_table(price_by_state)
            fig.update_layout(height=380)
            st.plotly_chart(fig, use_container_width=True)

    with col_r2:
        if selected_cat and selected_state:
            sim_data = compute_price_simulation(selected_cat, selected_state)
            fig = revenue_simulation_chart(sim_data)
            fig.update_layout(height=380)
            st.plotly_chart(fig, use_container_width=True)

            if sim_data:
                best = max(sim_data, key=lambda d: d["estimated_monthly_revenue"])
                st.success(
                    f"추천 가격대: **{best['label']}** — "
                    f"월 예상 매출 **R${best['estimated_monthly_revenue']:,.0f}**"
                )


def _price_position_table(stats_df, seller_prices: dict) -> go.Figure:
    """카테고리별 가격 포지셔닝 Plotly 테이블."""
    if stats_df is None or stats_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="카테고리 가격 정보 없음", x=0.5, y=0.5,
                           xref="paper", yref="paper", showarrow=False,
                           font=dict(size=14, color="gray"))
        fig.update_layout(height=400, xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig

    cats = stats_df["category"].tolist()
    my_prices = []
    positions = []
    for _, row in stats_df.iterrows():
        cat = row["category"]
        mp = seller_prices.get(cat)
        if mp is not None:
            my_prices.append(f"R${mp:,.0f}")
            if mp < row["p25"]:
                positions.append("저가")
            elif mp <= row["p75"]:
                positions.append("볼륨존")
            else:
                positions.append("프리미엄")
        else:
            my_prices.append("-")
            positions.append("-")

    # 포지션별 셀 색상
    pos_colors = []
    for p in positions:
        if p == "저가":
            pos_colors.append("#dbeafe")
        elif p == "볼륨존":
            pos_colors.append("#d1fae5")
        elif p == "프리미엄":
            pos_colors.append("#fed7aa")
        else:
            pos_colors.append("white")

    base_white = ["white"] * len(cats)

    fig = go.Figure(go.Table(
        header=dict(
            values=["카테고리", "내 평균가", "시장 중앙값", "P25", "P75", "포지션"],
            fill_color=COLORS["primary"],
            font=dict(color="white", size=11),
            align="center",
        ),
        cells=dict(
            values=[
                cats,
                my_prices,
                [f"R${v:,.0f}" for v in stats_df["median_price"]],
                [f"R${v:,.0f}" for v in stats_df["p25"]],
                [f"R${v:,.0f}" for v in stats_df["p75"]],
                positions,
            ],
            fill_color=[base_white, base_white, base_white, base_white, base_white, pos_colors],
            align="center",
            font=dict(size=11),
            height=28,
        ),
    ))
    fig.update_layout(
        title="내 가격 포지셔닝",
        height=400,
        margin=dict(t=50, b=20),
    )
    return fig


# ================================================================
# 섹션 3: 카테고리 확장 기회
# ================================================================

def _render_category_expansion(metrics: SellerMetrics) -> None:
    _section_header(
        "카테고리 확장 기회",
        "🚀",
        "미진출 고기회 카테고리와 동종 셀러의 크로스셀 패턴을 분석합니다",
    )

    seller_cats = _get_seller_categories(metrics)

    col_l, col_r = st.columns(2)

    with col_l:
        opp_df = compute_category_opportunity_for_seller(
            metrics.seller_id, seller_cats, metrics.seller_state
        )
        fig = category_opportunity_table(opp_df)
        fig.update_layout(height=380)
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        # 크로스셀도 Plotly 테이블로 통일
        fig = _cross_sell_table(seller_cats)
        st.plotly_chart(fig, use_container_width=True)


def _cross_sell_table(seller_cats: list[str]) -> go.Figure:
    """크로스셀 추천 Plotly 테이블."""
    if not seller_cats:
        fig = go.Figure()
        fig.add_annotation(text="카테고리 정보 없음", x=0.5, y=0.5,
                           xref="paper", yref="paper", showarrow=False,
                           font=dict(size=14, color="gray"))
        fig.update_layout(height=380, xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig

    cross_df = compute_cross_sell_categories(seller_cats)
    if cross_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="크로스셀 데이터 부족", x=0.5, y=0.5,
                           xref="paper", yref="paper", showarrow=False,
                           font=dict(size=14, color="gray"))
        fig.update_layout(height=380, xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig

    top7 = cross_df.head(7)
    fig = go.Figure(go.Table(
        header=dict(
            values=["카테고리", "채택률", "평균가(R$)", "매출(R$)", "주문수"],
            fill_color=COLORS["primary"],
            font=dict(color="white", size=11),
            align="center",
        ),
        cells=dict(
            values=[
                top7["category"],
                [f"{v:.0%}" for v in top7["adoption_rate"]],
                [f"R${v:,.0f}" for v in top7["avg_price"]],
                [f"R${v:,.0f}" for v in top7["revenue"]],
                [f"{v:,}" for v in top7["orders"]],
            ],
            fill_color="white",
            align="center",
            font=dict(size=11),
            height=28,
        ),
    ))
    fig.update_layout(
        title="크로스셀 추천 (동종 셀러 채택률 기반)",
        height=380,
        margin=dict(t=50, b=20),
    )
    return fig
