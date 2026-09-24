import os
import sys
import gc
import logging
import resource
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.utils.logging import get_logger

def get_peak_memory_usage_bytes() -> int:
    """
    Get the peak memory usage of the current process in bytes.
    Uses resource.getrusage which is POSIX compliant.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # maxrss is in kilobytes on Linux/macOS
    return usage.ru_maxrss * 1024

def get_peak_memory_usage_gb() -> float:
    """
    Get the peak memory usage of the current process in gigabytes.
    """
    return get_peak_memory_usage_bytes() / (1024 ** 3)

def log_memory_usage(logger: logging.Logger, constraint_gb: float = 7.0) -> Dict[str, Any]:
    """
    Log the current and peak memory usage statistics.
    Returns a dictionary with the stats for potential programmatic use.
    """
    peak_bytes = get_peak_memory_usage_bytes()
    peak_gb = peak_bytes / (1024 ** 3)
    current_bytes = get_peak_memory_usage_bytes() # resource doesn't give current distinct from peak easily in this call, but we log peak
    
    logger.info(f"Memory Statistics: Peak Usage = {peak_gb:.2f} GB ({peak_bytes} bytes)")
    
    stats = {
        "peak_memory_bytes": peak_bytes,
        "peak_memory_gb": peak_gb,
        "constraint_gb": constraint_gb,
        "within_limit": peak_gb <= constraint_gb
    }
    
    if not stats["within_limit"]:
        logger.warning(f"SC-004 Constraint Violation: Peak memory ({peak_gb:.2f} GB) exceeds limit ({constraint_gb} GB)")
    else:
        logger.info(f"SC-004 Constraint Satisfied: Peak memory ({peak_gb:.2f} GB) is within limit ({constraint_gb} GB)")
        
    return stats

def log_excluded_entries(logger: logging.Logger, excluded_entries: List[Dict[str, Any]], log_path: Optional[Path] = None) -> None:
    """
    Log details of excluded entries to the logger and optionally write them to a CSV file.
    
    Args:
        logger: The logger instance to use.
        excluded_entries: List of dictionaries containing details of excluded entries.
        log_path: Optional path to write the exclusion log CSV.
    """
    if not excluded_entries:
        logger.info("No entries were excluded during preprocessing.")
        return

    logger.info(f"Logging {len(excluded_entries)} excluded entries.")
    
    # Log summary to stdout
    reasons = [entry.get('reason', 'unknown') for entry in excluded_entries]
    reason_counts = {}
    for r in reasons:
        reason_counts[r] = reason_counts.get(r, 0) + 1
    
    logger.info("Exclusion Summary:")
    for reason, count in reason_counts.items():
        logger.info(f"  - {reason}: {count}")

    # Write to CSV if path provided
    if log_path:
        try:
            # Ensure directory exists
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            df = pd.DataFrame(excluded_entries)
            df.to_csv(log_path, index=False)
            logger.info(f"Exclusion log written to: {log_path}")
        except Exception as e:
            logger.error(f"Failed to write exclusion log to {log_path}: {e}")
            raise

def validate_and_log_memory_constraint(logger: logging.Logger, constraint_gb: float = 7.0) -> bool:
    """
    Validates the current peak memory usage against the SC-004 constraint.
    Logs the result and returns True if the constraint is satisfied, False otherwise.
    """
    stats = log_memory_usage(logger, constraint_gb)
    return stats["within_limit"]

def main():
    """
    Main entry point for testing logging utilities.
    """
    logger = get_logger("test_enhance_logging")
    
    # Simulate some memory usage
    data = [i for i in range(1000000)]
    gc.collect()
    
    log_memory_usage(logger)
    
    # Simulate excluded entries
    fake_excluded = [
        {"id": "1", "reason": "missing_code", "entry_preview": "..."},
        {"id": "2", "reason": "non_string_type", "entry_preview": "..."},
        {"id": "3", "reason": "missing_code", "entry_preview": "..."}
    ]
    
    log_excluded_entries(logger, fake_excluded, log_path=Path("data/processed/exclusion_log.csv"))
    
    validate_and_log_memory_constraint(logger)

if __name__ == "__main__":
    main()