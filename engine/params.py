"""연료전지 발전사업 재무모델 입력 파라미터

엑셀 재무모델 기준값을 디폴트로 설정.
[V] = 직접 키인 항목, [D] = 파생값
"""

from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class Params:
    # ── 사업 기본 ──────────────────────────────────
    construction_months: int = 16          # 공사기간(월)
    operation_years: int = 20              # 운영기간(년)
    annual_days: int = 365                 # 연간운영일수

    # ── 설비 ──────────────────────────────────────
    equipment_type: int = 1                # 1: PAFC, 2: SOFC
    num_units: int = 22                    # 기기 대수
    unit_capacity: float = 0.44            # 대당 용량(MW)
    availability: float = 0.88             # 가동률 (PAFC:0.88, SOFC:0.91)
    internal_consumption: float = 0.015    # 소내소비전력 비율 (PAFC:1.5%, SOFC:0%)

    # ── 매출 단가 ─────────────────────────────────
    fixed_price: float = 69.75             # 고정판매단가(원/kWh) = 입찰단가
    heat_price: float = 36490.0            # 열판매단가(원/Gcal)
    heat_sales_ratio: float = 1.0          # 열 판매 비율

    # ── 건설비 ────────────────────────────────────
    equipment_unit_cost: float = 1350.0    # 주기기 대당단가(백만원)
    install_cost_per_mw: float = 1325.0    # MW당 설치공사비(백만원)
    land_area: float = 5463.0              # 토지면적(m²)
    land_price: float = 749000.0           # 토지단가(원/m²)
    supervision_cost: float = 1450.0       # 감리비(백만원)
    contingency_rate: float = 0.03         # 예비비 비율

    # ── 운영비 ────────────────────────────────────
    labor_cost_pp: float = 104.47          # 인당 인건비(백만원/년)
    num_workers: int = 3                   # 인원수
    ltsa_per_unit: float = 70.0            # LTSA 대당(백만원/년, 2년차~)
    mgmt_cost: float = 225.0              # 관리비(백만원/년)
    water_usage: float = 2500.0            # 용수사용량(ton/년)
    water_price: float = 1330.0            # 용수단가(원/ton)
    insurance_per_mw: float = 15.0         # 보험료(백만원/MW/년)
    rent: float = 0.0                      # 임대료(백만원/년)
    trading_fee: float = 103.4             # 전력거래수수료(원/MWh)
    emission_factor: float = 0.0007        # 배출권 전환계수 (Nm3→tCO2)
    emission_price: float = 9781.0         # 배출권 단가(원/tCO2)
    property_tax: float = 9.0              # 재산세(백만원/년)
    initial_opex: float = 500.0            # 최초운영비(백만원)

    # ── 재무구조 ──────────────────────────────────
    target_irr: float = 0.065              # 목표 P-IRR
    npv_discount_rate: float = 0.045       # NPV 할인율
    equity_ratio: float = 0.15             # 자기자본 비율
    sub_debt_ratio: float = 0.10           # 후순위 비율

    # ── 금리 ──────────────────────────────────────
    rate_subordinate: float = 0.07         # 후순위 금리
    rate_senior_a: float = 0.055           # 선순위A 금리
    rate_senior_b: float = 0.055           # 선순위B 금리

    # ── 대출 상환 ─────────────────────────────────
    grace_years: int = 1                   # 추가 거치기간(년, 건설기간 외)
    repayment_years: int = 15              # 상환기간(년)

    # ── 감가상각 ──────────────────────────────────
    dep_years_structure: int = 20          # 구축물
    dep_years_equipment: int = 5           # 기타유형자산(주기기)

    # ── DSRA ──────────────────────────────────────
    dsra_quarters: int = 2                 # DSRA 적립 분기수

    # ── 물가상승률 ────────────────────────────────
    inflation_labor: float = 0.027         # 인건비
    inflation_land: float = 0.027          # 토지(임대료)
    inflation_general: float = 0.027       # 일반

    # ── 연료 ──────────────────────────────────────
    fuel_base_price: float = 15.27         # 연료기준단가(원/MJ)
    MJ_PER_NM3: float = 42.71             # 천연가스 열량환산계수

    # ── 법인세 ────────────────────────────────────
    tax_brackets: List[Tuple[float, float]] = field(default_factory=lambda: [
        (200.0, 0.099),          # 과세표준 2억 이하 (법인세+주민세)
        (20000.0, 0.209),        # 2억~200억
        (float('inf'), 0.231),   # 200억 초과
    ])
    min_tax_rate: float = 0.07             # 최저한세
    loss_carryforward: float = 0.8         # 이월결손금 공제한도

    # ── 금융부대비 ────────────────────────────────
    arrangement_fee: float = 0.01          # 주선수수료 (차입금 대비)
    agent_fee: float = 20.0               # 대리은행수수료(백만원/년)

    # ── 신주발행비 ────────────────────────────────
    registration_rate: float = 0.0048      # 등록세율
    legal_rate: float = 0.0007             # 법무사수수료율

    @property
    def total_capacity(self) -> float:
        """총 설치용량(MW)"""
        return self.num_units * self.unit_capacity

    @property
    def senior_ratio(self) -> float:
        """선순위 비율"""
        return 1.0 - self.equity_ratio - self.sub_debt_ratio
