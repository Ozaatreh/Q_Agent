"""Centralized logger for the Quran Reels Agent."""

import logging
import sys
from pathlib import Path
from datetime import datetime

from config.settings import LOGS_DIR, LOG_LEVEL


def get_logger(name: str) -> logging.Logger:
    """Return a named logger writing to stdout + daily rotating log file."""
    logger = logging.getLogger(name)

    if logger.handlers:          # already configured
        return logger

    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s  %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # File  (one file per day)
    log_file = LOGS_DIR / f"{datetime.now():%Y-%m-%d}.log"
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger
