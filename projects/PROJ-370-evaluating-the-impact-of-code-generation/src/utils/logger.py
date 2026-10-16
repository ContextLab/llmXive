"""
Utility module for pipeline logging.

Provides functions to set up a JSON‑lines logger that writes to
``logs/pipeline.jsonl`` and a helper to retrieve named loggers.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict

# Global handler reference to avoid duplicate handlers on repeated calls
_pipeline_handler: logging.Handler | None = None

def _json_log_record(record: logging.LogRecord) -> Dict[str, Any]:
    """
    Convert a LogRecord into a JSON‑serialisable dict.
    """
    # Basic fields
    log_entry: Dict[str, Any] = {
        "timestamp": record.created,
        "level": record.levelname,
        "name": record.name,
        "message": record.getMessage(),
    }
    # Include any extra fields passed via the ``extra`` argument
    extra = {
        key: value
        for key, value in record.__dict__.items()
        if key not in logging.LogRecord.__dict__ and key not in ("args", "msg", "levelname", "levelno", "pathname", "filename", "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName", "created", "msecs", "relativeCreated", "thread", "threadName", "processName", "process")
    }
    if extra:
        log_entry["extra"] = extra
    return log_entry

class _JsonLineHandler(logging.FileHandler):
    """
    Logging handler that writes each record as a single line of JSON.
    """
    def emit(self, record: logging.LogRecord) -> None:
        try:
            json_line = json.dumps(_json_log_record(record), ensure_ascii=False)
            stream = self.stream
            stream.write(json_line + "\n")
            self.flush()
        except Exception:
            self.handleError(record)

def setup_pipeline_logging() -> None:
    """
    Configure the root logger to write JSON‑lines to ``logs/pipeline.jsonl``.
    This function is idempotent – calling it multiple times will not add
    duplicate handlers.
    """
    global _pipeline_handler

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if _pipeline_handler is not None:
        # Handler already attached
        return

    # Ensure the logs directory exists
    logs_path = Path("logs")
    logs_path.mkdir(parents=True, exist_ok=True)

    # Create and attach the JSON‑lines handler
    handler = _JsonLineHandler(logs_path / "pipeline.jsonl", encoding="utf-8")
    formatter = logging.Formatter("%(message)s")  # Message is already JSON
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    _pipeline_handler = handler

def get_logger(name: str) -> logging.Logger:
    """
    Retrieve (or create) a named logger. The logger inherits the JSON‑lines
    configuration set up by :func:`setup_pipeline_logging`.
    """
    return logging.getLogger(name)

# Simple counters for PR processing statistics – used by the CLI
_processed_counter = 0
_skipped_counter = 0

def increment_pr_processed() -> None:
    """Increment the counter of successfully processed PRs."""
    global _processed_counter
    _processed_counter += 1

def increment_pr_skipped() -> None:
    """Increment the counter of PRs that were skipped (e.g., due to timeout)."""
    global _skipped_counter
    _skipped_counter += 1

def get_pr_counters() -> Dict[str, int]:
    """Return the current processing counters (useful for reporting)."""
    return {"processed": _processed_counter, "skipped": _skipped_counter}
