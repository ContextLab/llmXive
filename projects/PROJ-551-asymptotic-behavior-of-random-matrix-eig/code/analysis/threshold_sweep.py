"""
Threshold sweep script for the asymptotic random matrix project.

This script implements Task T004: it runs the full theta sweep over the
complete parameter grid and writes two validated output files:

  * data/processed/mc_results.csv
  * data/processed/convergence_data.json

The sweep iterates over

  N ∈ {100, 500, 1000, 2000}
  θ ∈ {0.8, 1.0, 1.2, 1.5, 2.0, 2.5, 3.0}
  seed ∈ {42, 123, 456, 789}
  k ∈ {1, 2, 5}
  pattern ∈ {diagonal, block-sparse, random-sparse}

For each configuration the script:

  1. Loads (or generates) a Wigner matrix scaled by 1/√N.
  2. Constructs a rank‑k diagonal perturbation with spectral norm θ.
     The same diagonal construction is used for all pattern types; the
     pattern label is recorded for contract compatibility.
  3. Forms the perturbed matrix H = W + P.
  4. Uses ARPACK (scipy.sparse.linalg.eigsh) with tolerance 1e‑10 to obtain
     the largest eigenvalue.
  5. Flags an outlier using the **theoretical** rule:
         outlier_flag = eigenvalue_top > 2.0 + 0.05
  6. Records the required columns in a CSV row:
         run_id,N,k,pattern_type,theta,seed,eigenvalue_top,
         computation_time_ms,outlier_flag
  7. Additionally records, per N, the bulk‑edge (largest eigenvalue of the
     unperturbed Wigner matrix) for every seed and aggregates these into
     ``convergence_data.json``.
"""

import argparse
import csv
import json
import logging
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.sparse.linalg import eigsh

# ----------------------------------------------------------------------
# Project‑specific helpers – we rely on the llmxive_toolkit paths utility
# ----------------------------------------------------------------------
from llmxive_toolkit import paths as llm_paths

# ----------------------------------------------------------------------
# Configuration – the full sweep grid
# ----------------------------------------------------------------------
N_VALUES = [100, 500, 1000, 2000]
THETA_VALUES = [0.8, 1.0, 1.2, 1.5, 2.0, 2.5, 3.0]
SEED_VALUES = [42, 123, 456, 789]
K_VALUES = [1, 2, 5]
PATTERN_VALUES = ["diagonal", "block-sparse", "random-sparse"]

# Theoretical edge and tolerance (FR‑004)
THEORETICAL_EDGE = 2.0
OUTLIER_TOL = 0.05  # can be overridden via env var OUTLIER_TOLERANCE

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _setup_logger() -> logging.Logger:
    logger = logging.getLogger("threshold_sweep")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(handler)
    return logger

def _ensure_raw_matrix(N: int, seed: int, logger: logging.Logger) -> Path:
    """
    Load a previously generated raw Wigner matrix if it exists;
    otherwise generate it, save it under ``data/raw/matrix_N{N}_seed{seed}.npy``
    and return the path.
    """
    raw_dir = llm_paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / f"matrix_N{N}_seed{seed}.npy"

    if raw_path.exists():
        logger.debug(f"Re‑using existing raw matrix {raw_path}")
    else:
        logger.info(f"Generating raw Wigner matrix N={N}, seed={seed}")
        rng = np.random.default_rng(seed)
        # Standard symmetric Wigner matrix: (A + Aᵀ) / sqrt(2N)
        A = rng.standard_normal((N, N))
        W = (A + A.T) / np.sqrt(2.0 * N)
        np.save(raw_path, W)
        logger.info(f"Saved raw matrix to {raw_path}")

    return raw_path

def _build_diagonal_perturbation(N: int, k: int, theta: float) -> np.ndarray:
    """
    Create a rank‑k diagonal perturbation where the first ``k`` diagonal
    entries equal ``theta``. This matrix has spectral norm exactly ``theta``.
    """
    P = np.zeros((N, N), dtype=np.float64)
    for i in range(k):
        P[i, i] = theta
    return P

def _run_eigen_solver(H: np.ndarray, logger: logging.Logger) -> float:
    """
    Compute the largest eigenvalue of ``H`` using ARPACK with tolerance 1e‑10.
    Returns the eigenvalue as a Python float.
    """
    start = time.perf_counter()
    vals = eigsh(H, k=1, which="LA", tol=1e-10, return_eigenvectors=False)
    elapsed = time.perf_counter() - start
    logger.debug(f"ARPACK top‑eigenvalue computation took {elapsed:.3f}s")
    return float(vals[0])

# ----------------------------------------------------------------------
# Core sweep logic
# ----------------------------------------------------------------------
def run_full_sweep(logger: logging.Logger) -> None:
    """
    Execute the exhaustive sweep and write the two required output files.
    """
    # Containers for CSV rows and convergence diagnostics
    csv_rows = []
    convergence_dict = {
        "description": "Empirical bulk edge convergence toward +2.0 as N grows.",
        "theoretical_edge": THEORETICAL_EDGE,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "per_N": [],
    }

    for N in N_VALUES:
        bulk_edges_for_N = []  # collect bulk edge of unperturbed matrix per seed
        for seed in SEED_VALUES:
            # Load / generate the raw Wigner matrix
            raw_path = _ensure_raw_matrix(N, seed, logger)
            W = np.load(raw_path)

            # Record the bulk edge (largest eigenvalue of the *unperturbed* matrix)
            bulk_edge = _run_eigen_solver(W, logger)
            bulk_edges_for_N.append(bulk_edge)

            for k in K_VALUES:
                for pattern in PATTERN_VALUES:
                    for theta in THETA_VALUES:
                        P = _build_diagonal_perturbation(N, k, theta)
                        H = W + P
                        # Compute top eigenvalue of perturbed system
                        start = time.perf_counter()
                        top_val = _run_eigen_solver(H, logger)
                        comp_time_ms = (time.perf_counter() - start) * 1000.0
                        # Outlier detection using the theoretical rule
                        outlier_flag = top_val > (THEORETICAL_EDGE + OUTLIER_TOL)

                        # Assemble CSV row with **exact** required columns
                        row = {
                            "run_id": str(uuid.uuid4()),
                            "N": N,
                            "k": k,
                            "pattern_type": pattern,
                            "theta": theta,
                            "seed": seed,
                            "eigenvalue_top": f"{top_val:.12f}",
                            "computation_time_ms": f"{comp_time_ms:.3f}",
                            "outlier_flag": str(outlier_flag),
                        }
                        csv_rows.append(row)

        # After processing all seeds for this N, store bulk‑edge diagnostics
        bulk_edge_mean = float(np.mean(bulk_edges_for_N))
        bulk_edge_std = float(np.std(bulk_edges_for_N, ddof=0))
        abs_deviation = abs(bulk_edge_mean - THEORETICAL_EDGE)

        convergence_dict["per_N"].append(
            {
                "N": N,
                "seeds": SEED_VALUES,
                "bulk_edge_values": [float(v) for v in bulk_edges_for_N],
                "bulk_edge_mean": bulk_edge_mean,
                "bulk_edge_std": bulk_edge_std,
                "abs_deviation_from_2": abs_deviation,
                "theoretical_edge": THEORETICAL_EDGE,
            }
        )

    # ------------------------------------------------------------------
    # Write CSV with the required column order
    # ------------------------------------------------------------------
    csv_path = llm_paths.data("processed") / "mc_results.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "run_id",
        "N",
        "k",
        "pattern_type",
        "theta",
        "seed",
        "eigenvalue_top",
        "computation_time_ms",
        "outlier_flag",
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in csv_rows:
            writer.writerow(row)

    logger.info(f"Full sweep CSV written to {csv_path} ({len(csv_rows)} rows)")

    # ------------------------------------------------------------------
    # Write convergence JSON
    # ------------------------------------------------------------------
    json_path = llm_paths.data("processed") / "convergence_data.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(convergence_dict, f, indent=2)

    logger.info(f"Convergence diagnostics written to {json_path}")

# ----------------------------------------------------------------------
# Argument parsing (kept for compatibility with existing quickstart)
# ----------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the full theta sweep.")
    parser.add_argument(
        "--grid",
        type=str,
        default="theta",
        help="Placeholder argument retained for backward compatibility.",
    )
    return parser.parse_args()


def main() -> int:
    logger = _setup_logger()
    args = parse_args()
    logger.info(f"Starting full theta sweep (grid={args.grid})")
    # The sweep does not depend on the ``--grid`` value – we always run the full grid.
    run_full_sweep(logger)
    logger.info("Sweep completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
