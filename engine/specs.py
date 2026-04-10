"""기기 성능 스펙 데이터 (PAFC / SOFC)

엑셀 '기기스펙' 시트 기준 — 1대당 연간 성능.
10년 주기로 반복 (11년차=1년차, 12년차=2년차, ...).
"""

import numpy as np

# ── PAFC (인산형 연료전지) — 1대 기준, 연차별 ─────────────

PAFC = {
    "availability": 0.88,            # 가동률
    "internal_consumption": 0.015,   # 소내소비전력 1.5%
    "unit_capacity": 0.44,           # MW/대
    # 연간 총 발전량 (MWh/대) — year 1~10
    "generation_mwh": [
        3584.592, 3568.298, 3527.564, 3494.977, 3454.243,
        3421.656, 3380.922, 3348.335, 3307.601, 3275.014,
    ],
    # 연간 총 연료소비열량 (MJ/대)
    "fuel_mj": [
        33_799_191, 33_566_434, 33_498_369, 33_507_105, 33_446_142,
        33_372_966, 33_300_463, 33_307_558, 33_232_941, 33_239_495,
    ],
    # 연간 열 출력량 (Gcal/대)
    "heat_gcal": [2444] * 10,
    # 연간 용수 사용량 (ton/대)
    "water_ton": [100] * 10,
}

# ── SOFC (고체산화물 연료전지, 블룸) — 1대 기준 ──────────

SOFC = {
    "availability": 0.91,
    "internal_consumption": 0.0,     # 소내소비전력 없음
    "unit_capacity": 0.33,           # MW/대
    # 시간당 기준값 → 연간 환산은 get_annual_specs에서 수행
    "capacity_mw": 0.33,
    "fuel_nm3_per_hr": 57.13,
    "water_ton_per_hr": 0.05778,
    "mj_per_nm3": 42.71,
}


def get_annual_specs(equipment_type: int, num_units: int, years: int = 20) -> dict:
    """연차별 기기 스펙 반환 (전체 기기 합산)

    Returns:
        dict with numpy arrays of shape (years,):
            generation_mwh : 연간 발전량 (MWh)
            fuel_mj        : 연간 연료소비량 (MJ)
            fuel_nm3       : 연간 연료소비량 (Nm3)
            heat_gcal      : 연간 열출력량 (Gcal)
            water_ton      : 연간 용수사용량 (ton)
    """
    if equipment_type == 1:  # PAFC
        spec = PAFC
        gen, fuel, heat, water = [], [], [], []
        for y in range(years):
            idx = y % 10  # 10년 주기 반복
            gen.append(spec["generation_mwh"][idx] * num_units)
            fuel.append(spec["fuel_mj"][idx] * num_units)
            heat.append(spec["heat_gcal"][idx] * num_units)
            water.append(spec["water_ton"][idx] * num_units)

        fuel_mj = np.array(fuel)
        return {
            "generation_mwh": np.array(gen),
            "fuel_mj": fuel_mj,
            "fuel_nm3": fuel_mj / 42.71,
            "heat_gcal": np.array(heat),
            "water_ton": np.array(water),
        }

    else:  # SOFC
        spec = SOFC
        hours_per_year = 24 * 365 * spec["availability"]

        gen_per_unit = spec["capacity_mw"] * hours_per_year * 1000  # kWh → MWh? No.
        # capacity_mw(MW) × hours = MWh
        gen_per_unit = spec["capacity_mw"] * hours_per_year  # MWh

        fuel_nm3_per_unit = spec["fuel_nm3_per_hr"] * hours_per_year
        fuel_mj_per_unit = fuel_nm3_per_unit * spec["mj_per_nm3"]
        water_per_unit = spec["water_ton_per_hr"] * hours_per_year

        fuel_mj = np.full(years, fuel_mj_per_unit * num_units)
        return {
            "generation_mwh": np.full(years, gen_per_unit * num_units),
            "fuel_mj": fuel_mj,
            "fuel_nm3": fuel_mj / 42.71,
            "heat_gcal": np.zeros(years),  # SOFC 열출력 없음
            "water_ton": np.full(years, water_per_unit * num_units),
        }
