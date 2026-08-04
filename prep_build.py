#!/usr/bin/env python3
"""
Convert WRI GCSC CSVs into browser-loadable JSON bundles for the EF extractor webapp.
Bundles: sLUC (adm0+adm1 CO2e + gas breakdown), jdLUC, co_products, GADM keys, yield factors.
Output -> ./webapp/data/
"""
import csv, json, os, collections

SRC = "/tmp/GCSC/data"
OUT = "/tmp/GCSC/webapp/data"
os.makedirs(f"{OUT}/sLUC", exist_ok=True)
os.makedirs(f"{OUT}/jdLUC", exist_ok=True)
os.makedirs(f"{OUT}/co", exist_ok=True)
os.makedirs(f"{OUT}/gadm", exist_ok=True)
os.makedirs(f"{OUT}/yield", exist_ok=True)

YEARS = ["2020","2021","2022","2023","2024"]
GASES = ["CO2e","CO2","CH4","N2O"]

def w(path, obj):
    with open(path,"w") as f:
        json.dump(obj,f,separators=(",",":"))
    return os.path.getsize(path)

# ---------------- COMMODITY MASTER ----------------
# map SPAM code -> human name + has_co_products
commodities = {
 "BANA":"Banana","BARL":"Barley","BEAN":"Bean","CASS":"Cassava","CHIC":"Chickpea",
 "CNUT":"Coconut","COCO":"Cocoa","ACOF":"Arabica Coffee","RCOF":"Robusta Coffee",
 "COTT":"Cotton","COWP":"Cowpea","GROU":"Groundnut","LENT":"Lentil","MAIZ":"Maize",
 "PMIL":"Pearl Millet","SMIL":"Small Millet","OILP":"Oil Palm","PIGE":"Pigeon Pea",
 "PLNT":"Plantain","POTA":"Potato","RAPE":"Rapeseed","RICE":"Rice","SESA":"Sesame Seed",
 "SORG":"Sorghum","SOYB":"Soybean","SUGB":"Sugarbeet","SUGC":"Sugarcane","SUNF":"Sunflower",
 "SWPO":"Sweet Potato","TEAS":"Tea","TOBA":"Tobacco","WHEA":"Wheat","YAMS":"Yams",
 "OCER":"Other Cereals","OFIB":"Other Fibre Crops","OOIL":"Other Oil Crops","OPUL":"Other Pulses",
 "ORTS":"Other Roots","REST":"Rest of Crops","TEMF":"Temperate Fruit","TROF":"Tropical Fruit","VEGE":"Vegetables",
}
co_products_of = {"OILP":"oilp","SOYB":"soyb","COCO":"cocoa"}  # crop -> co-product filename stem
jdLUC_commodities = {"OILP":"Oil Palm","SOYB":"Soybean","COCO":"Cocoa"}

# ---------------- sLUC admin0 (CO2e + gas breakdown) ----------------
adm0_root = f"{SRC}/sLUC_emission_factors/deforestation_emission_factors_admin0/individual_commodities"
# combine all crops into one file per gas for adm0 (small)
for gas in GASES:
    rows = []
    for code in commodities:
        p = f"{adm0_root}_{gas}/EF_ADM0_{code}_{gas}.csv"
        if not os.path.exists(p):
            continue
        with open(p) as f:
            rd = csv.DictReader(f)
            for r in rd:
                rows.append({
                    "g": r["GID_0"], "c": code,
                    "EF": {y: float(r[f"EF_{y}"] or 0) for y in YEARS},
                })
    sz = w(f"{OUT}/sLUC/adm0_{gas}.json", rows)
    print(f"sLUC adm0_{gas}: {len(rows)} rows, {sz/1024:.0f} KB")

# ---------------- sLUC admin1 (CO2e + gas breakdown) ----------------
for gas in GASES:
    rows = []
    for code in commodities:
        p = f"{SRC}/sLUC_emission_factors/deforestation_emission_factors_adm1/individual_commodities_{gas}/EF_ADM1_{code}_{gas}.csv"
        if not os.path.exists(p):
            continue
        with open(p) as f:
            rd = csv.DictReader(f)
            for r in rd:
                rows.append({
                    "g0": r["GID_0"], "g1": r["GID_1"], "c": code,
                    "EF": {y: float(r[f"EF_{y}"] or 0) for y in YEARS},
                })
    sz = w(f"{OUT}/sLUC/adm1_{gas}.json", rows)
    print(f"sLUC adm1_{gas}: {len(rows)} rows, {sz/1024/1024:.2f} MB")

# ---------------- jdLUC ----------------
for fn in os.listdir(f"{SRC}/jdLUC_emission_factors"):
    if not fn.endswith(".csv"): continue
    rows = []
    with open(f"{SRC}/jdLUC_emission_factors/{fn}") as f:
        rd = csv.DictReader(f)
        cols = rd.fieldnames
        is_long = "gas_type" in cols and "year" in cols
        if not is_long:
            for r in rd:
                entry = {"g0": r.get("GID_0",""), "g1": r.get("GID_1",""), "g2": r.get("GID_2",""),
                         "commodity": r["commodity"], "area_ha": float(r["area__ha"] or 0),
                         "yield_mt_ha": float(r["yield_mt_ha"] or 0), "production_mt": float(r["production_mt"] or 0)}
                ef = {}
                for gas in GASES:
                    ef[gas] = {y: float(r.get(f"EF_{y}_{gas}") or 0) for y in YEARS}
                entry["EF"] = ef
                rows.append(entry)
        else:
            # long format: one row per (gid, commodity, gas_type, year)
            acc = {}
            for r in rd:
                key = (r.get("GID_0",""), r.get("GID_1",""), r.get("GID_2",""), r["commodity"])
                if key not in acc:
                    acc[key] = {"g0": key[0], "g1": key[1], "g2": key[2], "commodity": r["commodity"],
                                "area_ha": float(r["area__ha"] or 0),
                                "yield_mt_ha": float(r.get("yield_mt_ha") or 0),
                                "production_mt": float(r["production_mt"] or 0), "EF": {}}
                acc[key]["EF"].setdefault(r["gas_type"], {})[r["year"]] = float(r["EF"] or 0)
            rows = list(acc.values())
    name = fn.replace(".csv",".json")
    sz = w(f"{OUT}/jdLUC/{name}", rows)
    print(f"jdLUC {name}: {len(rows)} rows, {sz/1024:.0f} KB")

# ---------------- co_products ----------------
for fn in os.listdir(f"{SRC}/co_products_sLUC"):
    if not fn.endswith(".csv"): continue
    rows = []
    with open(f"{SRC}/co_products_sLUC/{fn}") as f:
        rd = csv.DictReader(f)
        for r in rd:
            rows.append({
                "g0": r.get("GID_0",""), "g1": r.get("GID_1",""), "g2": r.get("GID_2",""),
                "crop": r["crop_type"], "co_product": r["co_product"],
                "functional_unit": r["functional_unit"], "allocation_ratio": float(r["allocation_ratio"] or 0),
                "EF": {y: float(r.get(f"co_product_EF_{y}") or 0) for y in YEARS},
            })
    name = fn.replace(".csv",".json")
    sz = w(f"{OUT}/co/{name}", rows)
    print(f"co {name}: {len(rows)} rows, {sz/1024:.0f} KB")

# ---------------- GADM keys ----------------
for lvl,fname in [("adm0","key_gadm_adm0.csv"),("adm1","key_gadm_adm1.csv"),("adm2","key_gadm_adm2.csv")]:
    rows = []
    with open(f"{SRC}/gadm_admin_keys/{fname}") as f:
        rd = csv.DictReader(f)
        for r in rd:
            rows.append([r["GID_0"], r.get("GID_1",""), r.get("GID_2",""),
                         r["NAME_0"], r.get("NAME_1",""), r.get("NAME_2","")])
    sz = w(f"{OUT}/gadm/{lvl}.json", rows)
    print(f"gadm {lvl}: {len(rows)} rows, {sz/1024:.0f} KB")

# ---------------- yield factors ----------------
for lvl in ["gadm0","gadm1"]:
    rows = []
    with open(f"{SRC}/yield_factors/yield_factor_{lvl}.csv") as f:
        rd = csv.DictReader(f)
        for r in rd:
            rows.append({"g0": r.get("GID_0",""), "g1": r.get("GID_1",""), "g2": r.get("GID_2",""),
                         "crop": r["crop"], "yield_mt": float(r["yield_mt"] or 0),
                         "yield_kg": float(r["yield_kg"] or 0),
                         "yield_factor_kg": float(r["yield_factor_kg"] or 0)})
    sz = w(f"{OUT}/yield/{lvl}.json", rows)
    print(f"yield {lvl}: {len(rows)} rows, {sz/1024:.0f} KB")

# ---------------- index ----------------
index = {
    "commodities": [{"code":k,"name":v,"co_products":(k in co_products_of)} for k,v in commodities.items()],
    "jdLUC_commodities": [{"code":k,"name":v} for k,v in jdLUC_commodities.items()],
    "co_product_sources": {k: {"admin0":f"co/{v}_co_products_adm0.json","admin1":f"co/{v}_co_products_adm1.json","admin2":f"co/{v}_co_products_adm2.json"} for k,v in co_products_of.items()},
    "sLUC": {g: {"admin0":f"sLUC/adm0_{g}.json","admin1":f"sLUC/adm1_{g}.json"} for g in GASES},
    "jdLUC_files": {"OILP":["jdLUC/jdLUC_OILP_admin0.json","jdLUC/jdLUC_OILP_admin1.json","jdLUC/jdLUC_OILP_admin2.json"],
                    "SOYB":["jdLUC/jdLUC_SOYB_SA_admin0.json","jdLUC/jdLUC_SOYB_SA_admin1.json","jdLUC/jdLUC_SOYB_SA_admin2.json"],
                    "COCO":["jdLUC/jdLUC_COCO_GHA_CIV_admin0.json","jdLUC/jdLUC_COCO_GHA_CIV_admin1.json","jdLUC/jdLUC_COCO_GHA_CIV_admin2.json"]},
    "gadm":{"admin0":"gadm/adm0.json","admin1":"gadm/adm1.json","admin2":"gadm/adm2.json"},
    "yield":{"admin0":"yield/gadm0.json","admin1":"yield/gadm1.json"},
    "years": YEARS, "gases": GASES,
}
w(f"{OUT}/index.json", index)
print("index written.")

print("\nDONE. Total bundle sizes:")
for root,_,files in os.walk(OUT):
    total = sum(os.path.getsize(os.path.join(root,f)) for f in files)
    if files:
        print(f"  {root.replace(OUT,'') or '/'}: {total/1024/1024:.2f} MB")
