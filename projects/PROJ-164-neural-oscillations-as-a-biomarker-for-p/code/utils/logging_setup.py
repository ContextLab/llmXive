"""Logging infrastructure for the PROJ-164 pipeline (Task T008).

Provides:
- ``setup_logging``: idempotent configuration of stdout + rotating file
  logging to ``logs/pipeline.log`` (RotatingFileHandler, 5 MB per file,
  3 backups) to prevent disk overflow.
- ``get_logger``: return a named logger under the configured root.
- ``log_mode_switch``: structured logging of pipeline mode switches
  (Primary / Data Insufficient / Underpowered).
- ``log_resource_usage``: periodic CPU / memory usage capture (NFR-001).
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

import psutil

LOGGER_NAME = "proj164"
DEFAULT_LOG_FILE = "pipeline.log"
MAX_BYTES = 5 * 1024 * 1024  # 5 MB per log file
BACKUP_COUNT = 3             # pipeline.log + 3 rotated backups

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

_configured = False


def _default_log_dir() -> Path:
    """Return the project ``logs/`` directory, creating it if needed."""
    try:
        from llmxive_toolkit import paths

        return paths.path("logs").parent / "logs"
    except Exception:
        # Fallback: locate logs/ relative to this file (code/utils/).
        root = Path(__file__).resolve().parents[1]
        logs = root / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        return logs


def setup_logging(
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    max_bytes: int = MAX_BYTES,
    backup_count: int = BACKUP_COUNT,
) -> logging.Logger:
    """Configure stdout + rotating-file logging (idempotent).

    Args:
        log_file: Path to the log file. Defaults to ``logs/pipeline.log``
            in the project root. A parent directory is created if needed.
        level: Logging level for handlers.
        max_bytes: Rotation size threshold for the file handler.
        backup_count: Number of rotated backups to keep.

    Returns:
        The configured root logger for the pipeline.
    """
    global _configured

    if log_file is None:
        log_path = _default_log_dir() / DEFAULT_LOG_FILE
    else:
        log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)
    logger.propagate = False

    if _configured:
        return logger

    formatter = logging.Formatter(LOG_FORMAT)

    file_handler = RotatingFileHandler(
        log_path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    _configured = True
    logger.info("Logging initialized: file=%s (rotation: %d bytes, %d backups)",
                log_path, max_bytes, backup_count)
    return logger


def get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """Return a named child logger of the pipeline root logger.

    Configures logging on first use so callers do not need to call
    ``setup_logging`` explicitly.
    """
    setup_logging(log_file=log_file)
    if not name.startswith(LOGGER_NAME):
        name = f"{LOGGER_NAME}.{name}"
    return logging.getLogger(name)


def log_mode_switch(logger: logging.Logger, old_mode: str, new_mode: str,
                    reason: str = "") -> None:
    """Log a pipeline mode switch (FR-001 / FR-008 evidence trail)."""
    logger.warning("MODE SWITCH: '%s' -> '%s' | reason: %s",
                   old_mode, new_mode, reason or "unspecified")


def log_resource_usage(logger: logging.Logger, context: str = "") -> None:
    """Log current process and system resource usage (NFR-001)."""
    process = psutil.Process(os.getpid())
    mem = process.memory_info().rss / (1024 ** 2)
    sys_mem = psutil.virtual_memory()
    logger.info(
        "RESOURCE USAGE%s | pid=%d | cpu_percent=%.1f%% | rss_mb=%.1f | "
        "system_mem_used_mb=%.1f | system_mem_percent=%.1f%%",
        f" [{context}]" if context else "",
        process.pid,
        process.cpu_percent(interval=0.1),
        mem,
        sys_mem.used / (1024 ** 2),
        sys_mem.percent,
    )


def utc_timestamp() -> str:
    """Return an ISO-8601 UTC timestamp string."""
    return datetime.now(timezone.utc).isoformat()
