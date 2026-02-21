"""물류 창고 최적화 — 셀러별 분석 함수."""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from claude_eda.dashboard.data.loader import (
    build_merged_table,
    load_geolocation,
    load_sellers,
    load_warehouse_recommendations,
    load_warehouse_scenarios,
)


def _haversine(lat1, lon1, lat2, lon2):
    """두 좌표 간 거리 (km) — 벡터 연산."""
    R = 6371
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return R * 2 * np.arcsin(np.sqrt(a))


BRAZIL_REGIONS = {
    "SP": "Southeast", "RJ": "Southeast", "MG": "Southeast", "ES": "Southeast",
    "RS": "South", "PR": "South", "SC": "South",
    "BA": "Northeast", "PE": "Northeast", "CE": "Northeast", "MA": "Northeast",
    "PB": "Northeast", "RN": "Northeast", "AL": "Northeast", "PI": "Northeast", "SE": "Northeast",
    "DF": "Central-West", "GO": "Central-West", "MT": "Central-West", "MS": "Central-West",
    "PA": "North", "AM": "North", "TO": "North", "RO": "North",
    "AC": "North", "AP": "North", "RR": "North",
}


@st.cache_data
def compute_seller_logistics(seller_id: str) -> dict:
    """셀러별 물류 현황 및 창고 활용 효과 분석.

    Returns dict with keys:
        seller_lat, seller_lng, seller_state
        customer_points: DataFrame (lat, lng, state, order_count, distance_km, freight, delivery_days)
        avg_distance, avg_freight, avg_delivery_days, late_pct
        platform_avg_distance, platform_avg_freight, platform_avg_delivery_days
        warehouse_recs: DataFrame (warehouse_recommendations + seller-specific distances)
        best_warehouse: dict (가장 유리한 창고)
        simulation: list[dict] (현재, 최근접1창고, 3창고, 5창고 시나리오)
        region_effect: DataFrame (권역별 거리 감소 효과)
    """
    merged = build_merged_table()
    geo = load_geolocation()
    sellers_df = load_sellers()
    wh_recs = load_warehouse_recommendations()
    wh_scenarios = load_warehouse_scenarios()

    result = {
        "seller_lat": None, "seller_lng": None, "seller_state": "",
        "customer_points": pd.DataFrame(),
        "avg_distance": 0.0, "avg_freight": 0.0, "avg_delivery_days": 0.0, "late_pct": 0.0,
        "platform_avg_distance": 0.0, "platform_avg_freight": 0.0, "platform_avg_delivery_days": 0.0,
        "warehouse_recs": pd.DataFrame(),
        "best_warehouse": {},
        "simulation": [],
        "region_effect": pd.DataFrame(),
    }

    # 셀러 좌표
    seller_info = sellers_df[sellers_df["seller_id"] == seller_id]
    if seller_info.empty:
        return result
    seller_zip = seller_info.iloc[0]["seller_zip_code_prefix"]
    result["seller_state"] = seller_info.iloc[0]["seller_state"]

    seller_geo = geo[geo["geolocation_zip_code_prefix"] == seller_zip]
    if seller_geo.empty:
        return result
    slat = float(seller_geo.iloc[0]["geolocation_lat"])
    slng = float(seller_geo.iloc[0]["geolocation_lng"])
    result["seller_lat"] = slat
    result["seller_lng"] = slng

    # 셀러의 배송 데이터
    seller_data = merged[
        (merged["seller_id"] == seller_id) & (merged["order_status"] == "delivered")
    ].copy()
    if seller_data.empty:
        return result

    # 고객 좌표 매핑
    cust = seller_data[["customer_zip_code_prefix", "customer_state",
                         "order_id", "freight_value", "delivery_days", "is_late"]].copy()
    cust["customer_zip_code_prefix"] = cust["customer_zip_code_prefix"].astype(int, errors="ignore")
    cust = cust.merge(
        geo, left_on="customer_zip_code_prefix",
        right_on="geolocation_zip_code_prefix", how="inner",
    )
    if cust.empty:
        return result

    cust["distance_km"] = _haversine(slat, slng, cust["geolocation_lat"].values, cust["geolocation_lng"].values)

    # 고객별 집계
    customer_points = cust.groupby(["geolocation_lat", "geolocation_lng", "customer_state"]).agg(
        order_count=("order_id", "nunique"),
        distance_km=("distance_km", "mean"),
        freight=("freight_value", "mean"),
        delivery_days=("delivery_days", "mean"),
    ).reset_index().rename(columns={"geolocation_lat": "lat", "geolocation_lng": "lng", "customer_state": "state"})
    result["customer_points"] = customer_points

    # 셀러 현재 평균
    result["avg_distance"] = float(cust["distance_km"].mean())
    result["avg_freight"] = float(cust["freight_value"].mean())
    dd = cust["delivery_days"].dropna()
    result["avg_delivery_days"] = float(dd.mean()) if len(dd) > 0 else 0.0
    result["late_pct"] = float(cust["is_late"].mean()) if len(cust) > 0 else 0.0

    # 플랫폼 평균 (시나리오 CSV에서)
    current_row = wh_scenarios[wh_scenarios["scenario"] == "현재(셀러직배)"]
    if not current_row.empty:
        result["platform_avg_distance"] = float(current_row.iloc[0]["avg_distance_km"])
        result["platform_avg_freight"] = float(current_row.iloc[0]["est_avg_freight"])
        result["platform_avg_delivery_days"] = float(current_row.iloc[0]["est_avg_days"])

    # 각 창고까지의 셀러 거리 + 고객-창고 평균 거리
    wh = wh_recs.copy()
    wh["seller_to_wh_km"] = _haversine(slat, slng, wh["lat"].values, wh["lng"].values)

    # 고객→각 창고 거리 계산
    wh_avg_dists = []
    for _, wrow in wh.iterrows():
        dists = _haversine(
            cust["geolocation_lat"].values, cust["geolocation_lng"].values,
            wrow["lat"], wrow["lng"],
        )
        wh_avg_dists.append(float(np.mean(dists)))
    wh["customer_to_wh_km"] = wh_avg_dists
    wh["distance_reduction_km"] = result["avg_distance"] - wh["customer_to_wh_km"]
    wh["reduction_pct"] = (wh["distance_reduction_km"] / result["avg_distance"] * 100).round(1)
    wh = wh.sort_values("customer_to_wh_km")
    result["warehouse_recs"] = wh

    # 최적 창고
    best = wh.iloc[0]
    result["best_warehouse"] = {
        "id": int(best["warehouse_id"]),
        "city": best["nearest_city"],
        "state": best["state"],
        "region": best["region"],
        "seller_to_wh_km": float(best["seller_to_wh_km"]),
        "customer_to_wh_km": float(best["customer_to_wh_km"]),
        "reduction_km": float(best["distance_reduction_km"]),
        "reduction_pct": float(best["reduction_pct"]),
    }

    # 시나리오 시뮬레이션 (현재 / 최근접1 / 3 / 5개)
    # 선형 모델 계수 (warehouse EDA에서 도출)
    freight_per_km = 0.0104
    freight_intercept = 13.70
    days_per_km = 0.00606
    days_intercept = 8.64

    sim = []
    # 현재
    sim.append({
        "scenario": "현재 (직배)",
        "avg_distance": result["avg_distance"],
        "est_freight": result["avg_freight"],
        "est_days": result["avg_delivery_days"],
    })

    # 최근접 1개 창고
    best_wh_lat, best_wh_lng = best["lat"], best["lng"]
    dists_1 = _haversine(
        cust["geolocation_lat"].values, cust["geolocation_lng"].values,
        best_wh_lat, best_wh_lng,
    )
    avg_1 = float(np.mean(dists_1))
    sim.append({
        "scenario": f"최근접 창고\n({best['nearest_city']}, {best['state']})",
        "avg_distance": avg_1,
        "est_freight": freight_per_km * avg_1 + freight_intercept,
        "est_days": days_per_km * avg_1 + days_intercept,
    })

    # 3개 창고 (상위 3개 중 최근접)
    top3_wh = wh.head(3)
    dists_3 = np.column_stack([
        _haversine(cust["geolocation_lat"].values, cust["geolocation_lng"].values,
                   row["lat"], row["lng"])
        for _, row in top3_wh.iterrows()
    ])
    avg_3 = float(np.mean(dists_3.min(axis=1)))
    sim.append({
        "scenario": "3개 창고 활용",
        "avg_distance": avg_3,
        "est_freight": freight_per_km * avg_3 + freight_intercept,
        "est_days": days_per_km * avg_3 + days_intercept,
    })

    # 5개 창고 전체
    dists_5 = np.column_stack([
        _haversine(cust["geolocation_lat"].values, cust["geolocation_lng"].values,
                   row["lat"], row["lng"])
        for _, row in wh.iterrows()
    ])
    avg_5 = float(np.mean(dists_5.min(axis=1)))
    sim.append({
        "scenario": "5개 창고 활용",
        "avg_distance": avg_5,
        "est_freight": freight_per_km * avg_5 + freight_intercept,
        "est_days": days_per_km * avg_5 + days_intercept,
    })
    result["simulation"] = sim

    # 권역별 효과 (5개 창고)
    cust_with_region = cust.copy()
    cust_with_region["region"] = cust_with_region["customer_state"].map(BRAZIL_REGIONS).fillna("Unknown")
    dists_5_min = dists_5.min(axis=1)
    cust_with_region["dist_wh5"] = dists_5_min
    cust_with_region["dist_reduction"] = cust_with_region["distance_km"] - cust_with_region["dist_wh5"]

    region_effect = cust_with_region.groupby("region").agg(
        current_avg=("distance_km", "mean"),
        wh5_avg=("dist_wh5", "mean"),
        reduction=("dist_reduction", "mean"),
        orders=("order_id", "nunique"),
    ).reset_index()
    region_effect["reduction_pct"] = (region_effect["reduction"] / region_effect["current_avg"] * 100).round(1)
    region_effect = region_effect.sort_values("orders", ascending=False)
    result["region_effect"] = region_effect

    return result
