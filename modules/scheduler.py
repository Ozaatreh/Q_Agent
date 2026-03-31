"""
scheduler.py
────────────
Runs the full pipeline on a configurable daily schedule.
Uses the `schedule` library (pip install schedule).

Usage:
    python scheduler.py           # run scheduler indefinitely
    python scheduler.py --once    # run pipeline once immediately, then exit
"""

import argparse
import sys
import time
from datetime import datetime

import schedule

from config.settings import PUBLISH_TIMES
from modules.logger import get_logger
from pipeline import run_pipeline

log = get_logger("scheduler")


def _validate_publish_times(times: list[str]) -> list[str]:
    """
    Validate HH:MM 24-hour times, remove duplicates, and sort them.
    """
    valid_times = []

    for t in times:
        try:
            datetime.strptime(t, "%H:%M")
            valid_times.append(t)
        except ValueError:
            log.warning(f"Invalid publish time skipped: {t}")

    # remove duplicates, then sort
    valid_times = sorted(set(valid_times), key=lambda x: datetime.strptime(x, "%H:%M"))

    return valid_times


def _job():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log.info(f"=== Scheduled job triggered at {now} ===")

    success = run_pipeline()

    if success:
        log.info("Job completed successfully ✓")
    else:
        log.warning("Job completed with errors ✗")


def start_scheduler():
    """
    Register jobs and block forever.
    """
    publish_times = _validate_publish_times(PUBLISH_TIMES)

    if not publish_times:
        log.error("No valid publish times found in PUBLISH_TIMES.")
        sys.exit(1)

    log.info(f"Starting scheduler with {len(publish_times)} daily runs: {publish_times}")

    for t in publish_times:
        schedule.every().day.at(t).do(_job)
        log.info(f"  → Scheduled daily at {t}")

    log.info("Scheduler running. Press Ctrl+C to stop.")

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        log.info("Scheduler stopped by user.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Quran Reels Agent Scheduler")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run the pipeline once immediately and exit",
    )
    args = parser.parse_args()

    if args.once:
        log.info("Running pipeline once…")
        ok = run_pipeline()
        sys.exit(0 if ok else 1)
    else:
        start_scheduler()