"""Plotly 차트 컴포넌트."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from claude_eda.dashboard.config import COLORS, STATE_CENTER_COORDS
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


def review_keyword_bar(issue_counts: dict, analyzed_count: int) -> go.Figure:
    """리뷰 키워드 분석 — 이슈 카테고리별 바 차트."""
    if not issue_counts:
        return _empty_chart("텍스트 리뷰 데이터 없음")

    categories = list(issue_counts.keys())
    counts = list(issue_counts.values())
    color_map = {
        "배송 지연": COLORS["warning"],
        "상품 품질": COLORS["danger"],
        "포장 문제": "#9467bd",
        "기대 불일치": COLORS["info"],
    }
    colors = [color_map.get(c, COLORS["primary"]) for c in categories]

    fig = go.Figure(
        go.Bar(
            x=counts,
            y=categories,
            orientation="h",
            marker_color=colors,
            text=[f"{c}건 ({c/analyzed_count:.0%})" if analyzed_count > 0 else f"{c}건"
                  for c in counts],
            textposition="outside",
        )
    )
    fig.update_layout(
        title=f"리뷰 이슈 키워드 분석 (텍스트 리뷰 {analyzed_count}건 중)",
        xaxis=dict(title="건수"),
        height=300,
        margin=dict(t=60, b=40, l=100),
    )
    return fig


def category_rank_table(category_ranks) -> go.Figure:
    """카테고리 내 순위 테이블 차트."""
    if category_ranks is None or category_ranks.empty:
        return _empty_chart("카테고리 순위 데이터 없음")

    fig = go.Figure(
        go.Table(
            header=dict(
                values=["카테고리", "셀러 수", "매출 순위", "리뷰 순위", "내 매출(R$)", "내 리뷰"],
                fill_color=COLORS["primary"],
                font=dict(color="white", size=12),
                align="center",
            ),
            cells=dict(
                values=[
                    category_ranks["category"],
                    category_ranks["total_sellers"],
                    [f"{r}위" for r in category_ranks["revenue_rank"]],
                    [f"{r}위" for r in category_ranks["review_rank"]],
                    [f"R${v:,.0f}" for v in category_ranks["my_revenue"]],
                    [f"{v:.1f}" for v in category_ranks["my_review"]],
                ],
                fill_color="white",
                align="center",
                font=dict(size=11),
            ),
        )
    )
    fig.update_layout(
        title="카테고리 내 경쟁 순위",
        height=250,
        margin=dict(t=60, b=20),
    )
    return fig


def distance_delivery_bar(distance_delivery) -> go.Figure:
    """거리 구간별 평균 배송일 바 차트."""
    if distance_delivery is None or distance_delivery.empty:
        return _empty_chart("거리 데이터 없음")

    fig = go.Figure(
        go.Bar(
            x=distance_delivery["dist_bin"].astype(str),
            y=distance_delivery["avg_days"],
            marker_color=COLORS["primary"],
            text=[f"{d:.1f}일\n({c}건)"
                  for d, c in zip(distance_delivery["avg_days"], distance_delivery["count"])],
            textposition="outside",
        )
    )
    fig.update_layout(
        title="거리별 평균 배송일",
        xaxis=dict(title="셀러-고객 거리"),
        yaxis=dict(title="평균 배송일"),
        height=350,
        margin=dict(t=60, b=40),
    )
    return fig


def payment_donut(payment_type_dist) -> go.Figure:
    """결제 수단 분포 도넛 차트."""
    if payment_type_dist is None or payment_type_dist.empty:
        return _empty_chart("결제 데이터 없음")

    label_map = {
        "credit_card": "신용카드",
        "boleto": "볼레토",
        "voucher": "바우처",
        "debit_card": "체크카드",
        "not_defined": "미정의",
    }
    labels = [label_map.get(t, t) for t in payment_type_dist["payment_type"]]

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=payment_type_dist["count"],
            hole=0.45,
            textinfo="percent+label",
        )
    )
    fig.update_layout(
        title="결제 수단 분포",
        height=350,
        margin=dict(t=60, b=20, l=20, r=20),
        showlegend=False,
    )
    return fig


def supply_demand_chart(sd_df, seller_state: str = "") -> go.Figure:
    """지역별 수급 불균형 수평 바 차트."""
    if sd_df is None or sd_df.empty:
        return _empty_chart("지역 데이터 없음")

    top15 = sd_df.head(15).copy()
    top15 = top15.sort_values("ratio", ascending=True)

    grade_colors = {
        "긴급 공급 부족": COLORS["danger"],
        "진출 가능": COLORS["danger"],
        "높은 기회": COLORS["warning"],
        "중간 기회": COLORS["info"],
        "포화": COLORS["muted"],
    }
    colors = [grade_colors.get(g, COLORS["primary"]) for g in top15["opportunity_grade"]]

    # 셀러 위치 강조
    labels = []
    for _, r in top15.iterrows():
        marker = " ★" if r["state"] == seller_state else ""
        labels.append(f"{r['state']}{marker}")

    fig = go.Figure(
        go.Bar(
            x=top15["ratio"],
            y=labels,
            orientation="h",
            marker_color=colors,
            text=[f"{r:.0f}:1 ({g})"
                  for r, g in zip(top15["ratio"], top15["opportunity_grade"])],
            textposition="outside",
        )
    )
    fig.update_layout(
        title="전체 시장 수급 현황 (고객/셀러 비율)",
        xaxis=dict(title="고객/셀러 비율"),
        height=420,
        margin=dict(t=50, b=30, l=50, r=120),
    )
    return fig


def price_boxplot(price_stats_df, seller_prices: dict | None = None) -> go.Figure:
    """카테고리별 가격 분포 박스플롯 (시장 vs 셀러)."""
    if price_stats_df is None or price_stats_df.empty:
        return _empty_chart("가격 데이터 없음")

    top10 = price_stats_df.head(10)
    categories = top10["category"].tolist()

    fig = go.Figure()

    # 시장 가격 범위 (P25-P75 박스)
    for _, row in top10.iterrows():
        cat = row["category"]
        fig.add_trace(go.Box(
            x=[cat],
            lowerfence=[row["p25"]],
            q1=[row["p25"]],
            median=[row["median_price"]],
            q3=[row["p75"]],
            upperfence=[row["p75"]],
            name="시장",
            marker_color=COLORS["info"],
            showlegend=False,
        ))

    # 셀러 가격 마커
    if seller_prices:
        seller_cats = []
        seller_vals = []
        for cat in categories:
            if cat in seller_prices:
                seller_cats.append(cat)
                seller_vals.append(seller_prices[cat])
        if seller_cats:
            fig.add_trace(go.Scatter(
                x=seller_cats,
                y=seller_vals,
                mode="markers",
                name="내 평균가",
                marker=dict(color=COLORS["warning"], size=12, symbol="diamond"),
            ))

    fig.update_layout(
        title="카테고리별 가격 분포 (P25-P75) vs 내 가격",
        yaxis=dict(title="가격 (R$)"),
        height=400,
        margin=dict(t=60, b=80),
        showlegend=True,
    )
    fig.update_xaxes(tickangle=30)
    return fig


def regional_price_table(price_by_state_df) -> go.Figure:
    """지역별 가격 비교 테이블."""
    if price_by_state_df is None or price_by_state_df.empty:
        return _empty_chart("지역별 가격 데이터 없음")

    top10 = price_by_state_df.head(10)
    fig = go.Figure(
        go.Table(
            header=dict(
                values=["주(State)", "평균 가격(R$)", "중앙값(R$)", "주문 수"],
                fill_color=COLORS["primary"],
                font=dict(color="white", size=12),
                align="center",
            ),
            cells=dict(
                values=[
                    top10["state"],
                    [f"R${v:,.0f}" for v in top10["avg_price"]],
                    [f"R${v:,.0f}" for v in top10["median_price"]],
                    [f"{v:,}" for v in top10["orders"]],
                ],
                fill_color="white",
                align="center",
                font=dict(size=11),
            ),
        )
    )
    fig.update_layout(
        title="지역별 가격 비교",
        height=300,
        margin=dict(t=60, b=20),
    )
    return fig


def revenue_simulation_chart(simulation_data: list[dict]) -> go.Figure:
    """가격대별 매출 시뮬레이션 바 차트."""
    if not simulation_data:
        return _empty_chart("시뮬레이션 데이터 없음")

    labels = [d["label"] for d in simulation_data]
    revenues = [d["estimated_monthly_revenue"] for d in simulation_data]
    orders = [d["estimated_monthly_orders"] for d in simulation_data]
    shares = [d["order_share"] for d in simulation_data]

    bar_colors = [COLORS["info"], COLORS["success"], COLORS["warning"], COLORS["danger"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=labels,
        y=revenues,
        marker_color=bar_colors[:len(labels)],
        text=[f"R${r:,.0f}\n({o:.1f}건/월, {s:.0%})"
              for r, o, s in zip(revenues, orders, shares)],
        textposition="outside",
    ))

    fig.update_layout(
        title="가격대별 예상 월 매출 시뮬레이션",
        yaxis=dict(title="예상 월 매출 (R$)"),
        height=350,
        margin=dict(t=60, b=40),
    )
    return fig


def category_opportunity_table(opp_df) -> go.Figure:
    """미진출 카테고리 기회 테이블."""
    if opp_df is None or opp_df.empty:
        return _empty_chart("카테고리 기회 데이터 없음")

    top8 = opp_df.head(8)
    fig = go.Figure(
        go.Table(
            header=dict(
                values=["카테고리", "시장 매출(R$)", "총 주문", "경쟁 셀러",
                         "셀러당 주문", "평균가(R$)", "기회 점수"],
                fill_color=COLORS["primary"],
                font=dict(color="white", size=11),
                align="center",
            ),
            cells=dict(
                values=[
                    top8["category"],
                    [f"R${v:,.0f}" for v in top8["total_revenue"]],
                    [f"{v:,}" for v in top8["total_orders"]],
                    top8["total_sellers"],
                    [f"{v:.0f}" for v in top8["orders_per_seller"]],
                    [f"R${v:.0f}" for v in top8["avg_price"]],
                    [f"{v:.1f}" for v in top8["opportunity_score"]],
                ],
                fill_color="white",
                align="center",
                font=dict(size=11),
            ),
        )
    )
    fig.update_layout(
        title="미진출 고기회 카테고리",
        height=300,
        margin=dict(t=60, b=20),
    )
    return fig


def logistics_map(
    seller_lat: float, seller_lng: float, seller_state: str,
    customer_points, warehouse_recs,
) -> go.Figure:
    """셀러 + 고객 분포 + 창고 위치 지도 (Plotly scatter)."""
    fig = go.Figure()

    # 고객 분포
    if customer_points is not None and not customer_points.empty:
        fig.add_trace(go.Scattergeo(
            lat=customer_points["lat"],
            lon=customer_points["lng"],
            marker=dict(
                size=np.clip(customer_points["order_count"] * 2, 3, 20),
                color=COLORS["info"],
                opacity=0.4,
                line=dict(width=0),
            ),
            name="고객",
            hovertemplate="고객 %{text}<extra></extra>",
            text=[f'{s} ({n}건)' for s, n in
                  zip(customer_points["state"], customer_points["order_count"])],
        ))

    # 셀러 위치
    if seller_lat is not None:
        fig.add_trace(go.Scattergeo(
            lat=[seller_lat], lon=[seller_lng],
            marker=dict(size=16, color=COLORS["warning"], symbol="diamond",
                        line=dict(width=2, color="black")),
            name=f"셀러 ({seller_state})",
            hovertemplate=f"셀러 위치 ({seller_state})<extra></extra>",
        ))

    # 창고 위치
    priority_colors = {"1차 (즉시)": "#F44336", "2차 (6개월)": "#FF9800", "3차 (12개월)": "#4CAF50"}
    if warehouse_recs is not None and not warehouse_recs.empty:
        for _, row in warehouse_recs.iterrows():
            color = priority_colors.get(row["priority"], "#999")
            fig.add_trace(go.Scattergeo(
                lat=[row["lat"]], lon=[row["lng"]],
                marker=dict(size=14, color=color, symbol="star",
                            line=dict(width=1.5, color="black")),
                name=f"WH{int(row['warehouse_id'])}: {row['nearest_city']}",
                hovertemplate=(
                    f"WH{int(row['warehouse_id'])}: {row['nearest_city']}, {row['state']}<br>"
                    f"우선순위: {row['priority']}<extra></extra>"
                ),
                showlegend=True,
            ))

    fig.update_geos(
        scope="south america",
        showland=True, landcolor="#f0f0f0",
        showcoastlines=True, coastlinecolor="#ccc",
        showcountries=True, countrycolor="#ccc",
        showsubunits=True, subunitcolor="#ddd",
        fitbounds="locations",
        resolution=50,
    )
    fig.update_layout(
        title="셀러 · 고객 · 추천 창고 위치",
        height=500,
        margin=dict(t=50, b=20, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5,
                    font=dict(size=10)),
    )
    return fig


def warehouse_ranking_bar(warehouse_recs) -> go.Figure:
    """셀러에게 유리한 창고 순위 (고객→창고 평균 거리)."""
    if warehouse_recs is None or warehouse_recs.empty:
        return _empty_chart("창고 데이터 없음")

    wh = warehouse_recs.sort_values("customer_to_wh_km")
    priority_colors = {"1차 (즉시)": "#F44336", "2차 (6개월)": "#FF9800", "3차 (12개월)": "#4CAF50"}
    colors = [priority_colors.get(p, "#999") for p in wh["priority"]]
    labels = [f"WH{int(r['warehouse_id'])}: {r['nearest_city']}, {r['state']}" for _, r in wh.iterrows()]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=wh["customer_to_wh_km"],
        y=labels,
        orientation="h",
        marker_color=colors,
        text=[f"{d:.0f}km (↓{r:.0f}%)" for d, r in
              zip(wh["customer_to_wh_km"], wh["reduction_pct"])],
        textposition="outside",
    ))
    fig.update_layout(
        title="창고별 고객 평균 거리 (낮을수록 유리)",
        xaxis=dict(title="고객→창고 평균 거리 (km)"),
        height=350,
        margin=dict(t=50, b=40, l=180, r=80),
    )
    return fig


def logistics_scenario_bar(simulation: list[dict]) -> go.Figure:
    """시나리오별 평균 거리 비교 바 차트."""
    if not simulation:
        return _empty_chart("시뮬레이션 데이터 없음")

    scenarios = [s["scenario"] for s in simulation]
    distances = [s["avg_distance"] for s in simulation]
    bar_colors = [COLORS["muted"], COLORS["primary"], COLORS["info"], COLORS["success"]]

    fig = go.Figure(go.Bar(
        x=scenarios,
        y=distances,
        marker_color=bar_colors[:len(scenarios)],
        text=[f"{d:.0f}km" for d in distances],
        textposition="outside",
    ))

    # 현재 대비 감소율 주석
    if len(distances) > 1:
        current = distances[0]
        for i in range(1, len(distances)):
            pct = (1 - distances[i] / current) * 100 if current > 0 else 0
            fig.add_annotation(
                x=scenarios[i], y=distances[i] + 15,
                text=f"-{pct:.0f}%", showarrow=False,
                font=dict(size=12, color=bar_colors[i], weight="bold"),
            )

    fig.update_layout(
        title="시나리오별 평균 배송 거리",
        yaxis=dict(title="평균 거리 (km)"),
        height=400,
        margin=dict(t=50, b=60),
    )
    return fig


def logistics_savings_bar(simulation: list[dict]) -> go.Figure:
    """시나리오별 운임/배송일 절감 비교."""
    if not simulation or len(simulation) < 2:
        return _empty_chart("시뮬레이션 데이터 없음")

    current = simulation[0]
    scenarios = [s["scenario"] for s in simulation[1:]]
    freight_saves = [current["est_freight"] - s["est_freight"] for s in simulation[1:]]
    days_saves = [current["est_days"] - s["est_days"] for s in simulation[1:]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=scenarios, y=freight_saves,
        name="운임 절감 (R$)",
        marker_color=COLORS["primary"],
        text=[f"R${v:.1f}" for v in freight_saves],
        textposition="outside",
        yaxis="y",
    ))
    fig.add_trace(go.Bar(
        x=scenarios, y=days_saves,
        name="배송일 단축 (일)",
        marker_color=COLORS["success"],
        text=[f"{v:.1f}일" for v in days_saves],
        textposition="outside",
        yaxis="y2",
    ))

    fig.update_layout(
        title="시나리오별 절감 효과 (운임 & 배송일)",
        yaxis=dict(title="운임 절감 (R$)", side="left"),
        yaxis2=dict(title="배송일 단축 (일)", side="right", overlaying="y"),
        barmode="group",
        legend=dict(orientation="h", y=1.12, x=0.5, xanchor="center"),
        height=400,
        margin=dict(t=70, b=60),
    )
    return fig


def region_effect_bar(region_effect) -> go.Figure:
    """권역별 5개 창고 활용 시 거리 감소 효과."""
    if region_effect is None or region_effect.empty:
        return _empty_chart("권역별 데이터 없음")

    re = region_effect.sort_values("reduction", ascending=True)
    region_colors = {
        "Southeast": "#2196F3", "South": "#4CAF50", "Northeast": "#FF5722",
        "Central-West": "#FFC107", "North": "#9C27B0",
    }
    colors = [region_colors.get(r, "#999") for r in re["region"]]

    fig = go.Figure(go.Bar(
        x=re["reduction"],
        y=re["region"],
        orientation="h",
        marker_color=colors,
        text=[f"{d:.0f}km (↓{p:.0f}%) · {o}건" for d, p, o in
              zip(re["reduction"], re["reduction_pct"], re["orders"])],
        textposition="outside",
    ))
    fig.update_layout(
        title="권역별 거리 감소 효과 (5개 창고)",
        xaxis=dict(title="평균 거리 감소 (km)"),
        height=350,
        margin=dict(t=50, b=40, l=100, r=120),
    )
    return fig


def delivery_inventory_map(
    seller_lat: float | None,
    seller_lng: float | None,
    seller_state: str,
    customer_points,
    warehouse_df,
    warehouse_inventory_summary: dict[str, dict],
    regional_delivery_days: dict[str, float],
) -> go.Figure:
    """배송·재고 통합 지도 — 고객 분포 + 5개 창고(재고 hover) + 지역별 배송일 라벨."""
    fig = go.Figure()

    # 1) 고객 분포 (파란 원)
    if customer_points is not None and not customer_points.empty:
        fig.add_trace(go.Scattergeo(
            lat=customer_points["lat"],
            lon=customer_points["lng"],
            marker=dict(
                size=np.clip(customer_points["order_count"] * 2, 3, 20),
                color=COLORS["info"],
                opacity=0.4,
                line=dict(width=0),
            ),
            name="고객",
            hovertemplate="고객 %{text}<extra></extra>",
            text=[f'{s} ({n}건)' for s, n in
                  zip(customer_points["state"], customer_points["order_count"])],
        ))

    # 2) 셀러 위치 (다이아몬드)
    if seller_lat is not None:
        fig.add_trace(go.Scattergeo(
            lat=[seller_lat], lon=[seller_lng],
            marker=dict(size=16, color=COLORS["warning"], symbol="diamond",
                        line=dict(width=2, color="black")),
            name=f"셀러 ({seller_state})",
            hovertemplate=f"셀러 위치 ({seller_state})<extra></extra>",
        ))

    # 3) 5개 창고 (별 마커 + 재고 요약 hover)
    priority_colors = {
        "Phase1": "#F44336", "Phase2": "#FF9800", "Phase3": "#4CAF50",
        "1차 (즉시)": "#F44336", "2차 (6개월)": "#FF9800", "3차 (12개월)": "#4CAF50",
    }
    if warehouse_df is not None and not warehouse_df.empty:
        for _, row in warehouse_df.iterrows():
            wid = row["warehouse_id"]
            color = priority_colors.get(
                row.get("priority_phase", row.get("priority", "")), "#999"
            )
            inv_info = warehouse_inventory_summary.get(wid, {})
            product_count = inv_info.get("product_count", 0)
            available_qty = inv_info.get("available_qty", 0)
            reorder_alerts = inv_info.get("reorder_alerts", 0)

            hover_text = (
                f"<b>{row.get('warehouse_name', wid)}</b><br>"
                f"{row.get('warehouse_city', row.get('nearest_city', ''))}, "
                f"{row.get('warehouse_state', row.get('state', ''))}<br>"
                f"용량: {row.get('capacity_units', 0):,}개<br>"
                f"───────────<br>"
                f"상품 수: {product_count}종<br>"
                f"가용 수량: {available_qty:,}개<br>"
                f"발주 경고: {reorder_alerts}건"
            )
            fig.add_trace(go.Scattergeo(
                lat=[row.get("warehouse_lat", row.get("lat", 0))],
                lon=[row.get("warehouse_lng", row.get("lng", 0))],
                marker=dict(size=14, color=color, symbol="star",
                            line=dict(width=1.5, color="black")),
                name=f"{wid}: {row.get('warehouse_name', '')}",
                hovertemplate=hover_text + "<extra></extra>",
                showlegend=True,
            ))

    # 4) 지역별 평균 배송일 텍스트 라벨
    if regional_delivery_days:
        label_lats = []
        label_lons = []
        label_texts = []
        label_colors = []
        for state_code, avg_days in regional_delivery_days.items():
            coords = STATE_CENTER_COORDS.get(state_code)
            if coords is None:
                continue
            label_lats.append(coords[0])
            label_lons.append(coords[1])
            label_texts.append(f"{state_code}<br><b>{avg_days:.0f}일</b>")
            if avg_days <= 10:
                label_colors.append("#2ca02c")
            elif avg_days <= 20:
                label_colors.append("#ff7f0e")
            else:
                label_colors.append("#d62728")

        if label_texts:
            fig.add_trace(go.Scattergeo(
                lat=label_lats,
                lon=label_lons,
                mode="text",
                text=label_texts,
                textfont=dict(size=9, color=label_colors),
                textposition="middle center",
                name="배송 소요일",
                hoverinfo="skip",
                showlegend=True,
            ))

    fig.update_geos(
        scope="south america",
        showland=True, landcolor="#f0f0f0",
        showcoastlines=True, coastlinecolor="#ccc",
        showcountries=True, countrycolor="#ccc",
        showsubunits=True, subunitcolor="#ddd",
        fitbounds="locations",
        resolution=50,
    )
    fig.update_layout(
        title="물류·재고 지도 — 고객 · 창고 · 배송 소요일",
        height=550,
        margin=dict(t=50, b=20, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5,
                    font=dict(size=10)),
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
