"""Page 1: 현황 대시보드."""

from __future__ import annotations

import streamlit as st

from claude_eda.dashboard.components.cards import kpi_card_row
from claude_eda.dashboard.components.charts import (
    category_pie,
    cluster_donut,
    delivery_histogram,
    health_gauge,
    monthly_trend_chart,
    radar_chart,
    review_distribution,
    review_trend_chart,
    state_bar,
)
from claude_eda.dashboard.data.preprocessor import (
    SellerMetrics,
    get_cluster_averages,
)
from claude_eda.dashboard.engine.benchmarks import CLUSTER_BENCHMARKS
from claude_eda.dashboard.engine.health_score import compute_full_health
from claude_eda.dashboard.utils.formatting import (
    fmt_percentile,
    health_grade,
)
from claude_eda.dashboard.utils.korean import (
    CUSTOMER_CLUSTER_LABELS,
    METRIC_LABELS,
    PRODUCT_CLUSTER_LABELS,
    SELLER_CLUSTER_LABELS,
    STATE_NAMES_KR,
)


def render_dashboard(metrics: SellerMetrics) -> None:
    """현황 대시보드 페이지 렌더."""
    # --- 건강 점수 계산 ---
    health_score, dim_scores = compute_full_health(
        total_revenue=metrics.total_revenue,
        total_orders=metrics.total_orders,
        avg_review=metrics.avg_review,
        low_review_pct=metrics.low_review_pct,
        avg_delivery_days=metrics.avg_delivery_days,
        late_delivery_pct=metrics.late_delivery_pct,
        product_variety=metrics.product_variety,
        unique_customers=metrics.unique_customers,
    )

    # --- 헤더: 프로필 + 클러스터 배지 + 건강 점수 ---
    col_info, col_gauge = st.columns([2, 1])
    with col_info:
        cluster_label = SELLER_CLUSTER_LABELS.get(
            metrics.cluster, "미분류"
        )
        state_kr = STATE_NAMES_KR.get(metrics.seller_state, metrics.seller_state)

        st.markdown(f"### 셀러 `{metrics.seller_id[:12]}...`")
        st.markdown(
            f"**클러스터:** {cluster_label} &nbsp;|&nbsp; "
            f"**지역:** {state_kr} ({metrics.seller_state}) &nbsp;|&nbsp; "
            f"**건강등급:** {health_grade(health_score)} "
            f"({health_score:.0f}점)"
        )
        st.markdown(
            f"**활동기간:** {metrics.first_order} ~ {metrics.last_order} "
            f"({metrics.active_months}개월) &nbsp;|&nbsp; "
            f"**총 상품:** {metrics.total_items}건"
        )

    with col_gauge:
        st.plotly_chart(health_gauge(health_score), use_container_width=True)

    st.divider()

    # --- KPI 카드 ---
    st.markdown("### 핵심 성과 지표 (KPI)")
    kpi_card_row(metrics)

    st.divider()

    # --- 벤치마크 레이더 + 퍼센타일 ---
    st.markdown("### 벤치마크 비교")
    col_radar, col_pctile = st.columns([3, 2])

    with col_radar:
        cluster_avgs = get_cluster_averages()
        seller_vals = {
            "total_orders": metrics.total_orders,
            "total_revenue": metrics.total_revenue,
            "avg_price": metrics.avg_price,
            "product_variety": metrics.product_variety,
            "avg_review": metrics.avg_review,
            "unique_customers": metrics.unique_customers,
        }
        my_cluster_avg = cluster_avgs.get(metrics.cluster, cluster_avgs.get(3, {}))
        top_perf = CLUSTER_BENCHMARKS[0]

        fig = radar_chart(seller_vals, my_cluster_avg, top_perf)
        st.plotly_chart(fig, use_container_width=True)

    with col_pctile:
        st.markdown("#### 퍼센타일 랭킹")
        st.markdown("전체 2,971명 셀러 중 위치:")
        if metrics.percentiles:
            for metric_key, pctile in metrics.percentiles.items():
                label = METRIC_LABELS.get(metric_key, metric_key)
                bar_width = max(5, 100 - pctile)
                st.markdown(
                    f"**{label}**: {fmt_percentile(pctile)}"
                )
                st.progress(bar_width / 100)
        else:
            st.info("퍼센타일 데이터를 계산할 수 없습니다.")

    st.divider()

    # --- 월별 추이 ---
    st.markdown("### 월별 추이")
    tab_order, tab_review = st.tabs(["주문/매출", "리뷰"])

    with tab_order:
        fig = monthly_trend_chart(metrics.monthly_orders, metrics.monthly_revenue)
        st.plotly_chart(fig, use_container_width=True)

    with tab_review:
        fig = review_trend_chart(metrics.monthly_review)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # --- 상품 분석 | 고객 분석 ---
    st.markdown("### 상세 분석")
    col_prod, col_cust = st.columns(2)

    with col_prod:
        st.markdown("#### 상품 분석")
        st.plotly_chart(
            category_pie(metrics.category_revenue),
            use_container_width=True,
        )
        if not metrics.product_cluster_dist.empty:
            st.plotly_chart(
                cluster_donut(
                    metrics.product_cluster_dist,
                    PRODUCT_CLUSTER_LABELS,
                    "상품 클러스터 분포",
                ),
                use_container_width=True,
            )

    with col_cust:
        st.markdown("#### 고객 분석")
        st.plotly_chart(
            state_bar(metrics.customer_state_dist),
            use_container_width=True,
        )
        if not metrics.customer_cluster_dist.empty:
            st.plotly_chart(
                cluster_donut(
                    metrics.customer_cluster_dist,
                    CUSTOMER_CLUSTER_LABELS,
                    "고객 클러스터 분포",
                ),
                use_container_width=True,
            )

    st.divider()

    # --- 배송 성과 | 리뷰 분석 ---
    col_del, col_rev = st.columns(2)

    with col_del:
        st.markdown("#### 배송 성과")
        st.plotly_chart(
            delivery_histogram(metrics.delivery_days_list),
            use_container_width=True,
        )

    with col_rev:
        st.markdown("#### 리뷰 분석")
        st.plotly_chart(
            review_distribution(metrics.review_distribution),
            use_container_width=True,
        )
