"""
Generate dummy CSV data for portfolio demo.
Simulates 90 days of telecom operator data — no real/confidential data.
Run: python scripts/generate_dummy_data.py
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import date, timedelta
import random

random.seed(42)
np.random.seed(42)

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

OPERATORS = ["GAH", "INS", "MVN", "TLG", "TLI", "TSV"]
LOKAB     = ["JAKARTA", "SURABAYA", "BANDUNG", "MEDAN", "SEMARANG", "MAKASSAR"]

end_date   = date.today()
start_date = end_date - timedelta(days=89)
dates      = [start_date + timedelta(days=i) for i in range(90)]

# Base daily duration per operator (in minutes — realistic telecom scale)
BASE_DURATION = {
    "GAH": 850_000,
    "INS": 620_000,
    "MVN": 1_100_000,
    "TLG": 940_000,
    "TLI": 380_000,
    "TSV": 510_000,
}

# ── 1. sample_voice_sli.csv ──────────────────────────────────────────────────
print("Generating sample_voice_sli.csv ...")
rows = []
for d in dates:
    for op in OPERATORS:
        for lokab in random.sample(LOKAB, k=random.randint(3, 6)):
            base          = BASE_DURATION[op] / len(LOKAB)
            weekday_factor = 1.0 if d.weekday() < 5 else 0.72
            trend          = 1 + (dates.index(d) / 90) * 0.05
            noise          = np.random.normal(1.0, 0.08)
            duration       = max(100.0, base * weekday_factor * trend * noise)
            charge         = duration * random.uniform(85.0, 115.0)
            rows.append({
                "call_date":    d.strftime("%Y-%m-%d"),
                "operator":     op,
                "lokab":        lokab,
                "duration_min": round(duration, 2),
                "charge":       round(charge, 0),
            })

voice_df = pd.DataFrame(rows)
voice_df.to_csv(DATA_DIR / "sample_voice_sli.csv", index=False)
print(f"  -> {len(voice_df):,} rows written")

# ── 2. sample_sms_a2p.csv ───────────────────────────────────────────────────
print("Generating sample_sms_a2p.csv ...")
OA_SAMPLES = [
    "BANK_BCA", "TOKOPEDIA", "GOJEK", "SHOPEE",
    "MYXL", "INDOSAT_MKT", "DANA", "OVO", "GRAB", "LAZADA",
]
sms_rows = []
for d in dates:
    for op in OPERATORS:
        for oa in random.sample(OA_SAMPLES, k=random.randint(3, 7)):
            for momt in ["MO", "MT"]:
                base_sms       = random.randint(5_000, 80_000)
                weekday_factor = 1.0 if d.weekday() < 5 else 0.5
                sms_count      = int(base_sms * weekday_factor * np.random.normal(1.0, 0.1))
                idr            = sms_count * random.uniform(150.0, 250.0)
                sms_rows.append({
                    "calldate":  d.strftime("%Y-%m-%d"),
                    "oa_p2a":   oa,
                    "momt":     momt,
                    "opr":      op,
                    "sms_count": max(0, sms_count),
                    "idr":      round(idr, 0),
                })

sms_df = pd.DataFrame(sms_rows)
sms_df.to_csv(DATA_DIR / "sample_sms_a2p.csv", index=False)
print(f"  -> {len(sms_df):,} rows written")

# ── 3. ref_operator.csv ─────────────────────────────────────────────────────
print("Generating ref_operator.csv ...")
ref_df = pd.DataFrame([
    {"operator_code": "GAH", "operator_name": "Hutchison 3 Indonesia",      "color_hex": "#E63946"},
    {"operator_code": "INS", "operator_name": "Indosat Ooredoo Hutchison",   "color_hex": "#2196F3"},
    {"operator_code": "MVN", "operator_name": "MVNO Aggregator",             "color_hex": "#4CAF50"},
    {"operator_code": "TLG", "operator_name": "Telkomsel Group",             "color_hex": "#FF9800"},
    {"operator_code": "TLI", "operator_name": "Telkom Indonesia",            "color_hex": "#9C27B0"},
    {"operator_code": "TSV", "operator_name": "Smartfren",                   "color_hex": "#00BCD4"},
])
ref_df.to_csv(DATA_DIR / "ref_operator.csv", index=False)
print(f"  -> {len(ref_df)} operators written")

print("\nAll dummy data generated successfully.")
print(f"  data/sample_voice_sli.csv  : {len(voice_df):,} rows")
print(f"  data/sample_sms_a2p.csv    : {len(sms_df):,} rows")
print(f"  data/ref_operator.csv      : {len(ref_df)} rows")
