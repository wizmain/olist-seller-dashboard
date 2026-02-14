"""숫자, 통화, 퍼센트 등 포맷팅 유틸리티."""


def fmt_currency(value: float) -> str:
    """브라질 헤알 통화 포맷. 예: R$ 12,345.67"""
    if value >= 1_000_000:
        return f"R$ {value:,.0f}"
    if value >= 1_000:
        return f"R$ {value:,.0f}"
    return f"R$ {value:,.2f}"


def fmt_currency_short(value: float) -> str:
    """짧은 통화 포맷. 예: R$12.3K"""
    if value >= 1_000_000:
        return f"R${value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"R${value / 1_000:.1f}K"
    return f"R${value:.0f}"


def fmt_percent(value: float, decimal: int = 1) -> str:
    """퍼센트 포맷. 0.123 → 12.3%"""
    return f"{value * 100:.{decimal}f}%"


def fmt_pct_value(value: float, decimal: int = 1) -> str:
    """이미 퍼센트인 값 포맷. 12.3 → 12.3%"""
    return f"{value:.{decimal}f}%"


def fmt_days(value: float) -> str:
    """일수 포맷. 예: 12.3일"""
    return f"{value:.1f}일"


def fmt_score(value: float) -> str:
    """점수 포맷. 예: 4.2점"""
    return f"{value:.1f}점"


def fmt_number(value: float) -> str:
    """숫자 포맷 (천 단위 콤마). 예: 1,234"""
    if value == int(value):
        return f"{int(value):,}"
    return f"{value:,.1f}"


def fmt_percentile(rank: float) -> str:
    """퍼센타일 포맷. 예: 상위 15.2%"""
    return f"상위 {rank:.1f}%"


def fmt_delta(current: float, target: float) -> str:
    """현재값 대비 타겟 차이 포맷."""
    diff = target - current
    if diff > 0:
        return f"+{diff:,.1f}"
    return f"{diff:,.1f}"


def health_grade(score: float) -> str:
    """건강 점수 등급. A/B/C/D/F"""
    if score >= 80:
        return "A"
    if score >= 60:
        return "B"
    if score >= 40:
        return "C"
    if score >= 20:
        return "D"
    return "F"


def health_grade_color(score: float) -> str:
    """건강 점수 등급에 따른 색상."""
    if score >= 80:
        return "#2ca02c"
    if score >= 60:
        return "#1f77b4"
    if score >= 40:
        return "#ff7f0e"
    if score >= 20:
        return "#d62728"
    return "#7f7f7f"
