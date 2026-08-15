import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

OUT = "/home/prateek/project/outputs"
CHARTS = "/home/prateek/project/charts"

plt.rcParams["font.family"] = "DejaVu Sans"

with open(f"{OUT}/financial_analysis.json") as f:
    fin = json.load(f)

result = fin["optimization_result"]
base_fin = fin["base_case"]
cf = fin["cash_flow_schedule"]
sens = pd.read_csv(f"{OUT}/sensitivity_analysis.csv")

NAVY = "#1B2A4A"
TEAL = "#0F8B8D"
CORAL = "#E8603C"
GREY = "#8A94A6"
LIGHT = "#EEF1F5"


# 1. Cost comparison bar (baseline vs optimized) + breakdown
fig, ax = plt.subplots(figsize=(8, 5), dpi=200)
labels = ["Legacy Network\n(current state)", "Optimized Network\n(MILP solution)"]
vals = [result["baseline_annual_cost"], result["total_annual_cost"]]
colors = [GREY, TEAL]
bars = ax.bar(labels, vals, color=colors, width=0.5)
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width() / 2, v + max(vals) * 0.02, f"${v/1e6:.1f}M",
            ha="center", fontsize=13, fontweight="bold", color=NAVY)
ax.set_ylabel("Total Annual Network Cost ($)", fontsize=11)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1e6:.0f}M"))
savings_pct = result["savings_pct"]
ax.annotate(f"-{savings_pct:.1f}%", xy=(1, vals[1]), xytext=(0.5, vals[0] * 0.55),
            fontsize=20, fontweight="bold", color=CORAL, ha="center")
ax.spines[["top", "right"]].set_visible(False)
ax.set_title("Annual Logistics Cost: Legacy vs. Optimized Network", fontsize=13, fontweight="bold", color=NAVY, pad=15)
plt.tight_layout()
plt.savefig(f"{CHARTS}/cost_comparison.png", transparent=True)
plt.close()

# 2. Cost breakdown stacked / donut for optimized network

bd = result["cost_breakdown"]
cat_labels = {
    "fixed_facility_cost": "Facility Fixed Cost",
    "inbound_transport_cost": "Inbound Transport",
    "outbound_transport_cost": "Outbound Transport",
    "handling_cost": "DC Handling",
    "cycle_stock_cost": "Cycle Stock (EOQ)",
    "safety_stock_cost": "Safety Stock",
}
vals2 = [bd[k] for k in cat_labels]
labs2 = list(cat_labels.values())
palette = [NAVY, TEAL, "#57B8B0", CORAL, "#F2A365", GREY]

fig, ax = plt.subplots(figsize=(10, 6), dpi=200)
wedges, _texts = ax.pie(vals2, colors=palette, startangle=90, wedgeprops=dict(width=0.42, edgecolor="white", linewidth=2))
ax.set_title("Optimized Network — Annual Cost Breakdown", fontsize=13, fontweight="bold", color=NAVY, pad=20, x=0.3)
total = sum(vals2)
legend_labels = [f"{l}  (${v/1e6:.2f}M, {v/total*100:.0f}%)" for l, v in zip(labs2, vals2)]
ax.legend(wedges, legend_labels, loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=10, frameon=False)
plt.subplots_adjust(left=0.02, right=0.62)
plt.savefig(f"{CHARTS}/cost_breakdown.png", transparent=True, bbox_inches="tight")
plt.close()

# 3. Cumulative cash flow (NPV build-up)

years = cf["years"]
cum = cf["cumulative"]
fig, ax = plt.subplots(figsize=(8, 5), dpi=200)
ax.plot(years, [c / 1e6 for c in cum], marker="o", color=TEAL, linewidth=2.5, markersize=7)
ax.axhline(0, color=GREY, linewidth=1)
ax.fill_between(years, [c / 1e6 for c in cum], 0, where=[c >= 0 for c in cum], color=TEAL, alpha=0.12)
ax.fill_between(years, [c / 1e6 for c in cum], 0, where=[c < 0 for c in cum], color=CORAL, alpha=0.12)
payback = base_fin["payback_year"]
if payback is not None:
    ax.axvline(payback, color=CORAL, linestyle="--", linewidth=1.5)
    ax.text(payback + 0.08, ax.get_ylim()[1] * 0.85, f"Payback: Yr {payback}", color=CORAL, fontsize=10, fontweight="bold")
ax.set_xlabel("Year", fontsize=11)
ax.set_ylabel("Cumulative Cash Flow ($M)", fontsize=11)
ax.set_xticks(years)
ax.spines[["top", "right"]].set_visible(False)
ax.set_title("5-Year Cumulative After-Tax Cash Flow", fontsize=13, fontweight="bold", color=NAVY, pad=15)
plt.tight_layout()
plt.savefig(f"{CHARTS}/cashflow.png", transparent=True)
plt.close()

# 4. Tornado sensitivity chart
sens["driver_scenario_pair"] = sens["driver"]
grouped = sens.groupby("driver")["delta_vs_base"].agg(["min", "max"])
grouped["range"] = grouped["max"] - grouped["min"]
grouped = grouped.sort_values("range")

fig, ax = plt.subplots(figsize=(8.5, 5), dpi=200)
y_pos = range(len(grouped))
for i, (driver, row) in enumerate(grouped.iterrows()):
    ax.barh(i, row["max"] - 0, left=0, color=TEAL, height=0.55, alpha=0.9 if row["max"] > 0 else 0.9)
    ax.barh(i, row["min"] - 0, left=0, color=CORAL, height=0.55, alpha=0.9)
ax.axvline(0, color=NAVY, linewidth=1.2)
ax.set_yticks(list(y_pos))
ax.set_yticklabels(grouped.index, fontsize=10)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1e6:.1f}M"))
ax.set_xlabel("NPV Impact vs. Base Case ($)", fontsize=11)
ax.set_title("Sensitivity of 5-Year NPV to Key Drivers", fontsize=13, fontweight="bold", color=NAVY, pad=15)
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig(f"{CHARTS}/tornado.png", transparent=True)
plt.close()

# 5. Network map (simple scatter of plants / opened DCs / customers)
dcs = pd.read_csv("/home/prateek/project/data/candidate_dcs.csv")
plants = pd.read_csv("/home/prateek/project/data/plants.csv")
customers = pd.read_csv("/home/prateek/project/data/customers.csv")
opened = set(result["dcs_opened"])

fig, ax = plt.subplots(figsize=(9, 6), dpi=200)
ax.scatter(customers.lon, customers.lat, s=45, color=GREY, alpha=0.6, label="Customer demand zones", zorder=2)
closed_dcs = dcs[~dcs.dc_id.isin(opened)]
open_dcs = dcs[dcs.dc_id.isin(opened)]
ax.scatter(closed_dcs.lon, closed_dcs.lat, s=140, facecolors="none", edgecolors=GREY, linewidths=1.5,
           marker="s", label="Candidate DC (not selected)", zorder=3)
ax.scatter(open_dcs.lon, open_dcs.lat, s=220, color=TEAL, marker="s", edgecolors=NAVY, linewidths=1.2,
           label="DC opened (optimal)", zorder=4)
ax.scatter(plants.lon, plants.lat, s=260, color=CORAL, marker="^", edgecolors=NAVY, linewidths=1.2,
           label="Manufacturing plant", zorder=5)
for _, d in open_dcs.iterrows():
    ax.annotate(d.dc_id, (d.lon, d.lat), textcoords="offset points", xytext=(6, 6), fontsize=8, color=NAVY, fontweight="bold")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_title("Optimized Multi-Echelon Network Footprint", fontsize=13, fontweight="bold", color=NAVY, pad=15)
ax.legend(loc="lower left", fontsize=8.5, frameon=True, framealpha=0.9)
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig(f"{CHARTS}/network_map.png", transparent=True)
plt.close()

print("Charts saved to", CHARTS)
