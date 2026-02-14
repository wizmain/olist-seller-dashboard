"""Streamlit 메인 앱 — Olist 셀러 컨설팅 대시보드."""

from __future__ import annotations

import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import streamlit as st

from claude_eda.dashboard.config import APP_ICON, APP_LAYOUT, APP_TITLE
from claude_eda.dashboard.data.loader import get_seller_list, load_seller_clusters
from claude_eda.dashboard.data.preprocessor import compute_seller_metrics
from claude_eda.dashboard.views.consulting import render_consulting
from claude_eda.dashboard.views.dashboard import render_dashboard
from claude_eda.dashboard.utils.formatting import fmt_currency_short
from claude_eda.dashboard.utils.korean import SELLER_CLUSTER_SHORT

# 페이지 설정
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout=APP_LAYOUT,
)

# --- 사이드바 ---
with st.sidebar:
    st.title(f"{APP_ICON} {APP_TITLE}")
    st.divider()

    # 페이지 라우팅 (맨 위)
    page = st.radio(
        "페이지",
        ["현황 대시보드", "컨설팅 리포트"],
        index=0,
    )

    st.divider()

    # 셀러 ID 직접 입력
    seller_id_input = st.text_input(
        "셀러 ID 직접 입력",
        placeholder="32자리 셀러 ID 입력...",
        help="seller_cluster_analysis_data.csv에 있는 seller_id를 입력하세요.",
    )

    st.markdown("**또는** 매출 상위 셀러 선택:")

    # 매출 상위 셀러 selectbox — format_func으로 표시
    seller_list = get_seller_list()
    top50 = seller_list.head(50)

    # seller_id 리스트 (None = 미선택)
    seller_id_options = [""] + top50["seller_id"].tolist()
    # 라벨 매핑 딕셔너리 (한 번만 생성)
    _label_cache = {}
    for _, r in top50.iterrows():
        _label_cache[r["seller_id"]] = (
            f"#{int(r['rank'])} | {r['seller_id'][:12]}... | "
            f"{fmt_currency_short(r['total_revenue'])} | "
            f"{SELLER_CLUSTER_SHORT.get(int(r['cluster']), '?')}"
        )

    def _format_seller(sid: str) -> str:
        if not sid:
            return "(선택하세요)"
        return _label_cache.get(sid, sid[:12])

    selected_from_list = st.selectbox(
        "매출 상위 50 셀러",
        seller_id_options,
        format_func=_format_seller,
        key="seller_select",
    )

    # 선택된 셀러 ID 결정 (텍스트 입력 우선)
    selected_seller_id = None
    if seller_id_input and len(seller_id_input) == 32:
        selected_seller_id = seller_id_input
    elif selected_from_list:
        selected_seller_id = selected_from_list

    st.divider()
    st.caption("Olist 셀러 컨설팅 시스템 v1.0")
    st.caption("데이터 기반 규칙 엔진으로 맞춤형 조언 제공")

# --- 메인 콘텐츠 ---
if selected_seller_id:
    # 셀러 존재 확인
    all_sellers = load_seller_clusters()
    if selected_seller_id not in all_sellers["seller_id"].values:
        st.error(f"셀러 ID `{selected_seller_id}`를 찾을 수 없습니다.")
        st.info("올바른 32자리 셀러 ID를 입력해주세요.")
        st.stop()

    with st.spinner("셀러 데이터 분석 중..."):
        metrics = compute_seller_metrics(selected_seller_id)

    if metrics is None:
        st.error("셀러 데이터를 불러올 수 없습니다.")
        st.stop()

    if page == "현황 대시보드":
        render_dashboard(metrics)
    else:
        render_consulting(metrics)
else:
    # 미선택 시 플랫폼 개요
    st.title(f"{APP_ICON} Olist 셀러 컨설팅 대시보드")
    st.markdown("---")
    st.markdown(
        """
        ### 사용 방법
        1. **왼쪽 사이드바**에서 셀러 ID를 입력하거나 상위 셀러를 선택하세요.
        2. **현황 대시보드**: 셀러의 핵심 KPI, 벤치마크 비교, 월별 추이를 확인합니다.
        3. **컨설팅 리포트**: 데이터 기반 맞춤형 컨설팅 조언과 성장 로드맵을 제공합니다.
        """
    )

    st.markdown("### 플랫폼 개요")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("전체 셀러", "2,971명")
    with col2:
        st.metric("전체 주문", "99,441건")
    with col3:
        st.metric("전체 고객", "92,722명")
    with col4:
        st.metric("전체 상품", "32,951종")

    st.markdown("### 셀러 클러스터 분포")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("우수 판매자", "322명 (10.8%)")
        st.caption("매출의 50.4% 차지")
    with col2:
        st.metric("일반 판매자", "2,178명 (73.3%)")
        st.caption("매출의 44.8% 차지")
    with col3:
        st.metric("저평가 판매자", "373명 (12.6%)")
        st.caption("매출의 3.6%")
    with col4:
        st.metric("배송 위험", "98명 (3.3%)")
        st.caption("매출의 1.2%")

    st.markdown("---")
    st.markdown(
        """
        ### 테스트 셀러 ID
        | 유형 | 셀러 ID |
        |------|---------|
        | Top Performer (200주문, R$25K) | `001cca7ae9ae17fb1caed9dfb1094831` |
        | Standard (3주문, R$2.7K) | `0015a82c2db000af6aaaf3ae2ecb0532` |
        | Low Review (1주문, 리뷰 1.0) | `001e6ad469a905060d959994f1b41e4f` |
        """
    )
