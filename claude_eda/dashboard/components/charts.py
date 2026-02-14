"""Plotly 차트 컴포넌트."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from claude_eda.dashboard.config import COLORS
from claude_eda.dashboard.utils.formatting import health_grade_color
from claude_eda.dashboard.utils.korean import (
    CUSTOMER_CLUSTER_LABELS,
    HEALTH_DIMENSIONS,
    PRODUCT_CLUSTER_LABELS,
    RADAR_LABELS,
)


def radar_chart(
    seller_values: dict[str, float],
    cluster_avg: dict[str, float],
    top_performer: dict[str, float],
    title: str = "셀러 성과 레이더",
) -> go.Figure:
    """셀러 vs 클러스터 평균 vs Top Performer 레이더 차트."""
    metrics = list(RADAR_LABELS.keys())
    labels = [RADAR_LABELS[m] for m in metrics]

    def normalize(values: dict, keys: list) -> list[float]:
        """0-100 정규화 (Top Performer 기준 100)."""
        result = []
        for k in keys:
            top_val = top_performer.get(k, 1)
            val = values.get(k, 0)
            if top_val > 0:
                result.append(min(val / top_val * 100, 150))
            else:
                result.append(0)
        return result

    seller_norm = normalize(seller_values, metrics)
    cluster_norm = normalize(cluster_avg, metrics)
    top_norm = normalize(top_performer, metrics)

    # 닫기 위해 첫 값 추가
    labels_closed = labels + [labels[0]]
    seller_closed = seller_norm + [seller_norm[0]]
    cluster_closed = cluster_norm + [cluster_norm[0]]
    top_closed = top_norm + [top_norm[0]]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=top_closed,
            theta=labels_closed,
            fill="toself",
            name="Top Performer",
            fillcolor="rgba(44, 160, 44, 0.1)",
            line=dict(color=COLORS["success"], dash="dash"),
        )
    )
    fig.add_trace(
        go.Scatterpolar(
            r=cluster_closed,
            theta=labels_closed,
            fill="toself",
            name="클러스터 평균",
            fillcolor="rgba(31, 119, 180, 0.1)",
            line=dict(color=COLORS["info"], dash="dot"),
        )
    )
    fig.add_trace(
        go.Scatterpolar(
            r=seller_closed,
            theta=labels_closed,
            fill="toself",
            name="이 셀러",
            fillcolor="rgba(255, 127, 14, 0.2)",
            line=dict(color=COLORS["warning"], width=2),
        )
    )

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 150])),
        showlegend=True,
        title=title,
        height=400,
        margin=dict(t=60, b=30, l=60, r=60),
    )
    return fig


def monthly_trend_chart(
    monthly_orders,
    monthly_revenue,
) -> go.Figure:
    """월별 주문수(바) + 매출(라인) 듀얼 Y축."""
    fig = go.Figure()

    if monthly_orders is not None and not monthly_orders.empty:
        fig.add_trace(
            go.Bar(
                x=monthly_orders["order_month"],
                y=monthly_orders["orders"],
                name="주문수",
                marker_color=COLORS["primary"],
                opacity=0.7,
                yaxis="y",
            )
        )

    if monthly_revenue is not None and not monthly_revenue.empty:
        fig.add_trace(
            go.Scatter(
                x=monthly_revenue["order_month"],
                y=monthly_revenue["revenue"],
                name="매출 (R$)",
                line=dict(color=COLORS["warning"], width=2),
                yaxis="y2",
            )
        )

    fig.update_layout(
        title="월별 주문 & 매출 추이",
        xaxis=dict(title="월"),
        yaxis=dict(title="주문수", side="left"),
        yaxis2=dict(title="매출 (R$)", side="right", overlaying="y"),
        legend=dict(x=0, y=1.1, orientation="h"),
        height=350,
        margin=dict(t=60, b=40),
    )
    return fig


def review_trend_chart(monthly_review) -> go.Figure:
    """월별 리뷰 점수 추이."""
    fig = go.Figure()
    if monthly_review is not None and not monthly_review.empty:
        fig.add_trace(
            go.Scatter(
                x=monthly_review["order_month"],
                y=monthly_review["avg_review"],
                mode="lines+markers",
                name="평균 리뷰",
                line=dict(color=COLORS["success"], width=2),
                marker=dict(size=8),
            )
        )
        # 기준선
        fig.add_hline(
            y=3.89, line_dash="dash", line_color="gray",
            annotation_text="플랫폼 평균 (3.89)",
        )
    fig.update_layout(
        title="월별 리뷰 점수 추이",
        xaxis=dict(title="월"),
        yaxis=dict(title="평균 리뷰 점수", range=[1, 5]),
        height=350,
        margin=dict(t=60, b=40),
    )
    return fig


def category_pie(category_revenue) -> go.Figure:
    """카테고리별 매출 비중 파이 차트."""
    if category_revenue is None or category_revenue.empty:
        return _empty_chart("카테고리 데이터 없음")

    fig = go.Figure(
        go.Pie(
            labels=category_revenue["category"],
            values=category_revenue["revenue"],
            hole=0.4,
            textinfo="percent+label",
            textposition="outside",
        )
    )
    fig.update_layout(
        title="카테고리별 매출 비중",
        height=350,
        margin=dict(t=60, b=20, l=20, r=20),
        showlegend=False,
    )
    return fig


def state_bar(customer_state_dist) -> go.Figure:
    """고객 지역 분포 바 차트."""
    if customer_state_dist is None or customer_state_dist.empty:
        return _empty_chart("지역 데이터 없음")

    fig = go.Figure(
        go.Bar(
            x=customer_state_dist["state"],
            y=customer_state_dist["customers"],
            marker_color=COLORS["primary"],
        )
    )
    fig.update_layout(
        title="고객 지역 분포 (상위 10)",
        xaxis=dict(title="주"),
        yaxis=dict(title="고객 수"),
        height=350,
        margin=dict(t=60, b=40),
    )
    return fig


def delivery_histogram(delivery_days_list: list) -> go.Figure:
    """배송일 분포 히스토그램."""
    if not delivery_days_list:
        return _empty_chart("배송 데이터 없음")

    avg_days = np.mean(delivery_days_list)
    fig = go.Figure(
        go.Histogram(
            x=delivery_days_list,
            nbinsx=20,
            marker_color=COLORS["primary"],
            opacity=0.7,
        )
    )
    fig.add_vline(
        x=avg_days, line_dash="dash", line_color=COLORS["danger"],
        annotation_text=f"평균 {avg_days:.1f}일",
    )
    fig.update_layout(
        title="배송일 분포",
        xaxis=dict(title="배송일 (일)"),
        yaxis=dict(title="건수"),
        height=350,
        margin=dict(t=60, b=40),
    )
    return fig


def review_distribution(review_dist) -> go.Figure:
    """리뷰 점수 분포 (색상 코딩)."""
    if review_dist is None or review_dist.empty:
        return _empty_chart("리뷰 데이터 없음")

    colors = []
    for score in review_dist["score"]:
        if score >= 4:
            colors.append(COLORS["success"])
        elif score >= 3:
            colors.append(COLORS["warning"])
        else:
            colors.append(COLORS["danger"])

    fig = go.Figure(
        go.Bar(
            x=review_dist["score"].astype(str) + "점",
            y=review_dist["count"],
            marker_color=colors,
        )
    )
    fig.update_layout(
        title="리뷰 점수 분포",
        xaxis=dict(title="리뷰 점수"),
        yaxis=dict(title="건수"),
        height=350,
        margin=dict(t=60, b=40),
    )
    return fig


def health_gauge(score: float) -> go.Figure:
    """건강 점수 게이지 차트."""
    color = health_grade_color(score)
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            title={"text": "셀러 건강 점수"},
            gauge=dict(
                axis=dict(range=[0, 100]),
                bar=dict(color=color),
                steps=[
                    dict(range=[0, 20], color="#f7d7d7"),
                    dict(range=[20, 40], color="#fde8d0"),
                    dict(range=[40, 60], color="#fff3cd"),
                    dict(range=[60, 80], color="#d4edda"),
                    dict(range=[80, 100], color="#c3e6cb"),
                ],
                threshold=dict(
                    line=dict(color="black", width=2),
                    thickness=0.75,
                    value=score,
                ),
            ),
        )
    )
    fig.update_layout(height=250, margin=dict(t=60, b=20))
    return fig


def cluster_donut(dist_df, label_map: dict, title: str) -> go.Figure:
    """클러스터 분포 도넛 차트."""
    if dist_df is None or dist_df.empty:
        return _empty_chart(f"{title} 데이터 없음")

    labels = [label_map.get(int(c), f"클러스터 {c}") for c in dist_df["cluster"]]
    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=dist_df["count"],
            hole=0.5,
            textinfo="percent+label",
        )
    )
    fig.update_layout(
        title=title,
        height=350,
        margin=dict(t=60, b=20, l=20, r=20),
        showlegend=False,
    )
    return fig


def health_breakdown_bar(dimension_scores: dict[str, float]) -> go.Figure:
    """건강 점수 차원별 분해 바 차트."""
    dims = list(dimension_scores.keys())
    labels = [HEALTH_DIMENSIONS.get(d, d) for d in dims]
    values = [dimension_scores[d] for d in dims]

    colors = []
    for v in values:
        if v >= 70:
            colors.append(COLORS["success"])
        elif v >= 40:
            colors.append(COLORS["warning"])
        else:
            colors.append(COLORS["danger"])

    fig = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker_color=colors,
            text=[f"{v:.0f}" for v in values],
            textposition="outside",
        )
    )
    fig.update_layout(
        title="건강 점수 차원별 분석",
        xaxis=dict(title="점수", range=[0, 110]),
        height=300,
        margin=dict(t=60, b=40, l=80),
    )
    return fig


def _empty_chart(message: str) -> go.Figure:
    """데이터 없을 때 빈 차트."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=16, color="gray"),
    )
    fig.update_layout(
        height=300,
        margin=dict(t=40, b=20),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig
