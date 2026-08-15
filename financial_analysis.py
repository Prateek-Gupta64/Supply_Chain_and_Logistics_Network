"""
Takes the MILP optimization result and evaluates the investment case:
  - NPV of switching from the legacy network to the optimized network
  - ROI / payback period
  - Sensitivity analysis: discount rate, demand growth, transport-cost
    inflation, and capex overrun

Investment framing:
  Year 0: capex to re-configure the DC footprint
  Years 1-5: incremental after-tax cash flow = annual cost savings x (1 - tax rate)
             + depreciation tax shield
"""

import json
import numpy as np
import pandas as pd
import milp_model as mm

OUT = "/home/prateek/project/outputs"


def npv_roi_analysis(result, params, num_new_dcs=2):
    horizon = int(params["planning_horizon_years"])
    wacc = float(params["discount_rate_wacc"])
    tax_rate = float(params["corporate_tax_rate"])
    capex_per_dc = float(params["capex_per_new_dc"])
    dep_years = int(params["depreciation_years"])

    annual_savings = result["savings_annual"]
    capex = capex_per_dc * num_new_dcs

    annual_dep = capex / dep_years
    dep_tax_shield = annual_dep * tax_rate
    after_tax_savings = annual_savings * (1 - tax_rate) + dep_tax_shield

    cash_flows = [-capex] + [after_tax_savings] * horizon
    years = list(range(0, horizon + 1))
    discount_factors = [(1 + wacc) ** -t for t in years]
    pv = [cf * df for cf, df in zip(cash_flows, discount_factors)]
    npv = sum(pv)

    # IRR (simple bisection to avoid needing numpy_financial)
    def npv_at(rate):
        return sum(cf / (1 + rate) ** t for t, cf in zip(years, cash_flows))

    lo, hi = -0.99, 5.0
    irr = None
    if npv_at(lo) * npv_at(hi) < 0:
        for _ in range(200):
            mid = (lo + hi) / 2
            if npv_at(lo) * npv_at(mid) <= 0:
                hi = mid
            else:
                lo = mid
        irr = (lo + hi) / 2

    cumulative = np.cumsum(cash_flows)
    payback_year = next((y for y, c in zip(years, cumulative) if c >= 0), None)
    roi_5yr = (sum(cash_flows[1:]) - capex) / capex * 100

    return {
        "capex": capex,
        "annual_pretax_savings": annual_savings,
        "annual_after_tax_cash_flow": after_tax_savings,
        "npv": npv,
        "irr_pct": irr * 100 if irr else None,
        "payback_year": payback_year,
        "roi_5yr_pct": roi_5yr,
        "cash_flows": cash_flows,
        "years": years,
        "cumulative_cash_flow": cumulative.tolist(),
    }


def sensitivity_analysis(base_result, params):
    """Vary demand growth, WACC, transport-cost inflation, and capex
    overrun one at a time (tornado-style) around the base case NPV."""

    base_fin = npv_roi_analysis(base_result, params)
    base_npv = base_fin["npv"]

    scenarios = []

    # 1. Demand growth -> re-solve MILP at +/- multipliers
    for label, mult in [("Demand -10%", 0.90), ("Demand +10%", 1.10)]:
        r = mm.build_and_solve(demand_multiplier=mult, verbose=False)
        base = mm.baseline_cost()  # baseline currently demand-fixed; scale proportionally
        base_scaled = base * mult
        r["baseline_annual_cost"] = base_scaled
        r["savings_annual"] = base_scaled - r["total_annual_cost"]
        fin = npv_roi_analysis(r, params)
        scenarios.append({"driver": "Customer Demand", "scenario": label, "npv": fin["npv"], "delta_vs_base": fin["npv"] - base_npv})

    # 2. WACC (discount rate) +/- 200 bps
    for label, wacc_delta in [("WACC +2pp", 0.02), ("WACC -2pp", -0.02)]:
        p2 = params.copy()
        p2["discount_rate_wacc"] = float(params["discount_rate_wacc"]) + wacc_delta
        fin = npv_roi_analysis(base_result, p2)
        scenarios.append({"driver": "Discount Rate (WACC)", "scenario": label, "npv": fin["npv"], "delta_vs_base": fin["npv"] - base_npv})

    # 3. Transport cost inflation +/- 15% 
    for label, factor in [("Freight Rates +15%", 1.15), ("Freight Rates -15%", 0.85)]:
        r = dict(base_result)
        r["savings_annual"] = base_result["savings_annual"] * factor
        fin = npv_roi_analysis(r, params)
        scenarios.append({"driver": "Freight Rate Inflation", "scenario": label, "npv": fin["npv"], "delta_vs_base": fin["npv"] - base_npv})

    # 4. Capex overrun +/- 25%
    for label, factor in [("Capex +25%", 1.25), ("Capex -25%", 0.75)]:
        p2 = params.copy()
        p2["capex_per_new_dc"] = float(params["capex_per_new_dc"]) * factor
        fin = npv_roi_analysis(base_result, p2)
        scenarios.append({"driver": "Capex", "scenario": label, "npv": fin["npv"], "delta_vs_base": fin["npv"] - base_npv})

    return base_fin, pd.DataFrame(scenarios)


if __name__ == "__main__":
    plants, dcs, customers, cost_pd, cost_dc, params = mm.load_data()

    result = mm.build_and_solve(verbose=False)
    base_cost = mm.baseline_cost()
    result["baseline_annual_cost"] = base_cost
    result["savings_annual"] = base_cost - result["total_annual_cost"]
    result["savings_pct"] = result["savings_annual"] / base_cost * 100

    base_fin, sens_df = sensitivity_analysis(result, params)

    print("=== Base Case Financials ===")
    print(f"Annual pre-tax logistics savings: ${base_fin['annual_pretax_savings']:,.0f} ({result['savings_pct']:.1f}%)")
    print(f"Capex (2 new/reconfigured DCs):    ${base_fin['capex']:,.0f}")
    print(f"5-yr NPV @ {float(params['discount_rate_wacc'])*100:.0f}% WACC:         ${base_fin['npv']:,.0f}")
    print(f"IRR:                               {base_fin['irr_pct']:.1f}%")
    print(f"Payback:                           Year {base_fin['payback_year']}")
    print(f"5-yr ROI:                          {base_fin['roi_5yr_pct']:.0f}%")

    print("\n=== Sensitivity (NPV impact) ===")
    print(sens_df.to_string(index=False))

    sens_df.to_csv(f"{OUT}/sensitivity_analysis.csv", index=False)
    with open(f"{OUT}/financial_analysis.json", "w") as f:
        json.dump({
            "base_case": {k: v for k, v in base_fin.items() if k not in ("cash_flows", "cumulative_cash_flow")},
            "cash_flow_schedule": {
                "years": base_fin["years"],
                "cash_flows": base_fin["cash_flows"],
                "cumulative": base_fin["cumulative_cash_flow"],
            },
            "optimization_result": result,
        }, f, indent=2)
    print(f"\nSaved -> {OUT}/financial_analysis.json, {OUT}/sensitivity_analysis.csv")
