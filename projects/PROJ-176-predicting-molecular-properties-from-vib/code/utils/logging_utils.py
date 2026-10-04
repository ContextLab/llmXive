"""
Logging utilities for the molecular properties prediction pipeline.
Provides setup functions and specialized loggers for data ingestion steps.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

def setup_logging(
    log_dir: Path,
    level: int = logging.INFO,
    console: bool = True,
    file: bool = True
) -> logging.Logger:
    """
    Set up logging configuration for the project.

    Args:
        log_dir: Directory where log files will be stored.
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
        console: Whether to log to console.
        file: Whether to log to file.

    Returns:
        Configured logger instance.
    """
    # Ensure log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger("molecular_properties")
    logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"pipeline_{timestamp}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

def get_logger(name: str = "molecular_properties") -> logging.Logger:
    """
    Get a logger instance by name.

    Args:
        name: Name of the logger.

    Returns:
        Logger instance.
    """
    return logging.getLogger(name)

def log_data_ingestion_step(
    logger: logging.Logger,
    step_name: str,
    mismatch_count: int = 0,
    download_size_bytes: int = 0,
    filtered_count: int = 0,
    level: int = logging.INFO
) -> None:
    """
    Log a data ingestion step with structured information.

    Args:
        logger: Logger instance to use.
        step_name: Name of the ingestion step.
        mismatch_count: Number of mismatched records.
        download_size_bytes: Size of downloaded data in bytes.
        filtered_count: Number of filtered records.
        level: Logging level.
    """
    log_message = (
        f"Data Ingestion Step: {step_name} | "
        f"Mismatches: {mismatch_count} | "
        f"Download Size: {download_size_bytes} bytes | "
        f"Filtered: {filtered_count}"
    )
    logger.log(level, log_message)

def log_coverage_audit_result(
    logger: logging.Logger,
    property_name: str,
    p_value: float,
    statistic: float,
    threshold: float = 0.05,
    level: int = logging.INFO
) -> None:
    """
    Log the result of a coverage audit (KS-test).

    Args:
        logger: Logger instance to use.
        property_name: Name of the property being audited.
        p_value: P-value from the KS-test.
        statistic: KS-test statistic.
        threshold: Significance threshold for the test.
        level: Logging level.
    """
    is_significant = p_value < threshold
    status = "WARNING: Selection bias detected" if is_significant else "OK: No significant bias"

    log_message = (
        f"Coverage Audit: {property_name} | "
        f"P-value: {p_value:.4f} | "
        f"Statistic: {statistic:.4f} | "
        f"Threshold: {threshold} | "
        f"Status: {status}"
    )
    logger.log(level, log_message)
