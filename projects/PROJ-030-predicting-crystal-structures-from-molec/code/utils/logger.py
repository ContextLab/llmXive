"""
Structured JSON logging infrastructure (Task T005).

Provides:
  - ``JsonFormatter``: formats log records as single-line JSON objects.
  - ``setup_logging``: configure the root project logger with a JSON
    file handler writing under ``logs/`` plus a human-readable stream
    handler.
  - ``get_logger``: return a named logger wired to the JSON handler.
  - ``log_event``: emit a structured event with an arbitrary payload.

Running this module as a script initializes the logging infrastructure
and writes ``logs/initialization.log`` containing real JSON log records
describing the environment (Python version, platform, project paths).

Only the Python standard library is used so this module can be imported
by any other stage of the pipeline without dependency risk.
"""
from __future__ import annotations

import json
import logging
import logging.handlers
import os
import platform
import sys
from datetime import datetime, timezone
pathlib_Path = None
from pathlib import Path  # noqa: E402  (kept after __future__ import)

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------
# This file lives at <project_root>/code/utils/logger.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGS_DIR = PROJECT_ROOT / "logs"

LOGGER_NAME_PREFIX = "crystalproj"
_CONFIGURED = False

# ---------------------------------------------------------------------------
# JSON formatter
# ---------------------------------------------------------------------------

class JsonFormatter(logging.Formatter):
    """Format a LogRecord as a single line of JSON.

    Fields: timestamp, level, logger, message, plus any entries in
    ``record.payload`` (a dict attached via ``log_event``) and the
    standard ``exc_info`` traceback when present.
    """

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "lineno": record.lineno,
        }
        payload = getattr(record, "payload", None)
        if isinstance(payload, dict):
            for key, value in payload.items():
                entry[key] = value
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, default=str, ensure_ascii=False)

# ---------------------------------------------------------------------------
# Setup / accessors
# ---------------------------------------------------------------------------

def setup_logging(
    level: int = logging.INFO,
    logs_dir: str | Path | None = None,
    filename: str = "pipeline.log",
) -> logging.Logger:
    """Configure and return the project's root logger.

    Args:
        level: Logging level (default INFO).
        logs_dir: Directory for JSON log files. Defaults to ``<root>/logs``.
        filename: Name of the JSON log file.

    Returns:
        The configured root project logger.
    """
    global _CONFIGURED
    root_logger = logging.getLogger(LOGGER_NAME_PREFIX)

    if _CONFIGURED and root_logger.handlers:
        root_logger.setLevel(level)
        return root_logger

    logs_path = Path(logs_dir) if logs_dir else LOGS_DIR
    logs_path.mkdir(parents=True, exist_ok=True)

    root_logger.setLevel(level)
    root_logger.propagate = False

    # JSON file handler (structured output required by T005)
    file_handler = logging.FileHandler(logs_path / filename, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(JsonFormatter())
    root_logger.addHandler(file_handler)

    # Console handler for operator visibility
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setLevel(level)
    stream_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    )
    root_logger.addHandler(stream_handler)

    _CONFIGURED = True
    root_logger.debug(
        "Logging infrastructure configured",
        extra={"payload": {"logs_dir": str(logs_path), "filename": filename}},
    )
    return root_logger

def get_logger(name: str = "default") -> logging.Logger:
    """Return a named child of the project logger, configuring if needed.

    Args:
        name: Logger name (suffix appended to the project prefix).

    Returns:
        A ``logging.Logger`` that emits structured JSON to ``logs/``.
    """
    if not _CONFIGURED:
        setup_logging()
    if name.startswith(LOGGER_NAME_PREFIX):
        return logging.getLogger(name)
    return logging.getLogger(f"{LOGGER_NAME_PREFIX}.{name}")

def log_event(
    logger: logging.Logger,
    level: str,
    event: str,
    payload: dict | None = None,
) -> None:
    """Emit a structured event with a JSON payload.

    Args:
        logger: Logger to emit through (use ``get_logger``).
        level: Level name, e.g. ``"INFO"``, ``"WARNING"``, ``"ERROR"``.
        event: Human-readable event name.
        payload: Additional structured fields merged into the JSON record.
    """
    log_fn = getattr(logger, level.lower(), logger.info)
    log_fn(event, extra={"payload": payload or {}})

# ---------------------------------------------------------------------------
# Initialization entry point (produces logs/initialization.log)
# ---------------------------------------------------------------------------

def initialize(logs_dir: str | Path | None = None) -> Path:
    """Initialize logging and write the initialization log file.

    Returns:
        The path of the written ``initialization.log``.
    """
    logs_path = Path(logs_dir) if logs_dir else LOGS_DIR
    logs_path.mkdir(parents=True, exist_ok=True)
    init_log = logs_path / "initialization.log"

    # Dedicated logger writing only to initialization.log
    init_logger = logging.getLogger(f"{LOGGER_NAME_PREFIX}.initialization")
    init_logger.setLevel(logging.INFO)
    init_logger.propagate = False
    init_logger.handlers.clear()

    handler = logging.FileHandler(init_log, mode="w", encoding="utf-8")
    handler.setFormatter(JsonFormatter())
    init_logger.addHandler(handler)

    log_event(
        init_logger,
        "INFO",
        "Logging infrastructure initialized",
        {
            "project_root": str(PROJECT_ROOT),
            "logs_dir": str(logs_path),
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "cpu_count": os.cpu_count(),
            "utc_time": datetime.now(timezone.utc).isoformat(),
            "structured_format": "json",
        },
    )

    # Verify the log file is valid JSON (real self-check on disk)
    with open(init_log, "r", encoding="utf-8") as fh:
        lines = [ln for ln in fh.read().splitlines() if ln.strip()]
        parsed = [json.loads(ln) for ln in lines]

    log_event(
        init_logger,
        "INFO",
        "Initialization log self-check passed",
        {
            "records_written": len(lines),
            "first_record_level": parsed[0]["level"] if parsed else None,
            "output_file": str(init_log),
        },
    )
    return init_log

def main() -> int:
    """CLI entry point: initialize logging and write initialization.log."""
    path = initialize()
    print(f"Initialization log written to {path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())