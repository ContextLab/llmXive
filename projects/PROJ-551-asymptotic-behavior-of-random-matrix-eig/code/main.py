import argparse
import json
import logging
import os
import sys
import time
import hashlib
import yaml
from datetime import datetime, timezone
from pathlib import Path
import psutil

import numpy as np
from scipy.sparse.linalg import eigsh

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def compute_sha256(file_path: Path) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def run_single_analysis(args):
    # 1. Setup paths
    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / f"matrix_N{args.N}_seed{args.seed}.npy"

    # 2. Generate Wigner Matrix (Scaling 1/sqrt(N))
    # To satisfy Var(W_ij) = 1/N, we use (A + A.T) / sqrt(2N)
    rng = np.random.default_rng(args.seed)
    A = rng.standard_normal((args.N, args.N))
    W = (A + A.T) / np.sqrt(2.0 * args.N)
    np.save(raw_path, W)
    
    # 3. Construct Rank-k Diagonal Perturbation
    P = np.zeros((args.N, args.N))
    for i in range(args.k):
        P[i, i] = args.theta
    
    # 4. Compute Top 10 Eigenvalues (ARPACK)
    H = W + P
    # eigsh returns eigenvalues in ascending order by default for 'SA'
    # 'LA' is largest magnitude. For perturbed Wigner, the outlier is the largest algebraic.
    vals = eigsh(H, k=10, which='LA', tol=1e-10, return_eigenvectors=False)
    vals = np.sort(vals)[::-1] # Sort descending

    # 5. Determine Outliers (Theoretical rule: value > 2.0 + 0.05)
    results_list = []
    for i, val in enumerate(vals):
        results_list.append({
            "index": i + 1,
            "value": float(val),
            "is_outlier": bool(val > 2.05)
        })

    # 6. Memory Monitoring
    process = psutil.Process(os.getpid())
    peak_mem_bytes = process.memory_info().rss
    peak_mem_gb = peak_mem_bytes / (1024**3)

    # Enforce SC-001: Fail if > 7GB
    if peak_mem_gb > 7.0:
        raise MemoryError(f"Peak memory usage {peak_mem_gb:.2f} GB exceeds limit of 7 GB")

    # 7. Write Outputs
    run_id = f"single_run_N{args.N}_s{args.seed}_t{args.theta}"
    
    # JSON Results
    output_json = paths.data("processed", "single_run_results.json")
    output_json.parent.mkdir(parents=True, exist_ok=True)
    
    full_payload = {
        "run_id": run_id,
        "simulation_run": {
            "run_id": run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "N": args.N,
            "seed": args.seed,
            "theta": args.theta,
            "k": args.k,
            "pattern": args.pattern,
            "peak_memory_gb": peak_mem_gb
        },
        "eigenvalue_results": results_list
    }
    
    with open(output_json, "w") as f:
        json.dump(full_payload, f, indent=2)

    # Checksums
    checksums_path = paths.data("checksums.yaml") # Root data/checksums.yaml
    checksum_val = compute_sha256(raw_path)
    
    # Load existing or create new
    checksums_data = {}
    if checksums_path.exists():
        with open(checksums_path, "r") as f:
            checksums_data = yaml.safe_load(f) or {}
    
    checksums_data[str(raw_path.relative_to(paths.root))] = checksum_val
    with open(checksums_path, "w") as f:
        yaml.dump(checksums_data, f)

    # Logs
    log_path = paths.data("logs", "single_run.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w") as f:
        f.write(f"Run ID: {run_id}\n")
        f.write(f"Top Eigenvalue: {vals[0]}\n")
        f.write(f"Peak Memory: {peak_mem_gb:.4f} GB\n")
        f.write(f"Timestamp: {datetime.now(timezone.utc).isoformat()}\n")

    log.info(f"Single run completed. Top eigenvalue: {vals[0]:.12f}")
    return vals[0]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["single", "sweep"], required=True)
    parser.add_argument("--N", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--theta", type=float, default=2.5)
    parser.add_argument("--k", type=int, default=1)
    parser.add_argument("--pattern", type=str, default="diagonal")
    args = parser.parse_args()

    if args.mode == "single":
        run_single_analysis(args)
    else:
        log.error("Sweep mode not implemented in this entry point. Use analysis/threshold_sweep.py")
        sys.exit(1)

if __name__ == "__main__":
    main()