import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

import numpy as np
from generators.wigner import generate_wigner_matrix
from generators.perturbation import create_perturbation
from analysis.eigen_solver import compute_top_eigenvalues, validate_eigenvalues
from utils.config import get_project_paths, load_config

def parse_args():
    parser = argparse.ArgumentParser(description="Sanity check for T051")
    parser.add_argument('--N', type=int, default=100, help='Matrix dimension')
    parser.add_argument('--theta', type=float, default=2.5, help='Perturbation strength')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--tol', type=float, default=1e-10, help='Validation tolerance')
    parser.add_argument('--baseline-file', type=str, default='state/sanity_baseline.json', help='Path to baseline file')
    parser.add_argument('--log-file', type=str, default='state/sanity_check_log.txt', help='Path to output log')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    return parser.parse_args()

def setup_logging(verbose=False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_baseline(baseline_path):
    """Load the baseline eigenvalue from the stored JSON file."""
    if not os.path.exists(baseline_path):
        raise FileNotFoundError(f"Baseline file not found: {baseline_path}")
    
    with open(baseline_path, 'r') as f:
        data = json.load(f)
    
    if 'top_eigenvalue' not in data:
        raise ValueError("Baseline file missing 'top_eigenvalue' key")
    
    return float(data['top_eigenvalue'])

def run_sanity_check(N, theta, seed, tol, baseline_path, log_path):
    """
    Execute a single small-scale run and compare against baseline.
    Returns True if check passes, False otherwise.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Starting sanity check: N={N}, theta={theta}, seed={seed}")
    
    # 1. Generate Wigner Matrix
    logger.info(f"Generating Wigner matrix (N={N}, seed={seed})...")
    W = generate_wigner_matrix(N, seed=seed)
    
    # 2. Create Perturbation (Rank-1 Diagonal with strength theta)
    logger.info(f"Creating perturbation (theta={theta})...")
    P = create_perturbation(N, rank=1, theta=theta, seed=seed, perturbation_type='diagonal')
    
    # 3. Construct Perturbed Matrix
    H = W + P
    
    # 4. Compute Top Eigenvalues
    logger.info("Computing top eigenvalues...")
    # We need the top 1 eigenvalue for this check
    eigenvalues, _ = compute_top_eigenvalues(H, k=1, which='LM')
    top_eig = float(eigenvalues[0])
    
    logger.info(f"Computed top eigenvalue: {top_eig}")
    
    # 5. Validate against Tolerance
    # Theoretical edge is 2.0. With theta=2.5 (>1), we expect an outlier > 2.0.
    is_outlier = validate_eigenvalues([top_eig], tol=tol)
    logger.info(f"Outlier validation (tol={tol}): {is_outlier}")
    
    # 6. Compare with Baseline
    logger.info(f"Loading baseline from {baseline_path}...")
    try:
        baseline_eig = load_baseline(baseline_path)
        logger.info(f"Baseline top eigenvalue: {baseline_eig}")
        
        diff = abs(top_eig - baseline_eig)
        logger.info(f"Difference: {diff}")
        
        # Use the same tolerance for comparison
        if diff <= tol:
            status = "PASS"
            logger.info("Sanity check PASSED: Eigenvalue matches baseline within tolerance.")
        else:
            status = "FAIL"
            logger.error(f"Sanity check FAILED: Eigenvalue mismatch. Diff={diff} > tol={tol}")
        
    except FileNotFoundError:
        status = "BASELINE_MISSING"
        logger.error(f"Baseline file not found: {baseline_path}. Cannot compare.")
    except Exception as e:
        status = "ERROR"
        logger.error(f"Error comparing with baseline: {e}")
        raise

    # 7. Write Log
    logger.info(f"Writing log to {log_path}...")
    log_content = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "parameters": {
            "N": N,
            "theta": theta,
            "seed": seed,
            "tol": tol
        },
        "results": {
            "top_eigenvalue": top_eig,
            "baseline_eigenvalue": baseline_eig if status != "BASELINE_MISSING" else None,
            "difference": diff if status != "BASELINE_MISSING" else None,
            "is_outlier": is_outlier,
            "status": status
        }
    }
    
    with open(log_path, 'w') as f:
        json.dump(log_content, f, indent=2)
    
    return status == "PASS"

def main():
    args = parse_args()
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # Ensure state directory exists
        state_dir = Path(args.log_file).parent
        state_dir.mkdir(parents=True, exist_ok=True)
        
        success = run_sanity_check(
            N=args.N,
            theta=args.theta,
            seed=args.seed,
            tol=args.tol,
            baseline_path=args.baseline_file,
            log_path=args.log_file
        )
        
        if success:
            logger.info("T051 Sanity Check: SUCCESS")
            return 0
        else:
            logger.error("T051 Sanity Check: FAILED")
            return 1

    except Exception as e:
        logger.error(f"Execution failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())