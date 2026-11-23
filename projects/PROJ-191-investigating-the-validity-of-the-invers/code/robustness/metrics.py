"""
T033: Calculate robustness metrics for the inverse-square law investigation.

This module computes:
1. Coefficient of Variation (CV) of the credible upper limits (95th percentile).
2. Relative shift of the credible upper limits across robustness iterations.
3. Verification against the acceptance criterion (relative_shift < 0.15).

Dependencies:
- T030 (cross_val.py): Must have produced `data/results/cross_val_results.json`
  containing the list of 95% credible upper limits for alpha.
"""

import os
import sys
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from config import get_logger, ProjectConfig

logger = get_logger("robustness.metrics")

# Constants
THRESHOLD_RELATIVE_SHIFT = 0.15
CROSS_VAL_RESULTS_PATH = "data/results/cross_val_results.json"
OUTPUT_METRICS_PATH = "data/results/robustness_metrics.json"


def load_cv_results() -> List[float]:
    """
    Load the credible upper limits (95th percentile) from the cross-validation results.

    Returns:
        List[float]: A list of alpha_95 limits from each iteration.

    Raises:
        FileNotFoundError: If the cross-validation results file does not exist.
        ValueError: If the file exists but contains no valid limit data.
    """
    config = ProjectConfig()
    results_path = config.root_dir / CROSS_VAL_RESULTS_PATH

    if not results_path.exists():
        raise FileNotFoundError(
            f"Cross-validation results not found at {results_path}. "
            "Ensure T030 (cross_val.py) has been executed successfully."
        )

    with open(results_path, "r") as f:
        data = json.load(f)

    # Expected structure: {"iterations": [{"alpha_95_upper": ...}, ...]}
    # or potentially a flat list depending on T030 output format.
    # We handle the most likely structure from T030.
    iterations = data.get("iterations", [])
    
    if not iterations:
        # Check if it's a flat list directly
        if isinstance(data, list):
            iterations = data
        else:
            raise ValueError(f"Invalid format in {results_path}: no 'iterations' key or list found.")

    limits = []
    for item in iterations:
        if isinstance(item, dict):
            val = item.get("alpha_95_upper")
            if val is None:
                # Try alternative keys if T030 used different naming
                val = item.get("credible_limit_95")
                val = item.get("limit", val)
        elif isinstance(item, (int, float)):
            val = float(item)
        else:
            logger.warning(f"Skipping unexpected item format in cross-val results: {item}")
            continue

        if val is not None:
            limits.append(float(val))

    if not limits:
        raise ValueError("No valid alpha_95 upper limits found in cross-validation results.")

    return limits


def calculate_robustness_metrics(limits: List[float]) -> Dict[str, Any]:
    """
    Calculate the robustness metrics: CV and relative shift.

    Args:
        limits: List of 95% credible upper limits for alpha.

    Returns:
        Dictionary containing:
            - cv_value: Coefficient of Variation (std / mean * 100)
            - relative_shift: (max - min) / mean
            - threshold: The acceptance threshold (0.15)
            - pass: Boolean indicating if relative_shift < threshold
            - mean_limit: Mean of the limits
            - std_limit: Standard deviation of the limits
            - min_limit: Minimum limit
            - max_limit: Maximum limit
            - count: Number of iterations
    """
    arr = np.array(limits)
    
    if len(arr) < 2:
        logger.warning("Less than 2 iterations found. Metrics may be undefined.")
        # Handle edge case: if only 1 point, shift is 0, CV is 0/mean = 0
        if len(arr) == 1:
            mean_val = arr[0]
            std_val = 0.0
            min_val = arr[0]
            max_val = arr[0]
        else:
            mean_val = 0.0
            std_val = 0.0
            min_val = 0.0
            max_val = 0.0
    else:
        mean_val = float(np.mean(arr))
        std_val = float(np.std(arr))
        min_val = float(np.min(arr))
        max_val = float(np.max(arr))

    # Calculate CV (Coefficient of Variation)
    # Avoid division by zero if mean is 0
    if mean_val == 0.0:
        cv_value = 0.0 if std_val == 0.0 else float('inf')
    else:
        cv_value = (std_val / mean_val) * 100.0

    # Calculate Relative Shift
    # (max - min) / mean
    if mean_val == 0.0:
        if (max_val - min_val) == 0.0:
            relative_shift = 0.0
        else:
            relative_shift = float('inf')
    else:
        relative_shift = (max_val - min_val) / mean_val

    pass_status = relative_shift < THRESHOLD_RELATIVE_SHIFT

    return {
        "cv_value": cv_value,
        "relative_shift": relative_shift,
        "threshold": THRESHOLD_RELATIVE_SHIFT,
        "pass": pass_status,
        "mean_limit": mean_val,
        "std_limit": std_val,
        "min_limit": min_val,
        "max_limit": max_val,
        "count": len(arr),
        "status": "stable" if pass_status else "unstable"
    }


def save_metrics(metrics: Dict[str, Any], output_path: str) -> None:
    """
    Save the calculated metrics to a JSON file.

    Args:
        metrics: Dictionary of calculated metrics.
        output_path: Relative path for the output file.
    """
    config = ProjectConfig()
    full_path = config.root_dir / output_path
    
    # Ensure directory exists
    full_path.parent.mkdir(parents=True, exist_ok=True)

    with open(full_path, "w") as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Robustness metrics saved to {full_path}")


def main() -> int:
    """
    Main entry point for T033.

    1. Loads results from T030 (cross_val.py).
    2. Calculates CV and relative shift.
    3. Checks against the 0.15 threshold.
    4. Writes `data/results/robustness_metrics.json`.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        logger.info("Starting robustness metrics calculation (T033).")
        
        # Load data
        limits = load_cv_results()
        logger.info(f"Loaded {len(limits)} credible upper limits from cross-validation.")

        # Calculate metrics
        metrics = calculate_robustness_metrics(limits)
        
        # Log results
        logger.info(f"Calculated CV: {metrics['cv_value']:.4f}%")
        logger.info(f"Calculated Relative Shift: {metrics['relative_shift']:.4f}")
        logger.info(f"Threshold: {metrics['threshold']}")
        logger.info(f"Result: {'PASS' if metrics['pass'] else 'FAIL'} - Status: {metrics['status']}")

        if not metrics['pass']:
            logger.warning("Robustness check FAILED: Relative shift exceeds 15%. Results may be unstable.")

        # Save output
        save_metrics(metrics, OUTPUT_METRICS_PATH)

        return 0

    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during metrics calculation: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
