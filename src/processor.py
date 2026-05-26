"""
processor.py — Aggregate data and compute DoD / WoW / MoM growth metrics.
"""
import pandas as pd


def aggregate_daily(df, date_col, metric_col, group_col="operator"):
    """
    Aggregate metric by [date, operator].
    Returns sorted DataFrame with one row per (date, operator).
    """
    daily = (
        df.groupby([date_col, group_col])[metric_col]
        .sum()
        .reset_index()
        .sort_values([group_col, date_col])
        .reset_index(drop=True)
    )
    return daily


def calculate_dod(daily, date_col, metric_col, group_col="operator"):
    """
    Day-over-Day: compare today vs yesterday within each operator group.
    Adds columns: prev_day, dod_abs, dod_pct
    """
    daily = daily.copy()
    daily["prev_day"] = daily.groupby(group_col)[metric_col].shift(1)
    daily["dod_abs"]  = daily[metric_col] - daily["prev_day"]
    daily["dod_pct"]  = (daily["dod_abs"] / daily["prev_day"] * 100).round(2)
    return daily


def calculate_wow(daily, date_col, metric_col, group_col="operator"):
    """
    Week-over-Week: compare today vs 7 days ago within each operator group.
    Adds columns: prev_week, wow_abs, wow_pct
    """
    daily = daily.copy()
    daily["prev_week"] = daily.groupby(group_col)[metric_col].shift(7)
    daily["wow_abs"]   = daily[metric_col] - daily["prev_week"]
    daily["wow_pct"]   = (daily["wow_abs"] / daily["prev_week"] * 100).round(2)
    return daily


def calculate_mom(daily, date_col, metric_col, group_col="operator"):
    """
    Month-over-Month: compare today vs 30 days ago within each operator group.
    Adds columns: prev_month, mom_abs, mom_pct
    """
    daily = daily.copy()
    daily["prev_month"] = daily.groupby(group_col)[metric_col].shift(30)
    daily["mom_abs"]    = daily[metric_col] - daily["prev_month"]
    daily["mom_pct"]    = (daily["mom_abs"] / daily["prev_month"] * 100).round(2)
    return daily


def get_latest_summary(daily, date_col, metric_col):
    """Return rows for the latest available date."""
    latest_date = daily[date_col].max()
    return daily[daily[date_col] == latest_date].copy()


def detect_anomalies(daily, metric_col, group_col="operator", threshold_pct=20.0):
    """
    Flag rows where DoD absolute change exceeds threshold_pct.
    Returns filtered DataFrame of anomalous rows.
    """
    if "dod_pct" not in daily.columns:
        raise ValueError("Run calculate_dod() before detect_anomalies()")
    anomalies = daily[daily["dod_pct"].abs() >= threshold_pct].copy()
    return anomalies
