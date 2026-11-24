"""
configure_logging.py
--------------------

This script sets up a structured JSON logging infrastructure for the project.
It creates (or appends to) ``data/results/execution.log`` and provides a
``log_event`` helper that writes a single JSON line per log entry.

The script is deliberately minimal – it is executed once during the
quick‑start to guarantee that the log file exists and contains at least one
well‑formed entry.  Subsequent modules can import ``log_event`` from this
file (or use the configured ``logger`` directly) to emit additional JSON
logs.

The implementation uses only the standard library and the ``llmxive_toolkit``
helper ``paths`` to resolve the output location in a platform‑agnostic way.
"""

import json
import logging
from pathlib import Path

from llmxive_toolkit import paths

# Resolve the log file path inside the project (creates the parent directory)
LOG_FILE: Path = paths.results("execution.log")

# Ensure the parent directory exists (paths.results already does this)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Configure a root logger that writes raw JSON strings to the file.
logger = logging.getLogger("execution_logger")
logger.setLevel(logging.INFO)

# Avoid adding duplicate handlers if this module is imported multiple times.
if not any(isinstance(h, logging.FileHandler) and h.baseFilename == str(LOG_FILE) for h in logger.handlers):
    file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    # Formatter emits the message exactly as we pass it (a JSON string)
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(file_handler)

def log_event(event: str, **kwargs) -> None:
    """
    Write a structured JSON log entry.

    Parameters
    ----------
    event: str
        A short identifier for the type of event (e.g., "pipeline_start").
    **kwargs:
        Arbitrary key‑value pairs that provide additional context.
    """
    record = {"event": event, **kwargs}
    # Ensure deterministic ordering for easier testing / diffing
    json_line = json.dumps(record, sort_keys=True)
    logger.info(json_line)

def _write_initial_entry() -> None:
    """
    Emit a single log line when the script is executed directly.
    This guarantees that ``data/results/execution.log`` is created
    and contains valid JSON, satisfying the T008 verification step.
    """
    log_event(
        event="logging_initialized",
        status="success",
        description="Structured JSON logging configured for the project.",
    )

if __name__ == "__main__":
    _write_initial_entry()