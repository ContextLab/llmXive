import time
import uuid
import numpy as np
from datetime import datetime, timezone
from generators.perturbation import create_perturbation
from analysis.eigen_solver import compute_top_eigenvalues_iterative

def run_single_simulation(params: dict) -> dict:
    N = params['N']
    seed = params['seed']
    theta = params['theta']
    k = params['k']
    pattern = params['pattern']

    # 1. Load Raw Matrix
    import numpy as np
    from pathlib import Path
    raw_path = Path(f"data/raw/matrix_N{N}_seed{seed}.npy")
    W = np.load(raw_path)

    start_time = time.perf_counter()

    # 2. Compute Empirical Bulk Edge (max eigenvalue of unperturbed W)
    # For T001, we use the raw matrix as the baseline.
    empirical_bulk_edge = float(np.max(np.linalg.eigvalsh(W)))

    # 3. Build Perturbation
    P = create_perturbation(N, theta, k, pattern)
    H = W + P

    # 4. Compute Top 10 Eigenvalues
    eigs = compute_top_eigenvalues_iterative(H, k=10)
    
    end_time = time.perf_counter()
    comp_time_ms = (end_time - start_time) * 1000

    # 5. Construct Result
    run_id = str(uuid.uuid4())
    theoretical_bbp = theta + (1.0 / theta) if theta != 0 else 0
    
    # Support density is null for diagonal
    support_density = None if pattern == 'diagonal' else 0.1 

    eigenvalue_results = []
    for idx, val in enumerate(eigs, 1):
        # FR-004: outlier if value > empirical_bulk_edge + 0.05
        is_outlier = bool(val > empirical_bulk_edge + 0.05)
        eigenvalue_results.append({
            "run_id": run_id,
            "eigenvalue_index": idx,
            "value": float(val),
            "is_outlier": is_outlier,
            "theoretical_bbp": float(theoretical_bbp),
            "deviation": float(val - theoretical_bbp)
        })

    return {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "seed": seed,
        "N": N,
        "k": k,
        "theta": theta,
        "pattern_type": pattern,
        "support_density": support_density,
        "computation_time_ms": comp_time_ms,
        "empirical_bulk_edge": empirical_bulk_edge,
        "eigenvalues": eigenvalue_results
    }
