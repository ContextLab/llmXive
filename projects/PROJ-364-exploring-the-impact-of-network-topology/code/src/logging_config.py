"""
Logging infrastructure configuration for the llmXive heat dissipation pipeline.

Provides distinct loggers and handlers for:
- Data Ingestion: Warnings about dropped rows, missing values, and data quality.
- Statistical Results: Detailed output of correlation coefficients, p-values, and analysis metrics.

Logs are written to `logs/` with distinct levels and formatting.
"""

import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any
import sys

# Custom log levels to distinguish specific concerns without cluttering standard levels
# 25 = WARNING (Standard), 30 = WARNING, 40 = ERROR
# We will use standard levels but route them to specific handlers based on logger name
# and potentially add a custom level for "STAT_RESULT" if strictly needed, 
# but standard INFO/WARNING separation is usually sufficient if loggers are named correctly.
# However, the task asks for distinct levels. Let's define a custom level for statistical results
# to ensure they are visually distinct in logs if they appear mixed.
STAT_RESULT_LEVEL = 25  # Between INFO (20) and WARNING (30)
logging.addLevelName(STAT_RESULT_LEVEL, "STAT_RESULT")

DATA_INGESTION_WARNING_LEVEL = 30  # Standard WARNING, but we will ensure the handler filters appropriately

LOG_DIR = Path("logs")
LOG_FILE_DATA = "data_ingestion.log"
LOG_FILE_STATS = "statistical_results.log"
LOG_FILE_ALL = "pipeline.log"

# Configuration for log format
FORMAT_STRING = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_loggers: Dict[str, logging.Logger] = {}
_initialized = False


def _ensure_log_dir() -> Path:
    """Ensure the logs directory exists."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    return LOG_DIR


def setup_logging(log_level: int = logging.INFO) -> None:
    """
    Initialize the logging infrastructure.
    
    Creates two distinct file handlers:
    1. Data Ingestion Logger: Writes to logs/data_ingestion.log
    2. Statistical Logger: Writes to logs/statistical_results.log
    
    Also configures the root logger to write to a general pipeline.log.
    """
    global _initialized
    if _initialized:
        return

    _ensure_log_dir()

    # Root logger configuration (General pipeline)
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers to avoid duplicates if called multiple times
    if root_logger.handlers:
        root_logger.handlers.clear()

    # General file handler
    general_handler = logging.FileHandler(_ensure_log_dir() / LOG_FILE_ALL)
    general_handler.setLevel(log_level)
    general_formatter = logging.Formatter(FORMAT_STRING, datefmt=DATE_FORMAT)
    general_handler.setFormatter(general_formatter)
    root_logger.addHandler(general_handler)

    # Data Ingestion Handler
    data_handler = logging.FileHandler(_ensure_log_dir() / LOG_FILE_DATA)
    data_handler.setLevel(logging.WARNING)  # Focus on warnings/errors for ingestion
    data_handler.setFormatter(general_formatter)
    
    # Statistical Handler
    stats_handler = logging.FileHandler(_ensure_log_dir() / LOG_FILE_STATS)
    stats_handler.setLevel(logging.INFO)  # Capture results and info
    stats_handler.setFormatter(general_formatter)

    # Prevent propagation to root for specific loggers to avoid double logging
    # if we want distinct files. Or we can let them propagate.
    # Strategy: Create specific loggers that don't propagate to root, 
    # or use handlers on the root. 
    # Better approach for distinct files: Create loggers with specific handlers.
    
    # We will configure the loggers dynamically in the getter functions 
    # to ensure they have the right handlers attached.
    
    _initialized = True


def get_data_ingestion_logger(name: str = "data_ingestion") -> logging.Logger:
    """
    Returns a logger specifically for data ingestion tasks.
    Logs are written to logs/data_ingestion.log.
    """
    if not _initialized:
        setup_logging()
    
    logger = logging.getLogger(f"llmXive.{name}")
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # Prevent double logging to root

    # Handler for data ingestion
    handler = logging.FileHandler(_ensure_log_dir() / LOG_FILE_DATA)
    handler.setLevel(logging.WARNING) # Only warnings and above for ingestion
    formatter = logging.Formatter(FORMAT_STRING, datefmt=DATE_FORMAT)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Also add a console handler for immediate feedback during development
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.WARNING)
    console.setFormatter(formatter)
    logger.addHandler(console)

    return logger


def get_statistical_logger(name: str = "statistics") -> logging.Logger:
    """
    Returns a logger specifically for statistical results.
    Logs are written to logs/statistical_results.log.
    """
    if not _initialized:
        setup_logging()

    logger = logging.getLogger(f"llmXive.{name}")
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    # Handler for statistical results
    handler = logging.FileHandler(_ensure_log_dir() / LOG_FILE_STATS)
    handler.setLevel(logging.INFO) # Capture info and above
    formatter = logging.Formatter(FORMAT_STRING, datefmt=DATE_FORMAT)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Console handler for results
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    logger.addHandler(console)

    return logger


def log_data_ingestion_warning(logger: Optional[logging.Logger] = None, message: str = "", row_id: Optional[int] = None) -> None:
    """
    Logs a warning for data ingestion issues.
    Format: [US1] Dropped row {row_id}: missing coordinate
    """
    if logger is None:
        logger = get_data_ingestion_logger()
    
    if row_id is not None:
        formatted_msg = f"[US1] Dropped row {row_id}: {message}"
    else:
        formatted_msg = f"[US1] {message}"
    
    logger.warning(formatted_msg)


def log_statistical_result(logger: Optional[logging.Logger] = None, metric_name: str = "", value: Any = "", p_value: Optional[float] = None) -> None:
    """
    Logs a statistical result.
    """
    if logger is None:
        logger = get_statistical_logger()
    
    msg = f"[STAT] {metric_name} = {value}"
    if p_value is not None:
        msg += f" (p={p_value:.4e})"
    
    logger.info(msg)
