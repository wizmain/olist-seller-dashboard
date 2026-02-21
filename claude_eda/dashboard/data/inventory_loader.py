"""재고 관리 데이터 로딩 모듈. @st.cache_data로 5개 CSV 캐싱."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from claude_eda.dashboard.config import INVENTORY_DATA_DIR


@st.cache_data
def load_warehouses() -> pd.DataFrame:
    """창고 마스터 (5행)."""
    return pd.read_csv(INVENTORY_DATA_DIR / "olist_warehouses.csv")


@st.cache_data
def load_warehouse_inventory() -> pd.DataFrame:
    """창고×상품 현재고."""
    return pd.read_csv(INVENTORY_DATA_DIR / "olist_warehouse_inventory.csv")


@st.cache_data
def load_inventory_movements() -> pd.DataFrame:
    """입출고 이력."""
    df = pd.read_csv(INVENTORY_DATA_DIR / "olist_inventory_movements.csv")
    df["movement_date"] = pd.to_datetime(df["movement_date"])
    return df


@st.cache_data
def load_seller_warehouse() -> pd.DataFrame:
    """셀러-창고 배정."""
    return pd.read_csv(INVENTORY_DATA_DIR / "olist_seller_warehouse.csv")


@st.cache_data
def load_reorder_rules() -> pd.DataFrame:
    """자동 발주 규칙."""
    return pd.read_csv(INVENTORY_DATA_DIR / "olist_reorder_rules.csv")


def get_seller_inventory_summary(seller_id: str) -> dict:
    """셀러의 재고 관련 정보를 종합하여 반환한다."""
    sw = load_seller_warehouse()
    warehouses = load_warehouses()
    inventory = load_warehouse_inventory()
    movements = load_inventory_movements()
    reorder = load_reorder_rules()

    result: dict = {
        "has_data": False,
        "primary_warehouse": None,
        "secondary_warehouse": None,
        "primary_info": None,
        "secondary_info": None,
        "inventory_items": pd.DataFrame(),
        "reorder_alerts": pd.DataFrame(),
        "recent_movements": pd.DataFrame(),
        "movement_summary": {},
    }

    # 셀러-창고 배정
    seller_wh = sw[sw["seller_id"] == seller_id]
    if seller_wh.empty:
        return result

    row = seller_wh.iloc[0]
    result["has_data"] = True
    result["primary_warehouse"] = row["primary_warehouse_id"]
    result["secondary_warehouse"] = row.get("secondary_warehouse_id")

    # 창고 상세 정보
    for key, wid in [("primary_info", result["primary_warehouse"]),
                     ("secondary_info", result["secondary_warehouse"])]:
        if pd.notna(wid):
            wh_info = warehouses[warehouses["warehouse_id"] == wid]
            if not wh_info.empty:
                result[key] = wh_info.iloc[0].to_dict()

    # 주 창고의 재고 현황
    primary_wid = result["primary_warehouse"]
    inv = inventory[inventory["warehouse_id"] == primary_wid].copy()
    result["inventory_items"] = inv

    # 발주점 이하 경고 상품
    rules = reorder[reorder["warehouse_id"] == primary_wid].copy()
    if not inv.empty and not rules.empty:
        merged = inv.merge(rules, on=["warehouse_id", "product_id"], how="inner")
        alerts = merged[
            merged["quantity_available"] <= merged["reorder_point"]
        ].copy()
        alerts["urgency"] = "warning"
        alerts.loc[alerts["quantity_available"] <= alerts["safety_stock"], "urgency"] = "critical"
        result["reorder_alerts"] = alerts.sort_values("quantity_available")

    # 셀러의 최근 입출고 이력 (최근 50건)
    seller_moves = movements[movements["seller_id"] == seller_id].copy()
    seller_moves = seller_moves.sort_values("movement_date", ascending=False).head(50)
    result["recent_movements"] = seller_moves

    # 입출고 요약
    if not seller_moves.empty:
        summary = seller_moves.groupby("movement_type")["quantity"].agg(["sum", "count"])
        result["movement_summary"] = {
            mtype: {"total_qty": int(row["sum"]), "count": int(row["count"])}
            for mtype, row in summary.iterrows()
        }

    return result
