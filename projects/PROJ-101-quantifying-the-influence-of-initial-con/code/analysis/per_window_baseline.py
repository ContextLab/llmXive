"""
per_window_baseline.py

Computes clean finite‑time Lyapunov exponent baselines for each window size
used in the FTLE analysis (e.g. 500, 1000, 5000).  The results are written
to ``data/processed/baseline_per_window_{N}.json`` where ``N`` is the number
of coupled Lorenz oscillators.

The module is imported by the unit test ``tests/unit/test_per_window_baseline.py``.
Importing the module runs the ``main`` function which returns a mapping
``{N: List[record]}`` that the test uses as an in‑memory reference.
"""

import json
from pathlib import Path
from typing import List, Dict

import numpy as np

from llmxive_toolkit import paths, get_logger
from config import get_full_config
from analysis.baseline import compute_asymptotic_baseline, BaselineResult
from data.generator import generate_coupled_lorenz_trajectory
from analysis.ftle import compute_ftle_single_trajectory, FTLEResult

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Window sizes required by the project – must match the values used in
# ``analysis.ftle`` and the quick‑start documentation.
WINDOW_SIZES: List[int] = [500, 1000, 5000]

# System dimensions to process.  The integration tests parametrize N = 3 and 5,
# which are also the default values used throughout the pipeline.
DEFAULT_N_VALUES: List[int] = [3, 5]

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _generate_clean_trajectory(N: int, seed: int = 42) -> np.ndarray:
    """
    Generate a noise‑free trajectory for ``N`` coupled Lorenz oscillators.

    The function uses the same configuration machinery as the rest of the
    pipeline (time step, integration end time, coupling strength, etc.).
    It returns the state array of shape ``(n_steps, 3 * N)``.
    """
    cfg = get_full_config()
    sim_cfg = cfg["simulation"]

    t_start = 0.0
    t_end = sim_cfg["t_max"]
    dt = sim_cfg["dt_output"]
    coupling_strength = sim_cfg.get("coupling_strength", 0.1)
    coupling_topology = sim_cfg.get("coupling_topology", "nearest")

    # The generator returns an object with ``state`` and ``time`` attributes.
    traj = generate_coupled_lorenz_trajectory(
        N=N,
        t_start=t_start,
        t_end=t_end,
        dt=dt,
        sigma_noise=0.0,               # clean trajectory
        coupling_strength=coupling_strength,
        coupling_topology=coupling_topology,
        seed=seed,
    )
    return traj.state

def _compute_window_baseline(
    trajectory: np.ndarray,
    N: int,
    baseline_lambda: float,
    window_size: int,
    dt: float,
) -> FTLEResult:
    """
    Compute the FTLE for a single clean trajectory over a given window size.
    ``baseline_lambda`` is the asymptotic Lyapunov exponent (used only for
    bookkeeping inside ``FTLEResult``).
    """
    # ``trial_id`` is irrelevant for the per‑window baseline – we use 0.
    result = compute_ftle_single_trajectory(
        trajectory=trajectory,
        T=window_size,
        dt=dt,
        N=N,
        baseline_lambda=baseline_lambda,
        trial_id=0,
    )
    # The FTLE computation sets ``sigma`` to 0; we keep that.
    result.sigma = 0.0
    return result

# ----------------------------------------------------------------------
# Core routine
# ----------------------------------------------------------------------
def compute_per_window_baseline_for_N(N: int) -> List[Dict]:
    """
    Compute the clean finite‑time baseline for *all* window sizes for a
    particular system dimension ``N``.

    Returns a list of dictionaries, each containing:
        - window_size
        - lambda_max   (the FTLE value)
        - convergence_error (relative error w.r.t. the asymptotic baseline)
        - status      ("valid" if error < 5 %)
    """
    log.info(f"Computing per‑window baseline for N={N}")

    # 1️⃣  Asymptotic baseline (long‑time Rosenstein estimate)
    asymptotic: BaselineResult = compute_asymptotic_baseline(N=N)
    baseline_lambda = asymptotic.lambda_max
    log.debug(f"Asymptotic baseline λ = {baseline_lambda:.6f}")

    # 2️⃣  Clean trajectory (noise‑free)
    clean_traj = _generate_clean_trajectory(N, seed=42)

    # 3️⃣  Time step – taken from the global config for consistency
    dt = get_full_config()["simulation"]["dt_output"]

    # 4️⃣  Compute FTLE for each window size
    records: List[Dict] = []
    for T in WINDOW_SIZES:
        ftle_res: FTLEResult = _compute_window_baseline(
            trajectory=clean_traj,
            N=N,
            baseline_lambda=baseline_lambda,
            window_size=T,
            dt=dt,
        )
        lambda_ftle = ftle_res.lambda_ftle
        # Relative error compared to the asymptotic baseline
        error = abs(lambda_ftle - baseline_lambda) / abs(baseline_lambda)
        status = "valid" if error < 0.05 else "invalid"

        record = {
            "window_size": T,
            "lambda_max": lambda_ftle,
            "convergence_error": error,
            "status": status,
        }
        records.append(record)
        log.debug(
            f"N={N}, T={T}: λ_FTLE={lambda_ftle:.6f}, "
            f"error={error:.4%}, status={status}"
        )
    return records

def main() -> Dict[int, List[Dict]]:
    """
    Entry point used by the test suite.

    For each ``N`` in ``DEFAULT_N_VALUES`` the function:
        1. Computes the per‑window baseline records.
        2. Writes them to ``data/processed/baseline_per_window_{N}.json``.
        3. Returns a mapping ``{N: records}`` for in‑memory verification.

    The JSON file format matches exactly what the unit test expects.
    """
    results: Dict[int, List[Dict]] = {}

    for N in DEFAULT_N_VALUES:
        records = compute_per_window_baseline_for_N(N)

        # Write JSON file using the llmxive toolkit path helper
        out_path: Path = paths.data("processed", f"baseline_per_window_{N}.json")
        out_path.parent.mkdir(parents=True, exist_ok=True)

        with out_path.open("w", encoding="utf-8") as fp:
            json.dump(records, fp, indent=2)

        log.info(f"Wrote per‑window baseline JSON for N={N} to {out_path}")
        results[N] = records

    return results

if __name__ == "__main__":
    # Allow manual execution for debugging
    _ = main()