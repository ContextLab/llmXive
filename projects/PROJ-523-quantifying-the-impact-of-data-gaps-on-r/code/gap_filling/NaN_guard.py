"""
NaN Propagation Guard for Gap-Filling Algorithms.

This module implements a strict validation layer that scans output maps
immediately after gap-filling. If any NaN values are detected, it raises
a NaNPropagationError to trigger the exclusion logic defined in T024.

Constraint: This guard NEVER falls back to synthetic data or interpolation
to fix NaNs. It fails loudly to ensure data integrity.
"""
import numpy as np
import logging
from typing import Union

# Configure logger
logger = logging.getLogger(__name__)

class NaNPropagationError(Exception):
    """
    Exception raised when NaN values are detected in a gap-filled map.
    This triggers the exclusion logic in T024 (failure_handler).
    """
    def __init__(self, message: str, realization_id: str = None, algo_name: str = None):
        self.realization_id = realization_id
        self.algo_name = algo_name
        super().__init__(message)

def scan_for_nans(
    data: Union[np.ndarray, list],
    realization_id: str = "unknown",
    algo_name: str = "unknown"
) -> bool:
    """
    Scans the input data array for NaN values.

    Args:
        data: The map data (numpy array or list) to scan.
        realization_id: Identifier for the current realization (for logging).
        algo_name: Name of the algorithm that produced the data (for logging).

    Returns:
        bool: True if NO NaNs are found (clean), False if NaNs are found.

    Raises:
        NaNPropagationError: Immediately if NaNs are detected.
    """
    if data is None:
        logger.error(f"NaN Guard: Data is None for {realization_id} ({algo_name})")
        raise NaNPropagationError(
            "Data is None",
            realization_id=realization_id,
            algo_name=algo_name
        )

    arr = np.asarray(data)

    # Check for NaNs
    nan_mask = np.isnan(arr)
    nan_count = np.sum(nan_mask)

    if nan_count > 0:
        error_msg = (
            f"NaN Propagation Detected: Found {nan_count} NaN values in map "
            f"for realization {realization_id} using algorithm {algo_name}. "
            f"Total pixels: {arr.size}. "
            f"This realization will be excluded from analysis."
        )
        logger.error(error_msg)
        raise NaNPropagationError(
            error_msg,
            realization_id=realization_id,
            algo_name=algo_name
        )

    # Additional sanity check for Inf (often accompanies NaN issues in numerical solvers)
    inf_mask = np.isinf(arr)
    inf_count = np.sum(inf_mask)
    if inf_count > 0:
        error_msg = (
            f"Infinity Detected: Found {inf_count} Inf values in map "
            f"for realization {realization_id} using algorithm {algo_name}. "
            f"Total pixels: {arr.size}. "
            f"This realization will be excluded from analysis."
        )
        logger.error(error_msg)
        raise NaNPropagationError(
            error_msg,
            realization_id=realization_id,
            algo_name=algo_name
        )

    logger.debug(f"NaN Guard: Map for {realization_id} ({algo_name}) is clean.")
    return True

def apply_nan_guard_wrapper(
    func,
    realization_id: str,
    algo_name: str
):
    """
    A decorator/factory to wrap gap-filling functions with NaN validation.

    Usage:
        wrapped_func = apply_nan_guard_wrapper(original_func, "real_001", "harmonic_interp")
        result = wrapped_func(input_map)

    If the wrapped function returns a map with NaNs, NaNPropagationError is raised.
    """
    def wrapper(*args, **kwargs):
        logger.info(f"Applying NaN Guard wrapper for {algo_name} on {realization_id}")
        try:
            result = func(*args, **kwargs)
            # Scan the result
            scan_for_nans(result, realization_id, algo_name)
            return result
        except NaNPropagationError:
            # Re-raise to trigger T024 exclusion logic
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {algo_name} for {realization_id}: {e}")
            raise

    return wrapper

def main():
    """
    Standalone test entry point to demonstrate the NaN guard behavior.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Test 1: Clean data
    clean_data = np.array([1.0, 2.0, 3.0, 4.0])
    try:
        scan_for_nans(clean_data, "test_clean", "mock_algo")
        print("PASS: Clean data accepted.")
    except NaNPropagationError:
        print("FAIL: Clean data rejected.")

    # Test 2: Data with NaN
    nan_data = np.array([1.0, np.nan, 3.0, 4.0])
    try:
        scan_for_nans(nan_data, "test_nan", "mock_algo")
        print("FAIL: NaN data was not caught.")
    except NaNPropagationError as e:
        print(f"PASS: NaN data caught correctly. Message: {e}")

    # Test 3: Data with Inf
    inf_data = np.array([1.0, np.inf, 3.0, 4.0])
    try:
        scan_for_nans(inf_data, "test_inf", "mock_algo")
        print("FAIL: Inf data was not caught.")
    except NaNPropagationError as e:
        print(f"PASS: Inf data caught correctly. Message: {e}")

if __name__ == "__main__":
    main()
