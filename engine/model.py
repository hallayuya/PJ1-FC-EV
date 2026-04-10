"""연료전지 발전사업 재무모델 계산 엔진

엑셀 재무모델의 핵심 로직을 Python으로 구현.
연간 단위 계산 (v1). 분기 단위는 v2에서 구현 예정.

계산 흐름:
  사업비 → 재원조달 → 매출 → 운영비 → 감가상각 → 세금 → FCFF → P-IRR
"""

import numpy as np
from scipy.optimize import brentq
from .params import Params
from .specs import get_annual_specs

UNIT = 1_000_000  # 원 → 백만원 변환


class FinancialModel:
    """연료전지 발전사업 재무모델"""

    def __init__(self, params: Params):
        self.p = params
        self.n = params.operation_years
        self.specs = get_annual_specs(
            params.equipment_type,
            params.num_units,
            params.operation_years,
        )

    # ──────────────────────────────────────────────
    #  메인 실행
    # ──────────────────────────────────────────────

    def run(self, fixed_price: float | None = None) -> dict:
        """재무모델 전체 실행

        Args:
            fixed_price: 고정판매단가(원/kWh) 오버라이드. None이면 params 값 사용.

        Returns:
            dict — 모든 계산 결과
        """
        price = fixed_price if fixed_price is not None else self.p.fixed_price
        p = self.p
        n = self.n

        # 1) 사업비 (순환참조 반복 해결)
        cost = self._calc_cost()

        # 2) 연간 매출
        revenue = self._calc_revenue(price)

        # 3) 연간 운영비
        opex = self._calc_opex()

        # 4) 감가상각
        dep = self._calc_depreciation(cost)

        # 5) EBITDA / EBIT
        ebitda = revenue["total"] - opex["total"]
        ebit = ebitda - dep["total"]

        # 6) 법인세 (P-IRR용: 이자비용 제외)
        tax = self._calc_tax(ebit)

        # 7) FCFF = EBITDA - Tax
        fcff = ebitda - tax

        # 8) P-IRR
        cf = np.concatenate([[-cost["total_investment"]], fcff])
        p_irr = self._irr(cf)

        # 9) NPV
        npv = self._npv(cf, p.npv_discount_rate)

        # 10) 변동판매단가
        total_sales_mwh = float(np.sum(revenue["sales_mwh"]))
        if total_sales_mwh > 0:
            var_fuel = float(np.sum(opex["fuel"])) / total_sales_mwh * 1000
            var_emission = float(np.sum(opex["emission"])) / total_sales_mwh * 1000
        else:
            var_fuel = var_emission = 0.0
        variable_price = var_fuel + var_emission

        return {
            "cost": cost,
            "revenue": revenue,
            "opex": opex,
            "depreciation": dep,
            "ebitda": ebitda,
            "ebit": ebit,
            "tax": tax,
            "fcff": fcff,
            "p_irr": p_irr,
            "npv": npv,
            "fixed_price": price,
            "variable_price": variable_price,
            "var_fuel_price": var_fuel,
            "var_emission_price": var_emission,
            "total_selling_price": price + variable_price,
        }

    # ──────────────────────────────────────────────
    #  1) 사업비
    # ──────────────────────────────────────────────

    def _calc_cost(self) -> dict:
        """총투자비 계산 (건설이자 순환참조를 반복법으로 해결)"""
        p = self.p

        # 직접 건설비
        equipment = p.equipment_unit_cost * p.num_units
        installation = p.install_cost_per_mw * p.total_capacity
        land = p.land_area * p.land_price / UNIT
        supervision = p.supervision_cost

        base = equipment + installation + land + supervision
        contingency = base * p.contingency_rate
        construction_sub = base + contingency

        # 순환참조 반복 해결
        total_inv = construction_sub  # 초기 추정
        for _ in range(30):
            equity = total_inv * p.equity_ratio
            sub_debt = total_inv * p.sub_debt_ratio
            senior_debt = total_inv * p.senior_ratio
            total_debt = sub_debt + senior_debt

            # 건설이자: 평균 잔액 × 가중금리 × 건설기간
            if total_debt > 0:
                w_rate = (
                    sub_debt * p.rate_subordinate
                    + senior_debt * (p.rate_senior_a + p.rate_senior_b) / 2
                ) / total_debt
            else:
                w_rate = 0.0
            construction_interest = total_debt * w_rate * (p.construction_months / 12) / 2

            # 금융부대비
            financial_fees = total_debt * p.arrangement_fee + p.agent_fee

            # 신주발행비
            issuance_fee = equity * (p.registration_rate + p.legal_rate)

            # DSRA 초기적립 (선순위 분기 원리금 × N분기)
            if p.repayment_years > 0:
                annual_principal = senior_debt / p.repayment_years
                annual_interest_sr = senior_debt * p.rate_senior_a
                dsra = (annual_principal + annual_interest_sr) * p.dsra_quarters / 4
            else:
                dsra = 0.0

            new_total = (
                construction_sub
                + construction_interest
                + financial_fees
                + issuance_fee
                + dsra
                + p.initial_opex
            )
            if abs(new_total - total_inv) < 0.001:
                total_inv = new_total
                break
            total_inv = new_total

        return {
            "equipment": equipment,
            "installation": installation,
            "land": land,
            "supervision": supervision,
            "contingency": contingency,
            "construction_subtotal": construction_sub,
            "construction_interest": construction_interest,
            "financial_fees": financial_fees,
            "issuance_fee": issuance_fee,
            "dsra": dsra,
            "initial_opex": p.initial_opex,
            "total_investment": total_inv,
            "equity": equity,
            "sub_debt": sub_debt,
            "senior_debt": senior_debt,
        }

    # ──────────────────────────────────────────────
    #  2) 매출
    # ──────────────────────────────────────────────

    def _calc_revenue(self, fixed_price: float) -> dict:
        """연간 매출 계산 (백만원)"""
        p = self.p
        specs = self.specs

        gen_mwh = specs["generation_mwh"]
        internal = gen_mwh * p.internal_consumption
        sales_mwh = gen_mwh - internal

        # 전력매출 = 판매량(MWh) × 고정단가(원/kWh) × 1000(kWh/MWh) / 1M
        power = sales_mwh * fixed_price / 1000

        # 열매출
        heat = specs["heat_gcal"] * p.heat_sales_ratio * p.heat_price / UNIT

        # 연료비 정산 (사용량 기준 pass-through)
        fuel_passthrough = specs["fuel_mj"] * p.fuel_base_price / UNIT

        # 배출비 정산
        emission_passthrough = (
            specs["fuel_nm3"] * p.emission_factor * p.emission_price / UNIT
        )

        total = power + heat + fuel_passthrough + emission_passthrough

        return {
            "gen_mwh": gen_mwh,
            "sales_mwh": sales_mwh,
            "power": power,
            "heat": heat,
            "fuel_passthrough": fuel_passthrough,
            "emission_passthrough": emission_passthrough,
            "total": total,
        }

    # ──────────────────────────────────────────────
    #  3) 운영비
    # ──────────────────────────────────────────────

    def _calc_opex(self) -> dict:
        """연간 운영비 계산 (백만원)"""
        p = self.p
        n = self.n
        specs = self.specs

        # 물가상승 인덱스 (0년차=1.0, 기준시점 대비)
        idx_labor = np.array([(1 + p.inflation_labor) ** y for y in range(n)])
        idx_land = np.array([(1 + p.inflation_land) ** y for y in range(n)])
        idx_gen = np.array([(1 + p.inflation_general) ** y for y in range(n)])

        labor = np.full(n, p.labor_cost_pp * p.num_workers) * idx_labor
        fuel = specs["fuel_mj"] * p.fuel_base_price / UNIT
        ltsa = np.full(n, p.ltsa_per_unit * p.num_units)
        ltsa[0] = 0.0  # 1년차 LTSA 없음
        mgmt = np.full(n, p.mgmt_cost) * idx_gen
        water = np.full(n, p.water_usage * p.water_price / UNIT) * idx_gen
        insurance = np.full(n, p.insurance_per_mw * p.total_capacity)
        rent = np.full(n, p.rent) * idx_land
        emission = specs["fuel_nm3"] * p.emission_factor * p.emission_price / UNIT
        sales_mwh = specs["generation_mwh"] * (1 - p.internal_consumption)
        trading = sales_mwh * p.trading_fee / UNIT
        prop_tax = np.full(n, p.property_tax)

        total = (
            labor + fuel + ltsa + mgmt + water
            + insurance + rent + emission + trading + prop_tax
        )

        return {
            "labor": labor,
            "fuel": fuel,
            "ltsa": ltsa,
            "mgmt": mgmt,
            "water": water,
            "insurance": insurance,
            "rent": rent,
            "emission": emission,
            "trading": trading,
            "property_tax": prop_tax,
            "total": total,
        }

    # ──────────────────────────────────────────────
    #  4) 감가상각
    # ──────────────────────────────────────────────

    def _calc_depreciation(self, cost: dict) -> dict:
        """정액법 감가상각 (백만원/년)"""
        p = self.p
        n = self.n

        # 기타유형자산 = 주기기 → 5년 상각
        equip_val = cost["equipment"]
        equip_dep = np.zeros(n)
        for y in range(min(p.dep_years_equipment, n)):
            equip_dep[y] = equip_val / p.dep_years_equipment

        # 구축물 = 건설비 - 주기기 - 토지 → 20년 상각
        struct_val = cost["construction_subtotal"] - equip_val - cost["land"]
        struct_dep = np.zeros(n)
        for y in range(min(p.dep_years_structure, n)):
            struct_dep[y] = struct_val / p.dep_years_structure

        return {
            "equipment": equip_dep,
            "structure": struct_dep,
            "total": equip_dep + struct_dep,
        }

    # ──────────────────────────────────────────────
    #  5) 법인세
    # ──────────────────────────────────────────────

    def _calc_tax(self, ebit: np.ndarray) -> np.ndarray:
        """법인세 계산 (누진세율, 이월결손금 반영)"""
        p = self.p
        n = self.n
        tax = np.zeros(n)
        loss_cf = 0.0  # 이월결손금 잔액

        for y in range(n):
            taxable = float(ebit[y])

            if taxable < 0:
                loss_cf += abs(taxable)
                continue

            # 이월결손금 공제
            if loss_cf > 0:
                deduction = min(loss_cf, taxable * p.loss_carryforward)
                taxable -= deduction
                loss_cf -= deduction

            if taxable <= 0:
                continue

            # 누진세율 적용
            t = 0.0
            prev = 0.0
            for bracket, rate in p.tax_brackets:
                if taxable <= bracket:
                    t += (taxable - prev) * rate
                    break
                else:
                    t += (bracket - prev) * rate
                    prev = bracket

            # 최저한세
            min_tax = taxable * p.min_tax_rate
            tax[y] = max(t, min_tax)

        return tax

    # ──────────────────────────────────────────────
    #  IRR / NPV
    # ──────────────────────────────────────────────

    @staticmethod
    def _irr(cashflows: np.ndarray) -> float:
        """IRR 계산 (Brent's method)"""
        def npv_at(r):
            return sum(cf / (1 + r) ** t for t, cf in enumerate(cashflows))

        try:
            return brentq(npv_at, -0.3, 1.0, xtol=1e-10)
        except (ValueError, RuntimeError):
            return float("nan")

    @staticmethod
    def _npv(cashflows: np.ndarray, rate: float) -> float:
        """NPV 계산"""
        return sum(cf / (1 + rate) ** t for t, cf in enumerate(cashflows))
