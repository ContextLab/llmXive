import os
import sys
import gc
import logging
import resource
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any

# Import existing logging utilities
try:
    from src.utils.logging import get_logger
except ImportError:
    # Fallback for execution context where src might not be in path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from src.utils.logging import get_logger

SC_004_MEMORY_LIMIT_GB = 7.0
SC_004_MEMORY_LIMIT_BYTES = SC_004_MEMORY_LIMIT_GB * (1024 ** 3)

def get_peak_memory_usage_bytes() -> int:
    """
    Returns the peak memory usage of the current process in bytes.
    Uses resource.getrusage for Unix-like systems.
    Falls back to a rough estimation for Windows if resource module is unavailable.
    """
    if sys.platform != 'win32':
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in kilobytes on Linux/macOS
        return usage.ru_maxrss * 1024
    else:
        # Fallback for Windows (approximate)
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().peak_wset
        except ImportError:
            logging.warning("psutil not available on Windows. Returning current RSS.")
            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024 if hasattr(resource, 'getrusage') else 0

def get_peak_memory_usage_gb() -> float:
    """Returns peak memory usage in GB."""
    return get_peak_memory_usage_bytes() / (1024 ** 3)

def log_memory_usage(logger: logging.Logger, stage: str = "Processing") -> None:
    """
    Logs the current peak memory usage for a given stage.
    """
    peak_gb = get_peak_memory_usage_gb()
    logger.info(f"[Memory Stats] {stage}: Peak memory usage: {peak_gb:.2f} GB")
    return peak_gb

def log_excluded_entries(logger: logging.Logger, excluded_entries: List[Dict[str, Any]], reason: str = "Validation Failure") -> None:
    """
    Logs details about excluded entries to satisfy the requirement for
    logging excluded entries during dataset validation.
    """
    count = len(excluded_entries)
    if count > 0:
        logger.warning(f"Excluded {count} entries due to {reason}.")
        # Log a sample of the first few excluded entries for debugging
        sample_size = min(5, count)
        for i, entry in enumerate(excluded_entries[:sample_size]):
            # Sanitize log to avoid printing massive code blocks
            safe_entry = {k: str(v)[:100] + "..." if len(str(v)) > 100 else str(v) for k, v in entry.items()}
            logger.debug(f"Excluded entry sample {i+1}/{sample_size}: {safe_entry}")
        
        if count > sample_size:
            logger.warning(f"... and {count - sample_size} more excluded entries.")
    else:
        logger.info("No entries excluded due to validation.")

def validate_and_log_memory_constraint(logger: logging.Logger, current_peak_gb: float) -> bool:
    """
    Validates current memory usage against SC-004 constraint (7GB).
    Returns True if within limits, False otherwise.
    Logs the result.
    """
    if current_peak_gb > SC_004_MEMORY_LIMIT_GB:
        logger.error(f"[SC-004 Violation] Peak memory {current_peak_gb:.2f} GB exceeds limit {SC_004_MEMORY_LIMIT_GB} GB.")
        return False
    else:
        logger.info(f"[SC-004 Compliant] Peak memory {current_peak_gb:.2f} GB is within limit {SC_004_MEMORY_LIMIT_GB} GB.")
        return True

def main():
    """
    Entry point for testing/logging utilities independently.
    """
    logger = get_logger(__name__)
    logger.info("Enhance Logging Module loaded.")
    log_memory_usage(logger, "Module Load Check")

if __name__ == "__main__":
    main()