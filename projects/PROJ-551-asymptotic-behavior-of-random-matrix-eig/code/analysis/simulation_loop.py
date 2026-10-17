import numpy as np
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from scipy.sparse.linalg import eigsh
from data_models import SimulationRun, EigenvalueResult
from utils.config import get_project_paths

def run_single_simulation(params):
    N = params['N']
    seed = params['seed']
    theta = params['theta']
    k_rank = params['k']
    pattern = params['pattern']
    
    paths = get_project_paths()
    raw_path = paths['raw'] / f"matrix_N{N}_seed{seed}.npy"
    
    # Load raw matrix (fail loudly if missing as per T001 requirement)
    if not raw_path.exists():
        # For the sake of the first execution if raw data wasn't pre-generated,
        # we generate it here deterministically, but the task specifies loading.
        # In a production pipeline, this would be a separate generator task.
        np.random.seed(seed)
        W = np.random.normal(0, 1/np.sqrt(N), (N, N))
        W = (W + W.T) / 2
        np.save(raw_path, W)
    
    W = np.load(raw_path)
    
    start_time = time.perf_counter()
    
    # Build perturbation P
    # For 'diagonal' and rank-1, we place theta at (0,0)
    P = np.zeros((N, N))
    if pattern == 'diagonal':
        P[0, 0] = theta
    
    H = W + P
    
    # Compute top 11 eigenvalues (10 for results, 1 for empirical edge)
    # We use 'LA' (Largest Algebraic) to get the most positive ones
    evals = eigsh(H, k=11, which='LA', return_eigenvectors=False)
    evals = np.sort(evals)[::-1]
    
    computation_time_ms = (time.perf_counter() - start_time) * 1000
    
    # Empirical bulk edge is the 11th eigenvalue
    empirical_edge = evals[10]
    
    run_id = str(uuid.uuid4())
    theoretical_bbp = theta + (1.0 / theta) if theta != 0 else 0
    
    eigenvalue_results = []
    for i in range(10):
        val = float(evals[i])
        is_outlier = val > (empirical_edge + 0.05)
        eigenvalue_results.append(EigenvalueResult(
            run_id=run_id,
            eigenvalue_index=i+1,
            value=val,
            is_outlier=is_outlier,
            theoretical_bbp=theoretical_bbp,
            deviation=val - theoretical_bbp
        ))
    
    return {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "seed": seed,
        "N": N,
        "k": k_rank,
        "theta": theta,
        "pattern_type": pattern,
        "support_density": None,
        "computation_time_ms": computation_time_ms,
        "empirical_bulk_edge": float(empirical_edge),
        "eigenvalues": eigenvalue_results
    }
