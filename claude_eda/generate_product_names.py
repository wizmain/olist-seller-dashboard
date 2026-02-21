"""product_id → 상품명 매핑 CSV 생성.

카테고리별 sales_count 내림차순 정렬 후 순번을 부여하여
"{Category Title} #NNNN" 형태의 상품명을 생성한다.
"""

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = PROJECT_ROOT / "claude_eda" / "product_cluster_analysis_data.csv"
OUTPUT_PATH = PROJECT_ROOT / "olist-ecommerce" / "output" / "product_id_name_mapping.csv"

# 영문 카테고리 → 한국어 매핑 (71개)
CATEGORY_KO: dict[str, str] = {
    "agro_industry_and_commerce": "농업·상업",
    "air_conditioning": "에어컨",
    "art": "아트",
    "arts_and_craftmanship": "공예",
    "audio": "오디오",
    "auto": "자동차용품",
    "baby": "유아용품",
    "bed_bath_table": "침구·욕실·테이블",
    "books_general_interest": "일반도서",
    "books_imported": "수입도서",
    "books_technical": "기술도서",
    "cds_dvds_musicals": "CD·DVD·뮤지컬",
    "christmas_supplies": "크리스마스용품",
    "cine_photo": "영상·사진",
    "computers": "컴퓨터",
    "computers_accessories": "컴퓨터 액세서리",
    "consoles_games": "콘솔·게임",
    "construction_tools_construction": "건축 공구",
    "construction_tools_lights": "건축 조명",
    "construction_tools_safety": "건축 안전용품",
    "cool_stuff": "쿨 스터프",
    "costruction_tools_garden": "정원 공구",
    "costruction_tools_tools": "공구류",
    "diapers_and_hygiene": "기저귀·위생용품",
    "drinks": "음료",
    "dvds_blu_ray": "DVD·블루레이",
    "electronics": "전자제품",
    "fashio_female_clothing": "여성의류",
    "fashion_bags_accessories": "가방·패션잡화",
    "fashion_childrens_clothes": "아동의류",
    "fashion_male_clothing": "남성의류",
    "fashion_shoes": "신발",
    "fashion_sport": "스포츠웨어",
    "fashion_underwear_beach": "언더웨어·비치웨어",
    "fixed_telephony": "유선전화",
    "flowers": "꽃",
    "food": "식품",
    "food_drink": "식음료",
    "furniture_bedroom": "침실가구",
    "furniture_decor": "장식가구",
    "furniture_living_room": "거실가구",
    "furniture_mattress_and_upholstery": "매트리스·소파",
    "garden_tools": "정원용품",
    "health_beauty": "건강·뷰티",
    "home_appliances": "가전제품",
    "home_appliances_2": "가전제품2",
    "home_comfort_2": "홈 컴포트2",
    "home_confort": "홈 컴포트",
    "home_construction": "주택건설",
    "housewares": "생활용품",
    "industry_commerce_and_business": "산업·비즈니스",
    "kitchen_dining_laundry_garden_furniture": "주방·세탁·정원가구",
    "la_cuisine": "주방용품",
    "luggage_accessories": "여행가방·액세서리",
    "market_place": "마켓플레이스",
    "music": "음악",
    "musical_instruments": "악기",
    "office_furniture": "사무가구",
    "party_supplies": "파티용품",
    "perfumery": "향수",
    "pet_shop": "반려동물용품",
    "security_and_services": "보안·서비스",
    "signaling_and_security": "신호·보안",
    "small_appliances": "소형가전",
    "small_appliances_home_oven_and_coffee": "오븐·커피머신",
    "sports_leisure": "스포츠·레저",
    "stationery": "문구",
    "tablets_printing_image": "태블릿·인쇄·이미지",
    "telephony": "통신기기",
    "toys": "완구",
    "watches_gifts": "시계·선물",
}


def _title_case(category: str) -> str:
    """underscore 구분 카테고리를 Title Case로 변환."""
    return category.replace("_", " ").title()


def main() -> None:
    df = pd.read_csv(INPUT_PATH)
    print(f"총 상품 수: {len(df):,}")

    # 카테고리 없는 상품 처리
    df["category"] = df["product_category_name_english"].fillna("uncategorized")

    # 카테고리별 sales_count 내림차순 정렬 → 순번 부여
    df = df.sort_values(["category", "sales_count"], ascending=[True, False])
    df["rank_in_cat"] = df.groupby("category").cumcount() + 1

    # 영문 상품명
    df["product_name_en"] = df.apply(
        lambda r: f"{_title_case(r['category'])} #{r['rank_in_cat']:04d}", axis=1
    )

    # 한국어 상품명
    df["product_name_ko"] = df.apply(
        lambda r: f"{CATEGORY_KO.get(r['category'], _title_case(r['category']))} #{r['rank_in_cat']:04d}",
        axis=1,
    )

    # display용 (한국어 우선)
    df["product_name_display"] = df["product_name_ko"]

    # 출력
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result = df[["product_id", "product_name_en", "product_name_ko", "product_name_display"]]
    result.to_csv(OUTPUT_PATH, index=False)
    print(f"저장 완료: {OUTPUT_PATH}")
    print(f"매핑 수: {len(result):,}")
    print(f"\n샘플 5건:")
    print(result.head().to_string(index=False))


if __name__ == "__main__":
    main()
