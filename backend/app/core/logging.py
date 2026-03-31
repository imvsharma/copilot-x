"""Logging setup — text for dev, JSON lines for production aggregators."""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class JsonFormatter(logging.Formatter):
    """Minimal JSON lines; extend with trace_id when request middleware is added."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(level: str = "INFO", log_format: str = "text") -> None:
    root = logging.getLogger()
    if root.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    if log_format == "json":
        handler.setFormatter(JsonFormatter())
    else:
        fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        handler.setFormatter(logging.Formatter(fmt))
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_extra(**kwargs: Any) -> dict[str, Any]:
    """Attach key=value pairs for structured log processors."""
    return kwargs
