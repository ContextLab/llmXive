import os
import subprocess
import logging
import time
import signal
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from utils.logging import get_logger

RESULTS_DIR = Path("data/results")

def ensure_results_dir() -> Path:
    """Ensure the results directory exists."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    return RESULTS_DIR

def get_available_cores() -> int:
    """Return the number of available CPU cores."""
    return os.cpu_count() or 1

def enforce_cpu_affinity(target_cores: int = 2) -> List[int]:
    """
    Enforce CPU affinity to restrict the process to a specific number of cores.
    Returns the list of assigned core IDs.
    """
    if not PSUTIL_AVAILABLE:
        logger = get_logger(__name__)
        logger.warning("psutil not available. Cannot enforce CPU affinity programmatically.")
        return list(range(min(target_cores, get_available_cores())))

    available_cores = list(range(get_available_cores()))
    selected_cores = available_cores[:target_cores]

    process = psutil.Process(os.getpid())
    process.cpu_affinity(selected_cores)

    logger = get_logger(__name__)
    logger.info(f"Enforced CPU affinity to cores: {selected_cores}")
    return selected_cores

def log_cpu_usage(duration: float = 5.0, interval: float = 1.0) -> List[Dict[str, Any]]:
    """
    Log CPU usage percentage over a duration.
    Returns a list of dicts with timestamp and cpu_percent.
    """
    if not PSUTIL_AVAILABLE:
        logger = get_logger(__name__)
        logger.warning("psutil not available. Cannot log CPU usage.")
        return []

    process = psutil.Process(os.getpid())
    # Initialize cpu_percent call
    process.cpu_percent(interval=None)

    log_data = []
    start_time = time.time()

    while time.time() - start_time < duration:
        usage = process.cpu_percent(interval=interval)
        log_data.append({
            "timestamp": time.time(),
            "cpu_percent": usage
        })
        time.sleep(interval)

    return log_data

class cpu_limit_context:
    """
    Context manager to enforce CPU affinity and log usage within a block.
    """
    def __init__(self, target_cores: int = 2):
        self.target_cores = target_cores
        self.assigned_cores: List[int] = []
        self.logger = get_logger(__name__)

    def __enter__(self):
        self.assigned_cores = enforce_cpu_affinity(self.target_cores)
        self.logger.info(f"Entered CPU limit context. Assigned cores: {self.assigned_cores}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.info("Exited CPU limit context.")
        return False

def verify_cpu_restriction() -> Tuple[bool, str]:
    """
    Verify that the current process is restricted to exactly 2 CPU cores.
    Uses psutil to check the CPU affinity mask.
    Returns (is_restricted, message).
    """
    if not PSUTIL_AVAILABLE:
        return False, "psutil is not installed. Cannot verify CPU restriction."

    try:
        process = psutil.Process(os.getpid())
        affinity_mask = process.cpu_affinity()
        num_cores = len(affinity_mask)

        logger = get_logger(__name__)
        logger.info(f"Current CPU affinity mask: {affinity_mask} (Count: {num_cores})")

        if num_cores == 2:
            return True, f"Process is correctly restricted to {num_cores} CPU cores: {affinity_mask}"
        else:
            return False, f"Process is restricted to {num_cores} CPU cores, expected 2. Mask: {affinity_mask}"

    except Exception as e:
        return False, f"Error verifying CPU restriction: {str(e)}"

def main():
    """
    Main entry point for T048: Verify CPU core restriction.
    Runs the verification and logs the result.
    """
    logger = get_logger(__name__)
    logger.info("Starting T048: CPU Core Restriction Verification")

    is_ok, message = verify_cpu_restriction()

    if is_ok:
        logger.info(f"VERIFICATION PASSED: {message}")
    else:
        logger.warning(f"VERIFICATION FAILED: {message}")
        logger.warning("This script should be run after enforce_cpu_affinity(2) has been called.")

    return 0 if is_ok else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())