"""
Logging configuration for ingestion steps.

This module provides utility functions to log ingestion steps including
download status, filter counts, and harmonization results.
"""
import logging
from typing import Dict, Any, Optional
from src.utils.logger import get_logger

# Define log categories for ingestion
LOG_DOWNLOAD = "ingestion.download"
LOG_FILTER = "ingestion.filter"
LOG_HARMONIZE = "ingestion.harmonize"
LOG_VALIDATION = "ingestion.validation"

def get_ingestion_logger(category: str) -> logging.Logger:
    """
    Get a logger configured for a specific ingestion category.
    
    Args:
        category: One of LOG_DOWNLOAD, LOG_FILTER, LOG_HARMONIZE, LOG_VALIDATION
        
    Returns:
        Configured logger instance
    """
    return get_logger(category)

def log_download_status(logger: logging.Logger, source: str, status: str, 
                         file_size: Optional[int] = None, 
                         checksum: Optional[str] = None) -> None:
    """
    Log download status for a data source.
    
    Args:
        logger: Logger instance to use
        source: Name/URL of the data source
        status: Status of the download (e.g., 'SUCCESS', 'FAILED', 'SKIPPED')
        file_size: Size of downloaded file in bytes (optional)
        checksum: SHA256 checksum of downloaded file (optional)
    """
    msg = f"Download status | source={source} | status={status}"
    if file_size is not None:
        msg += f" | size={file_size} bytes"
    if checksum is not None:
        msg += f" | checksum={checksum}"
    
    if status == "SUCCESS":
        logger.info(msg)
    elif status == "FAILED":
        logger.error(msg)
    else:
        logger.warning(msg)

def log_filter_counts(logger: logging.Logger, step_name: str, 
                      initial_count: int, final_count: int, 
                      excluded_count: int, reason: str) -> None:
    """
    Log filter step results.
    
    Args:
        logger: Logger instance to use
        step_name: Name of the filter step (e.g., 'read_depth', 'fiber_range')
        initial_count: Number of samples before filtering
        final_count: Number of samples after filtering
        excluded_count: Number of samples excluded
        reason: Reason for exclusion
    """
    logger.info(
        f"Filter applied | step={step_name} | "
        f"initial={initial_count} | final={final_count} | "
        f"excluded={excluded_count} | reason={reason}"
    )

def log_harmonization_result(logger: logging.Logger, 
                             source: str, 
                             column_mapping: Dict[str, str],
                             unit_conversion: Optional[Dict[str, str]] = None) -> None:
    """
    Log harmonization results for a dataset.
    
    Args:
        logger: Logger instance to use
        source: Name of the dataset source
        column_mapping: Dictionary mapping original columns to standardized columns
        unit_conversion: Dictionary showing unit conversions performed (optional)
    """
    logger.info(f"Harmonization complete | source={source}")
    logger.info(f"Column mapping: {column_mapping}")
    if unit_conversion:
        logger.info(f"Unit conversions: {unit_conversion}")

def log_merge_result(logger: logging.Logger, 
                     agp_count: int, 
                     ukbb_count: int, 
                     merged_count: int,
                     duplicate_count: int = 0) -> None:
    """
    Log dataset merge results.
    
    Args:
        logger: Logger instance to use
        agp_count: Number of samples from AGP
        ukbb_count: Number of samples from UKBB
        merged_count: Total number of samples in merged dataset
        duplicate_count: Number of duplicate samples found (optional)
    """
    logger.info(
        f"Dataset merge complete | AGP={agp_count} | UKBB={ukbb_count} | "
        f"merged={merged_count}"
    )
    if duplicate_count > 0:
        logger.warning(f"Duplicates found and handled: {duplicate_count}")

def log_validation_result(logger: logging.Logger, 
                          validation_type: str, 
                          passed: bool, 
                          details: Optional[str] = None) -> None:
    """
    Log validation results.
    
    Args:
        logger: Logger instance to use
        validation_type: Type of validation performed
        passed: Whether validation passed
        details: Additional details about the validation (optional)
    """
    status = "PASSED" if passed else "FAILED"
    msg = f"Validation {status} | type={validation_type}"
    if details:
        msg += f" | details={details}"
    
    if passed:
        logger.info(msg)
    else:
        logger.error(msg)
