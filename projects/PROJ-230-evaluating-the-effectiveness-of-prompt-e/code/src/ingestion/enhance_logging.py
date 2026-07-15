"""
T016: Add logging for excluded entries and memory usage statistics.

This module extends the logging capabilities for the ingestion pipeline to:
1. Log detailed information about entries excluded during validation.
2. Log peak memory usage statistics against the SC-004 constraint (7GB).
3. Integrate with the existing structured JSON logging system.
"""

import os
import sys
import gc
import logging
import resource
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import existing utilities from the project API surface
from src.utils.logging import get_logger, JsonFormatter

# Constants
MEMORY_LIMIT_GB = 7.0
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_GB * 1024 ** 3


def get_peak_memory_usage_bytes() -> int:
    """
    Get the peak memory usage of the current process in bytes.

    Uses resource.getrusage for Unix-like systems.
    Falls back to a lower-resolution estimate on Windows.

    Returns:
        int: Peak memory usage in bytes.
    """
    if sys.platform != 'win32':
        # ru_maxrss is in kilobytes on Linux/macOS
        usage = resource.getrusage(resource.RUSAGE_SELF)
        return usage.ru_maxrss * 1024
    else:
        # Fallback for Windows (less accurate, uses current memory)
        # Note: A proper Windows implementation would use psutil or similar
        # For now, we return current memory usage as an approximation
        try:
            import psutil
            return psutil.Process().memory_info().peak_wset
        except ImportError:
            # If psutil is not available, return 0 to indicate failure
            logging.warning("psutil not available for Windows memory tracking")
            return 0


def get_peak_memory_usage_gb() -> float:
    """
    Get the peak memory usage of the current process in gigabytes.

    Returns:
        float: Peak memory usage in GB.
    """
    return get_peak_memory_usage_bytes() / (1024 ** 3)


def log_memory_usage(logger: logging.Logger, context: str = "General") -> None:
    """
    Log the current peak memory usage statistics.

    Args:
        logger: The logger instance to use.
        context: A string describing the context of the measurement (e.g., "Preprocessing", "Validation").
    """
    peak_bytes = get_peak_memory_usage_bytes()
    peak_gb = peak_bytes / (1024 ** 3)
    limit_gb = MEMORY_LIMIT_GB

    logger.info(
        f"Memory Usage - {context}",
        extra={
            "event": "memory_usage",
            "context": context,
            "peak_memory_bytes": peak_bytes,
            "peak_memory_gb": round(peak_gb, 4),
            "limit_memory_gb": limit_gb,
            "within_limit": peak_gb <= limit_gb,
            "utilization_percent": round((peak_gb / limit_gb) * 100, 2)
        }
    )

    if peak_gb > limit_gb:
        logger.warning(
            f"CRITICAL: Peak memory usage ({peak_gb:.2f} GB) exceeds SC-004 limit ({limit_gb} GB)",
            extra={
                "event": "memory_limit_exceeded",
                "context": context,
                "peak_memory_gb": round(peak_gb, 4),
                "limit_memory_gb": limit_gb
            }
        )


def log_excluded_entries(
    logger: logging.Logger,
    excluded_entries: List[Dict[str, Any]],
    source_file: Optional[str] = None,
    reason_category: str = "validation"
) -> None:
    """
    Log detailed information about excluded entries.

    This function logs the count of excluded entries and a sample of the entries
    themselves to help with debugging and understanding data quality issues.

    Args:
        logger: The logger instance to use.
        excluded_entries: A list of dictionaries representing the excluded entries.
        source_file: The source file path where the data came from (optional).
        reason_category: A category for the exclusion reason (e.g., "validation", "filtering").
    """
    count = len(excluded_entries)

    if count == 0:
        logger.info(
            "No entries were excluded",
            extra={
                "event": "excluded_entries",
                "reason_category": reason_category,
                "count": 0,
                "source_file": source_file
            }
        )
        return

    # Log summary
    logger.info(
        f"Excluded {count} entries during {reason_category}",
        extra={
            "event": "excluded_entries_summary",
            "reason_category": reason_category,
            "count": count,
            "source_file": source_file
        }
    )

    # Log a sample of excluded entries (up to 5) for debugging
    sample_size = min(5, count)
    sample_entries = excluded_entries[:sample_size]

    for i, entry in enumerate(sample_entries):
        # Truncate large strings to avoid log flooding
        safe_entry = {}
        for key, value in entry.items():
            if isinstance(value, str) and len(value) > 200:
                safe_entry[key] = value[:200] + "..."
            else:
                safe_entry[key] = value

        logger.warning(
            f"Excluded entry sample [{i+1}/{sample_size}]",
            extra={
                "event": "excluded_entry_sample",
                "sample_index": i + 1,
                "total_excluded": count,
                "entry_data": safe_entry,
                "reason_category": reason_category,
                "source_file": source_file
            }
        )

    # If there are more than 5, log a summary
    if count > 5:
        logger.info(
            f"Showing 5 of {count} excluded entries. Check validation logs for full details.",
            extra={
                "event": "excluded_entries_truncated",
                "showing": 5,
                "total": count,
                "reason_category": reason_category
            }
        )


def validate_and_log_memory_constraint(
    logger: logging.Logger,
    current_usage_gb: float,
    context: str = "Validation"
) -> bool:
    """
    Validate that current memory usage is within the SC-004 constraint and log the result.

    Args:
        logger: The logger instance to use.
        current_usage_gb: The current memory usage in GB.
        context: The context of the validation (e.g., "Preprocessing", "Sampling").

    Returns:
        bool: True if within limits, False otherwise.
    """
    within_limit = current_usage_gb <= MEMORY_LIMIT_GB

    logger.info(
        f"Memory constraint check ({context})",
        extra={
            "event": "memory_constraint_check",
            "context": context,
            "current_memory_gb": round(current_usage_gb, 4),
            "limit_memory_gb": MEMORY_LIMIT_GB,
            "within_limit": within_limit,
            "constraint_id": "SC-004"
        }
    )

    if not within_limit:
        logger.error(
            f"SC-004 Constraint Violation: Memory usage ({current_usage_gb:.2f} GB) exceeds limit ({MEMORY_LIMIT_GB} GB)",
            extra={
                "event": "constraint_violation",
                "constraint_id": "SC-004",
                "context": context,
                "current_memory_gb": round(current_usage_gb, 4),
                "limit_memory_gb": MEMORY_LIMIT_GB
            }
        )

    return within_limit


def main():
    """
    Main function to demonstrate the enhanced logging functionality.
    This can be used for testing or as a standalone utility.
    """
    logger = get_logger(__name__)

    logger.info("Enhanced Logging Module Initialized", extra={"event": "module_init"})

    # Log initial memory usage
    log_memory_usage(logger, "Initialization")

    # Simulate some data processing
    logger.info("Simulating data processing...", extra={"event": "simulation_start"})

    # Create some dummy data to simulate memory usage
    dummy_data = [i * 1000 for i in range(100000)]
    gc.collect()

    # Log memory after processing
    log_memory_usage(logger, "After Data Processing")

    # Log some excluded entries
    sample_excluded = [
        {"id": 1, "reason": "Missing python_code", "data": {"javascript_code": "console.log('test');"}},
        {"id": 2, "reason": "Non-string type", "data": {"python_code": 123, "javascript_code": "console.log('test');"}},
        {"id": 3, "reason": "Empty code", "data": {"python_code": "", "javascript_code": ""}}
    ]
    log_excluded_entries(logger, sample_excluded, source_file="data/raw/sample.csv", reason_category="validation")

    # Validate memory constraint
    current_gb = get_peak_memory_usage_gb()
    is_valid = validate_and_log_memory_constraint(logger, current_gb, "Final Check")

    if is_valid:
        logger.info("All checks passed successfully", extra={"event": "validation_success"})
    else:
        logger.error("Validation failed due to memory constraints", extra={"event": "validation_failure"})

    return is_valid


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)