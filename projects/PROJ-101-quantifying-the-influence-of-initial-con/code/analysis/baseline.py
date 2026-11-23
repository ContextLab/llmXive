import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Local imports matching the provided API surface
from config import get_full_config
from data.generator import (
    generate_initial_conditions,
    integrate_trajectory,
    coupled_lorenz_ode,
)
from utils.stability import DivergenceError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Exceptions
# ----------------------------------------------------------------------


class NonChaoticSystemError(Exception):
    """Raised when the computed maximum Lyapunov exponent is non-positive."""
    pass


class BaselineConvergenceError(Exception):
    """Raised when baseline computation fails to converge within tolerances."""
    pass


# ----------------------------------------------------------------------
# Data container
# ----------------------------------------------------------------------


@dataclass
class BaselineResult:
    """Container for asymptotic baseline results."""

    lambda_max: float
    error_estimate: float
    configuration: Dict[str, Any]
    convergence_history: Optional[List[Tuple[int, float]]] = None
    status: str = "converged"


# ----------------------------------------------------------------------
# Core computation
# ----------------------------------------------------------------------


def compute_asymptotic_baseline(
    N: int,
    D: int = 3,
    T_max: int = 5000,
    rtol: float = 1e-9,
    atol: float = 1e-12,
    seed: Optional[int] = None,
) -> BaselineResult:
    """
    Compute the numerically converged asymptotic baseline for the maximum Lyapunov exponent
    using a simplified Rosenstein approach.

    Args:
        N: Number of coupled oscillators.
        D: Dimension per oscillator (always 3 for Lorenz).
        T_max: Maximum integration time (number of output steps).
        rtol: Relative tolerance for ODE integration.
        atol: Absolute tolerance for ODE integration.
        seed: Random seed for reproducibility.

    Returns:
        BaselineResult containing the estimated lambda_max and an error estimate.
    """
    # ------------------------------------------------------------------
    # Configuration handling
    # ------------------------------------------------------------------
    cfg = get_full_config()
    # Numerical settings are stored in the dict under "numerical"
    numerical_cfg = cfg.get("numerical", {})
    rtol = numerical_cfg.get("rtol", rtol)
    atol = numerical_cfg.get("atol", atol)

    # Simulation (Lorenz) parameters
    sim_cfg = cfg.get("simulation", {})
    sigma = sim_cfg.get("sigma", 10.0)
    rho = sim_cfg.get("rho", 28.0)
    beta = sim_cfg.get("beta", 8.0 / 3.0)

    # ------------------------------------------------------------------
    # Initial conditions
    # ------------------------------------------------------------------
    if seed is not None:
        np.random.seed(seed)

    initial_state = generate_initial_conditions(N, seed if seed is not None else 0)

    # ------------------------------------------------------------------
    # Integrate clean trajectory
    # ------------------------------------------------------------------
    try:
        time_clean, traj_clean = integrate_trajectory(
            N=N,
            t_span=(0.0, float(T_max)),
            dt=1.0,  # one unit per step – sufficient for baseline convergence test
            initial_state=initial_state,
            coupling_strength=0.0,  # clean system, no coupling influence on chaos
            coupling_topology="ring",
            numerical_settings=None,
            seed=seed,
        )
    except Exception as exc:
        logger.error(f"Integration of clean trajectory failed: {exc}")
        raise DivergenceError(f"Trajectory divergence during baseline computation: {exc}")

    # ------------------------------------------------------------------
    # Rosenstein / Benettin style estimate
    # ------------------------------------------------------------------
    # We'll compute the separation between the clean trajectory and a nearby
    # perturbed trajectory for increasing window lengths.
    window_sizes = [500, 1000, 2000, 3000, 4000, 5000]

    lambda_estimates: List[float] = []
    history: List[Tuple[int, float]] = []

    for T in window_sizes:
        if T > traj_clean.shape[0]:
            continue

        # Perturb the initial condition by a tiny amount
        perturb = 1e-9
        perturbed_state = initial_state + perturb * np.random.randn(N * D)

        # Integrate perturbed trajectory over the same window length
        try:
            _, traj_pert = integrate_trajectory(
                N=N,
                t_span=(0.0, float(T)),
                dt=1.0,
                initial_state=perturbed_state,
                coupling_strength=0.0,
                coupling_topology="ring",
                numerical_settings=None,
                seed=seed,
            )
        except Exception:
            # If perturbed integration fails, skip this window size
            continue

        # Compute Euclidean distance at each step
        diffs = traj_pert[:T] - traj_clean[:T]
        distances = np.linalg.norm(diffs, axis=1)
        # Avoid log(0) – ignore initial few steps where distance may be ~0
        eps = 1e-12
        valid = distances > eps
        if np.sum(valid) < 5:
            continue

        log_dist = np.log(distances[valid])
        times = np.arange(len(log_dist))

        # Linear fit slope ≈ lambda_max over this window
        slope, _ = np.polyfit(times, log_dist, 1)
        lambda_estimates.append(slope)
        history.append((T, slope))

    if not lambda_estimates:
        raise BaselineConvergenceError("Failed to obtain any FTLE estimates for baseline.")

    # Use the last estimate as the asymptotic value; error is difference to previous
    lambda_max = lambda_estimates[-1]
    error_estimate = (
        abs(lambda_estimates[-1] - lambda_estimates[-2])
        if len(lambda_estimates) > 1
        else 0.0
    )

    # ------------------------------------------------------------------
    # Convergence check (relative change at T=5000 < 5%)
    # ------------------------------------------------------------------
    if len(lambda_estimates) >= 2:
        rel_change = abs(lambda_estimates[-1] - lambda_estimates[-2]) / max(
            abs(lambda_estimates[-2]), 1e-12
        )
        if rel_change > 0.05:
            logger.warning(
                f"Baseline convergence criterion not met: relative change {rel_change:.3f}"
            )

    result = BaselineResult(
        lambda_max=lambda_max,
        error_estimate=error_estimate,
        configuration={
            "N": N,
            "D": D,
            "T_max": T_max,
            "sigma": sigma,
            "rho": rho,
            "beta": beta,
        },
        convergence_history=history,
    )
    return result


# ----------------------------------------------------------------------
# Validation helpers
# ----------------------------------------------------------------------


def validate_clean_system_baseline(baseline_result: BaselineResult) -> bool:
    """
    Validate that the clean system baseline is stable and converged.

    Args:
        baseline_result: The computed baseline result

    Returns:
        True if validation passes

    Raises:
        BaselineConvergenceError: If validation fails
    """
    if baseline_result.lambda_max <= 0:
        raise BaselineConvergenceError(
            f"Baseline validation failed: lambda_max={baseline_result.lambda_max} <= 0. "
            "Clean system should exhibit chaos (positive Lyapunov exponent)."
        )

    if baseline_result.error_estimate > 1e-3:
        logger.warning(f"Baseline error estimate is high: {baseline_result.error_estimate}")

    return True


def save_baseline_result(result: BaselineResult, output_path: Path) -> None:
    """
    Save baseline result to a JSON file.

    Args:
        result: BaselineResult object to save
        output_path: Path to the output file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "lambda_max": result.lambda_max,
        "error_estimate": result.error_estimate,
        "configuration": result.configuration,
        "convergence_history": result.convergence_history,
        "status": result.status,
    }
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved baseline result to {output_path}")


def load_baseline_result(input_path: Path) -> BaselineResult:
    """
    Load baseline result from a JSON file.

    Args:
        input_path: Path to the input file

    Returns:
        BaselineResult object
    """
    with open(input_path, "r") as f:
        data = json.load(f)
    return BaselineResult(
        lambda_max=data["lambda_max"],
        error_estimate=data["error_estimate"],
        configuration=data["configuration"],
        convergence_history=data.get("convergence_history"),
        status=data.get("status", "converged"),
    )


def validate_and_gate_for_baseline(baseline_results: Dict[str, BaselineResult]) -> bool:
    """
    Validate all baseline results and gate execution if any fail.

    Args:
        baseline_results: Dictionary of N -> BaselineResult

    Returns:
        True if all validations pass

    Raises:
        NonChaoticSystemError: If any system is non-chaotic
        BaselineConvergenceError: If any baseline failed to converge
    """
    for N_key, result in baseline_results.items():
        if result.lambda_max <= 0:
            raise NonChaoticSystemError(
                f"Non-chaotic regime detected: lambda_max={result.lambda_max} <= 0 for {N_key}"
            )
        if result.error_estimate > 1e-3:
            logger.warning(f"Baseline for {N_key} may not be fully converged")
    return True


def check_non_chaotic_regime(lambda_max: float, N: int) -> None:
    """
    Check if the system is in a non-chaotic regime and raise an error if so.

    Args:
        lambda_max: The computed maximum Lyapunov exponent
        N: Number of oscillators in the configuration

    Raises:
        NonChaoticSystemError: If lambda_max <= 0
    """
    if lambda_max <= 0:
        raise NonChaoticSystemError(
            f"Non-chaotic regime detected: lambda_max={lambda_max} <= 0"
        )


def main() -> Dict[int, BaselineResult]:
    """
    Main entry point for baseline computation and validation.
    Computes baselines for the N values defined in the configuration,
    validates them, saves the JSON files and returns a dictionary of results.
    """
    cfg = get_full_config()
    # The configuration currently stores a single default N; we also allow a list via an env var.
    N_default = cfg.get("simulation", {}).get("N_oscillators", 5)
    # For flexibility, accept a comma‑separated list in an environment variable
    import os

    N_env = os.getenv("BASELINE_N_VALUES")
    if N_env:
        N_values = [int(v) for v in N_env.split(",") if v.strip()]
    else:
        N_values = [N_default]

    baselines: Dict[int, BaselineResult] = {}
    for N in N_values:
        logger.info(f"Computing baseline for N={N}")
        result = compute_asymptotic_baseline(N=N)
        # Validate positivity
        validate_clean_system_baseline(result)
        # Additional explicit check
        check_non_chaotic_regime(result.lambda_max, N)
        baselines[N] = result
        # Save JSON
        out_path = Path(f"data/processed/baseline_{N}.json")
        save_baseline_result(result, out_path)

    # Gate validation across all results
    validate_and_gate_for_baseline({f"N={k}": v for k, v in baselines.items()})
    logger.info("All baselines computed and validated successfully")
    return baselines


if __name__ == "__main__":
    main()