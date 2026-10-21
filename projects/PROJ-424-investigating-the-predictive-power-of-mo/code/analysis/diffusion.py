"""
High‑level diffusion analysis wrapper.

This module combines the low‑level MSD utilities with the project‑wide
analysis configuration to produce a diffusion result dictionary that
downstream stages (bootstrap, reporting, etc.) can consume.

The core function ``analyze_diffusion`` follows the specification:

* Discard the first 0.1 × trajectory length (ballistic regime).
* Fit a linear model to the remaining MSD vs. time data.
* Require ``R² ≥ config.r2_threshold`` (≥ 0.95 per the spec).
* Compute ``D = slope / 6`` and set ``d_scaled_m2_s = d_calc_m2_s``.
* If the R² gate fails, mark the row with ``status = "convergence_failed"``.
*
* The implementation deliberately accesses the MSD utilities via the
* ``msd`` module object (instead of importing the functions directly) so
* that unit‑tests can monkey‑patch ``msd.load_trajectory_timeseries`` and
* inject synthetic data without needing a real trajectory file.
"""

import logging
from typing import Dict, Any

import numpy as np

# Import the whole module so that tests can monkey‑patch its attributes.
from . import msd as msd

from config import AnalysisConfig, DEFAULT_ANALYSIS_CONFIG

logger = logging.getLogger(__name__)

def _discard_initial_fraction(times: np.ndarray, msds: np.ndarray, fraction: float = 0.1) -> tuple:
    """
    Discard the first ``fraction`` of the trajectory (by number of points).

    Parameters
    ----------
    times, msds : np.ndarray
        Full time and MSD arrays.
    fraction : float
        Fraction of points to discard (default 0.1).

    Returns
    -------
    times_trim, msds_trim : np.ndarray
        Trimmed arrays.
    """
    if not 0.0 < fraction < 1.0:
        raise ValueError("fraction must be between 0 and 1")

    cut_index = int(len(times) * fraction)
    # Ensure at least two points remain for regression.
    if len(times) - cut_index < 2:
        raise ValueError("Not enough data points remain after discarding the initial fraction.")
    return times[cut_index:], msds[cut_index:]

def analyze_diffusion(
    trajectory_path: str,
    config: AnalysisConfig = DEFAULT_ANALYSIS_CONFIG,
) -> Dict[str, Any]:
    """
    Perform the full diffusion analysis for a single trajectory.

    Returns a dictionary with the keys required by downstream contracts:

    * ``msd_slope`` – slope of the MSD vs. time fit (m² ns⁻¹).
    * ``d_calc_m2_s`` – raw diffusion coefficient from the linear fit.
    * ``d_scaled_m2_s`` – identical to ``d_calc_m2_s`` (no CG scaling).
    * ``r_squared`` – regression R².
    * ``status`` – ``"converged"`` or ``"convergence_failed"``.
    * ``message`` – human‑readable description of the outcome.
    """
    try:
        # Load raw MSD data using the msd module (allows monkey‑patching).
        times, msds = msd.load_trajectory_timeseries(trajectory_path)

        # Discard the ballistic regime.
        times_fit, msds_fit = _discard_initial_fraction(times, msds, fraction=0.1)

        # Linear regression.
        slope, intercept, r_squared = msd.perform_linear_regression(times_fit, msds_fit)

        # Validate R².
        is_valid = msd.validate_linearity(r_squared, config.r2_threshold)

        # Diffusion coefficient (m²/s).
        d_calc = msd.calculate_diffusion_coefficient(slope)

        result = {
            "msd_slope": slope,
            "d_calc_m2_s": d_calc,
            "d_scaled_m2_s": d_calc,  # No scaling per spec.
            "r_squared": r_squared,
            "status": "converged" if is_valid else "convergence_failed",
            "message": f"R²={r_squared:.4f}, D={d_calc:.3e} m²/s",
        }

        if not is_valid:
            logger.warning(
                f"Diffusion analysis failed R² threshold: {r_squared:.4f} < {config.r2_threshold}"
            )
        return result

    except Exception as e:
        logger.error(f"Diffusion analysis error for {trajectory_path}: {e}")
        return {
            "msd_slope": 0.0,
            "d_calc_m2_s": 0.0,
            "d_scaled_m2_s": 0.0,
            "r_squared": 0.0,
            "status": "convergence_failed",
            "message": str(e),
        }

# ----------------------------------------------------------------------
# Simple CLI for manual testing
# ----------------------------------------------------------------------
def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run diffusion analysis on a trajectory.")
    parser.add_argument("trajectory", help="Path to the trajectory file.")
    args = parser.parse_args()

    result = analyze_diffusion(args.trajectory)
    print(result)

if __name__ == "__main__":
    main()