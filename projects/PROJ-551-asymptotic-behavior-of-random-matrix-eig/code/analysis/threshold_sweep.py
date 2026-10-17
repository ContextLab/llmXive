"""
T002: Theta sweep orchestrator (User Story 2).

Executes the full parameter sweep over:
  N in {100, 500, 1000, 2000}
  theta in {0.8, 1.0, 1.2, 1.5, 2.0, 2.5, 3.0}
  seeds in {42, 123, 456, 789}
  k in {1, 2, 5}
  pattern_type in {diagonal, block-sparse, random-sparse}

For each (N, seed) the base Wigner matrix is generated deterministically
(or loaded from data/raw/sweep/ if already present), checksummed with
SHA-256, and reused across all theta / k / pattern configurations.

Correct Wigner scaling: W = (A + A^T) / sqrt(2*N), so that each
off-diagonal entry has variance 1/N and the semicircle edge is +/-2.0.

Outputs (real ARPACK measurements, CPU-only):
  data/processed/mc_results.csv          (1008 rows)
  data/processed/convergence_data.json   (per-N bulk-edge convergence to +/-2.0)
  data/logs/threshold_sweep.log
"""

import argparse
import csv
import hashlib
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.sparse.linalg import eigsh

CODE_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = CODE_ROOT.parent
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

DATA_RAW_SWEEP = PROJECT_ROOT / "data" / "raw" / "sweep"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_LOGS = PROJECT_ROOT / "data" / "logs"

# Grid definition (T002)
N_VALUES = [100, 500, 1000, 2000]
THETA_VALUES = [0.8, 1.0, 1.2, 1.5, 2.0, 2.5, 3.0]
SEEDS = [42, 123, 456, 789]
K_VALUES = [1, 2, 5]
PATTERNS = ["diagonal", "block-sparse", "random-sparse"]
RANDOM_SPARSE_DENSITY = 0.1
EIGSH_TOL = 1e-8
THEORETICAL_EDGE = 2.0
# Cache filename suffix distinguishes the corrected scaling from any stale raw matrices.
CACHE_SUFFIX = "v2"


def setup_logging() -> logging.Logger:
    DATA_LOGS.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("threshold_sweep")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(fmt)
        fh = logging.FileHandler(DATA_LOGS / "threshold_sweep.log")
        fh.setFormatter(fmt)
        logger.addHandler(sh)
        logger.addHandler(fh)
    return logger


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def generate_wigner_matrix(N: int, seed: int) -> np.ndarray:
    """Standard Wigner matrix: symmetric, entries N(0,1), scaled 1/sqrt(N).
    W = (A + A^T) / sqrt(2*N).
    """
    rng = np.random.default_rng(seed)
    A = rng.standard_normal((N, N))
    W = (A + A.T) / np.sqrt(2.0 * N)
    return W


def get_base_matrix(N: int, seed: int, logger: logging.Logger) -> np.ndarray:
    """Load the checksummed raw matrix, or generate + checksum it once."""
    DATA_RAW_SWEEP.mkdir(parents=True, exist_ok=True)
    path = DATA_RAW_SWEEP / f"matrix_{CACHE_SUFFIX}_N{N}_seed{seed}.npy"
    if path.exists():
        logger.info(f"Loading raw matrix {path}")
        return np.load(path)
    logger.info(f"Generating raw Wigner matrix N={N} seed={seed}")
    W = generate_wigner_matrix(N, seed)
    np.save(path, W)
    digest = sha256_of_file(path)
    manifest_path = DATA_RAW_SWEEP / "checksums.json"
    manifest = {}
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = json.load(f)
    manifest[path.name] = {
        "sha256": digest,
        "N": N,
        "seed": seed,
        "scaling": "(A + A^T) / sqrt(2*N)",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    logger.info(f"Checksummed {path.name}: {digest}")
    return W


def build_perturbation(N: int, k: int, theta: float, pattern: str, seed: int) -> np.ndarray:
    """Rank-k symmetric perturbation with spectral norm theta."""
    rng = np.random.default_rng(seed + 7919)
    P = np.zeros((N, N), dtype=np.float64)
    if pattern == "diagonal":
        for j in range(k):
            P[j, j] = theta
    elif pattern == "block-sparse":
        block = N // k
        for j in range(k):
            v = np.zeros(N)
            lo = j * block
            hi = (j + 1) * block if j < k - 1 else N
            v[lo:hi] = 1.0 / np.sqrt(hi - lo)
            P += theta * np.outer(v, v)
    elif pattern == "random-sparse":
        m = max(1, int(RANDOM_SPARSE_DENSITY * N) // k)
        idx = rng.permutation(N)[: m * k].reshape(k, m)
        for j in range(k):
            v = np.zeros(N)
            v[idx[j]] = rng.choice([-1.0, 1.0], size=m) / np.sqrt(m)
            P += theta * np.outer(v, v)
    else:
        raise ValueError(f"Unknown pattern_type: {pattern}")
    return P


def top_eigenvalue_arpack(H: np.ndarray) -> float:
    """Real ARPACK (scipy.sparse.linalg.eigsh) largest algebraic eigenvalue."""
    vals = eigsh(H, k=1, which="LA", tol=EIGSH_TOL, return_eigenvectors=False)
    return float(np.max(vals))


def run_theta_sweep(logger: logging.Logger):
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    # 1. Base matrices + empirical bulk edge
    base_matrices = {}
    bulk_edges = {}
    for N in N_VALUES:
        bulk_edges[N] = {}
        for seed in SEEDS:
            W = get_base_matrix(N, seed, logger)
            base_matrices[(N, seed)] = W
            edge = top_eigenvalue_arpack(W)
            bulk_edges[N][seed] = edge
            logger.info(f"Bulk edge N={N} seed={seed}: {edge:.6f}")

    # Sanity check on scaling
    mean_edge_2000 = float(np.mean([bulk_edges[2000][s] for s in SEEDS]))
    if abs(mean_edge_2000 - THEORETICAL_EDGE) > 0.2:
        raise RuntimeError(
            f"Empirical bulk edge at N=2000 is {mean_edge_2000:.4f}, "
            f"expected ~2.0. Scaling is incorrect."
        )

    # 2. Full sweep
    rows = []
    total = len(N_VALUES) * len(THETA_VALUES) * len(SEEDS) * len(K_VALUES) * len(PATTERNS)
    expected = 1008
    logger.info(f"Starting sweep: {total} configurations (expected {expected})")

    done = 0
    t_sweep_start = time.perf_counter()
    for N in N_VALUES:
        for k in K_VALUES:
            for pattern in PATTERNS:
                for theta in THETA_VALUES:
                    for seed in SEEDS:
                        done += 1
                        W = base_matrices[(N, seed)]
                        P = build_perturbation(N, k, theta, pattern, seed)
                        H = W + P
                        t0 = time.perf_counter()
                        lam_top = top_eigenvalue_arpack(H)
                        elapsed_ms = (time.perf_counter() - t0) * 1000.0
                        run_id = f"N{N}_k{k}_{pattern}_theta{theta}_seed{seed}"
                        rows.append({
                            "run_id": run_id,
                            "N": N,
                            "k": k,
                            "pattern_type": pattern,
                            "theta": theta,
                            "seed": seed,
                            "eigenvalue_top": lam_top,
                            "empirical_bulk_edge": bulk_edges[N][seed],
                            "computation_time_ms": elapsed_ms,
                        })
                        if done % 100 == 0:
                            elapsed = time.perf_counter() - t_sweep_start
                            logger.info(f"Progress: {done}/{total} ({elapsed:.1f}s elapsed)")

    if len(rows) != expected:
        raise RuntimeError(f"Sweep produced {len(rows)} rows, expected {expected}")

    # 3. Write mc_results.csv
    csv_path = DATA_PROCESSED / "mc_results.csv"
    fieldnames = [
        "run_id", "N", "k", "pattern_type", "theta", "seed",
        "eigenvalue_top", "empirical_bulk_edge", "computation_time_ms",
    ]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    logger.info(f"Wrote {len(rows)} rows to {csv_path}")

    # 4. Convergence data
    per_N = []
    for N in N_VALUES:
        edges = np.array([bulk_edges[N][s] for s in SEEDS], dtype=float)
        per_N.append({
            "N": N,
            "seeds": SEEDS,
            "bulk_edge_values": [float(e) for e in edges],
            "bulk_edge_mean": float(np.mean(edges)),
            "bulk_edge_std": float(np.std(edges, ddof=1)) if len(edges) > 1 else 0.0,
            "abs_deviation_from_2": float(np.abs(np.mean(edges) - THEORETICAL_EDGE)),
            "theoretical_edge": THEORETICAL_EDGE,
        })
    convergence = {
        "description": "Empirical bulk edge convergence toward +2.0 as N grows.",
        "theoretical_edge": THEORETICAL_EDGE,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "per_N": per_N,
    }
    json_path = DATA_PROCESSED / "convergence_data.json"
    with open(json_path, "w") as f:
        json.dump(convergence, f, indent=2)
    logger.info(f"Wrote convergence data to {json_path}")

    return rows, convergence


def main():
    parser = argparse.ArgumentParser(description="T002 theta sweep orchestrator")
    parser.add_argument("--grid", type=str, default="theta", choices=["theta"])
    args = parser.parse_args()

    logger = setup_logging()
    logger.info(f"Starting threshold sweep (grid={args.grid}), CPU-only ARPACK solver")
    rows, convergence = run_theta_sweep(logger)
    logger.info(f"Sweep complete: {len(rows)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())