"""연료전지 발전사업 재무모델 — 데모 실행

엑셀 재무모델 기본값으로 실행하여 결과를 검증.
"""

from engine import Params, FinancialModel, find_min_price, sensitivity_interest_rate


def print_section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def main():
    # ── 기본 파라미터 (엑셀 기본값) ──
    params = Params()

    # ══════════════════════════════════════════════
    #  1. 기본 모델 실행 (엑셀 기본 단가 69.75원/kWh)
    # ══════════════════════════════════════════════
    print_section("1. 기본 모델 실행 (고정판매단가 = 69.75 원/kWh)")

    model = FinancialModel(params)
    result = model.run()

    cost = result["cost"]
    print(f"\n[사업비 구조]")
    print(f"  주기기비        : {cost['equipment']:>12,.1f} 백만원")
    print(f"  설치공사비      : {cost['installation']:>12,.1f} 백만원")
    print(f"  토지비          : {cost['land']:>12,.1f} 백만원")
    print(f"  감리비          : {cost['supervision']:>12,.1f} 백만원")
    print(f"  예비비          : {cost['contingency']:>12,.1f} 백만원")
    print(f"  건설비 소계     : {cost['construction_subtotal']:>12,.1f} 백만원")
    print(f"  건설이자        : {cost['construction_interest']:>12,.1f} 백만원")
    print(f"  금융부대비      : {cost['financial_fees']:>12,.1f} 백만원")
    print(f"  신주발행비      : {cost['issuance_fee']:>12,.1f} 백만원")
    print(f"  DSRA            : {cost['dsra']:>12,.1f} 백만원")
    print(f"  최초운영비      : {cost['initial_opex']:>12,.1f} 백만원")
    print(f"  ─────────────────────────────────────")
    print(f"  총 투자비       : {cost['total_investment']:>12,.1f} 백만원")
    print(f"  자기자본({params.equity_ratio*100:.0f}%)  : {cost['equity']:>12,.1f} 백만원")
    print(f"  후순위({params.sub_debt_ratio*100:.0f}%)   : {cost['sub_debt']:>12,.1f} 백만원")
    print(f"  선순위({params.senior_ratio*100:.0f}%)   : {cost['senior_debt']:>12,.1f} 백만원")

    print(f"\n[연간 주요 지표 (1년차)]")
    print(f"  발전량          : {result['revenue']['gen_mwh'][0]:>12,.1f} MWh")
    print(f"  판매량          : {result['revenue']['sales_mwh'][0]:>12,.1f} MWh")
    print(f"  전력매출        : {result['revenue']['power'][0]:>12,.1f} 백만원")
    print(f"  열매출          : {result['revenue']['heat'][0]:>12,.1f} 백만원")
    print(f"  매출합계        : {result['revenue']['total'][0]:>12,.1f} 백만원")
    print(f"  운영비합계      : {result['opex']['total'][0]:>12,.1f} 백만원")
    print(f"  EBITDA          : {result['ebitda'][0]:>12,.1f} 백만원")

    print(f"\n[수익성]")
    print(f"  P-IRR           : {result['p_irr']*100:>10.2f} %")
    print(f"  NPV             : {result['npv']:>12,.1f} 백만원")
    print(f"  고정판매단가    : {result['fixed_price']:>10.2f} 원/kWh")
    print(f"  변동판매단가    : {result['variable_price']:>10.2f} 원/kWh")
    print(f"    (연료비)      : {result['var_fuel_price']:>10.2f} 원/kWh")
    print(f"    (배출비)      : {result['var_emission_price']:>10.2f} 원/kWh")
    print(f"  총 판매단가     : {result['total_selling_price']:>10.2f} 원/kWh")

    # ══════════════════════════════════════════════
    #  2. 최소 입찰단가 역산
    # ══════════════════════════════════════════════
    print_section(f"2. 최소 입찰단가 역산 (목표 P-IRR = {params.target_irr*100:.1f}%)")

    price_result = find_min_price(params)

    if "error" in price_result:
        print(f"  오류: {price_result['error']}")
    else:
        print(f"  최소 고정판매단가 : {price_result['min_fixed_price']:>10.2f} 원/kWh")
        print(f"  변동판매단가      : {price_result['variable_price']:>10.2f} 원/kWh")
        print(f"    (연료비)        : {price_result['var_fuel_price']:>10.2f} 원/kWh")
        print(f"    (배출비)        : {price_result['var_emission_price']:>10.2f} 원/kWh")
        print(f"  총 판매단가       : {price_result['total_price']:>10.2f} 원/kWh")
        print(f"  달성 P-IRR        : {price_result['p_irr']*100:>10.4f} %")
        print(f"  NPV               : {price_result['npv']:>12.1f} 백만원")
        print(f"  총 투자비         : {price_result['total_investment']:>12.1f} 백만원")

    # ══════════════════════════════════════════════
    #  3. 금리 민감도 분석
    # ══════════════════════════════════════════════
    print_section("3. 금리 민감도 분석 (±2%p)")

    sensitivity = sensitivity_interest_rate(
        params,
        delta_range=(-0.02, 0.02),
        steps=9,
    )

    if sensitivity:
        print(f"\n  {'금리변동':>8} | {'후순위':>7} | {'선순위A':>7} | "
              f"{'고정단가':>10} | {'변동단가':>10} | {'총단가':>10} | {'총투자비':>12}")
        print(f"  {'-'*8} | {'-'*7} | {'-'*7} | "
              f"{'-'*10} | {'-'*10} | {'-'*10} | {'-'*12}")

        for row in sensitivity:
            sign = "+" if row["delta_bp"] >= 0 else ""
            print(
                f"  {sign}{row['delta_bp']:>5}bp | "
                f"{row['rate_sub']:>6.2f}% | "
                f"{row['rate_sr_a']:>6.2f}% | "
                f"{row['min_fixed_price']:>8.2f}원 | "
                f"{row['variable_price']:>8.2f}원 | "
                f"{row['total_price']:>8.2f}원 | "
                f"{row['total_investment']:>10.1f}M"
            )
    else:
        print("  민감도 분석 실패")

    print(f"\n{'='*60}")
    print("  완료")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
