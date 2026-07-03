"""
Logging configuration and helper utilities for the llmXive research pipeline.

This module provides:
- `setup_logging()`: Configures the root logger with console and file handlers,
  including a custom formatter for exclusion events.
- `log_subject_exclusion()`: Records why a subject was excluded (missing data,
  motion threshold, etc.) to both console and a dedicated exclusion log file.
- `log_memory_usage()`: Records memory usage events (peak RSS, limit checks)
  to both console and a dedicated memory log file.
"""

import logging
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Import config for seed pinning if needed elsewhere, though not strictly for logging
from utils.config import set_all_seeds


# Define log file paths relative to project root (assumed to be run from project root)
# We use a fixed relative path to ensure logs land in the data/results directory
LOG_DIR = Path("data/results/logs")
EXCLUSION_LOG_FILE = LOG_DIR / "exclusions.log"
MEMORY_LOG_FILE = LOG_DIR / "memory_usage.log"
GENERAL_LOG_FILE = LOG_DIR / "pipeline.log"


class ExclusionFormatter(logging.Formatter):
    """
    Custom formatter for exclusion events to ensure structured, parseable output.
    Output format: ISO_TIMESTAMP | LEVEL | EXCLUSION_TYPE | SUBJECT_ID | REASON
    """
    def format(self, record):
        # Ensure we have a structured message if it's a dict
        if isinstance(record.msg, dict):
            # Create a structured log entry
            entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "type": record.msg.get("type", "UNKNOWN"),
                "subject_id": record.msg.get("subject_id", "N/A"),
                "reason": record.msg.get("reason", "No reason provided"),
                "details": record.msg.get("details", {})
            }
            record.msg = json.dumps(entry)
            record.args = ()  # Clear args to prevent formatting issues
        return super().format(record)


def _ensure_log_dirs():
    """Create log directories if they don't exist."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def setup_logging(
    level: int = logging.INFO,
    general_log: bool = True,
    exclusion_log: bool = True,
    memory_log: bool = True
) -> None:
    """
    Configure the root logger with console and file handlers.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        general_log: If True, write general logs to pipeline.log.
        exclusion_log: If True, write exclusion events to exclusions.log.
        memory_log: If True, write memory events to memory_usage.log.
    """
    _ensure_log_dirs()

    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Clear existing handlers to avoid duplicates on re-calls
    if logger.handlers:
        logger.handlers.clear()

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # General File Handler
    if general_log:
        general_handler = logging.FileHandler(GENERAL_LOG_FILE)
        general_handler.setLevel(level)
        general_handler.setFormatter(console_formatter)
        logger.addHandler(general_handler)

    # Exclusion File Handler (Custom Formatter)
    if exclusion_log:
        exclusion_handler = logging.FileHandler(EXCLUSION_LOG_FILE)
        exclusion_handler.setLevel(level)
        exclusion_formatter = ExclusionFormatter(
            '%(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        exclusion_handler.setFormatter(exclusion_formatter)
        # Add a filter to only handle exclusion logs if we wanted to be strict,
        # but here we rely on the specific logger usage or just let the formatter handle structure
        logger.addHandler(exclusion_handler)

    # Memory File Handler
    if memory_log:
        memory_handler = logging.FileHandler(MEMORY_LOG_FILE)
        memory_handler.setLevel(level)
        memory_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        memory_handler.setFormatter(memory_formatter)
        logger.addHandler(memory_handler)

    logging.info("Logging infrastructure initialized.")
    logging.info(f"Exclusion log: {EXCLUSION_LOG_FILE}")
    logging.info(f"Memory log: {MEMORY_LOG_FILE}")


def log_subject_exclusion(
    subject_id: str,
    reason: str,
    exclusion_type: str = "SUBJECT_EXCLUSION",
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a subject exclusion event.

    Args:
        subject_id: The identifier of the excluded subject.
        reason: The reason for exclusion (e.g., "Mean FD > 0.2mm").
        exclusion_type: Category of exclusion (default: SUBJECT_EXCLUSION).
        details: Optional dictionary of additional context (e.g., actual FD value).
    """
    logger = logging.getLogger()
    log_entry = {
        "type": exclusion_type,
        "subject_id": subject_id,
        "reason": reason,
        "details": details or {}
    }
    # Use a specific log level for exclusions, e.g., WARNING
    logger.warning(log_entry)


def log_memory_usage(
    event: str,
    current_rss_mb: Optional[float] = None,
    peak_rss_mb: Optional[float] = None,
    limit_mb: float = 7000.0,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a memory usage event.

    Args:
        event: Description of the event (e.g., "Start processing subject", "Peak memory check").
        current_rss_mb: Current RSS in MB.
        peak_rss_mb: Peak RSS in MB.
        limit_mb: Memory limit in MB (default 7000).
        details: Optional additional context.
    """
    logger = logging.getLogger()
    msg_parts = [f"EVENT={event}"]
    if current_rss_mb is not None:
        msg_parts.append(f"current_rss_mb={current_rss_mb:.2f}")
    if peak_rss_mb is not None:
        msg_parts.append(f"peak_rss_mb={peak_rss_mb:.2f}")
    msg_parts.append(f"limit_mb={limit_mb}")
    if details:
        msg_parts.append(json.dumps(details))

    message = " | ".join(msg_parts)
    logger.info(message)

if __name__ == "__main__":
    # Simple test of the logging infrastructure
    setup_logging()
    logging.info("Testing logging configuration...")
    log_subject_exclusion("sub-001", "Missing behavioral scores", details={"file": "missing.csv"})
    log_subject_exclusion("sub-002", "Mean FD > 0.2mm", details={"mean_fd": 0.25})
    log_memory_usage("Initialization", current_rss_mb=500.0, peak_rss_mb=500.0)
    log_memory_usage("Post-load", current_rss_mb=3500.0, peak_rss_mb=3500.0)
    logging.info("Logging test complete. Check data/results/logs/ for output.")