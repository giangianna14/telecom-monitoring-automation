"""
scheduler.py — APScheduler: run full pipeline automatically every day at 06:12 WIB.

Usage:
    python scheduler.py          # keep this process running (e.g. via nohup / Windows Task Scheduler)

The scheduler uses Asia/Jakarta timezone.
misfire_grace_time=300 ensures missed runs (e.g. after reboot) are retried within 5 minutes.
"""
import logging
from pathlib import Path

# Load .env
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

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from main import run


def scheduled_job():
    """Wrapper so exceptions don't kill the scheduler process."""
    try:
        run()
    except Exception as exc:
        log.error("Pipeline job failed: %s", exc, exc_info=True)


scheduler = BlockingScheduler(timezone="Asia/Jakarta")

scheduler.add_job(
    scheduled_job,
    trigger=CronTrigger(hour=6, minute=12, timezone="Asia/Jakarta"),
    id="daily_telecom_report",
    name="Daily Telecom Report Pipeline",
    misfire_grace_time=300,
    replace_existing=True,
    max_instances=1,
)

if __name__ == "__main__":
    log.info("Scheduler started.")
    log.info("Next run: daily at 06:12 WIB (Asia/Jakarta)")
    log.info("Press Ctrl+C to stop.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("Scheduler stopped cleanly.")
