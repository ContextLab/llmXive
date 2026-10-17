import numpy as np
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from utils.config import get_project_paths
from analysis.eigen_solver import compute_top_eigenvalues_iterative
from data_models import SimulationRun, EigenvalueResult

def run_single_simulation(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    End-to-end simulation: loads/generates Wigner matrix, applies perturbation, 
    computes eigenvalues, and detects outliers.
    """
    N = params['N']
    seed = params['seed']
    theta = params['theta']
    k = params['k']
    pattern = params['pattern']
    
    paths = get_project_paths()
    raw_path = paths['raw'] / f"matrix_N{N}_seed{seed}.npy"
    
    # 1. Load or Generate Raw Matrix
    if raw_path.exists():
        W = np.load(raw_path)
    else:
        np.random.seed(seed)
        # Wigner matrix: entries ~ N(0, 1/N), symmetric
        W = np.random.normal(0, 1/np.sqrt(N), (N, N))
        W = (W + W.T) / 2.0
        np.save(raw_path, W)
    
    # 2. Apply Perturbation
    # For T001: rank-1 diagonal perturbation with spectral norm theta
    # P = diag(theta, 0, ..., 0)
    P = np.zeros((N, N))
    if pattern == 'diagonal':
        P[0, 0] = theta
    # (Other patterns would be implemented for T002/T007)
    
    H = W + P
    
    # 3. Compute Eigenvalues
    start_time = time.perf_counter()
    # Compute top 11 to determine empirical bulk edge (the 11th is our bulk proxy)
    eigs = compute_top_eigenvalues_iterative(H, k=11)
    end_time = time.perf_counter()
    
    comp_time_ms = (end_time - start_time) * 1000
    
    # The bulk edge is estimated as the 11th eigenvalue
    empirical_bulk_edge = float(eigs[10]) if len(eigs) > 10 else 2.0
    
    # 4. Process Results
    run_id = str(uuid.uuid4())
    theoretical_bbp = theta + (1.0 / theta)
    
    eigenvalues_list = []
    # We only record the top 10 in the final JSON as per T001
    for i in range(min(10, len(eigs))):
        val = float(eigs[i])
        # FR-004: value > empirical_bulk_edge + 0.05
        is_outlier = val > (empirical_bulk_edge + 0.05)
        
        eigenvalues_list.append(EigenvalueResult(
            run_id=run_id,
            eigenvalue_index=i + 1,
            value=val,
            is_outlier=is_outlier,
            theoretical_bbp=theoretical_bbp,
            deviation=val - theoretical_bbp
        ).model_dump())
    
    result = SimulationRun(
        run_id=run_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        seed=seed,
        N=N,
        k=k,
        theta=theta,
        pattern_type=pattern,
        support_density=None,
        computation_time_ms=comp_time_ms,
        empirical_bulk_edge=empirical_bulk_edge,
        eigenvalues=eigenvalues_list
    ).model_dump()
    
    return result
