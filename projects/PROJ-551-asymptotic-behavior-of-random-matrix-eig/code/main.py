"""
Single‑run entry point for the random‑matrix study (Task T003).

This script can be executed as a module:

    python -m code.main --mode single --N 1000 --seed 42 --theta 2.5 --k 1 --pattern diagonal

It performs the following steps:

1. Generates (or loads) a Wigner matrix ``data/raw/matrix_N<N>_seed<seed>.npy``.
   Scaling is 1/sqrt(N) as required by the specification.
2. Constructs a rank‑1 diagonal perturbation with spectral norm ``theta``.
3. Calls the project's eigen‑solver to obtain the top‑10 eigenvalues.
4. Flags outliers using the theoretical rule ``value > 2.0 + 0.05``.
5. Writes a JSON file ``data/processed/single_run_results.json`` that
   contains a ``SimulationRun`` record and an array of ten
   ``EigenvalueResult`` records (nested under the same ``run_id``).
6. Updates ``data/checksums.yaml`` with the SHA‑256 checksum of the raw matrix.
7. Logs the full run to ``data/logs/single_run.log`` (including peak memory usage).
8. Enforces SC‑001: raises an error if peak memory exceeds 7 GB.
"""

import argparse
import json
import logging
import sys
import time
import uuid
from pathlib import Path

import numpy as np
import psutil
import yaml
from scipy.sparse.linalg import eigsh

# Project‑specific utilities
from utils.config import get_project_paths, get_outlier_tolerance

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _setup_logger(log_path: Path) -> logging.Logger:
    """Configure a logger that writes to both stdout and a file."""
    logger = logging.getLogger("single_run")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # Console handler
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    # File handler
    if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
        log_path.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_path, mode="a")
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger


def _generate_wigner(N: int, seed: int) -> np.ndarray:
    """Generate a symmetric Wigner matrix scaled by 1/sqrt(N)."""
    rng = np.random.default_rng(seed)
    A = rng.standard_normal((N, N))
    A = (A + A.T) / 2.0  # Symmetrize
    A /= np.sqrt(N)
    return A


def _load_or_create_matrix(N: int, seed: int, raw_dir: Path, logger: logging.Logger) -> Path:
    """Return the path to the raw matrix file, creating it if necessary."""
    matrix_path = raw_dir / f"matrix_N{N}_seed{seed}.npy"
    if matrix_path.is_file():
        logger.info(f"Raw matrix already exists: {matrix_path}")
    else:
        logger.info(f"Generating Wigner matrix N={N}, seed={seed}")
        matrix = _generate_wigner(N, seed)
        raw_dir.mkdir(parents=True, exist_ok=True)
        np.save(matrix_path, matrix)
        logger.info(f"Saved raw matrix to {matrix_path}")
    return matrix_path


def _create_diagonal_perturbation(N: int, theta: float) -> np.ndarray:
    """Rank‑1 diagonal perturbation: only the (0,0) entry is non‑zero."""
    P = np.zeros((N, N))
    P[0, 0] = theta
    return P


def _compute_top_eigenvalues(matrix: np.ndarray, k: int = 10) -> np.ndarray:
    """Compute the top‑k eigenvalues using ARPACK (eigsh)."""
    # eigsh works on symmetric matrices; which='LA' gives largest algebraic.
    eigenvalues, _ = eigsh(matrix, k=k, which="LA", tol=1e-10, maxiter=1000)
    # eigsh returns eigenvalues in ascending order; reverse for descending.
    return np.sort(eigenvalues)[::-1]


def _is_outlier(value: float, edge: float = 2.0, tol: float = 0.05) -> bool:
    """Theoretical outlier rule (value > edge + tol)."""
    return value > (edge + tol)


def _write_checksum(matrix_path: Path, checksum_path: Path, logger: logging.Logger):
    """Compute SHA‑256 of the raw matrix and store it in a YAML manifest."""
    import hashlib

    with open(matrix_path, "rb") as f:
        sha256 = hashlib.sha256(f.read()).hexdigest()

    # Load existing manifest if present
    if checksum_path.is_file():
        with open(checksum_path, "r", encoding="utf-8") as f:
            manifest = yaml.safe_load(f) or {}
    else:
        manifest = {}

    manifest[str(matrix_path)] = sha256

    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    with open(checksum_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(manifest, f)

    logger.info(f"Checksum written to {checksum_path}")


def _record_memory_usage(logger: logging.Logger) -> float:
    """Return peak RSS memory usage (GB) and log it."""
    proc = psutil.Process()
    rss_bytes = proc.memory_info().rss
    rss_gb = rss_bytes / (1024 ** 3)
    logger.info(f"Peak Memory (RSS): {rss_gb:.3f} GB")
    return rss_gb


# ----------------------------------------------------------------------
# Main routine
# ----------------------------------------------------------------------
def main():
    """
    Entry point for the single‑run CLI.

    If the script is invoked without any command‑line arguments, we fall back
    to the canonical quick‑start parameters (N=1000, seed=42, theta=2.5,
    k=1, pattern=diagonal). This makes the module runnable both as a
    demonstration and as part of the automated verification pipeline.
    """
    # ------------------------------------------------------------------
    # Provide sensible defaults when the user supplies no arguments.
    # ------------------------------------------------------------------
    if len(sys.argv) == 1:
        # No arguments supplied – inject the quick‑start defaults.
        sys.argv.extend([
            "--mode", "single",
            "--N", "1000",
            "--seed", "42",
            "--theta", "2.5",
            "--k", "1",
            "--pattern", "diagonal",
        ])

    parser = argparse.ArgumentParser(
        description="Run a single random‑matrix simulation (Task T003)."
    )
    parser.add_argument("--mode", required=True, choices=["single"])
    parser.add_argument("--N", type=int, required=True, help="Matrix dimension")
    parser.add_argument("--seed", type=int, required=True, help="Random seed")
    parser.add_argument("--theta", type=float, required=True, help="Perturbation norm")
    parser.add_argument("--k", type=int, required=True, help="Perturbation rank")
    parser.add_argument(
        "--pattern",
        required=True,
        choices=["diagonal", "block-sparse", "random-sparse"],
        help="Sparsity pattern (only diagonal is used for the single run)",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Resolve project paths
    # ------------------------------------------------------------------
    paths = get_project_paths()
    raw_dir = paths["raw"]
    processed_dir = paths["processed"]
    logs_dir = paths["logs"]
    checksums_path = paths["root"] / "data" / "checksums.yaml"

    log_file = logs_dir / "single_run.log"
    logger = _setup_logger(log_file)

    logger.info("=== Single‑run simulation start ===")
    logger.info(
        f"Parameters: N={args.N}, seed={args.seed}, theta={args.theta}, "
        f"k={args.k}, pattern={args.pattern}"
    )

    start_time = time.time()

    # ------------------------------------------------------------------
    # 1. Load or generate raw Wigner matrix
    # ------------------------------------------------------------------
    matrix_path = _load_or_create_matrix(args.N, args.seed, raw_dir, logger)
    matrix = np.load(matrix_path)

    # ------------------------------------------------------------------
    # 2. Build perturbation
    # ------------------------------------------------------------------
    if args.pattern != "diagonal":
        logger.error("Only the 'diagonal' pattern is supported for the single‑run task.")
        sys.exit(1)

    perturbation = _create_diagonal_perturbation(args.N, args.theta)

    # ------------------------------------------------------------------
    # 3. Form the perturbed matrix and compute eigenvalues
    # ------------------------------------------------------------------
    perturbed = matrix + perturbation
    top_vals = _compute_top_eigenvalues(perturbed, k=10)

    # ------------------------------------------------------------------
    # 4. Determine outlier flags (theoretical rule)
    # ------------------------------------------------------------------
    outlier_flags = [_is_outlier(v) for v in top_vals]

    # ------------------------------------------------------------------
    # 5. Assemble JSON payload
    # ------------------------------------------------------------------
    run_id = str(uuid.uuid4())
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())
    computation_time_ms = (time.time() - start_time) * 1000.0

    # Empirical bulk edge: 99th percentile of eigenvalues of the *unperturbed* matrix
    raw_eig = _compute_top_eigenvalues(matrix, k=10)
    empirical_bulk_edge = float(np.percentile(raw_eig, 99))

    # The schema expects a numeric value for support_density; for a diagonal
    # perturbation the density is effectively zero.
    support_density = 0.0

    sim_record = {
        "run_id": run_id,
        "timestamp": timestamp,
        "seed": args.seed,
        "N": args.N,
        "k": args.k,
        "theta": args.theta,
        "pattern_type": args.pattern,
        "support_density": support_density,
        "computation_time_ms": computation_time_ms,
        "empirical_bulk_edge": empirical_bulk_edge,
    }

    eigen_records = []
    for idx, val in enumerate(top_vals, start=1):
        eigen_records.append(
            {
                "run_id": run_id,
                "eigenvalue_index": idx,
                "value": float(val),
                "is_outlier": outlier_flags[idx - 1],
                "theoretical_bbp": args.theta,
                "deviation": float(val) - args.theta,
            }
        )

    output_json = {
        **sim_record,
        "eigenvalues": eigen_records,
    }

    json_path = processed_dir / "single_run_results.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_json, f, indent=2)
    logger.info(f"Wrote SimulationRun JSON to {json_path}")

    # ------------------------------------------------------------------
    # 6. Write checksum manifest
    # ------------------------------------------------------------------
    _write_checksum(matrix_path, checksums_path, logger)

    # ------------------------------------------------------------------
    # 7. Memory usage & SC‑001 enforcement
    # ------------------------------------------------------------------
    peak_gb = _record_memory_usage(logger)
    if peak_gb > 7.0:
        logger.error(f"Peak memory {peak_gb:.2f} GB exceeds the 7 GB limit (SC‑001).")
        raise RuntimeError("Memory usage limit exceeded")

    logger.info("=== Single‑run simulation completed successfully ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())