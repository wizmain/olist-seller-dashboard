"""Page 4: 분석 방법론 — 대시보드 계산 로직 설명."""

from __future__ import annotations

from pathlib import Path

import streamlit as st


def render_methodology() -> None:
    """분석 방법론 페이지 렌더."""
    md_path = Path(__file__).resolve().parent.parent / "DASHBOARD_METHODOLOGY.md"

    if not md_path.exists():
        st.error("DASHBOARD_METHODOLOGY.md 파일을 찾을 수 없습니다.")
        return

    content = md_path.read_text(encoding="utf-8")

    # 헤더
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%);
             padding: 20px 24px; border-radius: 8px; margin-bottom: 24px;">
            <h2 style="color: white; margin: 0 0 8px 0;">분석 방법론</h2>
            <span style="color: rgba(255,255,255,0.85); font-size: 0.95em;">
                대시보드의 점수 계산, 조언 생성, 추천 로직을 설명합니다
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 목차 네비게이션
    with st.expander("목차 바로가기", expanded=False):
        st.markdown(
            """
1. 셀러 건강 점수 (Health Score)
2. 강점/약점 분석
3. 컨설팅 조언 생성 (13개 규칙)
4. 성장 로드맵
5. 퍼센타일 랭킹
6. 맞춤 추천 진출 지역
7. 지역 수급 분석
8. 카테고리 기회 분석
9. 가격 포지셔닝 & 시뮬레이션
10. 크로스셀 카테고리 추천
11. 리뷰 키워드 분류
12. 벤치마크 상수 출처
            """
        )

    # MD 본문에서 첫 번째 제목(# 셀러 컨설팅...)과 목차 부분을 제거하고 본문만 렌더
    # "---" 두 번째 이후부터가 실제 본문
    sections = content.split("\n---\n")

    # 첫 번째 섹션은 제목+목차이므로 건너뜀
    if len(sections) > 1:
        body = "\n---\n".join(sections[1:])
    else:
        body = content

    st.markdown(body, unsafe_allow_html=True)
