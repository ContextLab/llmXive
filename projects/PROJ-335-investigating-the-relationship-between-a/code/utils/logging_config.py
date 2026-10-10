"""Structured logging infrastructure for the alpha-WM pipeline.

T008: Configures logging that outputs structured (JSON) log records to
``data/results/`` and human-readable records to the console.

Usage:
    from utils.logging_config import setup_logging, get_logger
    setup_logging()
    logger = get_logger(__name__)
    logger.info("message", extra={"event": "download", "dataset": "ds000248"})
"""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

# Default log file location (relative to repository root).
DEFAULT_LOG_DIR = Path("data/results")
DEFAULT_LOG_FILE = "pipeline.log"

# Reserved LogRecord attributes; everything else in `extra` is treated
# as structured payload.
_RESERVED = set(
    logging.LogRecord("", 0, "", 0, "", None, None).__dict__.keys()
) | {"message", "asctime", "taskName"}


class StructuredFormatter(logging.Formatter):
    """Format log records as single-line JSON objects.

    Standard LogRecord fields (level, time, logger, message) plus any
    keyword payload passed via ``extra={...}`` are serialized.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                try:
                    json.dumps(value)
                    payload[key] = value
                except (TypeError, ValueError):
                    payload[key] = repr(value)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


_configured = False


def setup_logging(
    log_dir: Optional[str] = None,
    log_file: str = DEFAULT_LOG_FILE,
    level: int = logging.INFO,
    console_level: int = logging.INFO,
    logger_name: Optional[str] = None,
) -> logging.Logger:
    """Configure structured logging to ``data/results/`` and console.

    Args:
        log_dir: Directory for the structured log file. Defaults to
            ``data/results``.
        log_file: Filename of the structured log inside ``log_dir``.
        level: Minimum level for the file (JSON) handler.
        console_level: Minimum level for the console handler.
        logger_name: Root logger name to configure (default: root).

    Returns:
        The configured logger.
    """
    global _configured

    target = logging.getLogger(logger_name)
    target.setLevel(min(level, console_level))

    if _configured and target.handlers:
        # Already configured; return the existing logger.
        return target

    log_path_dir = Path(log_dir) if log_dir else DEFAULT_LOG_DIR
    log_path_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_path_dir / log_file

    # File handler: structured JSON lines.
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(StructuredFormatter())
    target.addHandler(file_handler)

    # Console handler: human-readable.
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    target.addHandler(console_handler)

    target.propagate = False
    _configured = True
    target.info(
        "Logging initialized",
        extra={"event": "logging_setup", "log_file": str(log_path)},
    )
    return target


def get_logger(name: str = "alpha_wm") -> logging.Logger:
    """Return a named logger, configuring defaults if needed."""
    if not _configured:
        setup_logging()
    return logging.getLogger(name)


def log_metric(logger: logging.Logger, metric_name: str, value: Any, **context: Any) -> None:
    """Log a metric with structured context at INFO level."""
    extra = {"event": "metric", "metric": metric_name, "value": value}
    extra.update(context)
    logger.info(f"metric {metric_name}={value!r}", extra=extra)


def main() -> None:
    """Entry point: initialize logging and emit a startup record.

    Writes a structured log file to ``data/results/pipeline.log`` and
    echoes a human-readable record to the console.
    """
    logger = setup_logging()
    logger.info(
        "Pipeline logging infrastructure ready",
        extra={
            "event": "startup",
            "log_dir": str(DEFAULT_LOG_DIR),
            "structured_format": "json",
        },
    )


if __name__ == "__main__":
    main()
