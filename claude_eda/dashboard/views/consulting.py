"""Page 2: 컨설팅 리포트."""

from __future__ import annotations

import streamlit as st

from claude_eda.dashboard.components.cards import (
    advice_card,
    roadmap_timeline,
    strength_weakness_card,
)
from claude_eda.dashboard.components.charts import (
    health_breakdown_bar,
    health_gauge,
)
from claude_eda.dashboard.data.preprocessor import (
    SellerMetrics,
    get_cluster_averages,
)
from claude_eda.dashboard.engine.benchmarks import CLUSTER_BENCHMARKS
from claude_eda.dashboard.engine.health_score import compute_full_health
from claude_eda.dashboard.engine.rule_engine import (
    generate_all_advice,
    generate_growth_roadmap,
    identify_strengths_weaknesses,
)
from claude_eda.dashboard.utils.formatting import health_grade
from claude_eda.dashboard.utils.korean import (
    METRIC_LABELS,
    SELLER_CLUSTER_LABELS,
)


def render_consulting(metrics: SellerMetrics) -> None:
    """컨설팅 리포트 페이지 렌더."""
    # 건강 점수
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

    # === 섹션 1: 종합 진단 ===
    st.markdown("## 종합 진단")

    col_gauge, col_break = st.columns([1, 2])
    with col_gauge:
        st.plotly_chart(health_gauge(health_score), use_container_width=True)
        grade = health_grade(health_score)
        cluster_label = SELLER_CLUSTER_LABELS.get(metrics.cluster, "미분류")

        st.markdown(
            f"**종합 등급: {grade}** ({health_score:.0f}/100) &nbsp;|&nbsp; "
            f"클러스터: {cluster_label}"
        )

        # 한줄 진단
        if health_score >= 80:
            st.success("우수한 성과를 보이고 있습니다. 현 수준 유지와 세부 최적화에 집중하세요.")
        elif health_score >= 60:
            st.info("양호한 수준입니다. 약점 지표 개선으로 Top Performer 진입이 가능합니다.")
        elif health_score >= 40:
            st.warning("개선이 필요한 영역이 있습니다. 우선순위별 집중 개선을 권장합니다.")
        else:
            st.error("긴급 개선이 필요합니다. 아래 컨설팅 조언을 즉시 실행하세요.")

    with col_break:
        st.plotly_chart(
            health_breakdown_bar(dim_scores), use_container_width=True
        )

    st.divider()

    # === 섹션 2: 강점/약점 ===
    st.markdown("## 강점 & 약점 분석")
    strengths, weaknesses = identify_strengths_weaknesses(metrics)
    # 낮을수록 좋은 지표의 라벨도 포함
    extended_labels = {**METRIC_LABELS}
    strength_weakness_card(strengths, weaknesses, extended_labels)

    st.divider()

    # === 섹션 3: 우선 개선 사항 ===
    st.markdown("## 컨설팅 조언")
    advices = generate_all_advice(metrics)
    if advices:
        st.markdown(f"총 **{len(advices)}개** 개선 사항이 발견되었습니다.")
        for adv in advices:
            advice_card(adv)
    else:
        st.success("현재 긴급한 개선 사항이 없습니다. 현 수준을 유지하세요!")

    st.divider()

    # === 섹션 4: 성장 로드맵 ===
    st.markdown("## 성장 로드맵")
    roadmap = generate_growth_roadmap(metrics)
    roadmap_timeline(roadmap)

    st.divider()

    # === 섹션 5: 리뷰 원인 심층 분석 ===
    rka = metrics.review_keyword_analysis
    if rka and rka.get("analyzed_count", 0) > 0 and rka.get("issue_counts"):
        st.markdown("## 리뷰 이슈 심층 분석")
        _render_review_deep_analysis(metrics)
        st.divider()

    # === 섹션 6: 유사 셀러 비교 ===
    st.markdown("## 유사 셀러 비교 (같은 클러스터)")
    _render_cluster_comparison(metrics)


def _render_cluster_comparison(metrics: SellerMetrics) -> None:
    """같은 클러스터 평균과 비교."""
    cluster_avgs = get_cluster_averages()
    my_avg = cluster_avgs.get(metrics.cluster)
    top_avg = CLUSTER_BENCHMARKS[0]

    if my_avg is None:
        st.info("클러스터 정보가 없어 비교할 수 없습니다.")
        return

    compare_metrics = [
        ("total_orders", "총 주문수", metrics.total_orders),
        ("total_revenue", "총 매출 (R$)", metrics.total_revenue),
        ("avg_price", "평균 단가 (R$)", metrics.avg_price),
        ("product_variety", "상품 다양성", metrics.product_variety),
        ("avg_review", "평균 리뷰", metrics.avg_review),
        ("avg_delivery_days", "평균 배송일", metrics.avg_delivery_days),
        ("late_delivery_pct", "배송 지연율", metrics.late_delivery_pct),
        ("unique_customers", "고유 고객수", metrics.unique_customers),
    ]

    # 테이블 형태로 표시
    rows = []
    for key, label, seller_val in compare_metrics:
        cluster_val = my_avg.get(key, 0)
        top_val = top_avg.get(key, 0)

        # 차이 표시
        if cluster_val > 0:
            diff_cluster = (seller_val / cluster_val - 1) * 100
        else:
            diff_cluster = 0
        if top_val > 0:
            diff_top = (seller_val / top_val - 1) * 100
        else:
            diff_top = 0

        rows.append({
            "지표": label,
            "이 셀러": f"{seller_val:,.1f}",
            "클러스터 평균": f"{cluster_val:,.1f}",
            "클러스터 대비": f"{diff_cluster:+.0f}%",
            "Top Performer": f"{top_val:,.1f}",
            "TP 대비": f"{diff_top:+.0f}%",
        })

    import pandas as pd
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


def _render_review_deep_analysis(metrics: SellerMetrics) -> None:
    """리뷰 텍스트 키워드 기반 원인 심층 분석."""
    rka = metrics.review_keyword_analysis
    issue_counts = rka.get("issue_counts", {})
    examples = rka.get("examples", {})
    primary = rka.get("primary_issue")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 이슈 카테고리별 분포")
        from claude_eda.dashboard.components.charts import review_keyword_bar
        st.plotly_chart(
            review_keyword_bar(issue_counts, rka["analyzed_count"]),
            use_container_width=True,
        )

    with col2:
        st.markdown("#### 핵심 인사이트")
        if primary:
            st.error(f"가장 빈번한 이슈: **{primary}** ({issue_counts.get(primary, 0)}건)")
        analyzed = rka["analyzed_count"]
        pos_count = rka.get("positive_count", 0)
        neg_issues = rka.get("negative_issues", {})

        st.markdown(
            f"- 분석 대상 텍스트 리뷰: **{analyzed}건** "
            f"(전체 {rka.get('total_count', 0)}건 중)\n"
            f"- 긍정 키워드 포함 리뷰: **{pos_count}건** ({pos_count / analyzed:.0%})\n"
            f"- 이슈 키워드 포함 리뷰: **{sum(issue_counts.values())}건**"
        )

        if neg_issues:
            st.markdown("**저평가(1-2점) 리뷰의 이슈 분포:**")
            for cat, cnt in sorted(neg_issues.items(), key=lambda x: x[1], reverse=True):
                st.markdown(f"  - {cat}: {cnt}건")

    # 예시 리뷰
    if examples:
        with st.expander("이슈 카테고리별 리뷰 예시", expanded=False):
            for cat, exs in examples.items():
                st.markdown(f"**{cat}:**")
                for ex in exs:
                    st.caption(f"> {ex}")
                st.write("")
