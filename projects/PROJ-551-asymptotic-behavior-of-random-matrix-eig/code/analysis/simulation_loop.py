import time
import uuid
import numpy as np
from pathlib import Path
from datetime import datetime, timezone
from analysis.eigen_solver import compute_top_eigenvalues_iterative
from utils.config import get_outlier_tolerance

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
        density = 0.1
        m = max(1, int(density * N) // k)
        idx = rng.permutation(N)[: m * k].reshape(k, m)
        for j in range(k):
            v = np.zeros(N)
            v[idx[j]] = rng.choice([-1.0, 1.0], size=m) / np.sqrt(m)
            P += theta * np.outer(v, v)
    else:
        raise ValueError(f"Unknown pattern_type: {pattern}")
    return P

def run_single_simulation(params: dict) -> dict:
    """
    Executes a single simulation run: loads raw Wigner matrix,
    applies perturbation, and computes eigenvalues.
    """
    N = params['N']
    seed = params['seed']
    theta = params['theta']
    k = params['k']
    pattern = params['pattern']

    start_time = time.perf_counter()
    
    # Load checksummed raw matrix
    raw_path = Path("data/raw") / f"matrix_N{N}_seed{seed}.npy"
    W = np.load(raw_path)
    
    # Compute empirical bulk edge (largest eigenvalue of unperturbed W)
    bulk_edge = float(compute_top_eigenvalues_iterative(W, k=1)[0])
    
    # Apply perturbation
    P = build_perturbation(N, k, theta, pattern, seed)
    H = W + P
    
    # Compute top 10 eigenvalues
    eigenvalues_raw = compute_top_eigenvalues_iterative(H, k=10)
    
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    run_id = str(uuid.uuid4())
    
    # Outlier rule FR-004: value > bulk_edge + 0.05
    tol = get_outlier_tolerance()
    theoretical_bbp = theta + 1.0/theta if theta != 0 else 0.0
    
    eigenvalue_results = []
    for i, val in enumerate(eigenvalues_raw, 1):
        val_float = float(val)
        eigenvalue_results.append({
            "run_id": run_id,
            "eigenvalue_index": i,
            "value": val_float,
            "is_outlier": val_float > (bulk_edge + tol),
            "theoretical_bbp": float(theoretical_bbp),
            "deviation": float(val_float - theoretical_bbp)
        })
        
    return {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "seed": seed,
        "N": N,
        "k": k,
        "theta": theta,
        "pattern_type": pattern,
        "support_density": None,
        "computation_time_ms": float(elapsed_ms),
        "empirical_bulk_edge": bulk_edge,
        "eigenvalues": eigenvalue_results
    }
