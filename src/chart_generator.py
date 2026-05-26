"""
chart_generator.py — Generate line charts with matplotlib.
Saves charts as .jpg to the output/ directory.
"""
import matplotlib
matplotlib.use("Agg")          # non-interactive backend — safe for scheduler
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Consistent color per operator — matches ref_operator.csv
OPERATOR_COLORS = {
    "GAH": "#E63946",
    "INS": "#2196F3",
    "MVN": "#4CAF50",
    "TLG": "#FF9800",
    "TLI": "#9C27B0",
    "TSV": "#00BCD4",
}

BG_DARK   = "#0d1117"
BG_PANEL  = "#161b22"
GRID_LINE = "#21262d"
TEXT_DIM  = "#8b949e"


def plot_daily_trend(daily, date_col, metric_col, title, ylabel, filename):
    """
    Plot multi-operator line chart from daily aggregated DataFrame.

    Parameters
    ----------
    daily     : pd.DataFrame  result of aggregate_daily()
    date_col  : str           name of the date column
    metric_col: str           name of the metric column (y-axis)
    title     : str           chart title
    ylabel    : str           y-axis label
    filename  : str           output file name (e.g. "voice_sli_2026-05-26.jpg")

    Returns
    -------
    str : absolute path to saved chart file
    """
    fig, ax = plt.subplots(figsize=(14, 6))
    fig.patch.set_facecolor(BG_DARK)
    ax.set_facecolor(BG_PANEL)

    operators = sorted(daily["operator"].unique()) if "operator" in daily.columns else sorted(daily[daily.columns[1]].unique())

    for op in operators:
        subset = daily[daily["operator"] == op].sort_values(date_col)
        color  = OPERATOR_COLORS.get(op, "#ffffff")
        ax.plot(
            subset[date_col],
            subset[metric_col],
            label=op,
            color=color,
            linewidth=2,
            marker="o",
            markersize=3,
            alpha=0.9,
        )

    # Axis formatting
    ax.set_title(title, color="white", fontsize=13, pad=14, fontweight="bold")
    ax.set_xlabel("Date", color=TEXT_DIM, fontsize=10)
    ax.set_ylabel(ylabel, color=TEXT_DIM, fontsize=10)
    ax.tick_params(colors=TEXT_DIM, labelsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=0, interval=2))
    plt.xticks(rotation=45)

    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["bottom", "left"]:
        ax.spines[spine].set_color("#30363d")

    ax.grid(axis="y", color=GRID_LINE, linestyle="--", linewidth=0.8, alpha=0.7)
    ax.legend(
        facecolor="#1a1a2e",
        labelcolor="white",
        framealpha=0.85,
        fontsize=9,
        ncol=3,
        loc="upper left",
    )

    plt.tight_layout()
    output_path = OUTPUT_DIR / filename
    plt.savefig(str(output_path), dpi=120, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return str(output_path)


def plot_bar_latest(summary, metric_col, title, ylabel, filename):
    """
    Bar chart showing the latest day value per operator.
    Used as a secondary chart in email reports.
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(BG_DARK)
    ax.set_facecolor(BG_PANEL)

    operators = summary["operator"].tolist()
    values    = summary[metric_col].tolist()
    colors    = [OPERATOR_COLORS.get(op, "#ffffff") for op in operators]

    bars = ax.bar(operators, values, color=colors, width=0.55, zorder=3)

    # Value labels on bars
    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() * 1.02,
            f"{val:,.0f}",
            ha="center", va="bottom",
            color="white", fontsize=9,
        )

    ax.set_title(title, color="white", fontsize=12, pad=12, fontweight="bold")
    ax.set_ylabel(ylabel, color=TEXT_DIM, fontsize=10)
    ax.tick_params(colors=TEXT_DIM)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["bottom", "left"]:
        ax.spines[spine].set_color("#30363d")
    ax.grid(axis="y", color=GRID_LINE, linestyle="--", alpha=0.6, zorder=0)

    plt.tight_layout()
    output_path = OUTPUT_DIR / filename
    plt.savefig(str(output_path), dpi=120, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return str(output_path)
