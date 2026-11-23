"""
Memory Logger for the llmXive pipeline.

This module provides functionality to measure peak memory usage during
the execution of the full pipeline and log the results to a JSON file.
It explicitly compares the measured memory against the 7GB limit (SC-005).
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Attempt to import resource for memory tracking (Unix-like systems)
# For Windows, we will attempt to use psutil if available, or fall back to a warning
try:
    import resource
    HAS_RESOURCE = True
except ImportError:
    HAS_RESOURCE = False

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from utils.config import get_project_root, get_path, ensure_dir

logger = logging.getLogger(__name__)

MEMORY_LIMIT_GB = 7.0


def get_peak_memory_gb() -> float:
    """
    Measure the peak memory usage of the current process in GB.

    Returns:
        float: Peak memory usage in GB.

    Raises:
        RuntimeError: If no supported memory measurement method is available.
    """
    peak_bytes = 0.0

    if HAS_PSUTIL:
        # psutil is generally more portable and accurate across platforms
        process = psutil.Process(os.getpid())
        # rusage is not available in psutil, but memory_info().rss is current
        # psutil does not natively track "peak" RSS in a cross-platform way easily
        # without /proc on Linux. Let's try resource first for Unix, then psutil for current.
        # However, for "peak" specifically, resource.ru_maxrss is the standard on Unix.
        # We will prioritize resource if available, else psutil (current only, with a note).
        pass

    if HAS_RESOURCE:
        # Unix-like systems (Linux, macOS)
        # resource.getrusage(resource.RUSAGE_SELF).ru_maxrss is in KB on Linux,
        # but in bytes on some BSDs/macOS? Actually on macOS it's bytes, on Linux KB.
        # Linux: ru_maxrss is in kilobytes.
        # macOS: ru_maxrss is in bytes.
        # We need to detect the platform or try to be safe.
        # Standard Linux: KB.
        r_usage = resource.getrusage(resource.RUSAGE_SELF)
        max_rss = r_usage.ru_maxrss

        # Heuristic: If the value is very large ( > 10GB in KB), it might be bytes.
        # 10GB in KB is ~10,000,000.
        # 10GB in bytes is ~10,000,000,000.
        # On Linux, typical values are in the thousands/millions (KB).
        # Let's assume Linux behavior (KB) unless it looks like bytes.
        # A safer check: if max_rss > 100_000_000 (100GB in KB? unlikely), assume bytes.
        # Actually, standard practice:
        if sys.platform.startswith('linux'):
            peak_bytes = max_rss * 1024
        elif sys.platform == 'darwin':
            # macOS reports in bytes
            peak_bytes = max_rss
        else:
            # Fallback: assume KB (Linux default)
            peak_bytes = max_rss * 1024

    elif HAS_PSUTIL:
        # Fallback to psutil if resource is not available (e.g., Windows)
        # Note: psutil.Process.memory_info().rss is *current*, not peak.
        # We will log a warning that peak is not available and use current as a proxy.
        process = psutil.Process(os.getpid())
        current_rss = process.memory_info().rss
        logger.warning(
            "Running on Windows or non-Unix system without 'resource' module. "
            "Using current RSS as a proxy for peak memory. 'peak_memory_gb' may be inaccurate."
        )
        peak_bytes = current_rss
    else:
        raise RuntimeError(
            "Cannot measure memory usage: 'resource' module (Unix) and 'psutil' are not available. "
            "Install psutil or run on a Unix-like system."
        )

    return peak_bytes / (1024 ** 3)


def log_memory_usage(output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Measure peak memory, compare against limit, and log to JSON.

    Args:
        output_path: Optional path to the output JSON file.
                     Defaults to data/processed/memory_log.json.

    Returns:
        Dict containing the log data.
    """
    if output_path is None:
        project_root = get_project_root()
        output_path = str(project_root / "data" / "processed" / "memory_log.json")

    ensure_dir(output_path)

    try:
        peak_memory_gb = get_peak_memory_gb()
    except RuntimeError as e:
        logger.error(f"Failed to measure memory: {e}")
        # Still write a log indicating failure to measure, but limit_exceeded is unknown/false
        # or we can set it to true to block? The task says "measure... and compare".
        # If we can't measure, we can't verify. We'll log the error.
        result = {
            "status": "error",
            "error_message": str(e),
            "peak_memory_gb": None,
            "limit_gb": MEMORY_LIMIT_GB,
            "limit_exceeded": False, # Cannot determine
            "message": "Memory measurement failed."
        }
    else:
        limit_exceeded = peak_memory_gb > MEMORY_LIMIT_GB
        result = {
            "status": "success",
            "peak_memory_gb": round(peak_memory_gb, 4),
            "limit_gb": MEMORY_LIMIT_GB,
            "limit_exceeded": limit_exceeded,
            "message": "Memory limit check completed."
        }

        if limit_exceeded:
            logger.warning(
                f"Peak memory usage ({peak_memory_gb:.4f} GB) exceeded the limit ({MEMORY_LIMIT_GB} GB)."
            )
        else:
            logger.info(
                f"Peak memory usage ({peak_memory_gb:.4f} GB) is within the limit ({MEMORY_LIMIT_GB} GB)."
            )

    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Memory log written to {output_path}")

    return result


def main():
    """Entry point for the memory logger script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    log_memory_usage()


if __name__ == "__main__":
    main()
