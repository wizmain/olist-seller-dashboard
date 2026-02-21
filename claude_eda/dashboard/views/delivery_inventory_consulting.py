"""Page 6: 배송·재고 컨설팅."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from claude_eda.dashboard.components.charts import delivery_inventory_map
from claude_eda.dashboard.config import COLORS, PRIORITY_COLORS
from claude_eda.dashboard.data.delivery_analyzer import (
    compute_regional_delivery_days,
    compute_seller_delivery,
)
from claude_eda.dashboard.data.inventory_loader import (
    get_seller_inventory_summary,
    load_reorder_rules,
    load_warehouse_inventory,
    load_warehouses,
)
from claude_eda.dashboard.data.loader import load_product_names
from claude_eda.dashboard.data.logistics_analyzer import compute_seller_logistics
from claude_eda.dashboard.data.preprocessor import SellerMetrics
from claude_eda.dashboard.engine.delivery_rules import (
    generate_delivery_advice,
    generate_delivery_roadmap,
)
from claude_eda.dashboard.utils.formatting import fmt_pct_value
from claude_eda.dashboard.utils.korean import STATE_NAMES_KR


def render_delivery_inventory_consulting(metrics: SellerMetrics) -> None:
    """배송·재고 컨설팅 페이지 렌더."""
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #00695C 0%, #004D40 50%, #1B5E20 100%);
             padding: 20px 24px; border-radius: 8px; margin-bottom: 16px;">
            <h2 style="color: white; margin: 0 0 8px 0;">배송·재고 컨설팅</h2>
            <span style="color: rgba(255,255,255,0.85); font-size: 0.95em;">
                셀러 <code style="background: rgba(255,255,255,0.2); color: white;
                padding: 2px 6px; border-radius: 4px;">{metrics.company_name or metrics.seller_id[:12]}</code>
                &nbsp;&nbsp;|&nbsp;&nbsp;
                지역: <b>{STATE_NAMES_KR.get(metrics.seller_state, metrics.seller_state)}</b>
                &nbsp;&nbsp;|&nbsp;&nbsp;
                배송 성과 진단 · 물류 지도 · 재고 현황 · 맞춤 컨설팅
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.spinner("배송·재고 데이터 분석 중..."):
        delivery = compute_seller_delivery(metrics.seller_id)
        inventory = get_seller_inventory_summary(metrics.seller_id)

    if not delivery.get("has_data"):
        st.warning("이 셀러의 배송 완료 주문이 없어 분석이 불가합니다.")
        return

    # 섹션 1: 배송 성과 진단
    _render_delivery_diagnosis(delivery)
    st.write("")

    # 섹션 2: 물류·재고 지도
    _render_logistics_map(metrics)
    st.write("")

    # 섹션 3: 재고·발주 현황
    _render_inventory_status(inventory)
    st.write("")

    # 섹션 4: 통합 컨설팅 액션
    _render_consulting_actions(delivery, inventory)


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


# ═══════════════════════════════════════════════════════════════
# 섹션 1: 배송 성과 진단
# ═══════════════════════════════════════════════════════════════

def _render_delivery_diagnosis(d: dict) -> None:
    _section_header("배송 성과 진단", "📦", "셀러의 발송·배송 지연 현황을 플랫폼 평균과 비교합니다")

    # KPI 카드 4개
    col1, col2, col3, col4 = st.columns(4)

    dispatch_rate = d["dispatch_delay_rate"]
    platform_dispatch = d["platform_dispatch_delay_rate"]
    delivery_rate = d["delivery_delay_rate"]
    platform_delivery = d["platform_delivery_delay_rate"]

    with col1:
        delta = dispatch_rate - platform_dispatch
        st.metric(
            "발송 지연율",
            f"{dispatch_rate:.1%}",
            delta=f"{delta:+.1%}p vs 평균",
            delta_color="inverse",
        )
    with col2:
        delta = delivery_rate - platform_delivery
        st.metric(
            "배송 지연율",
            f"{delivery_rate:.1%}",
            delta=f"{delta:+.1%}p vs 평균",
            delta_color="inverse",
        )
    with col3:
        avg_total = d["avg_total_delivery"]
        platform_total = d["platform_avg_total_delivery"]
        st.metric(
            "평균 배송 소요",
            f"{avg_total:.1f}일",
            delta=f"{avg_total - platform_total:+.1f}일 vs 평균",
            delta_color="inverse",
        )
    with col4:
        st.metric("분석 주문 수", f"{d['seller_orders']:,}건")

    col_left, col_right = st.columns(2)

    # 발송 지연 구간별 분포
    with col_left:
        dist = d["dispatch_group_dist"]
        labels = list(dist.keys())
        values = list(dist.values())
        color_map = [COLORS["success"], COLORS["warning"], COLORS["danger"], "#C0392B"]

        fig = go.Figure(go.Bar(
            x=labels, y=values,
            marker_color=color_map,
            text=[f"{v}건<br>({v/sum(values):.0%})" if sum(values) > 0 else "0" for v in values],
            textposition="outside",
        ))
        fig.update_layout(
            title="발송 지연 구간별 주문 분포",
            yaxis_title="주문 수",
            height=350,
            margin=dict(t=50, b=40),
        )
        st.plotly_chart(fig, use_container_width=True)

    # 월별 배송 지연율 추이
    with col_right:
        seller_m = d["seller_monthly"]
        platform_m = d["platform_monthly"]

        fig = go.Figure()
        if not seller_m.empty:
            fig.add_trace(go.Scatter(
                x=seller_m["order_ym"], y=seller_m["delivery_delay_rate"] * 100,
                mode="lines+markers", name="셀러 배송 지연율",
                line=dict(color=COLORS["danger"], width=2.5),
                marker=dict(size=7),
            ))
        if not platform_m.empty:
            fig.add_trace(go.Scatter(
                x=platform_m["order_ym"], y=platform_m["delivery_delay_rate"] * 100,
                mode="lines", name="플랫폼 평균",
                line=dict(color=COLORS["muted"], width=1.5, dash="dash"),
            ))
        fig.update_layout(
            title="월별 배송 지연율 추이",
            yaxis_title="배송 지연율 (%)",
            height=350,
            margin=dict(t=50, b=40),
            legend=dict(orientation="h", y=-0.15),
        )
        st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# 섹션 2: 물류·재고 지도
# ═══════════════════════════════════════════════════════════════

def _build_warehouse_inventory_summary() -> dict[str, dict]:
    """5개 창고 각각의 재고 요약(상품 수, 가용 수량, 발주 경고 수)."""
    warehouses = load_warehouses()
    inventory = load_warehouse_inventory()
    reorder = load_reorder_rules()

    summary: dict[str, dict] = {}
    for _, wh in warehouses.iterrows():
        wid = wh["warehouse_id"]
        inv = inventory[inventory["warehouse_id"] == wid]
        product_count = len(inv)
        available_qty = int(inv["quantity_available"].sum()) if not inv.empty else 0

        # 발주 경고 수
        reorder_alerts = 0
        if not inv.empty:
            rules = reorder[reorder["warehouse_id"] == wid]
            if not rules.empty:
                merged = inv.merge(rules, on=["warehouse_id", "product_id"], how="inner")
                reorder_alerts = int(
                    (merged["quantity_available"] <= merged["reorder_point"]).sum()
                )

        summary[wid] = {
            "product_count": product_count,
            "available_qty": available_qty,
            "reorder_alerts": reorder_alerts,
        }
    return summary


def _render_logistics_map(metrics: SellerMetrics) -> None:
    _section_header(
        "물류·재고 지도", "🗺️",
        "5개 창고 위치 · 지역별 배송 소요일 · 고객 분포를 한눈에 확인합니다",
    )

    with st.spinner("물류 지도 데이터 로딩 중..."):
        logi = compute_seller_logistics(metrics.seller_id)
        regional_days = compute_regional_delivery_days(metrics.seller_id)
        wh_inv_summary = _build_warehouse_inventory_summary()
        warehouses = load_warehouses()

    if logi["seller_lat"] is None:
        st.caption("셀러 위치 데이터가 없어 지도를 표시할 수 없습니다.")
        return

    # 지도 렌더링
    fig = delivery_inventory_map(
        seller_lat=logi["seller_lat"],
        seller_lng=logi["seller_lng"],
        seller_state=logi["seller_state"],
        customer_points=logi["customer_points"],
        warehouse_df=warehouses,
        warehouse_inventory_summary=wh_inv_summary,
        regional_delivery_days=regional_days,
    )
    st.plotly_chart(fig, use_container_width=True)

    # 창고 선택 → 재고 상세 테이블
    wh_options = {
        f"{row['warehouse_id']}: {row['warehouse_name']} ({row['warehouse_city']}, {row['warehouse_state']})": row["warehouse_id"]
        for _, row in warehouses.iterrows()
    }
    selected_label = st.selectbox(
        "창고를 선택하면 해당 창고의 셀러 재고 현황을 확인할 수 있습니다",
        options=list(wh_options.keys()),
        key="delivery_inv_wh_select",
    )
    selected_wid = wh_options[selected_label]

    _render_warehouse_inventory_detail(selected_wid, wh_inv_summary)


def _render_warehouse_inventory_detail(warehouse_id: str, summary: dict[str, dict]) -> None:
    """선택한 창고의 재고 상세 테이블."""
    inv_data = load_warehouse_inventory()
    wh_inv = inv_data[inv_data["warehouse_id"] == warehouse_id].copy()

    info = summary.get(warehouse_id, {})
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("상품 수", f"{info.get('product_count', 0)}종")
    with c2:
        st.metric("가용 수량", f"{info.get('available_qty', 0):,}개")
    with c3:
        alerts = info.get("reorder_alerts", 0)
        st.metric(
            "발주 경고",
            f"{alerts}건",
            delta="주의" if alerts > 0 else "양호",
            delta_color="inverse" if alerts > 0 else "off",
        )

    if wh_inv.empty:
        st.caption("이 창고에 재고 데이터가 없습니다.")
        return

    with st.expander(f"재고 상세 ({len(wh_inv)}건)", expanded=False):
        display = wh_inv[["product_id", "quantity_on_hand", "quantity_reserved",
                          "quantity_available", "last_restock_date"]].copy()
        pnames = load_product_names()[["product_id", "product_name_display"]]
        display = display.merge(pnames, on="product_id", how="left")
        display["product_name_display"] = display["product_name_display"].fillna(
            display["product_id"].str[:12] + "..."
        )
        display = display[["product_name_display", "quantity_on_hand", "quantity_reserved",
                           "quantity_available", "last_restock_date"]]
        display.columns = ["상품명", "보유 수량", "출고 예약", "가용 수량", "최근 입고일"]
        st.dataframe(display.head(30), use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════
# 섹션 3: 재고·발주 현황
# ═══════════════════════════════════════════════════════════════

def _render_inventory_status(inv: dict) -> None:
    _section_header("재고·발주 현황", "📋", "셀러 배정 창고의 재고 수준과 발주 필요 상품을 확인합니다")

    if not inv.get("has_data"):
        st.caption("이 셀러의 재고 데이터가 없습니다.")
        return

    # 창고 정보 카드
    col1, col2 = st.columns(2)

    primary = inv.get("primary_info")
    secondary = inv.get("secondary_info")

    with col1:
        if primary:
            st.markdown(
                f"""
                <div style="background: #E8F5E9; border-left: 4px solid {COLORS['success']};
                     padding: 16px; border-radius: 4px;">
                    <h4 style="margin: 0 0 8px 0;">🏭 주 창고: {primary.get('warehouse_name', '')}</h4>
                    <table style="width: 100%; font-size: 0.9em;">
                        <tr><td>ID</td><td style="text-align:right;font-weight:bold;">{inv['primary_warehouse']}</td></tr>
                        <tr><td>위치</td><td style="text-align:right;">{primary.get('warehouse_city', '')} - {primary.get('warehouse_state', '')}</td></tr>
                        <tr><td>권역</td><td style="text-align:right;">{primary.get('region', '')}</td></tr>
                        <tr><td>최대 용량</td><td style="text-align:right;">{primary.get('capacity_units', 0):,}개</td></tr>
                        <tr><td>구축 단계</td><td style="text-align:right;">{primary.get('priority_phase', '')}</td></tr>
                    </table>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col2:
        if secondary:
            st.markdown(
                f"""
                <div style="background: #F3E5F5; border-left: 4px solid {COLORS['info']};
                     padding: 16px; border-radius: 4px;">
                    <h4 style="margin: 0 0 8px 0;">🏭 보조 창고: {secondary.get('warehouse_name', '')}</h4>
                    <table style="width: 100%; font-size: 0.9em;">
                        <tr><td>ID</td><td style="text-align:right;font-weight:bold;">{inv['secondary_warehouse']}</td></tr>
                        <tr><td>위치</td><td style="text-align:right;">{secondary.get('warehouse_city', '')} - {secondary.get('warehouse_state', '')}</td></tr>
                        <tr><td>권역</td><td style="text-align:right;">{secondary.get('region', '')}</td></tr>
                        <tr><td>최대 용량</td><td style="text-align:right;">{secondary.get('capacity_units', 0):,}개</td></tr>
                    </table>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.caption("보조 창고가 배정되지 않았습니다.")

    # 재고 요약 메트릭
    items = inv.get("inventory_items")
    if items is not None and not items.empty:
        st.write("")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("재고 상품 수", f"{len(items):,}종")
        with c2:
            st.metric("총 보유 수량", f"{items['quantity_on_hand'].sum():,}개")
        with c3:
            st.metric("출고 예약", f"{items['quantity_reserved'].sum():,}개")
        with c4:
            st.metric("가용 수량", f"{items['quantity_available'].sum():,}개")

    # 발주점 이하 경고
    alerts = inv.get("reorder_alerts")
    if alerts is not None and not alerts.empty:
        st.write("")
        critical = alerts[alerts["urgency"] == "critical"] if "urgency" in alerts.columns else alerts
        warn = alerts[alerts["urgency"] == "warning"] if "urgency" in alerts.columns else alerts.iloc[0:0]

        if len(critical) > 0:
            st.error(f"🚨 안전재고 이하 상품: **{len(critical)}개** — 즉시 발주 필요")

        if len(warn) > 0:
            st.warning(f"⚠️ 발주점 이하 상품: **{len(warn)}개** — 정기 발주 권고")

        with st.expander(f"발주 필요 상품 목록 ({len(alerts)}건)", expanded=len(critical) > 0):
            display_cols = ["product_id", "quantity_available", "reorder_point",
                            "safety_stock", "urgency"]
            display = alerts[[c for c in display_cols if c in alerts.columns]].copy()
            if "product_id" in display.columns:
                pnames = load_product_names()[["product_id", "product_name_display"]]
                display = display.merge(pnames, on="product_id", how="left")
                display["product_name_display"] = display["product_name_display"].fillna(
                    display["product_id"].str[:12] + "..."
                )
                display = display.drop(columns=["product_id"])
                # product_name_display를 첫 번째 컬럼으로 이동
                cols = ["product_name_display"] + [c for c in display.columns if c != "product_name_display"]
                display = display[cols]
            display.columns = [
                c.replace("product_name_display", "상품명")
                .replace("quantity_available", "가용 수량")
                .replace("reorder_point", "발주점")
                .replace("safety_stock", "안전재고")
                .replace("urgency", "긴급도")
                for c in display.columns
            ]
            st.dataframe(display.head(20), use_container_width=True, hide_index=True)

    # 최근 입출고 이력
    moves = inv.get("recent_movements")
    move_summary = inv.get("movement_summary", {})
    if move_summary:
        st.write("")
        st.markdown("**최근 입출고 요약**")
        cols = st.columns(len(move_summary))
        type_icons = {"INBOUND": "📥", "OUTBOUND": "📤", "RETURN": "🔄", "ADJUSTMENT": "⚙️"}
        type_names = {"INBOUND": "입고", "OUTBOUND": "출고", "RETURN": "반품", "ADJUSTMENT": "조정"}
        for col, (mtype, info) in zip(cols, move_summary.items()):
            with col:
                st.metric(
                    f"{type_icons.get(mtype, '')} {type_names.get(mtype, mtype)}",
                    f"{info['count']}건",
                    delta=f"수량: {info['total_qty']:,}",
                    delta_color="off",
                )


# ═══════════════════════════════════════════════════════════════
# 섹션 4: 통합 컨설팅 액션
# ═══════════════════════════════════════════════════════════════

def _render_consulting_actions(delivery: dict, inventory: dict) -> None:
    _section_header(
        "통합 컨설팅 액션", "💡",
        "배송·재고 분석 결합한 맞춤형 개선 전략"
    )

    # 조언 생성
    advices = generate_delivery_advice(delivery, inventory)

    if not advices:
        st.success("현재 배송·재고 관련 긴급 이슈가 없습니다. 현 성과를 유지하세요!")
    else:
        for advice in advices:
            color = PRIORITY_COLORS.get(advice.priority, COLORS["muted"])
            priority_kr = {
                "critical": "긴급", "high": "높음", "medium": "보통", "low": "낮음"
            }.get(advice.priority, "")
            category_icon = {
                "dispatch": "📦", "delivery": "🚚", "seasonal": "🌧️", "inventory": "📋"
            }.get(advice.category, "💡")

            st.markdown(
                f"""
                <div style="border-left: 4px solid {color}; padding: 12px 16px;
                     margin-bottom: 12px; background: #fafafa; border-radius: 4px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: bold; font-size: 1.05em;">{category_icon} {advice.title}</span>
                        <span style="background: {color}; color: white; padding: 2px 10px;
                              border-radius: 12px; font-size: 0.8em;">{priority_kr}</span>
                    </div>
                    <div style="color: #555; margin-top: 4px; font-size: 0.85em;">
                        현재: <b>{advice.current_value}</b> → 목표: <b>{advice.target_value}</b>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.expander("상세 보기"):
                st.markdown(advice.description)
                st.markdown("**실행 방안:**")
                for action in advice.actions:
                    st.markdown(f"- {action}")
                if advice.expected_effect:
                    st.info(f"📈 기대 효과: {advice.expected_effect}")

    # 90일 로드맵
    st.write("")
    st.markdown("### 🗓️ 90일 개선 로드맵")

    roadmap = generate_delivery_roadmap(delivery, inventory)
    for phase in roadmap:
        st.markdown(
            f"""
            <div style="border-left: 3px solid #ccc; padding: 8px 16px; margin-bottom: 8px;">
                <b>{phase['icon']} {phase['phase']}</b>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for action in phase["actions"]:
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;✅ {action}")
