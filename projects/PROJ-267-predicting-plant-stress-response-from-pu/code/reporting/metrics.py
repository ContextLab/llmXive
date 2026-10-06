import os
import sys
import json
import logging
import resource
import time
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Union

from utils.logging_config import get_logger
from utils.config import get_results_path

logger = get_logger(__name__)

# Resource limits (as per T027 requirements)
MAX_RUNTIME_HOURS = 6
MAX_MEMORY_GB = 7

def get_runtime_stats() -> Dict[str, Any]:
    """Capture current runtime statistics."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    peak_memory_mb = usage.ru_maxrss  # On Linux, this is KB; on macOS, KB. Adjust if necessary.
    # Note: ru_maxrss is in KB on Linux, KB on macOS (different units on BSD).
    # Assuming Linux/standard environment where it's KB.
    peak_memory_gb = peak_memory_mb / 1024.0

    return {
        "cpu_time_seconds": usage.ru_utime + usage.ru_stime,
        "peak_memory_gb": peak_memory_gb,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

def check_resource_limits(runtime_stats: Dict[str, Any]) -> bool:
    """
    Check if runtime or memory usage exceeds limits.
    Returns True if limits are exceeded (should exit), False if safe.
    """
    cpu_time = runtime_stats["cpu_time_seconds"]
    peak_mem = runtime_stats["peak_memory_gb"]

    if cpu_time > MAX_RUNTIME_HOURS * 3600:
        logger.error(f"Resource Limit Exceeded: Runtime {cpu_time:.2f}s > {MAX_RUNTIME_HOURS}h")
        return True
    if peak_mem > MAX_MEMORY_GB:
        logger.error(f"Resource Limit Exceeded: Memory {peak_mem:.2f}GB > {MAX_MEMORY_GB}GB")
        return True
    return False

def validate_input_data(data: Union[Dict, np.ndarray, list, None]) -> bool:
    """
    Sanitization check to verify input data is not a mock object or degenerate.
    
    Checks:
    1. Data is not None.
    2. If array-like, checks for non-zero variance (at least one column/element varies).
    3. If dict, checks for required keys and non-empty values.
    
    Returns:
        bool: True if data is valid, False if it appears to be mock/degenerate.
    
    Raises:
        ValueError: If data fails validation (fails loudly).
    """
    if data is None:
        raise ValueError("Input data is None. Cannot write metrics for missing data.")

    # Case 1: Numpy array or list
    if isinstance(data, (np.ndarray, list)):
        arr = np.array(data)
        if arr.size == 0:
            raise ValueError("Input data is empty. Cannot write metrics for empty data.")
        
        # Check variance
        # Flatten if multi-dimensional to check global variance, or check per column if 2D
        if arr.ndim == 1:
            var = np.var(arr)
            if var == 0:
                raise ValueError("Input data has zero variance (constant values). Likely mock or degenerate data.")
        else:
            # Check if any column has variance
            if arr.shape[1] == 0:
                raise ValueError("Input data has no columns.")
            col_vars = np.var(arr, axis=0)
            if np.all(col_vars == 0):
                raise ValueError("All columns in input data have zero variance. Likely mock or degenerate data.")
        
        return True

    # Case 2: Dictionary (common for metrics inputs)
    if isinstance(data, dict):
        if len(data) == 0:
            raise ValueError("Input data dictionary is empty.")
        
        # Check for common mock indicators
        # If it's a metrics dict, it should have keys like 'R2', 'RMSE', 'metrics', etc.
        # We check that values are not None and not empty lists
        for key, value in data.items():
            if value is None:
                raise ValueError(f"Input data contains None value for key '{key}'.")
            if isinstance(value, (list, np.ndarray)) and len(value) == 0:
                raise ValueError(f"Input data contains empty list/array for key '{key}'.")
            
            # If the dict is supposed to contain arrays, check variance
            if isinstance(value, (np.ndarray, list)):
                arr = np.array(value)
                if arr.size > 0:
                    if np.var(arr) == 0 and arr.size > 1:
                        # If a single value, variance is 0 but that's okay. 
                        # If multiple identical values, it's suspicious but maybe valid.
                        # We flag it as a warning or error depending on strictness.
                        # Per task: "verifies input data is not a mock object (e.g., non-zero variance)"
                        # We enforce non-zero variance for multi-element arrays.
                        if arr.size > 1:
                            raise ValueError(f"Input data array for key '{key}' has zero variance (constant values).")
        
        return True

    # Case 3: Other objects (e.g., Pandas DataFrame)
    # Try to convert to array to check variance
    try:
        if hasattr(data, 'values'):
            arr = data.values
        elif hasattr(data, 'to_numpy'):
            arr = data.to_numpy()
        else:
            arr = np.asarray(data)
        
        if arr.size == 0:
            raise ValueError("Input data converts to empty array.")
        
        if arr.ndim > 1 and arr.shape[1] > 0:
            col_vars = np.var(arr, axis=0)
            if np.all(col_vars == 0) and arr.shape[0] > 1:
                raise ValueError("Input data has zero variance across all columns. Likely mock data.")
        elif arr.ndim == 1:
            if np.var(arr) == 0 and arr.size > 1:
                raise ValueError("Input data has zero variance. Likely mock data.")
        
        return True
    except Exception as e:
        # If we can't convert or check, it might be a custom mock object
        raise ValueError(f"Input data type {type(data)} could not be validated. It may be a mock object. Error: {str(e)}")

def write_metrics_report(stats: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Write runtime metrics to JSON file.
    
    Args:
        stats: Dictionary of runtime statistics.
        output_path: Optional path to write to. Defaults to results/runtime_metrics.json.
    
    Returns:
        Path to the written file.
    """
    if output_path is None:
        output_path = get_results_path() / "runtime_metrics.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Metrics report written to {output_path}")
    return output_path

def run_metrics_check(data: Optional[Union[Dict, np.ndarray, list]] = None) -> Dict[str, Any]:
    """
    Main entry point for the metrics check task (T029).
    
    1. Validates input data (sanity check).
    2. Captures runtime stats.
    3. Checks resource limits.
    4. Writes report.
    
    Args:
        data: The data artifact to validate before writing metrics.
    
    Returns:
        Dictionary of the final metrics report.
    """
    logger.info("Starting metrics check (T029)...")
    
    # 1. Sanity Check: Validate input data is not a mock object
    if data is not None:
        try:
            validate_input_data(data)
            logger.info("Input data validation passed (non-zero variance, not None).")
        except ValueError as e:
            logger.error(f"Input data validation failed: {str(e)}")
            raise  # Fail loudly
    else:
        # If no data is provided, we still run stats but log a warning
        logger.warning("No input data provided for validation. Skipping data sanity check.")
    
    # 2. Get Runtime Stats
    stats = get_runtime_stats()
    
    # 3. Check Resource Limits
    if check_resource_limits(stats):
        logger.error("Resource limits exceeded. Exiting with error.")
        sys.exit(1)
    
    # 4. Write Report
    write_metrics_report(stats)
    
    return stats

def main():
    """
    CLI entry point.
    Expects optional data path or flag to run self-check.
    """
    # For T029, we primarily run the check.
    # If this script is run as a standalone, we might not have the 'data' artifact yet.
    # We run the stats and check, but skip data validation if no data is passed.
    # In the actual pipeline (generate_report.py), data will be passed.
    
    logger.info("Running metrics check as standalone (T029).")
    try:
        # Run without data to test the stats and limits logic
        # In a real pipeline, data would be passed here
        run_metrics_check(data=None)
    except Exception as e:
        logger.error(f"Metrics check failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()