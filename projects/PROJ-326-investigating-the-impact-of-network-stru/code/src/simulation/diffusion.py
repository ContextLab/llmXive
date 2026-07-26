"""
Diffusion rate calculator for spin network simulations.

Calculates the rate of change of spatial variance using finite differences.
Verifies mathematical definitions and asserts variance monotonicity with
tolerance for stochastic noise.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

from code.src.simulation.metrics import compute_spatial_variance
from code.src.simulation.stability import check_for_nan_inf, StabilityError

logger = logging.getLogger(__name__)

def calculate_diffusion_rate(
    variance_history: List[float],
    time_steps: Optional[List[float]] = None,
    method: str = "central"
) -> Dict[str, Any]:
    """
    Calculate the diffusion rate from a history of spatial variance values.

    Uses finite difference approximation to estimate the rate of change (dV/dt).

    Args:
        variance_history: List of spatial variance values at each time step.
        time_steps: Optional list of actual time values corresponding to each step.
                    If None, assumes unit time steps [0, 1, 2, ...].
        method: Finite difference method ('forward', 'backward', 'central').
                'central' is most accurate but requires >= 3 points.

    Returns:
        Dict containing:
            - 'diffusion_rates': List of calculated rates (dV/dt)
            - 'mean_diffusion_rate': Average rate over the simulation
            - 'max_diffusion_rate': Maximum instantaneous rate
            - 'monotonicity_verified': Boolean indicating if variance is generally increasing
            - 'noise_tolerance_used': Float threshold used for monotonicity check
    """
    if not variance_history or len(variance_history) < 2:
        raise ValueError("At least 2 variance values are required to calculate diffusion rate.")

    variance_array = np.array(variance_history)

    # Check for numerical stability issues
    nan_inf_check = check_for_nan_inf(variance_array, "variance_history")
    if not nan_inf_check["is_valid"]:
        raise StabilityError(
            f"Invalid values detected in variance history: {nan_inf_check['issues']}"
        )

    # Generate time steps if not provided
    if time_steps is None:
        time_steps = list(range(len(variance_history)))
    time_array = np.array(time_steps)

    if len(time_array) != len(variance_array):
        raise ValueError(
            f"Time steps length ({len(time_array)}) must match variance history "
            f"length ({len(variance_array)})."
        )

    # Calculate finite differences
    rates = []
    n = len(variance_array)

    if method == "central" and n >= 3:
        # Central difference: (V_{i+1} - V_{i-1}) / (t_{i+1} - t_{i-1})
        # Valid for indices 1 to n-2
        for i in range(1, n - 1):
            dt = time_array[i + 1] - time_array[i - 1]
            if dt == 0:
                rates.append(0.0)  # Avoid division by zero
            else:
                dV = variance_array[i + 1] - variance_array[i - 1]
                rates.append(float(dV / dt))

        # Handle endpoints with forward/backward difference
        # First point: forward difference
        dt_first = time_array[1] - time_array[0]
        if dt_first != 0:
            rates.insert(0, float((variance_array[1] - variance_array[0]) / dt_first))
        else:
            rates.insert(0, 0.0)

        # Last point: backward difference
        dt_last = time_array[n - 1] - time_array[n - 2]
        if dt_last != 0:
            rates.append(float((variance_array[n - 1] - variance_array[n - 2]) / dt_last))
        else:
            rates.append(0.0)

    elif method == "forward":
        # Forward difference: (V_{i+1} - V_i) / (t_{i+1} - t_i)
        for i in range(n - 1):
            dt = time_array[i + 1] - time_array[i]
            if dt == 0:
                rates.append(0.0)
            else:
                dV = variance_array[i + 1] - variance_array[i]
                rates.append(float(dV / dt))
        # Add a zero for the last point (no forward neighbor)
        rates.append(0.0)

    elif method == "backward":
        # Backward difference: (V_i - V_{i-1}) / (t_i - t_{i-1})
        rates.append(0.0)  # First point has no backward neighbor
        for i in range(1, n):
            dt = time_array[i] - time_array[i - 1]
            if dt == 0:
                rates.append(0.0)
            else:
                dV = variance_array[i] - variance_array[i - 1]
                rates.append(float(dV / dt))
    else:
        raise ValueError(f"Unknown method '{method}'. Use 'forward', 'backward', or 'central'.")

    rates_array = np.array(rates)

    # Calculate statistics
    mean_rate = float(np.mean(rates_array))
    max_rate = float(np.max(rates_array))

    # Verify monotonicity with tolerance for stochastic noise
    # In a diffusion process, variance should generally increase, but noise can cause
    # small local decreases. We check if the overall trend is increasing.
    noise_tolerance = 0.05 * np.mean(variance_array) if np.mean(variance_array) > 0 else 1e-6
    monotonicity_verified = _verify_monotonicity(variance_array, noise_tolerance)

    return {
        "diffusion_rates": rates,
        "mean_diffusion_rate": mean_rate,
        "max_diffusion_rate": max_rate,
        "monotonicity_verified": monotonicity_verified,
        "noise_tolerance_used": float(noise_tolerance),
        "method_used": method,
        "num_points": n
    }


def _verify_monotonicity(
    values: np.ndarray,
    tolerance: float,
    required_trend: str = "increasing"
) -> bool:
    """
    Verify that the sequence is monotonically increasing (or decreasing) with tolerance.

    Args:
        values: Array of values to check.
        tolerance: Allowed deviation (absolute or relative).
        required_trend: 'increasing' or 'decreasing'.

    Returns:
        True if the trend is verified within tolerance, False otherwise.
    """
    if len(values) < 2:
        return True

    # Calculate differences
    diffs = np.diff(values)

    if required_trend == "increasing":
        # Allow small negative differences due to noise
        # If most differences are positive or slightly negative (within tolerance), it's increasing
        significant_violations = diffs < -tolerance
        violation_ratio = np.sum(significant_violations) / len(diffs)
        # Allow up to 20% violations due to stochastic noise
        return violation_ratio < 0.20
    elif required_trend == "decreasing":
        significant_violations = diffs > tolerance
        violation_ratio = np.sum(significant_violations) / len(diffs)
        return violation_ratio < 0.20
    else:
        raise ValueError(f"Unknown trend: {required_trend}")


def compute_diffusion_from_simulation(
    simulation_output: Dict[str, Any],
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Extract diffusion metrics from a full simulation output and optionally save verification.

    Args:
        simulation_output: Dictionary containing simulation results, including:
            - 'spatial_variance_history': List of variance values over time
            - 'time_steps': List of time values (optional)
            - 'network_id': Identifier for the network
            - 'seed': Random seed used
        output_path: Optional path to save the verification results JSON.

    Returns:
        Dictionary containing diffusion rate analysis results.
    """
    if "spatial_variance_history" not in simulation_output:
        raise KeyError(
            "Simulation output must contain 'spatial_variance_history' key."
        )

    variance_history = simulation_output["spatial_variance_history"]
    time_steps = simulation_output.get("time_steps")

    # Calculate diffusion rate
    diffusion_results = calculate_diffusion_rate(
        variance_history=variance_history,
        time_steps=time_steps,
        method="central"
    )

    # Add metadata from simulation output
    diffusion_results["network_id"] = simulation_output.get("network_id", "unknown")
    diffusion_results["seed"] = simulation_output.get("seed", -1)
    diffusion_results["total_steps"] = len(variance_history)

    # Verify mathematical definition: diffusion rate should be positive for spreading
    # In Ising-like systems with energy propagation, variance typically increases
    expected_positive = diffusion_results["mean_diffusion_rate"] > -diffusion_results["noise_tolerance_used"]
    diffusion_results["mathematical_definition_verified"] = expected_positive

    if not expected_positive:
        logger.warning(
            f"Diffusion rate for network {diffusion_results['network_id']} is not "
            f"positive (mean={diffusion_results['mean_diffusion_rate']}). "
            f"This may indicate numerical issues or a non-spreading regime."
        )

    # Save verification results if path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(diffusion_results, f, indent=2)
        logger.info(f"Diffusion verification results saved to {output_path}")

    return diffusion_results


def main():
    """
    Main entry point for standalone execution.

    Loads simulation data, calculates diffusion rates, and saves verification results.
    This function is designed to be called by the simulation runner or analysis pipeline.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Calculate diffusion rates from simulation output."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to JSON file containing simulation output."
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to save diffusion verification results."
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level."
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Load simulation data
    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_path, "r") as f:
        simulation_data = json.load(f)

    # Compute diffusion
    output_path = Path(args.output)
    results = compute_diffusion_from_simulation(simulation_data, output_path)

    # Print summary
    print(f"Network: {results['network_id']}")
    print(f"Mean Diffusion Rate: {results['mean_diffusion_rate']:.6f}")
    print(f"Max Diffusion Rate: {results['max_diffusion_rate']:.6f}")
    print(f"Monotonicity Verified: {results['monotonicity_verified']}")
    print(f"Mathematical Definition Verified: {results['mathematical_definition_verified']}")
    print(f"Results saved to: {output_path}")

    return 0


if __name__ == "__main__":
    exit(main())
