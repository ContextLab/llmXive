"""
Single‑run entry point for the random‑matrix study (Task T002).

This script can be executed as a module:
    python -m code.main --mode single --N 1000 --seed 42 --theta 2.5 --k 1 --pattern diagonal

It performs the following steps:
1. Generates (or loads) a Wigner matrix `data/raw/matrix_N<N>_seed<seed>.npy`.
   Scaling is 1/sqrt(N) as required by the specification.
2. Constructs a rank‑1 diagonal perturbation with spectral norm `theta`.
3. Calls ARPACK via `scipy.sparse.linalg.eigsh` to obtain the top‑10 eigenvalues.
4. Flags outliers using the theoretical rule `value > 2.0 + 0.05`.
5. Writes a JSON file `data/processed/single_run_results.json` containing a
   `SimulationRun` record and an array of ten `EigenvalueResult` records.
6. Updates `data/checksums.yaml` with the SHA‑256 checksum of the raw matrix.
7. Logs the full run to `data/logs/single_run.log` (including peak memory usage).
8. Enforces SC‑001: raises an error if peak memory exceeds 7 GB.
"""

import argparse
import json
import logging
import sys
import time
import uuid
import hashlib
import resource
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import psutil
import yaml
from scipy.sparse.linalg import eigsh

from llmxive_toolkit import paths as llm_paths

def _setup_logger(log_path: Path) -> logging.Logger:
    """Configure a logger that writes to both stdout and a file."""
    logger = logging.getLogger("single_run")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

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
    A = (A + A.T) / 2.0
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
    # which="LA" finds the largest algebraic eigenvalues
    eigenvalues, _ = eigsh(matrix, k=k, which="LA", tol=1e-10, maxiter=1000)
    return np.sort(eigenvalues)[::-1]

def _is_outlier(value: float, edge: float = 2.0, tol: float = 0.05) -> bool:
    """Theoretical outlier rule (value > edge + tol)."""
    return value > (edge + tol)

def _write_checksum(matrix_path: Path, checksum_path: Path, logger: logging.Logger):
    """Compute SHA‑256 of the raw matrix and store it in a YAML manifest."""
    with open(matrix_path, "rb") as f:
        sha256 = hashlib.sha256(f.read()).hexdigest()

    if checksum_path.is_file():
        with open(checksum_path, "r", encoding="utf-8") as f:
            try:
                manifest = yaml.safe_load(f) or {}
            except yaml.YAMLError:
                manifest = {}
    else:
        manifest = {}

    # Store as a detailed entry to match existing project style
    manifest[matrix_path.name] = {
        "path": str(matrix_path),
        "sha256": sha256,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    with open(checksum_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(manifest, f)

    logger.info(f"Checksum written to {checksum_path}")

def _get_peak_memory_gb() -> float:
    """Return peak RSS memory usage in GB using resource module (Linux)."""
    # ru_maxrss is in KB on Linux
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return usage / (1024 * 1024)

def main():
    parser = argparse.ArgumentParser(description="Run a single random‑matrix simulation (Task T002).")
    parser.add_argument("--mode", required=True, choices=["single"])
    parser.add_argument("--N", type=int, required=True, help="Matrix dimension")
    parser.add_argument("--seed", type=int, required=True, help="Random seed")
    parser.add_argument("--theta", type=float, required=True, help="Perturbation norm")
    parser.add_argument("--k", type=int, required=True, help="Perturbation rank")
    parser.add_argument("--pattern", required=True, choices=["diagonal", "block-sparse", "random-sparse"])
    args = parser.parse_args()

    raw_dir = llm_paths.data("raw")
    processed_dir = llm_paths.data("processed")
    logs_dir = llm_paths.data("logs")
    checksum_path = llm_paths.data("checksums.yaml")

    log_file = logs_dir / "single_run.log"
    logger = _setup_logger(log_file)

    logger.info("=== Single‑run simulation start ===")
    logger.info(f"Parameters: N={args.N}, seed={args.seed}, theta={args.theta}, k={args.k}, pattern={args.pattern}")

    start_time = time.time()

    # 1. Matrix Generation
    matrix_path = _load_or_create_matrix(args.N, args.seed, raw_dir, logger)
    matrix = np.load(matrix_path)

    # 2. Perturbation
    if args.pattern != "diagonal":
        logger.error("Only 'diagonal' pattern is supported for T002 single-run.")
        sys.exit(1)
    perturbation = _create_diagonal_perturbation(args.N, args.theta)

    # 3. Eigenvalues
    perturbed = matrix + perturbation
    top_vals = _compute_top_eigenvalues(perturbed, k=10)

    # 4. Outlier detection
    outlier_flags = [_is_outlier(v) for v in top_vals]

    # 5. JSON Payload
    run_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    computation_time_ms = (time.time() - start_time) * 1000.0

    # Empirical bulk edge: 99th percentile of the unperturbed matrix
    # For N=1000, dense eigvalsh is efficient
    raw_eigs = np.linalg.eigvalsh(matrix)
    empirical_bulk_edge = float(np.percentile(raw_eigs, 99))

    sim_record = {
        "run_id": run_id,
        "timestamp": timestamp,
        "seed": args.seed,
        "N": args.N,
        "k": args.k,
        "theta": args.theta,
        "pattern_type": args.pattern,
        "support_density": 0.0,
        "computation_time_ms": computation_time_ms,
        "empirical_bulk_edge": empirical_bulk_edge,
    }

    eigen_records = []
    for idx, val in enumerate(top_vals, start=1):
        eigen_records.append({
            "run_id": run_id,
            "eigenvalue_index": idx,
            "value": float(val),
            "is_outlier": outlier_flags[idx - 1],
            "theoretical_bbp": args.theta,
            "deviation": float(val) - args.theta,
        })

    output_json = {**sim_record, "eigenvalues": eigen_records}
    json_path = processed_dir / "single_run_results.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_json, f, indent=2)
    logger.info(f"Wrote results to {json_path}")

    # 6. Checksum
    _write_checksum(matrix_path, checksum_path, logger)

    # 7. Memory Monitoring
    peak_gb = _get_peak_memory_gb()
    logger.info(f"Peak Memory (RSS): {peak_gb:.3f} GB")

    # 8. SC-001 Enforcement
    if peak_gb > 7.0:
        logger.error(f"Peak memory {peak_gb:.2f} GB exceeds 7 GB limit.")
        raise RuntimeError("Memory usage limit exceeded (SC-001)")

    logger.info("=== Single‑run simulation completed successfully ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
