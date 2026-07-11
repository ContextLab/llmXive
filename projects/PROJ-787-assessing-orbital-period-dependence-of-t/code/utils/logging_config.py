import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

_loggers: Dict[str, logging.Logger] = {}

def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    format_str: Optional[str] = None,
) -> None:
    """
    Configure the root logger and create a standard formatter.
    """
    if format_str is None:
        format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    formatter = logging.Formatter(format_str)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    # Avoid adding handlers multiple times if called repeatedly
    if not root_logger.handlers:
        root_logger.addHandler(console_handler)

    # File handler (optional)
    if log_file is None:
        log_file = LOG_DIR / "pipeline.log"
    else:
        log_file = Path(log_file)

    log_file.parent.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Retrieve or create a logger for a specific module/component.
    Caches loggers to avoid re-creation overhead.
    """
    if name not in _loggers:
        logger = logging.getLogger(name)
        # Ensure it inherits handlers from root
        logger.propagate = True
        _loggers[name] = logger
    return _loggers[name]

def configure_module_logger(
    module_name: str,
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
) -> logging.Logger:
    """
    Convenience wrapper to get a logger and ensure logging is setup.
    """
    setup_logging(level=level, log_file=log_file)
    return get_logger(module_name)

def get_module_logger(name: str) -> logging.Logger:
    """
    Alias for get_logger to match existing API expectations.
    """
    return get_logger(name)

def log_ingestion_summary(
    logger: logging.Logger,
    stage: str,
    total_input: int,
    excluded_count: int,
    reasons: Dict[str, int],
) -> None:
    """
    Standardized logging for ingestion filtering steps.
    Logs the total count, excluded count, and a breakdown of reasons.
    """
    logger.info("=== Ingestion Summary: %s ===", stage)
    logger.info("Total input records: %d", total_input)
    logger.info("Total excluded records: %d", excluded_count)
    
    if reasons:
        logger.info("Exclusion breakdown:")
        for reason, count in sorted(reasons.items(), key=lambda x: x[1], reverse=True):
            logger.info("  - %s: %d", reason, count)
    
    logger.info("Records passed to next stage: %d", total_input - excluded_count)
    logger.info("========================================")
