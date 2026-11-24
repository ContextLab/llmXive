"""
MSD analysis utilities.

This module provides functions to load a molecular dynamics trajectory,
compute the mean‑squared‑displacement (MSD) time series using MDTraj,
perform a linear regression on the MSD curve, and calculate a diffusion
coefficient from the regression slope.

All functions raise explicit exceptions on failure – there is no synthetic
fallback or fabricated data generation.
"""

import logging
from pathlib import Path
from typing import Tuple

import numpy as np
import mdtraj as md

logger = logging.getLogger(__name__)

def load_trajectory_timeseries(trajectory_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load a trajectory file and compute the MSD time series.

    Parameters
    ----------
    trajectory_path : str
        Path to a trajectory file readable by MDTraj (e.g. .xtc, .dcd,
        .pdb, etc.). The file must exist; otherwise a FileNotFoundError is
        raised.

    Returns
    -------
    times_ns : np.ndarray
        1‑D array of times in nanoseconds.
    msd_m2 : np.ndarray
        1‑D array of mean‑squared‑displacement values in square meters.

    Notes
    -----
    * MDTraj returns distances in nanometres.  The MSD is therefore in
      nm² and is converted to m² (1 nm = 1e‑9 m, so 1 nm² = 1e‑18 m²).
    * If the trajectory does not contain time information, a uniform
      spacing of 1 ps per frame (0.001 ns) is assumed.
    """
    traj_path = Path(trajectory_path)
    if not traj_path.is_file():
        raise FileNotFoundError(f"Trajectory not found: {trajectory_path}")

    # Load the trajectory; MDTraj will infer the format from the suffix.
    try:
        traj = md.load(str(traj_path))
    except Exception as e:
        logger.error(f"Failed to load trajectory {trajectory_path}: {e}")
        raise

    if traj.n_frames == 0:
        raise ValueError("Trajectory contains no frames.")

    # Compute time axis (ns).  MDTraj stores time in picoseconds if available.
    if hasattr(traj, "time") and traj.time is not None and len(traj.time) == traj.n_frames:
        # MDTraj time is in picoseconds.
        times_ns = traj.time / 1000.0
    else:
        # Assume constant 1 ps per frame.
        times_ns = np.arange(traj.n_frames) * 0.001  # ns

    # Compute MSD (nm^2) using MDTraj's built‑in routine.
    try:
        msd_nm2 = md.compute_mean_squared_displacement(traj)
    except Exception as e:
        logger.error(f"MDTraj MSD computation failed: {e}")
        raise

    # Convert to m^2.
    msd_m2 = msd_nm2 * 1e-18
    return times_ns, msd_m2

def perform_linear_regression(times: np.ndarray, msds: np.ndarray) -> Tuple[float, float, float]:
    """
    Perform a simple linear regression ``MSD = slope * t + intercept``.

    Returns
    -------
    slope : float
        Slope of the fitted line (units: m² ns⁻¹).
    intercept : float
        Intercept of the fitted line (units: m²).
    r_squared : float
        Coefficient of determination.
    """
    if len(times) < 2:
        raise ValueError("At least two data points are required for regression.")

    coeffs = np.polyfit(times, msds, 1)
    slope, intercept = coeffs[0], coeffs[1]

    # Predicted values and R²
    y_pred = slope * times + intercept
    ss_res = np.sum((msds - y_pred) ** 2)
    ss_tot = np.sum((msds - np.mean(msds)) ** 2)
    r_squared = 1.0 - ss_res / ss_tot if ss_tot != 0 else 0.0

    return slope, intercept, r_squared

def validate_linearity(r_squared: float, threshold: float) -> bool:
    """
    Return ``True`` if the regression R² meets the required threshold.
    """
    return r_squared >= threshold

def calculate_diffusion_coefficient(slope: float, scaling_factor: float = 1.0) -> float:
    """
    Convert the regression slope to a diffusion coefficient.

    The Einstein relation for three‑dimensional diffusion is
    ``MSD = 6 D t``.  When ``t`` is expressed in nanoseconds,
    the slope has units of m² ns⁻¹, so

        D (m²/ns) = slope / 6

    To obtain D in the conventional SI unit m² s⁻¹ we multiply by 1e9
    (since 1 ns = 1e‑9 s).  The optional ``scaling_factor`` is kept for
    compatibility with downstream code (e.g. finite‑size corrections) but
    defaults to 1.0.
    """
    # Convert from m²/ns to m²/s
    d_m2_per_s = (slope / 6.0) * 1e9
    return d_m2_per_s * scaling_factor

def main() -> None:
    """
    Demonstrate the MSD pipeline on a user‑provided trajectory.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Compute MSD from a trajectory.")
    parser.add_argument("trajectory", help="Path to the trajectory file.")
    args = parser.parse_args()

    times, msd = load_trajectory_timeseries(args.trajectory)
    slope, intercept, r2 = perform_linear_regression(times, msd)
    D = calculate_diffusion_coefficient(slope)

    print(f"Linear fit: slope={slope:.3e} m²/ns, intercept={intercept:.3e} m², R²={r2:.4f}")
    print(f"Diffusion coefficient D = {D:.3e} m²/s")

if __name__ == "__main__":
    main()
