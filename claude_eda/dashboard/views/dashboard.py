"""Page 1: 현황 대시보드."""

from __future__ import annotations

import streamlit as st

from claude_eda.dashboard.components.cards import kpi_card_row
from claude_eda.dashboard.components.charts import (
    category_pie,
    category_rank_table,
    cluster_donut,
    delivery_histogram,
    distance_delivery_bar,
    health_gauge,
    monthly_trend_chart,
    payment_donut,
    radar_chart,
    review_distribution,
    review_keyword_bar,
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

        display_name = metrics.company_name or metrics.seller_id[:12]
        st.markdown(f"### {display_name}")
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

    st.divider()

    # --- 리뷰 키워드 분석 | 카테고리 내 순위 ---
    st.markdown("### 심층 분석")
    col_kw, col_rank = st.columns(2)

    with col_kw:
        st.markdown("#### 리뷰 키워드 분석")
        rka = metrics.review_keyword_analysis
        if rka and rka.get("analyzed_count", 0) > 0:
            st.plotly_chart(
                review_keyword_bar(
                    rka.get("issue_counts", {}),
                    rka["analyzed_count"],
                ),
                use_container_width=True,
            )
            pos = rka.get("positive_count", 0)
            total = rka["analyzed_count"]
            st.markdown(
                f"긍정 리뷰: **{pos}건** ({pos / total:.0%}) &nbsp;|&nbsp; "
                f"분석 대상: **{total}건** / 전체 {rka.get('total_count', 0)}건"
            )
            if rka.get("primary_issue"):
                st.warning(f"주요 이슈: **{rka['primary_issue']}**")
        else:
            st.info("텍스트 리뷰가 없어 키워드 분석이 불가합니다.")

    with col_rank:
        st.markdown("#### 카테고리 내 순위")
        st.plotly_chart(
            category_rank_table(metrics.category_ranks),
            use_container_width=True,
        )

    st.divider()

    # --- 거리별 배송 | 결제 패턴 ---
    col_dist, col_pay = st.columns(2)

    with col_dist:
        st.markdown("#### 거리별 배송 분석")
        if metrics.avg_distance_km > 0:
            st.markdown(f"평균 셀러-고객 거리: **{metrics.avg_distance_km:,.0f}km**")
        st.plotly_chart(
            distance_delivery_bar(metrics.distance_delivery),
            use_container_width=True,
        )

    with col_pay:
        st.markdown("#### 결제 패턴")
        st.plotly_chart(
            payment_donut(metrics.payment_type_dist),
            use_container_width=True,
        )
        if metrics.avg_installments > 0:
            st.markdown(
                f"평균 할부: **{metrics.avg_installments:.1f}회** &nbsp;|&nbsp; "
                f"신용카드 비율: **{metrics.credit_card_pct:.0%}**"
            )

    st.divider()

    # --- 취소율 & 재구매율 ---
    st.markdown("### 고객 유지 지표")
    col_cancel, col_repeat, col_empty = st.columns(3)

    with col_cancel:
        st.metric(
            "주문 취소율",
            f"{metrics.cancel_rate:.1%}",
            delta=f"{(metrics.cancel_rate - 0.005) * 100:.1f}%p"
            if metrics.cancel_rate > 0
            else None,
            delta_color="inverse",
            help=f"취소/미배송 주문: {metrics.cancel_count}건",
        )

    with col_repeat:
        st.metric(
            "재구매 고객 비율",
            f"{metrics.repeat_customer_rate:.1%}",
            help=f"재구매 고객: {metrics.repeat_customer_count}명",
        )

    with col_empty:
        st.metric(
            "고객당 평균 주문",
            f"{metrics.items_per_order:.1f}건",
            help="주문 1건당 평균 아이템 수",
        )
