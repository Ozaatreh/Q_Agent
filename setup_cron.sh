#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────
#  setup_cron.sh — Install cron jobs for Quran Reels Agent
#  Run once:  chmod +x setup_cron.sh && ./setup_cron.sh
# ─────────────────────────────────────────────────────────────────

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${SCRIPT_DIR}/venv/bin/python"
PIPELINE="${SCRIPT_DIR}/pipeline.py"
LOG_FILE="${SCRIPT_DIR}/output/logs/cron.log"

echo "Installing cron jobs for Quran Reels Agent…"
echo "  Script dir : $SCRIPT_DIR"
echo "  Python     : $PYTHON_BIN"
echo "  Log        : $LOG_FILE"

# Build cron entries (07:00, 13:00, 20:00 daily)
CRON_CMD="cd ${SCRIPT_DIR} && ${PYTHON_BIN} ${PIPELINE} >> ${LOG_FILE} 2>&1"

( crontab -l 2>/dev/null | grep -v "quran_reels"; \
  echo "0  7  * * *  ${CRON_CMD}   # quran_reels_morning"; \
  echo "0 13  * * *  ${CRON_CMD}   # quran_reels_afternoon"; \
  echo "0 20  * * *  ${CRON_CMD}   # quran_reels_evening" \
) | crontab -

echo "✓ Cron jobs installed. Current crontab:"
crontab -l
