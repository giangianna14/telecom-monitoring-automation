"""
data_loader.py — Load CSV files into pandas DataFrames.
"""
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def load_voice_sli() -> pd.DataFrame:
    """Load Voice SLI data. Returns DataFrame with parsed call_date."""
    path = DATA_DIR / "sample_voice_sli.csv"
    df = pd.read_csv(path, parse_dates=["call_date"])
    df["operator"] = df["operator"].str.upper().str.strip()
    return df


def load_sms_a2p() -> pd.DataFrame:
    """Load SMS A2P data. Returns DataFrame with parsed calldate."""
    path = DATA_DIR / "sample_sms_a2p.csv"
    df = pd.read_csv(path, parse_dates=["calldate"])
    df["opr"] = df["opr"].str.upper().str.strip()
    return df


def load_ref_operator() -> pd.DataFrame:
    """Load operator reference table."""
    path = DATA_DIR / "ref_operator.csv"
    return pd.read_csv(path)
