"""
Diffusion rate calculator for spin network simulations.

This module implements the calculation of diffusion rates based on the
spatial variance evolution over time steps. It provides functions to
compute the rate of change and verify numerical stability.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from code.src.simulation.metrics import calculate_spatial_variance

logger = logging.getLogger(__name__)


class DiffusionError(Exception):
    """Custom exception for diffusion calculation errors."""
    pass


def calculate_diffusion_rate(
    spatial_variance_history: List[float],
    time_steps: List[int]
) -> Dict[str, Any]:
    """
    Calculate the diffusion rate as the rate of change of spatial variance over time.

    This function computes the linear regression slope of spatial variance
    against time steps to estimate the diffusion rate.

    Args:
        spatial_variance_history: List of spatial variance values at each time step.
        time_steps: List of time step indices corresponding to the variance values.

    Returns:
        Dictionary containing:
            - diffusion_rate (float): The calculated diffusion rate (slope).
            - r_squared (float): R² value of the linear fit (goodness of fit).
            - intercept (float): Y-intercept of the linear fit.
            - num_points (int): Number of data points used.
            - is_monotonic (bool): Whether the variance increased monotonically.

    Raises:
        DiffusionError: If input validation fails or calculation cannot proceed.
    """
    if len(spatial_variance_history) != len(time_steps):
        raise DiffusionError(
            f"Mismatched lengths: spatial_variance_history ({len(spatial_variance_history)}) "
            f"vs time_steps ({len(time_steps)})"
        )

    if len(spatial_variance_history) < 2:
        raise DiffusionError(
            f"Insufficient data points for diffusion rate calculation. "
            f"Expected at least 2, got {len(spatial_variance_history)}."
        )

    # Convert to numpy arrays for calculation
    variance_array = np.array(spatial_variance_history, dtype=np.float64)
    time_array = np.array(time_steps, dtype=np.float64)

    # Check for NaN or Inf values
    if np.any(np.isnan(variance_array)) or np.any(np.isinf(variance_array)):
        raise DiffusionError("Spatial variance history contains NaN or Inf values")

    # Check for monotonicity (variance should generally increase)
    # Allow small numerical tolerances for floating point comparisons
    tolerance = 1e-10
    diffs = np.diff(variance_array)
    is_monotonic = bool(np.all(diffs >= -tolerance))

    if not is_monotonic:
        logger.warning(
            f"Spatial variance is not monotonically increasing. "
            f"Negative differences detected: {diffs[diffs < -tolerance]}"
        )

    # Perform linear regression to find the diffusion rate (slope)
    # Using numpy's polyfit for linear fit (degree 1)
    try:
        coefficients = np.polyfit(time_array, variance_array, 1)
        slope = coefficients[0]  # diffusion rate
        intercept = coefficients[1]

        # Calculate R-squared
        # R² = 1 - (SS_res / SS_tot)
        y_pred = np.polyval(coefficients, time_array)
        ss_res = np.sum((variance_array - y_pred) ** 2)
        ss_tot = np.sum((variance_array - np.mean(variance_array)) ** 2)

        if ss_tot == 0:
            r_squared = 0.0
        else:
            r_squared = float(1 - (ss_res / ss_tot))

    except Exception as e:
        raise DiffusionError(f"Linear regression failed: {str(e)}") from e

    return {
        "diffusion_rate": float(slope),
        "r_squared": float(r_squared),
        "intercept": float(intercept),
        "num_points": len(time_steps),
        "is_monotonic": is_monotonic
    }


def verify_diffusion_stability(
    spatial_variance_history: List[float],
    tolerance: float = 0.01
) -> Dict[str, Any]:
    """
    Verify numerical stability of the diffusion process.

    Checks that the spatial variance evolution is stable and doesn't
    exhibit unphysical oscillations or divergences.

    Args:
        spatial_variance_history: List of spatial variance values over time.
        tolerance: Maximum allowed relative change between consecutive steps.

    Returns:
        Dictionary containing:
            - is_stable (bool): Whether the process passed stability checks.
            - max_relative_change (float): Largest relative change observed.
            - num_violations (int): Number of stability violations detected.
            - violation_indices (List[int]): Indices where violations occurred.
    """
    if len(spatial_variance_history) < 2:
        return {
            "is_stable": True,
            "max_relative_change": 0.0,
            "num_violations": 0,
            "violation_indices": [],
            "message": "Insufficient data for stability check"
        }

    variance_array = np.array(spatial_variance_history, dtype=np.float64)

    # Calculate relative changes
    # Avoid division by zero by using a small epsilon
    epsilon = 1e-10
    base_values = np.abs(variance_array[:-1]) + epsilon
    relative_changes = np.abs(np.diff(variance_array)) / base_values

    max_relative_change = float(np.max(relative_changes))
    violations = relative_changes > tolerance
    violation_indices = np.where(violations)[0].tolist()
    num_violations = len(violation_indices)

    is_stable = num_violations == 0

    result = {
        "is_stable": is_stable,
        "max_relative_change": max_relative_change,
        "num_violations": num_violations,
        "violation_indices": violation_indices
    }

    if not is_stable:
        logger.warning(
            f"Diffusion stability check failed: {num_violations} violations detected. "
            f"Max relative change: {max_relative_change:.4f}"
        )
        result["message"] = f"Stability check failed with {num_violations} violations"
    else:
        result["message"] = "Stability check passed"

    return result


def compute_diffusion_metrics(
    simulation_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compute comprehensive diffusion metrics from simulation results.

    This function extracts spatial variance history from simulation results,
    calculates the diffusion rate, and performs stability verification.

    Args:
        simulation_results: Dictionary containing simulation output including
                            'spatial_variance_history' and 'time_steps'.

    Returns:
        Dictionary containing:
            - diffusion_rate (float): Calculated diffusion rate.
            - r_squared (float): Goodness of fit for the linear model.
            - is_monotonic (bool): Whether variance increased monotonically.
            - is_stable (bool): Whether the process passed stability checks.
            - stability_details (dict): Detailed stability verification results.
            - diffusion_details (dict): Detailed diffusion rate calculation results.
    """
    if "spatial_variance_history" not in simulation_results:
        raise DiffusionError(
            "Missing 'spatial_variance_history' in simulation results"
        )

    if "time_steps" not in simulation_results:
        # Generate default time steps if not provided
        n_steps = len(simulation_results["spatial_variance_history"])
        simulation_results["time_steps"] = list(range(n_steps))

    spatial_variance_history = simulation_results["spatial_variance_history"]
    time_steps = simulation_results["time_steps"]

    # Calculate diffusion rate
    diffusion_details = calculate_diffusion_rate(
        spatial_variance_history,
        time_steps
    )

    # Verify stability
    stability_details = verify_diffusion_stability(
        spatial_variance_history
    )

    return {
        "diffusion_rate": diffusion_details["diffusion_rate"],
        "r_squared": diffusion_details["r_squared"],
        "is_monotonic": diffusion_details["is_monotonic"],
        "is_stable": stability_details["is_stable"],
        "stability_details": stability_details,
        "diffusion_details": diffusion_details
    }


def save_diffusion_results(
    results: Dict[str, Any],
    output_path: Union[str, Path]
) -> None:
    """
    Save diffusion calculation results to a JSON file.

    Args:
        results: Dictionary containing diffusion metrics and details.
        output_path: Path to the output JSON file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"Diffusion results saved to {output_path}")


def load_simulation_results(
    input_path: Union[str, Path]
) -> Dict[str, Any]:
    """
    Load simulation results from a JSON file.

    Args:
        input_path: Path to the input JSON file.

    Returns:
        Dictionary containing simulation results.
    """
    input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Simulation results file not found: {input_path}")

    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main() -> None:
    """
    Main entry point for diffusion verification script.

    Loads simulation results, computes diffusion metrics, and saves
    the verification output.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Compute diffusion rate from simulation results"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/analysis/simulation_results.json",
        help="Path to simulation results JSON file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/analysis/diffusion_verification.json",
        help="Path to output diffusion verification JSON file"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    else:
        logging.basicConfig(
            level=logging.WARNING,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    try:
        # Load simulation results
        logger.info(f"Loading simulation results from {args.input}")
        simulation_results = load_simulation_results(args.input)

        # Compute diffusion metrics
        logger.info("Computing diffusion metrics...")
        diffusion_metrics = compute_diffusion_metrics(simulation_results)

        # Save results
        logger.info(f"Saving diffusion verification results to {args.output}")
        save_diffusion_results(diffusion_metrics, args.output)

        # Print summary
        print(f"\nDiffusion Rate Verification Summary:")
        print(f"  Diffusion Rate: {diffusion_metrics['diffusion_rate']:.6f}")
        print(f"  R-squared: {diffusion_metrics['r_squared']:.6f}")
        print(f"  Is Monotonic: {diffusion_metrics['is_monotonic']}")
        print(f"  Is Stable: {diffusion_metrics['is_stable']}")
        print(f"\nResults saved to: {args.output}")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except DiffusionError as e:
        logger.error(f"Diffusion calculation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise