"""입찰단가 역산 및 민감도 분석

핵심 기능:
  1. find_min_price  — 목표 IRR 달성을 위한 최소 고정판매단가 역산
  2. sensitivity_interest_rate — 금리 변동에 따른 입찰단가 민감도
"""

from copy import deepcopy
import numpy as np
from scipy.optimize import brentq
from .params import Params
from .model import FinancialModel


def find_min_price(
    params: Params,
    target_irr: float | None = None,
    price_range: tuple[float, float] = (10.0, 300.0),
) -> dict:
    """목표 P-IRR 달성을 위한 최소 고정판매단가(원/kWh) 찾기

    Args:
        params: 재무모델 입력 파라미터
        target_irr: 목표 P-IRR (None이면 params.target_irr 사용)
        price_range: 탐색 범위 (원/kWh)

    Returns:
        dict with:
            min_fixed_price  : 최소 고정판매단가 (원/kWh)
            variable_price   : 변동판매단가 (원/kWh)
            total_price      : 총 판매단가 (원/kWh)
            p_irr            : 달성 P-IRR
            npv              : NPV (백만원)
            detail           : 전체 모델 결과
    """
    if target_irr is None:
        target_irr = params.target_irr

    model = FinancialModel(params)

    def irr_diff(price: float) -> float:
        result = model.run(fixed_price=price)
        return result["p_irr"] - target_irr

    try:
        min_price = brentq(irr_diff, price_range[0], price_range[1], xtol=0.001)
    except ValueError:
        return {"error": f"범위 {price_range} 내에서 해를 찾을 수 없습니다."}

    result = model.run(fixed_price=min_price)

    return {
        "min_fixed_price": round(min_price, 2),
        "variable_price": round(result["variable_price"], 2),
        "var_fuel_price": round(result["var_fuel_price"], 2),
        "var_emission_price": round(result["var_emission_price"], 2),
        "total_price": round(min_price + result["variable_price"], 2),
        "p_irr": round(result["p_irr"], 6),
        "npv": round(result["npv"], 1),
        "total_investment": round(result["cost"]["total_investment"], 1),
        "detail": result,
    }


def sensitivity_interest_rate(
    params: Params,
    delta_range: tuple[float, float] = (-0.02, 0.02),
    steps: int = 9,
    target_irr: float | None = None,
) -> list[dict]:
    """금리 민감도 분석

    모든 금리(후순위, 선순위A, 선순위B)를 동일 delta만큼 변동시켜
    각 시나리오별 최소 입찰단가를 계산.

    Args:
        params: 기본 파라미터
        delta_range: 금리 변동 범위 (예: (-0.02, 0.02) = ±2%p)
        steps: 분석 단계 수
        target_irr: 목표 P-IRR

    Returns:
        list of dict — 각 시나리오 결과
    """
    deltas = np.linspace(delta_range[0], delta_range[1], steps)
    results = []

    for delta in deltas:
        p = deepcopy(params)
        p.rate_subordinate = params.rate_subordinate + delta
        p.rate_senior_a = params.rate_senior_a + delta
        p.rate_senior_b = params.rate_senior_b + delta

        res = find_min_price(p, target_irr=target_irr)

        if "error" not in res:
            results.append({
                "delta_bp": int(round(delta * 10000)),  # basis points
                "rate_sub": round(p.rate_subordinate * 100, 2),
                "rate_sr_a": round(p.rate_senior_a * 100, 2),
                "rate_sr_b": round(p.rate_senior_b * 100, 2),
                "min_fixed_price": res["min_fixed_price"],
                "variable_price": res["variable_price"],
                "total_price": res["total_price"],
                "total_investment": res["total_investment"],
            })

    return results
