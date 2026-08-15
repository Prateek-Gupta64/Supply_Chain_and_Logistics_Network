"""
generate_data.py
-----------------
Builds a synthetic but realistic multi-echelon supply-chain dataset:
Plants (echelon 1) -> Distribution Centers / DCs (echelon 2, candidate
locations) -> Customer demand zones (echelon 3).

Output: four CSVs in ../data/ used directly by milp_model.py, plus a
consolidated workbook (supply_chain_data.xlsx) for human review.
"""

import math
import random
import pandas as pd

random.seed(42)

# ---------------------------------------------------------------------
# 1. Plants (existing, fixed network — echelon 1)
# ---------------------------------------------------------------------
plants = [
    {"plant_id": "PLANT_MW", "name": "Midwest Manufacturing Hub", "city": "Chicago, IL",
     "lat": 41.8781, "lon": -87.6298, "capacity_units": 620000, "unit_prod_cost": 11.20},
    {"plant_id": "PLANT_SE", "name": "Southeast Manufacturing Hub", "city": "Atlanta, GA",
     "lat": 33.7490, "lon": -84.3880, "capacity_units": 480000, "unit_prod_cost": 10.75},
    {"plant_id": "PLANT_W", "name": "West Coast Manufacturing Hub", "city": "Reno, NV",
     "lat": 39.5296, "lon": -119.8138, "capacity_units": 400000, "unit_prod_cost": 12.05},
]
df_plants = pd.DataFrame(plants)

# ---------------------------------------------------------------------
# 2. Candidate Distribution Centers (echelon 2 — facility-location decision)
# ---------------------------------------------------------------------
dcs = [
    {"dc_id": "DC_01", "city": "Dallas, TX",        "lat": 32.7767, "lon": -96.7970, "capacity_units": 260000, "fixed_cost_annual": 2_450_000, "unit_handling_cost": 1.35},
    {"dc_id": "DC_02", "city": "Columbus, OH",       "lat": 39.9612, "lon": -82.9988, "capacity_units": 240000, "fixed_cost_annual": 2_180_000, "unit_handling_cost": 1.20},
    {"dc_id": "DC_03", "city": "Ontario, CA",        "lat": 34.0633, "lon": -117.6509, "capacity_units": 300000, "fixed_cost_annual": 3_050_000, "unit_handling_cost": 1.55},
    {"dc_id": "DC_04", "city": "Harrisburg, PA",     "lat": 40.2732, "lon": -76.8867, "capacity_units": 220000, "fixed_cost_annual": 2_320_000, "unit_handling_cost": 1.28},
    {"dc_id": "DC_05", "city": "Kansas City, MO",    "lat": 39.0997, "lon": -94.5786, "capacity_units": 200000, "fixed_cost_annual": 1_890_000, "unit_handling_cost": 1.10},
    {"dc_id": "DC_06", "city": "Savannah, GA",       "lat": 32.0809, "lon": -81.0912, "capacity_units": 210000, "fixed_cost_annual": 1_950_000, "unit_handling_cost": 1.18},
    {"dc_id": "DC_07", "city": "Denver, CO",         "lat": 39.7392, "lon": -104.9903, "capacity_units": 180000, "fixed_cost_annual": 2_010_000, "unit_handling_cost": 1.32},
    {"dc_id": "DC_08", "city": "Portland, OR",       "lat": 45.5152, "lon": -122.6784, "capacity_units": 170000, "fixed_cost_annual": 2_260_000, "unit_handling_cost": 1.40},
]
df_dcs = pd.DataFrame(dcs)

# ---------------------------------------------------------------------
# 3. Customer demand zones (echelon 3 — aggregated by metro region)
# ---------------------------------------------------------------------
customer_cities = [
    ("CUST_NYC", "New York, NY", 40.7128, -74.0060),
    ("CUST_LAX", "Los Angeles, CA", 34.0522, -118.2437),
    ("CUST_CHI", "Chicago, IL", 41.8781, -87.6298),
    ("CUST_HOU", "Houston, TX", 29.7604, -95.3698),
    ("CUST_PHX", "Phoenix, AZ", 33.4484, -112.0740),
    ("CUST_PHL", "Philadelphia, PA", 39.9526, -75.1652),
    ("CUST_SAT", "San Antonio, TX", 29.4241, -98.4936),
    ("CUST_SD", "San Diego, CA", 32.7157, -117.1611),
    ("CUST_DAL", "Dallas, TX", 32.7767, -96.7970),
    ("CUST_SJ", "San Jose, CA", 37.3382, -121.8863),
    ("CUST_AUS", "Austin, TX", 30.2672, -97.7431),
    ("CUST_JAX", "Jacksonville, FL", 30.3322, -81.6557),
    ("CUST_COL", "Columbus, OH", 39.9612, -82.9988),
    ("CUST_CLT", "Charlotte, NC", 35.2271, -80.8431),
    ("CUST_SF", "San Francisco, CA", 37.7749, -122.4194),
    ("CUST_IND", "Indianapolis, IN", 39.7684, -86.1581),
    ("CUST_SEA", "Seattle, WA", 47.6062, -122.3321),
    ("CUST_DEN", "Denver, CO", 39.7392, -104.9903),
    ("CUST_BOS", "Boston, MA", 42.3601, -71.0589),
    ("CUST_ATL", "Atlanta, GA", 33.7490, -84.3880),
    ("CUST_DET", "Detroit, MI", 42.3314, -83.0458),
    ("CUST_MIA", "Miami, FL", 25.7617, -80.1918),
    ("CUST_MSP", "Minneapolis, MN", 44.9778, -93.2650),
    ("CUST_STL", "St. Louis, MO", 38.6270, -90.1994),
]

customers = []
for cid, city, lat, lon in customer_cities:
    base_demand = random.randint(14000, 42000)
    customers.append({
        "customer_id": cid,
        "region": city,
        "lat": lat,
        "lon": lon,
        "annual_demand_units": base_demand,
        "demand_growth_pct": round(random.uniform(0.02, 0.07), 3),
        "service_level_priority": random.choice(["High", "Medium", "Medium", "Low"]),
    })
df_customers = pd.DataFrame(customers)

# ---------------------------------------------------------------------
# 4. Distance-based transport cost matrices (haversine distance x $/unit-mile)
# ---------------------------------------------------------------------
def haversine(lat1, lon1, lat2, lon2):
    R = 3958.8  # miles
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))

RATE_PLANT_DC = 0.0021       # $ per unit per mile (full truckload, inbound)
RATE_DC_CUST = 0.0038        # $ per unit per mile (LTL/parcel, outbound - costlier per mile)

plant_dc_rows = []
for _, p in df_plants.iterrows():
    for _, d in df_dcs.iterrows():
        dist = haversine(p.lat, p.lon, d.lat, d.lon)
        plant_dc_rows.append({
            "plant_id": p.plant_id, "dc_id": d.dc_id,
            "distance_miles": round(dist, 1),
            "unit_transport_cost": round(dist * RATE_PLANT_DC, 3),
        })
df_plant_dc_cost = pd.DataFrame(plant_dc_rows)

dc_cust_rows = []
for _, d in df_dcs.iterrows():
    for _, c in df_customers.iterrows():
        dist = haversine(d.lat, d.lon, c.lat, c.lon)
        dc_cust_rows.append({
            "dc_id": d.dc_id, "customer_id": c.customer_id,
            "distance_miles": round(dist, 1),
            "unit_transport_cost": round(dist * RATE_DC_CUST, 3),
        })
df_dc_cust_cost = pd.DataFrame(dc_cust_rows)

# ---------------------------------------------------------------------
# 5. Global financial / inventory parameters
# ---------------------------------------------------------------------
parameters = {
    "parameter": [
        "planning_horizon_years", "discount_rate_wacc", "holding_cost_rate_annual",
        "avg_unit_value", "order_cost_per_shipment", "safety_stock_z_score",
        "corporate_tax_rate", "capex_per_new_dc", "depreciation_years",
        "baseline_num_dcs_open",
    ],
    "value": [5, 0.09, 0.22, 42.50, 185, 1.65, 0.24, 4_200_000, 10, 8],
    "notes": [
        "Strategic evaluation window for NPV/ROI",
        "Weighted-average cost of capital used as discount rate",
        "Annual holding cost as % of unit value (capital, insurance, obsolescence, storage)",
        "Average finished-good value used for inventory carrying cost",
        "Fixed cost per replenishment order/shipment (EOQ inventory routing input)",
        "z-score for ~95% cycle service level (safety stock sizing)",
        "Effective corporate tax rate for NPV after-tax cash flows",
        "One-time capital expenditure to commission a new/upgraded DC",
        "Straight-line depreciation life for new DC capex",
        "Current-state network: all 8 candidate DCs operating (pre-optimization baseline)",
    ],
}
df_params = pd.DataFrame(parameters)

# ---------------------------------------------------------------------
# Write outputs
# ---------------------------------------------------------------------
out_dir = "/home/claude/project/data"
df_plants.to_csv(f"{out_dir}/plants.csv", index=False)
df_dcs.to_csv(f"{out_dir}/candidate_dcs.csv", index=False)
df_customers.to_csv(f"{out_dir}/customers.csv", index=False)
df_plant_dc_cost.to_csv(f"{out_dir}/transport_cost_plant_to_dc.csv", index=False)
df_dc_cust_cost.to_csv(f"{out_dir}/transport_cost_dc_to_customer.csv", index=False)
df_params.to_csv(f"{out_dir}/parameters.csv", index=False)

with pd.ExcelWriter(f"{out_dir}/supply_chain_data.xlsx", engine="openpyxl") as xw:
    df_plants.to_excel(xw, sheet_name="Plants", index=False)
    df_dcs.to_excel(xw, sheet_name="Candidate_DCs", index=False)
    df_customers.to_excel(xw, sheet_name="Customers", index=False)
    df_plant_dc_cost.to_excel(xw, sheet_name="Cost_Plant_to_DC", index=False)
    df_dc_cust_cost.to_excel(xw, sheet_name="Cost_DC_to_Customer", index=False)
    df_params.to_excel(xw, sheet_name="Parameters", index=False)

print("Data generated:")
print(f"  Plants:            {len(df_plants)}")
print(f"  Candidate DCs:     {len(df_dcs)}")
print(f"  Customer zones:    {len(df_customers)}")
print(f"  Total base demand: {df_customers.annual_demand_units.sum():,} units/yr")
