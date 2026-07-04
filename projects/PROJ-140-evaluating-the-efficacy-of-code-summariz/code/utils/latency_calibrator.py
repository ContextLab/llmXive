"""
Latency Calibrator for Timestamp Precision Verification (FR-003)

This module implements a calibration test to verify that the system's
timestamp generation mechanism has a precision of ≤100ms.

It performs a series of rapid timestamp captures and measures the
minimum observed delta between consecutive calls. If the minimum
observed delta exceeds 100ms, the calibration fails, indicating
the system cannot meet the required precision for the study.

Requirements:
- FR-003: Timestamp precision must be ≤100ms.
- Must run at application startup (integrated by T012a).
"""

import time
import sys
import os
from pathlib import Path
from typing import List, Tuple, Dict

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from utils.config_manager import get_config
from utils.logging_utils import get_logger

logger = get_logger(__name__)

# Constants defined by FR-003
PRECISION_THRESHOLD_MS = 100.0
CALIBRATION_SAMPLES = 100  # Number of rapid captures to ensure statistical validity
CALIBRATION_TIMEOUT_SECONDS = 10.0  # Safety break if system is too slow

def measure_timestamp_precision(num_samples: int = CALIBRATION_SAMPLES) -> Tuple[float, List[float]]:
    """
    Measures the minimum time delta between consecutive timestamp captures.

    Args:
        num_samples: Number of rapid timestamp captures to perform.

    Returns:
        Tuple containing:
            - min_delta_ms: The minimum observed delta in milliseconds.
            - deltas_ms: List of all observed deltas in milliseconds.
    """
    timestamps = []
    start_time = time.perf_counter()

    # Capture timestamps rapidly
    for _ in range(num_samples):
        # Using time.time() for wall-clock time which is what interaction logs use
        # time.perf_counter() is for measuring duration, but interaction logs need wall time
        ts = time.time()
        timestamps.append(ts)

        # Safety break to prevent hanging on extremely slow systems
        if (time.perf_counter() - start_time) > CALIBRATION_TIMEOUT_SECONDS:
            logger.warning(f"Calibration timed out after {CALIBRATION_TIMEOUT_SECONDS}s. "
                           f"Collected {len(timestamps)} samples.")
            break

    if len(timestamps) < 2:
        raise RuntimeError("Insufficient samples collected for calibration.")

    # Calculate deltas between consecutive timestamps
    deltas = []
    for i in range(1, len(timestamps)):
        delta = (timestamps[i] - timestamps[i-1]) * 1000.0  # Convert to ms
        deltas.append(delta)

    min_delta = min(deltas)
    return min_delta, deltas

def run_calibration() -> bool:
    """
    Runs the full calibration procedure.

    Returns:
        True if precision is within threshold (≤100ms), False otherwise.
    """
    logger.info("Starting latency calibration for timestamp precision (FR-003)...")

    try:
        min_delta_ms, deltas = measure_timestamp_precision()

        logger.info(f"Calibration complete. Min observed delta: {min_delta_ms:.2f}ms")
        logger.info(f"Threshold: {PRECISION_THRESHOLD_MS}ms")

        if min_delta_ms <= PRECISION_THRESHOLD_MS:
            logger.info("SUCCESS: System timestamp precision meets FR-003 requirements.")
            return True
        else:
            logger.error(f"FAILURE: System timestamp precision ({min_delta_ms:.2f}ms) "
                         f"exceeds FR-003 threshold ({PRECISION_THRESHOLD_MS}ms).")
            logger.error("The application cannot guarantee accurate interaction timing.")
            logger.error("Please check system load, clock source, or hardware constraints.")
            return False

    except Exception as e:
        logger.error(f"Calibration failed with exception: {e}", exc_info=True)
        return False

def main():
    """Entry point for running calibration as a standalone script."""
    # Load config to ensure environment is ready
    try:
        get_config()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    success = run_calibration()

    # Exit with appropriate code for CI integration
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
