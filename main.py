"""
main.py — Orchestrate the full reporting pipeline.

Usage:
    python main.py                  # run once immediately
    python main.py --dry-run        # skip email/whatsapp, just print summary
"""
import sys
import logging
from datetime import date
from pathlib import Path

# Load .env if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

from src.data_loader     import load_voice_sli
from src.processor       import (
    aggregate_daily, calculate_dod, calculate_wow,
    get_latest_summary, detect_anomalies,
)
from src.chart_generator import plot_daily_trend, plot_bar_latest


def build_summary_html(summary_df):
    rows = ""
    for _, row in summary_df.iterrows():
        dod_val   = row.get("dod_pct")
        wow_val   = row.get("wow_pct")
        dod_color = "#00e5c3" if (dod_val is not None and dod_val >= 0) else "#ff4d4f"
        wow_color = "#00e5c3" if (wow_val is not None and wow_val >= 0) else "#ff4d4f"
        dod_txt   = f"{dod_val:.1f}%" if dod_val is not None else "N/A"
        wow_txt   = f"{wow_val:.1f}%" if wow_val is not None else "N/A"
        rows += (
            f"<tr>"
            f"<td style='padding:8px'>{row['operator']}</td>"
            f"<td style='padding:8px;text-align:right'>{row['duration_min']:,.0f}</td>"
            f"<td style='padding:8px;text-align:right;color:{dod_color}'>{dod_txt}</td>"
            f"<td style='padding:8px;text-align:right;color:{wow_color}'>{wow_txt}</td>"
            f"</tr>"
        )
    return (
        "<table border='0' cellpadding='0' cellspacing='0' "
        "style='border-collapse:collapse;width:100%;background:#161b22;color:#e6edf3'>"
        "<tr style='background:#1f2937;color:#9ca3af'>"
        "<th style='padding:8px;text-align:left'>Operator</th>"
        "<th style='padding:8px;text-align:right'>Duration (min)</th>"
        "<th style='padding:8px;text-align:right'>DoD %</th>"
        "<th style='padding:8px;text-align:right'>WoW %</th>"
        "</tr>"
        + rows
        + "</table>"
    )


def run(dry_run=False):
    today_str = date.today().strftime("%Y-%m-%d")
    log.info("=" * 60)
    log.info("Pipeline started — %s", today_str)
    log.info("=" * 60)

    # ── 1. Load ──────────────────────────────────────────────────
    df = load_voice_sli()
    log.info("Loaded %d rows from sample_voice_sli.csv", len(df))

    # ── 2. Process ───────────────────────────────────────────────
    daily = aggregate_daily(df, "call_date", "duration_min")
    daily = calculate_dod(daily, "call_date", "duration_min")
    daily = calculate_wow(daily, "call_date", "duration_min")
    log.info("Processed: %d daily aggregations", len(daily))

    # ── 3. Summary & Anomaly Detection ───────────────────────────
    summary     = get_latest_summary(daily, "call_date", "duration_min")
    anomalies   = detect_anomalies(daily, "duration_min", threshold_pct=20.0)
    latest_date = daily["call_date"].max().strftime("%Y-%m-%d")

    log.info("Latest date in data: %s", latest_date)
    log.info("Anomalies detected: %d", len(anomalies))

    print("\n--- Latest Day Summary ---")
    print(summary[["operator", "duration_min", "dod_pct", "wow_pct"]].to_string(index=False))
    if not anomalies.empty:
        print("\n--- Anomalies (DoD > 20%) ---")
        print(anomalies[["call_date", "operator", "duration_min", "dod_pct"]].to_string(index=False))

    # ── 4. Charts ────────────────────────────────────────────────
    chart_line = plot_daily_trend(
        daily, "call_date", "duration_min",
        title=f"Voice SLI — Daily Duration per Operator ({latest_date})",
        ylabel="Duration (min)",
        filename=f"voice_sli_trend_{today_str}.jpg",
    )
    log.info("Line chart saved: %s", chart_line)

    chart_bar = plot_bar_latest(
        summary, "duration_min",
        title=f"Voice SLI — Latest Day by Operator ({latest_date})",
        ylabel="Duration (min)",
        filename=f"voice_sli_bar_{today_str}.jpg",
    )
    log.info("Bar chart saved: %s", chart_bar)

    if dry_run:
        log.info("Dry-run mode — skipping email and WhatsApp.")
        log.info("Pipeline complete (dry-run).")
        return

    # ── 5. Email ─────────────────────────────────────────────────
    try:
        from src.email_sender import send_report
        summary_html = build_summary_html(summary)
        send_report(chart_line, summary_html, latest_date, anomaly_count=len(anomalies))
    except Exception as exc:
        log.error("Email failed (configure .env to enable): %s", exc)

    # ── 6. WhatsApp ──────────────────────────────────────────────
    # Uncomment after Chrome + ChromeDriver are set up:
    # try:
    #     from src.whatsapp_sender import send_wa_report
    #     op_list = summary[["operator","duration_min","dod_pct"]].to_dict("records")
    #     send_wa_report(latest_date, op_list)
    # except Exception as exc:
    #     log.error("WhatsApp failed: %s", exc)

    log.info("Pipeline complete.")


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    run(dry_run=dry)
