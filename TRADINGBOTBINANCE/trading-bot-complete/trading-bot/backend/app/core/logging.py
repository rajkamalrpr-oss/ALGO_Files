"""
app/core/logging.py — Structured JSON logging for the FastAPI backend.
"""

import logging
import logging.handlers
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_FILE = LOG_DIR / "trading_bot.log"


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        obj = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(obj)


def setup_logging(log_level: str = "DEBUG") -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger("trading_bot")
    root.setLevel(logging.DEBUG)
    root.propagate = False

    # File — JSON rotating
    fh = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    fh.setLevel(getattr(logging, log_level.upper(), logging.DEBUG))
    fh.setFormatter(JSONFormatter())

    # Console — simple
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s"))

    root.addHandler(fh)
    root.addHandler(ch)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"trading_bot.{name}")
