import numpy as np
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from scipy.sparse.linalg import eigsh
from utils.config import get_project_paths
from analysis.checksum_raw import compute_file_sha256

def generate_and_save_wigner(N, seed):
    """Generates Wigner matrix with variance 1/N scaling."""
    np.random.seed(seed)
    # A is N x N with variance 1/(2N)
    A = np.random.randn(N, N) / np.sqrt(2 * N)
    W = A + A.T
    
    paths = get_project_paths()
    filename = f"matrix_N{N}_seed{seed}.npy"
    filepath = paths['raw'] / filename
    np.save(filepath, W)
    
    # Checksum it
    sha = compute_file_sha256(filepath)
    manifest_path = paths['raw'] / 'checksums_raw.json'
    import json
    manifest = {}
    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
    manifest[filename] = {"sha256": sha, "N": N, "seed": seed}
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    return W

def run_single_simulation(params):
    N = params['N']
    seed = params['seed']
    theta = params['theta']
    k_rank = params['k']
    pattern = params['pattern']
    
    start_time = time.time()
    paths = get_project_paths()
    raw_path = paths['raw'] / f"matrix_N{N}_seed{seed}.npy"
    
    if raw_path.exists():
        W = np.load(raw_path)
    else:
        W = generate_and_save_wigner(N, seed)
    
    # 1. Compute empirical bulk edge (max eigenvalue of W)
    # We use a small k for the bulk edge as it's just the boundary
    bulk_eigs = eigsh(W, k=1, which='LA', return_eigenvectors=False)
    empirical_bulk_edge = float(bulk_eigs[0])
    
    # 2. Construct Perturbation P
    # Rank-k diagonal perturbation with spectral norm theta
    # We put the weight on the first k diagonal elements
    P = np.zeros((N, N))
    for i in range(k_rank):
        P[i, i] = theta
    
    # 3. Compute top 10 eigenvalues of H = W + P
    H = W + P
    # ARPACK eigsh
    all_eigs = eigsh(H, k=10, which='LA', return_eigenvectors=False)
    all_eigs = np.sort(all_eigs)[::-1]
    
    # 4. Process results
    run_id = str(uuid.uuid4())
    theoretical_bbp = theta + 1.0/theta if theta > 1.0 else 2.0
    
    eigenvalues_list = []
    for i, val in enumerate(all_eigs):
        # FR-004: value > empirical_bulk_edge + 0.05
        is_outlier = bool(val > empirical_bulk_edge + 0.05)
        eigenvalues_list.append({
            "run_id": run_id,
            "eigenvalue_index": i + 1,
            "value": float(val),
            "is_outlier": is_outlier,
            "theoretical_bbp": float(theoretical_bbp),
            "deviation": float(val - theoretical_bbp)
        })
    
    computation_time_ms = (time.time() - start_time) * 1000
    
    # Calculate support density: for diagonal, it's k/N
    support_density = k_rank / N if pattern == 'diagonal' else None
    
    return {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "seed": seed,
        "N": N,
        "k": k_rank,
        "theta": theta,
        "pattern_type": pattern,
        "support_density": support_density,
        "computation_time_ms": computation_time_ms,
        "empirical_bulk_edge": empirical_bulk_edge,
        "eigenvalues": eigenvalues_list
    }
