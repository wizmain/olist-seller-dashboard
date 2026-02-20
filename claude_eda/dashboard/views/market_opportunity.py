"""Page 3: 시장 기회 분석."""

from __future__ import annotations

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
    compute_category_state_matrix,
    compute_cross_sell_categories,
    compute_price_simulation,
    compute_regional_supply_demand,
    compute_seller_growth_regions,
)
from claude_eda.dashboard.data.preprocessor import SellerMetrics
from claude_eda.dashboard.utils.korean import STATE_NAMES_KR


def render_market_opportunity(metrics: SellerMetrics) -> None:
    """시장 기회 분석 페이지 렌더."""
    st.markdown("## 시장 기회 분석")
    st.markdown(
        f"셀러 `{metrics.seller_id[:12]}...` | "
        f"지역: **{STATE_NAMES_KR.get(metrics.seller_state, metrics.seller_state)}** | "
        f"카테고리: **{_get_seller_categories_str(metrics)}**"
    )

    st.divider()

    # === 섹션 1: 성장 가능 지역 분석 ===
    _render_growth_regions(metrics)

    st.divider()

    # === 섹션 2: 카테고리별 가격 스위트스팟 ===
    _render_price_sweet_spot(metrics)

    st.divider()

    # === 섹션 3: 카테고리 확장 기회 ===
    _render_category_expansion(metrics)


def _get_seller_categories(metrics: SellerMetrics) -> list[str]:
    """셀러의 카테고리 리스트."""
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


# ================================================================
# 섹션 1: 성장 가능 지역 분석
# ================================================================

def _render_growth_regions(metrics: SellerMetrics) -> None:
    st.markdown("### 1. 성장 가능 지역 분석")

    seller_cats = _get_seller_categories(metrics)

    # 현재 고객 지역 현황 + 전체 수급 불균형
    col_current, col_supply = st.columns([1, 2])

    with col_current:
        st.markdown("#### 현재 고객 지역 분포")
        if metrics.customer_state_dist is not None and not metrics.customer_state_dist.empty:
            dist = metrics.customer_state_dist.copy()
            total = dist["customers"].sum()
            for _, r in dist.iterrows():
                state_kr = STATE_NAMES_KR.get(r["state"], r["state"])
                pct = r["customers"] / total * 100
                st.markdown(f"**{state_kr}** ({r['state']}): {r['customers']}명 ({pct:.0f}%)")
                st.progress(min(pct / 100, 1.0))
        else:
            st.info("고객 지역 데이터가 없습니다.")

    with col_supply:
        st.markdown("#### 전체 시장 수급 현황")
        sd_df = compute_regional_supply_demand()
        fig = supply_demand_chart(sd_df, metrics.seller_state)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # 맞춤 추천 지역
    st.markdown("#### 추천 진출 지역")
    if not seller_cats:
        st.warning("카테고리 정보가 없어 지역 추천이 불가합니다.")
        return

    growth_regions = compute_seller_growth_regions(
        metrics.seller_id, seller_cats, metrics.seller_state
    )

    if not growth_regions:
        st.info("추천 가능한 지역이 없습니다.")
        return

    # Top 3 카드
    cols = st.columns(min(3, len(growth_regions)))
    grade_emoji = {
        "긴급 공급 부족": "🔴",
        "진출 가능": "🔴",
        "높은 기회": "🟠",
        "중간 기회": "🔵",
        "포화": "⚪",
    }
    grade_color = {
        "긴급 공급 부족": COLORS["danger"],
        "진출 가능": COLORS["danger"],
        "높은 기회": COLORS["warning"],
        "중간 기회": COLORS["info"],
        "포화": COLORS["muted"],
    }

    for i, region in enumerate(growth_regions[:3]):
        with cols[i]:
            emoji = grade_emoji.get(region["opportunity_grade"], "📍")
            color = grade_color.get(region["opportunity_grade"], COLORS["primary"])
            state_kr = STATE_NAMES_KR.get(region["state"], region["state"])

            st.markdown(
                f"""
                <div style="border: 2px solid {color}; border-radius: 8px;
                     padding: 16px; background-color: #fafafa;">
                    <h4 style="margin: 0; color: {color};">
                        {emoji} {state_kr} ({region['state']})
                    </h4>
                    <div style="font-size: 2em; font-weight: bold; color: {color};
                         margin: 8px 0;">{region['opportunity_score']:.0f}점</div>
                    <div style="font-size: 0.85em; color: #555;">
                        <b>시장 규모:</b> R${region['market_revenue']:,.0f}<br>
                        <b>주문 수:</b> {region['market_orders']:,}건<br>
                        <b>경쟁 셀러:</b> {region['competitors']}명<br>
                        <b>셀러당 주문:</b> {region['orders_per_seller']:.0f}건<br>
                        <b>평균 가격:</b> R${region['avg_price']:,.0f}<br>
                        <b>고객 수:</b> {region['customers']:,}명
                    </div>
                    <hr style="margin: 8px 0;">
                    <div style="font-size: 0.8em; color: #777;">{region['reason']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # 나머지 지역 테이블
    if len(growth_regions) > 3:
        with st.expander(f"추가 추천 지역 ({len(growth_regions) - 3}개)", expanded=False):
            for region in growth_regions[3:]:
                state_kr = STATE_NAMES_KR.get(region["state"], region["state"])
                st.markdown(
                    f"**{state_kr}** ({region['state']}) — "
                    f"기회점수 {region['opportunity_score']:.0f} | "
                    f"시장 R${region['market_revenue']:,.0f} | "
                    f"경쟁 {region['competitors']}명 | "
                    f"{region['reason']}"
                )


# ================================================================
# 섹션 2: 카테고리별 가격 스위트스팟
# ================================================================

def _render_price_sweet_spot(metrics: SellerMetrics) -> None:
    st.markdown("### 2. 카테고리 가격 스위트스팟")

    seller_cats = _get_seller_categories(metrics)
    price_stats = compute_category_price_stats()

    # 셀러 카테고리만 필터
    if seller_cats:
        my_stats = price_stats[price_stats["category"].isin(seller_cats)]
    else:
        my_stats = price_stats.head(10)

    # 셀러 가격 딕셔너리
    seller_prices = {}
    if metrics.category_revenue is not None and not metrics.category_revenue.empty:
        merged_data = None
        try:
            from claude_eda.dashboard.data.loader import build_merged_table
            merged_data = build_merged_table()
            sd = merged_data[merged_data["seller_id"] == metrics.seller_id]
            cat_prices = sd.groupby("product_category_name_english")["price"].mean()
            seller_prices = cat_prices.to_dict()
        except Exception:
            pass

    # 가격 포지셔닝 차트
    col_box, col_table = st.columns([3, 2])

    with col_box:
        st.markdown("#### 시장 가격 분포 vs 내 가격")
        fig = price_boxplot(my_stats if not my_stats.empty else price_stats.head(10), seller_prices)
        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        st.markdown("#### 내 카테고리 가격 현황")
        if not my_stats.empty:
            for _, row in my_stats.iterrows():
                cat = row["category"]
                my_price = seller_prices.get(cat)
                price_pos = ""
                if my_price is not None:
                    if my_price < row["p25"]:
                        price_pos = "🔵 저가"
                    elif my_price <= row["p75"]:
                        price_pos = "🟢 볼륨존"
                    else:
                        price_pos = "🟠 프리미엄"

                st.markdown(f"**{cat}**")
                if my_price is not None:
                    st.markdown(
                        f"내 가격: R${my_price:,.0f} {price_pos} | "
                        f"시장 중앙값: R${row['median_price']:,.0f}"
                    )
                else:
                    st.markdown(f"시장 중앙값: R${row['median_price']:,.0f}")
                st.caption(
                    f"P25: R${row['p25']:,.0f} | P75: R${row['p75']:,.0f} | "
                    f"주문: {int(row['order_count']):,}건"
                )
        else:
            st.info("카테고리 가격 정보가 없습니다.")

    st.markdown("---")

    # 지역별 가격 차이 + 매출 시뮬레이션
    st.markdown("#### 지역별 가격 분석 & 매출 시뮬레이션")

    # 카테고리 / 지역 선택
    all_cats = seller_cats if seller_cats else price_stats["category"].head(20).tolist()

    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        selected_cat = st.selectbox(
            "카테고리 선택",
            all_cats,
            key="market_cat_select",
        )
    with col_sel2:
        sd_df = compute_regional_supply_demand()
        states = sd_df["state"].tolist()
        state_labels = [f"{s} ({STATE_NAMES_KR.get(s, s)})" for s in states]
        selected_state_label = st.selectbox(
            "지역 선택",
            state_labels,
            key="market_state_select",
        )
        selected_state = selected_state_label.split(" (")[0] if selected_state_label else ""

    col_region_price, col_sim = st.columns(2)

    with col_region_price:
        if selected_cat:
            price_by_state = compute_category_price_by_state(selected_cat)
            fig = regional_price_table(price_by_state)
            st.plotly_chart(fig, use_container_width=True)

    with col_sim:
        if selected_cat and selected_state:
            sim_data = compute_price_simulation(selected_cat, selected_state)
            fig = revenue_simulation_chart(sim_data)
            st.plotly_chart(fig, use_container_width=True)

            if sim_data:
                total_est = sum(d["estimated_monthly_revenue"] for d in sim_data)
                best = max(sim_data, key=lambda d: d["estimated_monthly_revenue"])
                st.success(
                    f"**{selected_cat}** in **{selected_state}**: "
                    f"추천 가격대 **{best['label']}** "
                    f"(월 예상 매출 R${best['estimated_monthly_revenue']:,.0f})"
                )


# ================================================================
# 섹션 3: 카테고리 확장 기회
# ================================================================

def _render_category_expansion(metrics: SellerMetrics) -> None:
    st.markdown("### 3. 카테고리 확장 기회")

    seller_cats = _get_seller_categories(metrics)

    col_opp, col_cross = st.columns(2)

    with col_opp:
        st.markdown("#### 미진출 고기회 카테고리")
        opp_df = compute_category_opportunity_for_seller(
            metrics.seller_id, seller_cats, metrics.seller_state
        )
        fig = category_opportunity_table(opp_df)
        st.plotly_chart(fig, use_container_width=True)

    with col_cross:
        st.markdown("#### 크로스셀 추천")
        st.caption("같은 카테고리 셀러들이 함께 판매하는 카테고리")

        if seller_cats:
            cross_df = compute_cross_sell_categories(seller_cats)
            if not cross_df.empty:
                for _, r in cross_df.head(7).iterrows():
                    adoption = r["adoption_rate"]
                    st.markdown(
                        f"**{r['category']}** — "
                        f"채택률 {adoption:.0%} | "
                        f"평균가 R${r['avg_price']:,.0f} | "
                        f"매출 R${r['revenue']:,.0f}"
                    )
                    st.progress(min(adoption, 1.0))
            else:
                st.info("크로스셀 데이터가 부족합니다.")
        else:
            st.info("카테고리 정보가 없습니다.")
