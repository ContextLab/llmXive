import logging
import sys
from typing import Dict, Any, Optional
from pathlib import Path

from src.utils.logger import get_logger

# Constants for log file paths
INGESTION_LOG_PATH = Path("logs/ingestion.log")


def get_ingestion_logger() -> logging.Logger:
    """
    Retrieves or creates a logger specifically for the ingestion pipeline.
    This logger writes to both the console and the specific ingestion log file.
    """
    logger = get_logger("ingestion")

    # Avoid adding handlers multiple times if this function is called repeatedly
    if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
        # Ensure the logs directory exists
        INGESTION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(INGESTION_LOG_PATH)
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def log_download_status(logger: logging.Logger, cohort: str, status: str, details: Optional[str] = None) -> None:
    """
    Logs the status of a dataset download.

    Args:
        logger: The logger instance to use.
        cohort: The name of the cohort (e.g., 'AGP', 'UKBB').
        status: The status string (e.g., 'SUCCESS', 'FAIL').
        details: Optional additional details about the status.
    """
    message = f"Download {cohort}: {status}"
    if details:
        message += f" - {details}"
    
    if status == "SUCCESS":
        logger.info(message)
    else:
        logger.error(message)


def log_filter_counts(logger: logging.Logger, filter_type: str, count: int, reason: Optional[str] = None) -> None:
    """
    Logs the number of samples filtered out during the harmonization process.

    Args:
        logger: The logger instance to use.
        filter_type: The type of filter applied (e.g., 'Read Count', 'Fiber Intake').
        count: The number of samples removed.
        reason: Optional reason for the filter.
    """
    message = f"Filtered Samples ({filter_type}): {count}"
    if reason:
        message += f" ({reason})"
    logger.info(message)


def log_harmonization_result(logger: logging.Logger, metric: str, value: Any) -> None:
    """
    Logs a specific harmonization metric result.

    Args:
        logger: The logger instance to use.
        metric: The name of the metric (e.g., 'Unit Conversion', 'Merging').
        value: The value associated with the metric.
    """
    logger.info(f"Harmonization Result ({metric}): {value}")


def log_merge_result(logger: logging.Logger, total_samples: int, agp_samples: int, ukbb_samples: int) -> None:
    """
    Logs the final counts after merging datasets.

    Args:
        logger: The logger instance to use.
        total_samples: Total number of samples in the merged dataset.
        agp_samples: Number of samples from the AGP cohort.
        ukbb_samples: Number of samples from the UKBB cohort.
    """
    logger.info(f"Harmonized Samples: {total_samples}")
    logger.info(f"  - AGP samples: {agp_samples}")
    logger.info(f"  - UKBB samples: {ukbb_samples}")


def log_validation_result(logger: logging.Logger, check_name: str, passed: bool, details: Optional[str] = None) -> None:
    """
    Logs the result of a validation check.

    Args:
        logger: The logger instance to use.
        check_name: The name of the validation check.
        passed: Boolean indicating if the check passed.
        details: Optional details about the validation.
    """
    status = "PASSED" if passed else "FAILED"
    message = f"Validation ({check_name}): {status}"
    if details:
        message += f" - {details}"
    
    if passed:
        logger.info(message)
    else:
        logger.error(message)
