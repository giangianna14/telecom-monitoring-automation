"""
app.py — Streamlit interactive dashboard for Telecom Monitoring.

Run:
    streamlit run app.py

Deploy (free):
    https://streamlit.io/cloud  →  connect GitHub repo → deploy
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import streamlit as st
from datetime import datetime

from src.data_loader import load_voice_sli, load_sms_a2p, load_ref_operator
from src.processor   import aggregate_daily, calculate_dod, calculate_wow, detect_anomalies
from src.chart_generator import OPERATOR_COLORS

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Telecom Monitoring Dashboard",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Inter:wght@300;400;500;600;700&display=swap');

  html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
  }

  /* ── Base ── */
  .stApp {
    background: #060c16 !important;
    color: #cdd9e5;
  }
  .block-container {
    padding: 1.2rem 2rem 2rem !important;
    max-width: 1400px;
  }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
    background: #0a1220 !important;
    border-right: 1px solid #1a2d45;
  }
  [data-testid="stSidebar"] * { color: #8da4be !important; }
  [data-testid="stSidebar"] .stRadio label,
  [data-testid="stSidebar"] .stMultiSelect label { color: #8da4be !important; }

  /* ── Headings ── */
  h1 { font-size: 1.5rem !important; font-weight: 700 !important; color: #e8f4ff !important; letter-spacing: -0.3px; }
  h2, h3 { font-weight: 600 !important; color: #c9d8e8 !important; font-size: 0.95rem !important; letter-spacing: 0.5px; text-transform: uppercase; }

  /* ── KPI cards (custom HTML) ── */
  .kpi-card {
    background: #0d1e30;
    border: 1px solid #1a3050;
    border-radius: 10px;
    padding: 18px 20px;
    position: relative;
    overflow: hidden;
  }
  .kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #00c8ff, #0066ff);
  }
  .kpi-card.green::before { background: linear-gradient(90deg, #00e5a0, #00c8ff); }
  .kpi-card.red::before   { background: linear-gradient(90deg, #ff4560, #ff9020); }
  .kpi-card.warn::before  { background: linear-gradient(90deg, #ffb020, #ff6030); }
  .kpi-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    letter-spacing: 2px;
    color: #4a6a8a;
    text-transform: uppercase;
    margin-bottom: 8px;
  }
  .kpi-value {
    font-size: 28px;
    font-weight: 700;
    color: #e8f4ff;
    line-height: 1;
    margin-bottom: 6px;
  }
  .kpi-delta {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    color: #4a6a8a;
  }
  .kpi-delta.pos { color: #00e5a0; }
  .kpi-delta.neg { color: #ff4560; }

  /* ── Section header ── */
  .section-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    letter-spacing: 3px;
    color: #2a5a8a;
    text-transform: uppercase;
    margin: 0 0 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid #0f2035;
  }

  /* ── Status badge ── */
  .badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 10px;
    border-radius: 100px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    letter-spacing: 1px;
  }
  .badge-live { background: rgba(0,229,160,0.08); border: 1px solid rgba(0,229,160,0.2); color: #00e5a0; }
  .badge-dot  { width: 6px; height: 6px; border-radius: 50%; background: #00e5a0;
                box-shadow: 0 0 8px #00e5a0; animation: blink 1.8s ease-in-out infinite; }
  @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }

  /* ── Operator legend ── */
  .op-dot {
    display: inline-block;
    width: 8px; height: 8px;
    border-radius: 50%;
    margin-right: 7px;
    vertical-align: middle;
  }

  /* ── Anomaly row ── */
  .anom-row {
    background: rgba(255,69,96,0.05);
    border: 1px solid rgba(255,69,96,0.15);
    border-radius: 6px;
    padding: 8px 14px;
    margin-bottom: 6px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    color: #cdd9e5;
    display: flex;
    gap: 16px;
    align-items: center;
  }
  .anom-op   { color: #e8f4ff; font-weight: 600; min-width: 40px; }
  .anom-date { color: #4a6a8a; }
  .anom-pct  { color: #ff4560; }

  /* ── DataFrame ── */
  [data-testid="stDataFrame"] {
    border: 1px solid #1a2d45 !important;
    border-radius: 8px !important;
    overflow: hidden;
  }
  /* Force dark on dataframe canvas/table */
  [data-testid="stDataFrame"] iframe,
  [data-testid="stDataFrame"] > div,
  .stDataFrame { background: #0a1525 !important; }
  /* Arrow table (newer Streamlit) */
  [data-testid="stDataFrameResizable"] { background: #0a1525 !important; }

  /* ── Tabs ── */
  [data-testid="stTabs"] [role="tablist"] {
    background: transparent !important;
    border-bottom: 1px solid #0f2035 !important;
    gap: 4px;
  }
  [data-testid="stTabs"] button[role="tab"] {
    background: transparent !important;
    color: #4a6a8a !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 1px !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    padding: 8px 16px !important;
    border-radius: 0 !important;
    transition: color 0.2s, border-color 0.2s !important;
  }
  [data-testid="stTabs"] button[role="tab"]:hover {
    color: #8da4be !important;
    background: rgba(0,200,255,0.04) !important;
  }
  [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: #00c8ff !important;
    border-bottom: 2px solid #00c8ff !important;
    background: transparent !important;
  }
  [data-testid="stTabs"] [data-testid="stTabsContent"] {
    background: transparent !important;
    padding-top: 20px;
  }

  /* ── Date input ── */
  [data-testid="stDateInput"] input,
  [data-testid="stDateInput"] > div {
    background: #0d1e30 !important;
    color: #8da4be !important;
    border-color: #1a3050 !important;
  }

  /* ── Multiselect ── */
  [data-testid="stMultiSelect"] > div > div {
    background: #0d1e30 !important;
    border-color: #1a3050 !important;
  }
  [data-testid="stMultiSelect"] [data-baseweb="tag"] {
    background: #1a3050 !important;
  }
  /* Dropdown popup */
  [data-baseweb="popover"] [data-baseweb="menu"],
  [data-baseweb="popover"] ul {
    background: #0d1e30 !important;
    border: 1px solid #1a3050 !important;
  }
  [data-baseweb="popover"] li:hover {
    background: #1a3050 !important;
  }

  /* ── Alert / info boxes ── */
  [data-testid="stAlert"] {
    background: #0d1e30 !important;
    border-color: #1a3050 !important;
    color: #8da4be !important;
  }

  /* ── Divider ── */
  hr { border-color: #0f2035 !important; }

  /* ── Scrollbar ── */
  ::-webkit-scrollbar { width: 4px; height: 4px; }
  ::-webkit-scrollbar-track { background: #060c16; }
  ::-webkit-scrollbar-thumb { background: #1a3050; border-radius: 2px; }
</style>
""", unsafe_allow_html=True)

# ── Load & cache data ─────────────────────────────────────────────────────────
@st.cache_data
def get_voice_data():
    df    = load_voice_sli()
    daily = aggregate_daily(df, "call_date", "duration_min")
    daily = calculate_dod(daily, "call_date", "duration_min")
    daily = calculate_wow(daily, "call_date", "duration_min")
    return df, daily

@st.cache_data
def get_sms_data():
    df    = load_sms_a2p()
    daily = aggregate_daily(df, "calldate", "sms_count", group_col="opr")
    daily = daily.rename(columns={"opr": "operator", "calldate": "call_date"})
    daily = calculate_dod(daily, "call_date", "sms_count")
    daily = calculate_wow(daily, "call_date", "sms_count")
    return df, daily

try:
    df_voice, daily_voice = get_voice_data()
    df_sms,   daily_sms   = get_sms_data()
    ref_op  = load_ref_operator()
    DATA_OK = True
except FileNotFoundError:
    DATA_OK = False

if not DATA_OK:
    st.error("⚠️ Data files not found. Run: `python scripts/generate_dummy_data.py` first.")
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown("""
<div style='padding:6px 0 18px'>
  <div style='font-family:IBM Plex Mono,monospace;font-size:11px;letter-spacing:2px;color:#2a5a8a;margin-bottom:4px'>PORTFOLIO DEMO</div>
  <div style='font-size:15px;font-weight:700;color:#c9d8e8'>Telecom Monitor</div>
  <div style='font-size:11px;color:#2a5a8a;margin-top:2px'>by @giangianna14</div>
</div>
""", unsafe_allow_html=True)

min_date = daily_voice["call_date"].min().date()
max_date = daily_voice["call_date"].max().date()

st.sidebar.markdown('<div class="section-label">Date Range</div>', unsafe_allow_html=True)
date_range = st.sidebar.date_input("", value=[min_date, max_date],
                                    min_value=min_date, max_value=max_date,
                                    label_visibility="collapsed")

all_operators = sorted(daily_voice["operator"].unique().tolist())
st.sidebar.markdown('<div class="section-label" style="margin-top:16px">Operators</div>', unsafe_allow_html=True)
selected_ops = st.sidebar.multiselect("", options=all_operators, default=all_operators,
                                       label_visibility="collapsed")

# Operator legend
legend_html = ""
for op in all_operators:
    color = OPERATOR_COLORS.get(op, "#ffffff")
    opacity = "1" if op in selected_ops else "0.25"
    legend_html += f'<div style="opacity:{opacity};margin-bottom:6px"><span class="op-dot" style="background:{color}"></span><span style="font-family:IBM Plex Mono,monospace;font-size:11px;color:#8da4be">{op}</span></div>'
st.sidebar.markdown(f'<div style="margin-top:8px">{legend_html}</div>', unsafe_allow_html=True)

st.sidebar.markdown("""
<div style='margin-top:28px;padding-top:16px;border-top:1px solid #0f2035'>
  <div style='font-family:IBM Plex Mono,monospace;font-size:9px;color:#1e3a5a;letter-spacing:1px'>TECH STACK</div>
  <div style='font-size:10px;color:#2a5a8a;margin-top:6px;line-height:1.8'>
    Python · Pandas · Matplotlib<br>smtplib · APScheduler · Selenium
  </div>
</div>
""", unsafe_allow_html=True)

# ── Apply filters ─────────────────────────────────────────────────────────────
ops_filter = selected_ops if selected_ops else all_operators

if len(date_range) == 2:
    d0, d1 = date_range
    mask_v = ((daily_voice["call_date"].dt.date >= d0) &
              (daily_voice["call_date"].dt.date <= d1) &
              (daily_voice["operator"].isin(ops_filter)))
    mask_s = ((daily_sms["call_date"].dt.date >= d0) &
              (daily_sms["call_date"].dt.date <= d1) &
              (daily_sms["operator"].isin(ops_filter)))
    fv = daily_voice[mask_v].copy()
    fs = daily_sms[mask_s].copy()
else:
    fv = daily_voice[daily_voice["operator"].isin(ops_filter)].copy()
    fs = daily_sms[daily_sms["operator"].isin(ops_filter)].copy()

# ── Chart constants ───────────────────────────────────────────────────────────
BG      = "#060c16"
PANEL   = "#0a1525"
GRIDCOL = "#0f2035"
TXTDIM  = "#2a4a6a"

# ── Header ────────────────────────────────────────────────────────────────────
ref_date     = daily_voice["call_date"].max()
ref_date_str = ref_date.strftime("%Y-%m-%d") if pd.notna(ref_date) else "N/A"

h_col, badge_col = st.columns([6, 1])
with h_col:
    st.markdown(
        "<h1>📡 Telecom Monitoring & Automated Reporting</h1>"
        "<p style='color:#2a5a8a;font-size:12px;margin:-4px 0 0;font-family:IBM Plex Mono,monospace;letter-spacing:1px'>"
        f"PORTFOLIO DEMO · DUMMY DATA · LATEST DATE: {ref_date_str}</p>",
        unsafe_allow_html=True,
    )
with badge_col:
    st.markdown(
        '<div style="text-align:right;padding-top:8px">'
        '<div class="badge badge-live"><div class="badge-dot"></div>LIVE PIPELINE</div>'
        '</div>',
        unsafe_allow_html=True,
    )

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ── Empty operator guard ──────────────────────────────────────────────────────
if not selected_ops:
    st.markdown("""
    <div style='background:#0d1e30;border:1px solid #1a3050;border-radius:10px;
                padding:48px;text-align:center;margin-top:12px'>
      <div style='font-size:36px;margin-bottom:14px'>📭</div>
      <div style='font-family:IBM Plex Mono,monospace;font-size:13px;color:#4a6a8a;
                  letter-spacing:2px;text-transform:uppercase'>No Operators Selected</div>
      <div style='font-size:13px;color:#2a5a8a;margin-top:10px'>
        Pilih minimal 1 operator dari sidebar untuk menampilkan data.
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Helper functions ──────────────────────────────────────────────────────────
def _delta_html(val, suffix=""):
    if val is None or not pd.notna(val):
        return '<span class="kpi-delta">— N/A</span>'
    cls   = "pos" if val >= 0 else "neg"
    arrow = "▲" if val >= 0 else "▼"
    return f'<span class="kpi-delta {cls}">{arrow} {abs(val):.1f}{suffix} vs prev day</span>'

def _delta_wow_html(val, suffix=""):
    if val is None or not pd.notna(val):
        return '<span class="kpi-delta">— N/A</span>'
    cls   = "pos" if val >= 0 else "neg"
    arrow = "▲" if val >= 0 else "▼"
    return f'<span class="kpi-delta {cls}">{arrow} {abs(val):.1f}{suffix} vs last week</span>'

def _render_trend(active_daily, active_metric, metric_label, ops_list):
    """Render line trend chart into current st context."""
    if active_daily.empty:
        st.info("Tidak ada data untuk filter yang dipilih.")
        return
    fig, ax = plt.subplots(figsize=(14, 5))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(PANEL)
    for op in ops_list:
        subset = active_daily[active_daily["operator"] == op].sort_values("call_date")
        if subset.empty:
            continue
        color  = OPERATOR_COLORS.get(op, "#ffffff")
        x_vals = subset["call_date"].values
        y_vals = subset[active_metric].values
        ax.plot(x_vals, y_vals, label=op, color=color, linewidth=1.8, zorder=3)
        ax.fill_between(x_vals, y_vals, alpha=0.06, color=color, zorder=2)
        if len(x_vals) > 0:
            ax.scatter(x_vals[-1], y_vals[-1], color=color, s=30, zorder=5, linewidths=0)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=0, interval=2))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"{x/1_000_000:.1f}M" if x >= 1_000_000 else f"{x/1_000:.0f}K"
    ))
    plt.xticks(rotation=0, color=TXTDIM, fontsize=8)
    plt.yticks(color=TXTDIM, fontsize=8)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0)
    ax.grid(axis="y", color=GRIDCOL, linewidth=0.8, zorder=0)
    ax.grid(axis="x", color=GRIDCOL, linewidth=0.5, linestyle=":", zorder=0)
    ax.legend(facecolor="#0a1525", labelcolor="#8da4be", framealpha=1,
              edgecolor="#0f2035", fontsize=9, ncol=len(ops_list), loc="upper left", handlelength=1.2)
    x_min = active_daily["call_date"].min()
    x_max = active_daily["call_date"].max()
    if pd.notna(x_min) and pd.notna(x_max):
        ax.set_xlim(x_min, x_max)
    plt.tight_layout(pad=0.5)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

def _render_dod_bar(latest_rows, ops_list):
    """Render horizontal DoD bar chart."""
    if "dod_pct" not in latest_rows.columns or not latest_rows["dod_pct"].notna().any():
        st.info("DoD data tidak tersedia.")
        return
    ops_sorted = latest_rows.sort_values("dod_pct")
    ol  = ops_sorted["operator"].tolist()
    dv  = ops_sorted["dod_pct"].tolist()
    bc  = [OPERATOR_COLORS.get(op, "#fff") for op in ol]
    fig2, ax2 = plt.subplots(figsize=(7, max(2.5, len(ol) * 0.55)))
    fig2.patch.set_facecolor(BG)
    ax2.set_facecolor(PANEL)
    bars = ax2.barh(ol, dv, color=bc, height=0.5, zorder=3)
    for bar, val in zip(bars, dv):
        x_pos = val + (0.4 if val >= 0 else -0.4)
        ax2.text(x_pos, bar.get_y() + bar.get_height() / 2,
                 f"{val:+.1f}%", va="center",
                 ha="left" if val >= 0 else "right",
                 color="#cdd9e5", fontsize=8)
    ax2.axvline(0, color="#1a3050", linewidth=1)
    ax2.tick_params(colors=TXTDIM, labelsize=8, length=0)
    ax2.set_yticks(range(len(ol)))
    ax2.set_yticklabels(ol, color="#8da4be", fontsize=9)
    for sp in ax2.spines.values():
        sp.set_visible(False)
    ax2.grid(axis="x", color=GRIDCOL, linewidth=0.7, zorder=0)
    plt.tight_layout(pad=0.5)
    st.pyplot(fig2, use_container_width=True)
    plt.close(fig2)

def _render_anomaly_log(anomalies, active_metric, metric_unit):
    """Render styled anomaly log rows."""
    if anomalies.empty:
        return
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">⚠ Anomaly Log — DoD Change > 20%</div>', unsafe_allow_html=True)
    recent = anomalies.sort_values("call_date", ascending=False).head(20)
    html   = ""
    for _, row in recent.iterrows():
        color = OPERATOR_COLORS.get(row["operator"], "#fff")
        arrow = "▲" if row["dod_pct"] >= 0 else "▼"
        html += (
            f'<div class="anom-row">'
            f'<span class="op-dot" style="background:{color}"></span>'
            f'<span class="anom-op">{row["operator"]}</span>'
            f'<span class="anom-date">{pd.Timestamp(row["call_date"]).strftime("%Y-%m-%d")}</span>'
            f'<span style="color:#8da4be;font-family:IBM Plex Mono,monospace;font-size:11px">'
            f'{row[active_metric]:,.0f} {metric_unit}</span>'
            f'<span class="anom-pct">{arrow} {abs(row["dod_pct"]):.1f}% DoD</span>'
            f'</div>'
        )
    st.markdown(html, unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_voice, tab_sms = st.tabs(["  📞  Voice SLI — Duration  ", "  💬  SMS A2P — Count  "])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — Voice SLI
# ════════════════════════════════════════════════════════════════════════════
with tab_voice:
    latest_v      = fv["call_date"].max() if not fv.empty else None
    latest_v_str  = latest_v.strftime("%Y-%m-%d") if (latest_v is not None and pd.notna(latest_v)) else "N/A"
    latest_rows_v = fv[fv["call_date"] == latest_v] if latest_v is not None else fv.iloc[0:0]
    anomalies_v   = detect_anomalies(fv, "duration_min")
    a_count_v     = len(anomalies_v[anomalies_v["call_date"] == latest_v]) if latest_v is not None else 0

    total_dur  = fv["duration_min"].sum()
    avg_dod_v  = latest_rows_v["dod_pct"].mean()  if "dod_pct" in latest_rows_v.columns else None
    avg_wow_v  = latest_rows_v["wow_pct"].mean()  if "wow_pct" in latest_rows_v.columns else None

    dod_cls_v  = "green" if (avg_dod_v is not None and pd.notna(avg_dod_v) and avg_dod_v >= 0) else "red"
    wow_cls_v  = "green" if (avg_wow_v is not None and pd.notna(avg_wow_v) and avg_wow_v >= 0) else "red"
    anom_cls_v = "warn" if a_count_v > 0 else "green"

    # KPI row
    vc1, vc2, vc3, vc4 = st.columns(4)
    with vc1:
        st.markdown(f"""
        <div class="kpi-card">
          <div class="kpi-label">Total Voice Duration</div>
          <div class="kpi-value">{total_dur/1_000_000:.2f}M</div>
          <div class="kpi-delta">minutes · {len(ops_filter)} operators</div>
        </div>""", unsafe_allow_html=True)
    with vc2:
        dod_str = f"{avg_dod_v:+.1f}%" if (avg_dod_v is not None and pd.notna(avg_dod_v)) else "N/A"
        st.markdown(f"""
        <div class="kpi-card {dod_cls_v}">
          <div class="kpi-label">Avg DoD Change</div>
          <div class="kpi-value">{dod_str}</div>
          {_delta_html(avg_dod_v, "%")}
        </div>""", unsafe_allow_html=True)
    with vc3:
        wow_str = f"{avg_wow_v:+.1f}%" if (avg_wow_v is not None and pd.notna(avg_wow_v)) else "N/A"
        st.markdown(f"""
        <div class="kpi-card {wow_cls_v}">
          <div class="kpi-label">Avg WoW Change</div>
          <div class="kpi-value">{wow_str}</div>
          {_delta_wow_html(avg_wow_v, "%")}
        </div>""", unsafe_allow_html=True)
    with vc4:
        icon_v = "⚠" if a_count_v > 0 else "✓"
        sub_v  = "anomalies detected" if a_count_v > 0 else "all operators normal"
        st.markdown(f"""
        <div class="kpi-card {anom_cls_v}">
          <div class="kpi-label">Anomalies Today</div>
          <div class="kpi-value">{icon_v} {a_count_v}</div>
          <div class="kpi-delta">{sub_v}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # Trend chart
    st.markdown('<div class="section-label">Daily Trend — Duration (min) per Operator · 90 Days</div>', unsafe_allow_html=True)
    _render_trend(fv, "duration_min", "Duration (min)", ops_filter)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # Bottom row
    vcl, vcr = st.columns([3, 2], gap="large")
    with vcl:
        st.markdown(f'<div class="section-label">Latest Day Summary — {latest_v_str}</div>', unsafe_allow_html=True)
        if not latest_rows_v.empty:
            cols_v = [c for c in ["operator", "duration_min", "dod_pct", "wow_pct"] if c in latest_rows_v.columns]
            disp_v = latest_rows_v[cols_v].copy()
            disp_v.columns = ["Operator", "Duration (min)", "DoD %", "WoW %"][:len(cols_v)]
            st.dataframe(disp_v.sort_values("Operator").reset_index(drop=True),
                         use_container_width=True, hide_index=True)
        else:
            st.info("Tidak ada data untuk tanggal ini.")
    with vcr:
        st.markdown('<div class="section-label">DoD % — Latest Day by Operator</div>', unsafe_allow_html=True)
        _render_dod_bar(latest_rows_v, ops_filter)

    # Anomaly log
    _render_anomaly_log(anomalies_v, "duration_min", "min")

# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — SMS A2P
# ════════════════════════════════════════════════════════════════════════════
with tab_sms:
    latest_s      = fs["call_date"].max() if not fs.empty else None
    latest_s_str  = latest_s.strftime("%Y-%m-%d") if (latest_s is not None and pd.notna(latest_s)) else "N/A"
    latest_rows_s = fs[fs["call_date"] == latest_s] if latest_s is not None else fs.iloc[0:0]
    anomalies_s   = detect_anomalies(fs, "sms_count")
    a_count_s     = len(anomalies_s[anomalies_s["call_date"] == latest_s]) if latest_s is not None else 0

    total_sms  = fs["sms_count"].sum()
    avg_dod_s  = latest_rows_s["dod_pct"].mean() if "dod_pct" in latest_rows_s.columns else None
    avg_wow_s  = latest_rows_s["wow_pct"].mean() if "wow_pct" in latest_rows_s.columns else None

    # Revenue from raw df_sms filtered same date range + operator
    if len(date_range) == 2:
        d0, d1 = date_range
        raw_sms_filt = df_sms[
            (pd.to_datetime(df_sms["calldate"]).dt.date >= d0) &
            (pd.to_datetime(df_sms["calldate"]).dt.date <= d1) &
            (df_sms["opr"].isin(ops_filter))
        ]
    else:
        raw_sms_filt = df_sms[df_sms["opr"].isin(ops_filter)]
    total_idr = raw_sms_filt["idr"].sum() if "idr" in raw_sms_filt.columns else 0

    dod_cls_s  = "green" if (avg_dod_s is not None and pd.notna(avg_dod_s) and avg_dod_s >= 0) else "red"
    wow_cls_s  = "green" if (avg_wow_s is not None and pd.notna(avg_wow_s) and avg_wow_s >= 0) else "red"
    anom_cls_s = "warn"  if a_count_s > 0 else "green"

    # KPI row
    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        st.markdown(f"""
        <div class="kpi-card">
          <div class="kpi-label">Total SMS Count</div>
          <div class="kpi-value">{total_sms/1_000:.1f}K</div>
          <div class="kpi-delta">messages · {len(ops_filter)} operators</div>
        </div>""", unsafe_allow_html=True)
    with sc2:
        idr_str = f"Rp {total_idr/1_000_000:.1f}M" if total_idr >= 1_000_000 else f"Rp {total_idr:,.0f}"
        st.markdown(f"""
        <div class="kpi-card green">
          <div class="kpi-label">Total Revenue (IDR)</div>
          <div class="kpi-value">{idr_str}</div>
          <div class="kpi-delta">periode yang dipilih</div>
        </div>""", unsafe_allow_html=True)
    with sc3:
        dod_str_s = f"{avg_dod_s:+.1f}%" if (avg_dod_s is not None and pd.notna(avg_dod_s)) else "N/A"
        st.markdown(f"""
        <div class="kpi-card {dod_cls_s}">
          <div class="kpi-label">Avg DoD Change</div>
          <div class="kpi-value">{dod_str_s}</div>
          {_delta_html(avg_dod_s, "%")}
        </div>""", unsafe_allow_html=True)
    with sc4:
        icon_s = "⚠" if a_count_s > 0 else "✓"
        sub_s  = "anomalies detected" if a_count_s > 0 else "all operators normal"
        st.markdown(f"""
        <div class="kpi-card {anom_cls_s}">
          <div class="kpi-label">Anomalies Today</div>
          <div class="kpi-value">{icon_s} {a_count_s}</div>
          <div class="kpi-delta">{sub_s}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # Trend chart
    st.markdown('<div class="section-label">Daily Trend — SMS Count per Operator · 90 Days</div>', unsafe_allow_html=True)
    _render_trend(fs, "sms_count", "SMS Count", ops_filter)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # Bottom row
    scl, scr = st.columns([3, 2], gap="large")
    with scl:
        st.markdown(f'<div class="section-label">Latest Day Summary — {latest_s_str}</div>', unsafe_allow_html=True)
        if not latest_rows_s.empty:
            cols_s = [c for c in ["operator", "sms_count", "dod_pct", "wow_pct"] if c in latest_rows_s.columns]
            disp_s = latest_rows_s[cols_s].copy()
            disp_s.columns = ["Operator", "SMS Count", "DoD %", "WoW %"][:len(cols_s)]
            st.dataframe(disp_s.sort_values("Operator").reset_index(drop=True),
                         use_container_width=True, hide_index=True)
        else:
            st.info("Tidak ada data untuk tanggal ini.")
    with scr:
        st.markdown('<div class="section-label">DoD % — Latest Day by Operator</div>', unsafe_allow_html=True)
        _render_dod_bar(latest_rows_s, ops_filter)

    # Top OA section
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">Top 10 OA (Originating Address) — By SMS Volume</div>', unsafe_allow_html=True)
    if "oa_p2a" in raw_sms_filt.columns:
        top_oa = (
            raw_sms_filt.groupby("oa_p2a")["sms_count"]
            .sum().sort_values(ascending=False).head(10).reset_index()
        )
        top_oa.columns = ["OA / Brand", "Total SMS"]
        # Mini bar chart for top OA
        oa_cols = st.columns([2, 3])
        with oa_cols[0]:
            st.dataframe(top_oa, use_container_width=True, hide_index=True)
        with oa_cols[1]:
            fig3, ax3 = plt.subplots(figsize=(7, 3.2))
            fig3.patch.set_facecolor(BG)
            ax3.set_facecolor(PANEL)
            y_labels = top_oa["OA / Brand"].tolist()[::-1]
            x_vals3  = top_oa["Total SMS"].tolist()[::-1]
            bar_cols3 = ["#00c8ff"] * len(y_labels)
            ax3.barh(y_labels, x_vals3, color=bar_cols3, height=0.55, zorder=3)
            ax3.xaxis.set_major_formatter(mticker.FuncFormatter(
                lambda x, _: f"{x/1_000:.0f}K" if x >= 1_000 else str(int(x))
            ))
            ax3.tick_params(colors=TXTDIM, labelsize=8, length=0)
            ax3.set_yticklabels(y_labels, color="#8da4be", fontsize=8)
            for sp in ax3.spines.values():
                sp.set_visible(False)
            ax3.grid(axis="x", color=GRIDCOL, linewidth=0.7, zorder=0)
            plt.tight_layout(pad=0.5)
            st.pyplot(fig3, use_container_width=True)
            plt.close(fig3)

    # MO/MT breakdown
    if "momt" in raw_sms_filt.columns:
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="section-label">MO vs MT Breakdown</div>', unsafe_allow_html=True)
        momt_grp = raw_sms_filt.groupby("momt")["sms_count"].sum().reset_index()
        momt_grp.columns = ["Type", "SMS Count"]
        momt_grp["Share %"] = (momt_grp["SMS Count"] / momt_grp["SMS Count"].sum() * 100).round(1)
        st.dataframe(momt_grp.reset_index(drop=True), use_container_width=True, hide_index=True)

    # Operator-level anomaly log
    _render_anomaly_log(anomalies_s, "sms_count", "SMS")

    # ── OA-level anomaly breakdown ─────────────────────────────────────────
    if "oa_p2a" in raw_sms_filt.columns and not raw_sms_filt.empty:
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="section-label">⚠ Anomaly Breakdown per OA — DoD Change > 20%</div>',
                    unsafe_allow_html=True)

        # Aggregate daily per OA
        oa_daily = (
            raw_sms_filt
            .assign(calldate=pd.to_datetime(raw_sms_filt["calldate"]))
            .groupby(["calldate", "oa_p2a", "opr"], as_index=False)["sms_count"]
            .sum()
            .sort_values(["oa_p2a", "calldate"])
        )

        # DoD per OA
        oa_daily["sms_prev"] = oa_daily.groupby("oa_p2a")["sms_count"].shift(1)
        oa_daily["dod_pct"]  = ((oa_daily["sms_count"] - oa_daily["sms_prev"])
                                 / oa_daily["sms_prev"].replace(0, float("nan")) * 100).round(2)

        # Filter anomalies (|DoD| > 20%) on latest date
        latest_oa_date = oa_daily["calldate"].max()
        oa_anom = oa_daily[
            (oa_daily["calldate"] == latest_oa_date) &
            (oa_daily["dod_pct"].notna()) &
            (oa_daily["dod_pct"].abs() > 20)
        ].sort_values("dod_pct", ascending=False).head(30)

        if oa_anom.empty:
            st.markdown(
                "<div style='background:#0d1e30;border:1px solid #1a3050;border-radius:8px;"
                "padding:16px 20px;font-family:IBM Plex Mono,monospace;font-size:11px;color:#2a5a8a'>"
                "✓ Tidak ada anomali OA pada tanggal terakhir.</div>",
                unsafe_allow_html=True,
            )
        else:
            # Summary chips
            spike_cnt = int((oa_anom["dod_pct"] > 0).sum())
            drop_cnt  = int((oa_anom["dod_pct"] < 0).sum())
            st.markdown(
                f'<div style="display:flex;gap:10px;margin-bottom:12px">'
                f'<span style="background:rgba(255,69,96,0.12);border:1px solid rgba(255,69,96,0.25);'
                f'border-radius:20px;padding:3px 12px;font-family:IBM Plex Mono,monospace;'
                f'font-size:10px;color:#ff4560;letter-spacing:1px">▲ SPIKE: {spike_cnt} OA</span>'
                f'<span style="background:rgba(0,200,255,0.08);border:1px solid rgba(0,200,255,0.2);'
                f'border-radius:20px;padding:3px 12px;font-family:IBM Plex Mono,monospace;'
                f'font-size:10px;color:#00c8ff;letter-spacing:1px">▼ DROP: {drop_cnt} OA</span>'
                f'<span style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#2a5a8a;'
                f'padding:3px 0">tanggal: {latest_oa_date.strftime("%Y-%m-%d")}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # Styled rows
            oa_html = ""
            for _, row in oa_anom.iterrows():
                op_color = OPERATOR_COLORS.get(row["opr"], "#8da4be")
                arrow    = "▲" if row["dod_pct"] >= 0 else "▼"
                pct_col  = "#ff4560" if row["dod_pct"] >= 0 else "#00c8ff"
                oa_html += (
                    f'<div style="background:rgba(255,255,255,0.02);border:1px solid #0f2035;'
                    f'border-radius:6px;padding:8px 14px;margin-bottom:5px;'
                    f'font-family:IBM Plex Mono,monospace;font-size:11px;color:#cdd9e5;'
                    f'display:flex;gap:14px;align-items:center;flex-wrap:wrap">'
                    # OA name
                    f'<span style="color:#e8f4ff;font-weight:600;min-width:120px;'
                    f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'
                    f'{row["oa_p2a"]}</span>'
                    # Operator badge
                    f'<span style="background:{op_color}22;border:1px solid {op_color}55;'
                    f'border-radius:4px;padding:1px 7px;color:{op_color};font-size:10px">'
                    f'{row["opr"]}</span>'
                    # SMS count
                    f'<span style="color:#8da4be">{int(row["sms_count"]):,} SMS</span>'
                    # Prev count
                    f'<span style="color:#2a5a8a">prev: {int(row["sms_prev"]) if pd.notna(row["sms_prev"]) else "—":,}</span>'
                    # DoD %
                    f'<span style="color:{pct_col};font-weight:600;margin-left:auto">'
                    f'{arrow} {abs(row["dod_pct"]):.1f}% DoD</span>'
                    f'</div>'
                )
            st.markdown(oa_html, unsafe_allow_html=True)

            # Compact chart: top 15 OA by |DoD|
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            top15 = oa_anom.reindex(
                oa_anom["dod_pct"].abs().sort_values(ascending=True).index
            ).tail(15)
            fig_oa, ax_oa = plt.subplots(figsize=(14, max(2.5, len(top15) * 0.52)))
            fig_oa.patch.set_facecolor(BG)
            ax_oa.set_facecolor(PANEL)
            dod_v  = top15["dod_pct"].tolist()
            oa_lbl = [f"{r['oa_p2a']} ({r['opr']})" for _, r in top15.iterrows()]
            bar_c  = ["#ff4560" if v >= 0 else "#00c8ff" for v in dod_v]
            bars_oa = ax_oa.barh(oa_lbl, dod_v, color=bar_c, height=0.55, zorder=3)
            for bar, val in zip(bars_oa, dod_v):
                x_pos = val + (1 if val >= 0 else -1)
                ax_oa.text(x_pos, bar.get_y() + bar.get_height() / 2,
                           f"{val:+.1f}%", va="center",
                           ha="left" if val >= 0 else "right",
                           color="#cdd9e5", fontsize=8)
            ax_oa.axvline(0, color="#1a3050", linewidth=1)
            ax_oa.tick_params(colors=TXTDIM, labelsize=7.5, length=0)
            ax_oa.set_yticklabels(oa_lbl, color="#8da4be", fontsize=8)
            for sp in ax_oa.spines.values():
                sp.set_visible(False)
            ax_oa.grid(axis="x", color=GRIDCOL, linewidth=0.7, zorder=0)
            plt.tight_layout(pad=0.5)
            st.pyplot(fig_oa, use_container_width=True)
            plt.close(fig_oa)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
st.markdown("""
<div style='border-top:1px solid #0f2035;padding-top:14px;display:flex;
            justify-content:space-between;align-items:center'>
  <span style='font-family:IBM Plex Mono,monospace;font-size:10px;color:#1e3a5a'>
    PORTFOLIO DEMO · DUMMY DATA ONLY · NO REAL OPERATOR DATA
  </span>
  <span style='font-family:IBM Plex Mono,monospace;font-size:10px;color:#1e3a5a'>
    Built by Gian Gianna · @giangianna14 · Python Automation Engineer
  </span>
</div>
""", unsafe_allow_html=True)
