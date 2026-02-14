"""포르투갈어 리뷰 텍스트 키워드 기반 원인 분류기."""

from __future__ import annotations

import re
from collections import Counter

import pandas as pd

# 카테고리별 포르투갈어 키워드
ISSUE_KEYWORDS = {
    "배송 지연": [
        "entrega", "atraso", "atrasou", "demora", "demorou", "demoro",
        "prazo", "dias", "semana", "semanas", "chegou tarde", "não chegou",
        "nao chegou", "frete", "correios", "transportadora", "encomenda",
        "rastreio", "rastreamento", "extraviado", "perdido",
    ],
    "상품 품질": [
        "qualidade", "defeito", "defeituoso", "quebrado", "quebrou",
        "danificado", "estragado", "ruim", "péssimo", "pessimo",
        "horrível", "horrivel", "lixo", "porcaria", "não funciona",
        "nao funciona", "parou", "problema", "falha",
    ],
    "포장 문제": [
        "embalagem", "amassado", "amassada", "caixa", "proteção",
        "protecao", "aberta", "aberto", "rasgado", "rasgada",
        "mal embalado", "sem proteção", "sem protecao",
    ],
    "기대 불일치": [
        "foto", "imagem", "descrição", "descricao", "tamanho",
        "cor", "diferente", "parece", "esperava", "não corresponde",
        "nao corresponde", "enganoso", "propaganda", "falso", "falsa",
        "menor", "maior", "errado", "errada",
    ],
}

# 긍정 키워드 (강점 분석용)
POSITIVE_KEYWORDS = [
    "excelente", "ótimo", "otimo", "perfeito", "maravilhoso",
    "recomendo", "amei", "adorei", "rápido", "rapido",
    "antes do prazo", "chegou antes", "boa qualidade",
    "muito bom", "satisfeito", "satisfeita", "nota 10",
]


def classify_review(text: str) -> list[str]:
    """리뷰 텍스트를 이슈 카테고리로 분류. 복수 카테고리 가능."""
    if not text or not isinstance(text, str):
        return []
    text_lower = text.lower()
    categories = []
    for category, keywords in ISSUE_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                categories.append(category)
                break
    return categories


def is_positive_review(text: str) -> bool:
    """긍정 리뷰 여부 판단."""
    if not text or not isinstance(text, str):
        return False
    text_lower = text.lower()
    return any(kw in text_lower for kw in POSITIVE_KEYWORDS)


def analyze_seller_reviews(reviews_df: pd.DataFrame) -> dict:
    """셀러의 리뷰 텍스트를 분석하여 이슈 분포 반환.

    Args:
        reviews_df: review_score, review_comment_message 컬럼이 있는 DataFrame

    Returns:
        dict with:
            - issue_counts: {카테고리: 건수}
            - issue_pct: {카테고리: 비율}
            - negative_issues: 저평가(1-2점) 리뷰의 이슈 분포
            - positive_count: 긍정 리뷰 수
            - analyzed_count: 분석된 리뷰 수 (텍스트 있는 것)
            - total_count: 전체 리뷰 수
            - primary_issue: 가장 많은 이슈 카테고리
            - examples: 카테고리별 예시 리뷰 (최대 2개)
    """
    result = {
        "issue_counts": Counter(),
        "issue_pct": {},
        "negative_issues": Counter(),
        "positive_count": 0,
        "analyzed_count": 0,
        "total_count": len(reviews_df),
        "primary_issue": None,
        "examples": {},
    }

    if reviews_df.empty:
        return result

    text_reviews = reviews_df.dropna(subset=["review_comment_message"])
    result["analyzed_count"] = len(text_reviews)

    if text_reviews.empty:
        return result

    all_issues = Counter()
    neg_issues = Counter()
    examples: dict[str, list[str]] = {cat: [] for cat in ISSUE_KEYWORDS}

    for _, row in text_reviews.iterrows():
        text = row["review_comment_message"]
        score = row.get("review_score", 3)
        categories = classify_review(text)

        for cat in categories:
            all_issues[cat] += 1
            if len(examples[cat]) < 2:
                snippet = text[:100] + "..." if len(text) > 100 else text
                examples[cat].append(snippet)

        if score <= 2:
            for cat in categories:
                neg_issues[cat] += 1

        if is_positive_review(text):
            result["positive_count"] += 1

    result["issue_counts"] = dict(all_issues)
    if result["analyzed_count"] > 0:
        result["issue_pct"] = {
            cat: count / result["analyzed_count"]
            for cat, count in all_issues.items()
        }
    result["negative_issues"] = dict(neg_issues)
    result["examples"] = {cat: exs for cat, exs in examples.items() if exs}

    if all_issues:
        result["primary_issue"] = all_issues.most_common(1)[0][0]

    return result
