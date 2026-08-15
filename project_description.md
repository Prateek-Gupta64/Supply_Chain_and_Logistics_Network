# Multi-Echelon Supply Chain Network Optimization
### Facility Location & Inventory Routing MILP | Strategic Growth Roadmap | Financial Business Case

---

## 1. Project Overview

This project designs and evaluates an optimal **multi-echelon supply chain network** —
manufacturing plants, candidate distribution centers (DCs), and customer demand
zones — using a **Mixed-Integer Linear Programming (MILP)** model built in Python.
The model jointly decides *which DCs to open* and *how to route product and
inventory through them* to minimize total annualized network cost, then feeds
those results into a financial business case (NPV, ROI, sensitivity analysis)
that supports the investment decision.

**Note on data:** No proprietary company data was provided for this exercise,
so the network (3 plants, 8 candidate DC sites, 24 U.S. customer demand zones)
was synthesized to be realistic in scale, geography, and cost structure. Every
script in this project is written to run on real ERP/TMS extracts by simply
swapping the CSVs in `/data` — no model logic needs to change.

## 2. Business Problem

A mid-market distributor's DC network grew organically, city-by-city, rather
than by design. Facilities were added as regions came online rather than
re-evaluated as demand shifted. This creates three quantifiable inefficiencies
the project addresses:

1. **Misaligned facility footprint** — legacy DCs are not necessarily where
   current demand and freight lanes make them cheapest to run.
2. **Sub-optimal customer-to-DC assignment** — legacy routing follows nearest-
   distance heuristics, not true landed cost (transport + handling + inbound).
3. **Un-pooled inventory risk** — each DC carries safety stock independently,
   forgoing the statistical risk-pooling benefit of a well-designed network.

## 3. Methodology

### 3.1 Network structure (multi-echelon)
`Plants → Distribution Centers (candidate, binary open/close) → Customers`

### 3.2 MILP formulation
- **Decision variables:** binary DC-open indicators; continuous plant→DC and
  DC→customer flow variables.
- **Objective:** minimize facility fixed cost + inbound transport + outbound
  transport + DC handling + inventory carrying cost (cycle stock + safety
  stock).
- **Constraints:** demand satisfaction, DC/plant capacity, flow conservation,
  a minimum-DC-count service resilience rule.
- **Inventory routing:** Economic Order Quantity (EOQ) cycle-stock cost and
  a safety-stock term parameterized by lead time and service level, linearized
  per DC so the whole model solves as an exact MILP (via CBC, open-source).

### 3.3 Solver
[PuLP](https://coin-or.github.io/pulp/) with the CBC solver — open-source,
production-safe, no commercial license required. The model solves to proven
optimality in under a second at this problem scale.

### 3.4 Financial evaluation
Annual network-cost savings from the optimization are converted into an
investment case: after-tax cash flows (savings + depreciation tax shield) are
discounted at the company's WACC over a 5-year horizon to compute NPV, IRR,
payback period, and ROI. A tornado sensitivity analysis stress-tests the case
against demand growth, discount rate, freight-rate inflation, and capex
overrun.

## 4. Key Results

| Metric | Legacy Network | Optimized Network |
|---|---|---|
| Annual network cost | $15.5M | $12.7M |
| DCs operating | 5 (fixed legacy set) | 5 (re-optimized locations) |
| **Annual savings** | — | **$2.76M (17.8%)** |

| Financial Metric | Value |
|---|---|
| Capex (footprint transition) | $8.4M |
| 5-year NPV @ 9% WACC | $0.55M |
| IRR | 11.5% |
| Payback period | Year 4 |
| 5-year ROI | 37% |

**Sensitivity:** NPV is most sensitive to customer demand growth (±10% demand
swings NPV by roughly ±$4M) and capex execution risk, and least sensitive to
the discount rate — meaning the investment case is directionally robust but
demand-forecast accuracy is the highest-value input to get right before
committing capital.

## 5. Strategic Growth Roadmap — Key Insights for Stakeholders

1. **Re-site, don't just resize.** The 17.8% savings come almost entirely from
   better facility *placement* and customer *assignment* — not from closing
   facilities outright. This is a lower-risk, easier-to-sell change internally
   than a headcount- or footprint-reduction story.
2. **Facility fixed cost dominates the cost stack (~81%).** Future network
   reviews should prioritize lease renewal / build-vs-lease timing windows as
   the highest-leverage decision point, ahead of transportation-rate
   negotiations.
3. **The investment clears its hurdle rate but with a 4-year payback** — the
   roadmap should sequence the two highest-value DC transitions first (phase
   the capex) rather than transitioning the full footprint in year one, to
   pull the payback forward and de-risk the capital commitment.
4. **Demand-growth risk deserves more diligence than financing risk.** Given
   the tornado analysis, a follow-on workstream should tighten the regional
   demand forecast (e.g., a rolling S&OP feed into this model) before final
   sign-off, rather than spending further cycles on discount-rate debates.

## 6. Deliverables in this package

| File | Description |
|---|---|
| `data/supply_chain_data.xlsx` | Consolidated input dataset (plants, candidate DCs, customers, transport cost matrices, financial parameters) |
| `data/*.csv` | Same data, as individual CSVs for direct model/script consumption |
| `scripts/generate_data.py` | Synthesizes the network dataset (swap in real ERP/TMS extracts here) |
| `scripts/milp_model.py` | The core MILP model — facility location + inventory routing (PuLP/CBC) |
| `scripts/financial_analysis.py` | NPV, ROI, IRR, payback, and tornado sensitivity analysis |
| `scripts/make_charts.py` | Generates all chart assets used in the report |
| `outputs/optimization_result.json` | Raw MILP solution (facility decisions, flows, cost breakdown) |
| `outputs/financial_analysis.json`, `sensitivity_analysis.csv` | Financial model outputs |
| `Supply_Chain_Network_Optimization_Report.pptx` | Stakeholder-ready presentation of the full project |

## 7. How to reproduce

```bash
pip install pulp pandas openpyxl matplotlib --break-system-packages
python scripts/generate_data.py       # builds /data
python scripts/milp_model.py          # solves the MILP -> /outputs/optimization_result.json
python scripts/financial_analysis.py  # NPV/ROI/sensitivity -> /outputs/financial_analysis.json
python scripts/make_charts.py         # chart assets -> /charts
```

## 8. Limitations & Next Steps

- **Synthetic data:** results are illustrative of methodology, not a real
  network's numbers. Swapping in actual facility, demand, and freight-rate
  data (schemas already match common ERP/TMS extracts) would make this
  directly decision-ready.
- **Single product / deterministic demand:** a natural next iteration is a
  multi-SKU model with stochastic demand and explicit service-level chance
  constraints rather than a fixed safety-stock z-score.
- **Static single-period model:** a rolling multi-period version would let the
  roadmap phase DC openings/closures year-by-year rather than as one switch.
