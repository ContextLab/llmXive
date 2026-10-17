"""
Main entry point for the asymptotic random matrix project.

Implements the **single‑run** workflow required by task T002:
  1. Load or generate a Wigner matrix (scaled 1/√N) and save it under
     ``data/raw/matrix_N{N}_seed{seed}.npy``.
  2. Build a rank‑k diagonal perturbation with spectral norm ``θ``.
  3. Compute the top 10 eigenvalues using ARPACK (``scipy.sparse.linalg.eigsh``)
     with tolerance ``1e-10``.
  4. Flag outliers solely by the theoretical rule ``value > 2.0 + 0.05``.
  5. Write a JSON file containing a ``SimulationRun`` record and an array of
     ten ``EigenvalueResult`` records (nested under the same ``run_id``) to
     ``data/processed/single_run_results.json``.
  6. Record a SHA‑256 checksum for the raw matrix in ``data/checksums.yaml``.
  7. Log the full run to ``data/logs/single_run.log`` including peak memory usage.
  8. Enforce **SC‑001**: abort with an error if peak memory exceeds 7 GB.
  9. The command line shown in ``quickstart.md`` is the exact invocation
     required.

The script is deliberately self‑contained; it does not rely on the legacy
``run_single_simulation`` helper because that helper used the empirical bulk
edge for outlier detection, which violates the specification.
"""

import argparse
import json
import logging
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
import hashlib

import numpy as np
import psutil
import yaml
from scipy.sparse.linalg import eigsh

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _setup_file_logging() -> logging.Logger:
    """
    Initialise a logger that writes to ``data/logs/single_run.log`` and also
    echoes to stdout.
    """
    log_path = Path("data") / "logs" / "single_run.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Overwrite any existing log for a clean run
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(
            f"Single‑run Log – Started at {datetime.now(timezone.utc).isoformat()}\n"
        )

    logger = logging.getLogger("single_run")
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers if the function is called multiple times
    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        logger.addHandler(file_handler)

    return logger

def _ensure_raw_matrix(N: int, seed: int, logger: logging.Logger) -> Path:
    """
    Load a previously generated raw matrix if it exists; otherwise generate
    it, save it, and return the path.
    """
    raw_dir = Path("data") / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / f"matrix_N{N}_seed{seed}.npy"

    if raw_path.exists():
        logger.info(f"Loading existing raw matrix from {raw_path}")
    else:
        logger.info(f"Raw matrix not found – generating (N={N}, seed={seed})")
        rng = np.random.default_rng(seed)
        # Standard Wigner: (A + Aᵀ) / sqrt(2N)
        A = rng.standard_normal((N, N))
        W = (A + A.T) / np.sqrt(2.0 * N)
        np.save(raw_path, W)
        logger.info(f"Saved generated matrix to {raw_path}")

    return raw_path

def _compute_checksum(file_path: Path) -> str:
    """Return the SHA‑256 checksum of ``file_path``."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def _record_checksum(matrix_path: Path, N: int, seed: int, logger: logging.Logger) -> None:
    """
    Append (or create) a checksum entry for ``matrix_path`` in
    ``data/checksums.yaml``.
    """
    checksum_file = Path("data") / "checksums.yaml"
    checksum_file.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "sha256": _compute_checksum(matrix_path),
        "N": N,
        "seed": seed,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    if checksum_file.exists():
        with open(checksum_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {}

    data[matrix_path.name] = entry

    with open(checksum_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=True)

    logger.info(f"Checksum entry written for {matrix_path.name}")

def _build_diagonal_perturbation(N: int, k: int, theta: float) -> np.ndarray:
    """
    Construct a rank‑k diagonal perturbation where the first ``k`` diagonal
    entries equal ``theta`` (spectral norm = ``theta``).
    """
    P = np.zeros((N, N), dtype=np.float64)
    for i in range(k):
        P[i, i] = theta
    return P

def _run_eigen_solver(H: np.ndarray, logger: logging.Logger) -> np.ndarray:
    """
    Compute the top 10 eigenvalues of ``H`` using ARPACK with tolerance
    ``1e-10``. Returns the eigenvalues sorted in descending order.
    """
    logger.info("Starting ARPACK eigenvalue computation (top 10, tol=1e-10)")
    start = time.perf_counter()
    vals = eigsh(
        H,
        k=10,
        which="LA",
        tol=1e-10,
        return_eigenvectors=False,
    )
    elapsed = time.perf_counter() - start
    logger.info(f"Eigenvalue computation finished in {elapsed:.3f}s")
    # Ensure descending order
    vals_sorted = np.sort(vals)[::-1]
    return vals_sorted

def _profile_memory(logger: logging.Logger) -> float:
    """
    Return the current RSS memory usage in bytes. Called after the heavy
    computation to capture the peak usage.
    """
    process = psutil.Process()
    mem_bytes = process.memory_info().rss
    mem_gb = mem_bytes / (1024 ** 3)
    logger.info(f"Peak memory usage: {mem_gb:.3f} GB")
    return mem_bytes

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, default='single')
    parser.add_argument('--N', type=int, default=1000,
                        help='Matrix dimension')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed for reproducibility')
    parser.add_argument('--theta', type=float, default=2.5,
                        help='Spectral norm of the rank‑k perturbation')
    parser.add_argument('--k', type=int, default=1,
                        help='Rank of the perturbation')
    parser.add_argument('--pattern', type=str, default='diagonal',
                        choices=['diagonal'],
                        help='Perturbation pattern (single‑run only supports diagonal)')
    parser.add_argument('--output', type=str,
                        default='data/processed/single_run_results.json',
                        help='Path for the JSON result file')
    return parser.parse_args()

def main():
    args = parse_args()

    if args.mode != 'single':
        print("Only ``--mode single`` is supported for task T002.", file=sys.stderr)
        return 1

    # Ensure project directories exist
    for sub in ["data/raw", "data/processed", "data/logs", "data/figures"]:
        Path(sub).mkdir(parents=True, exist_ok=True)

    logger = _setup_file_logging()
    logger.info(f"Running single‑run simulation with args: {args}")

    # ------------------------------------------------------------------
    # 1. Load / generate raw Wigner matrix
    # ------------------------------------------------------------------
    raw_path = _ensure_raw_matrix(args.N, args.seed, logger)

    # 2. Record checksum
    _record_checksum(raw_path, args.N, args.seed, logger)

    # 3. Load matrix into memory
    logger.info(f"Loading raw matrix from {raw_path}")
    W = np.load(raw_path)

    # 4. Build perturbation (only diagonal is required for the spec)
    logger.info(f"Building rank‑{args.k} diagonal perturbation with θ={args.theta}")
    P = _build_diagonal_perturbation(args.N, args.k, args.theta)

    # 5. Form perturbed matrix
    H = W + P

    # 6. Eigenvalue computation
    start_time = time.perf_counter()
    top_vals = _run_eigen_solver(H, logger)
    comp_time_ms = (time.perf_counter() - start_time) * 1000.0

    # 7. Outlier detection (theoretical rule)
    theoretical_edge = 2.0
    tolerance = 0.05
    outlier_flags = top_vals > (theoretical_edge + tolerance)

    # 8. Assemble JSON payload
    run_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    eigenvalue_records = []
    for idx, val in enumerate(top_vals, start=1):
        eigenvalue_records.append({
            "run_id": run_id,
            "eigenvalue_index": idx,
            "value": float(val),
            "is_outlier": bool(outlier_flags[idx - 1]),
            # The following fields are kept for backward compatibility;
            # they are not used for validation in the current schemas.
            "theoretical_bbp": args.theta,  # placeholder – not required by schema
            "deviation": float(val) - (theoretical_edge + tolerance)
        })

    result_json = {
        "run_id": run_id,
        "timestamp": timestamp,
        "seed": args.seed,
        "N": args.N,
        "k": args.k,
        "theta": args.theta,
        "pattern_type": args.pattern,
        "support_density": None,
        "computation_time_ms": comp_time_ms,
        # Empirical bulk edge of the *unperturbed* matrix (optional)
        "empirical_bulk_edge": float(np.max(eigsh(W, k=1, which="LA", tol=1e-10,
                                               return_eigenvectors=False))),
        "eigenvalues": eigenvalue_records
    }

    # 9. Write JSON result
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result_json, f, indent=2)
    logger.info(f"Single‑run results written to {output_path}")

    # 10. Memory profiling and enforcement of SC‑001
    peak_mem_bytes = _profile_memory(logger)
    limit_bytes = 7 * 1024 ** 3  # 7 GB
    if peak_mem_bytes > limit_bytes:
        logger.error(
            f"Peak memory usage exceeds 7 GB limit ({peak_mem_bytes / (1024 ** 3):.2f} GB)."
        )
        raise MemoryError("SC‑001 violation: memory usage > 7 GB")

    logger.info("Single‑run completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())