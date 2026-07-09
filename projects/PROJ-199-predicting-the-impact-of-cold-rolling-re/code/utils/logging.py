"""
Logging infrastructure for tracking data lineage and processing steps.

This module provides a centralized logging configuration that ensures:
1. Consistent formatting across all pipeline components.
2. Lineage tracking via structured log records (sample_id, step, reduction).
3. Dual output: console for debugging, file for audit trails.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LOG_DIR = PROJECT_ROOT / "data" / "logs"

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Global logger registry to prevent duplicate handlers
_loggers: dict = {}


class LineageAdapter(logging.LoggerAdapter):
    """
    Logger adapter that injects lineage context (sample_id, step, reduction)
    into every log record without modifying the format string.
    """

    def process(self, msg, kwargs):
        extra = kwargs.get("extra", {})
        extra.update(self.extra)
        kwargs["extra"] = extra
        return f"[Lineage: {self.extra.get('step', 'unknown')}] {msg}", kwargs


def _get_log_filename() -> str:
    """Generate a timestamped log filename."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"pipeline_{timestamp}.log"


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    enable_console: bool = True,
) -> None:
    """
    Configure the root logger with console and file handlers.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional custom log file path. Defaults to data/logs/pipeline_<timestamp>.log.
        enable_console: Whether to log to stdout.
    """
    if log_file is None:
        log_file = str(LOG_DIR / _get_log_filename())
    else:
        # Ensure the directory for custom log file exists
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates in interactive environments
    if root_logger.handlers:
        root_logger.handlers.clear()

    # Formatter with lineage support
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler
    try:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except (PermissionError, OSError) as e:
        print(f"Warning: Could not create log file at {log_file}: {e}", file=sys.stderr)

    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)


def get_logger(
    name: str,
    sample_id: Optional[str] = None,
    step: Optional[str] = None,
    reduction: Optional[float] = None,
) -> logging.Logger | LineageAdapter:
    """
    Retrieve or create a named logger, optionally wrapped with lineage context.

    Args:
        name: Logger name (e.g., 'code.data.download').
        sample_id: Optional sample identifier for lineage tracking.
        step: Optional processing step name (e.g., 'download', 'preprocess').
        reduction: Optional cold-rolling reduction percentage.

    Returns:
        A standard Logger or a LineageAdapter if context is provided.
    """
    # Avoid duplicate handlers for named loggers
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Let root handler filter

    # Prevent adding handlers if already configured (for named loggers)
    if not logger.handlers:
        # Inherit handlers from root
        logger.handlers = list(logging.root.handlers)
        logger.propagate = False  # Prevent double logging

    _loggers[name] = logger

    if sample_id or step or reduction:
        context = {
            "sample_id": sample_id or "unknown",
            "step": step or "unknown",
            "reduction": reduction if reduction is not None else "unknown",
        }
        return LineageAdapter(logger, context)

    return logger


def configure_lineage(
    logger_name: str,
    sample_id: str,
    step: str,
    reduction: Optional[float] = None,
) -> LineageAdapter:
    """
    Convenience wrapper to get a logger pre-configured with lineage.

    Args:
        logger_name: Base logger name.
        sample_id: Sample identifier.
        step: Processing step.
        reduction: Cold-rolling reduction percentage.

    Returns:
        LineageAdapter with context injected.
    """
    return get_logger(
        name=logger_name,
        sample_id=sample_id,
        step=step,
        reduction=reduction,
    )
