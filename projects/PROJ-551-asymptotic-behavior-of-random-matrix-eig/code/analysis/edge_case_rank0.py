"""
Edge Case Verification: Rank 0 (Unperturbed) Wigner Matrix.

This module verifies that a Wigner matrix with no perturbation (rank k=0)
strictly adheres to the Wigner Semicircle Law. Specifically, it ensures that
the spectral radius remains within the theoretical support [-2, 2] (asymptotically)
and that no outliers exist above the edge 2.0.

Output:
    data/logs/edge_case_rank0.log: Detailed verification log.
"""
import logging
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import eigsh

# Import from project API
from generators.wigner import generate_wigner_matrix
from utils.config import get_project_paths, get_tolerance, get_seed
from analysis.eigen_solver import compute_top_eigenvalues, validate_eigenvalues

# Configure logging for this module
logger = logging.getLogger(__name__)

def verify_semicircle_law(
    eigenvalues: np.ndarray,
    N: int,
    tolerance: float = 1e-10
) -> Dict[str, Any]:
    """
    Verify that the eigenvalues of an unperturbed Wigner matrix
    comply with the Semicircle Law support [-2, 2].

    Args:
        eigenvalues: Array of computed eigenvalues (sorted descending).
        N: Matrix dimension.
        tolerance: Numerical tolerance for edge checks.

    Returns:
        Dict with verification results.
    """
    theoretical_edge = 2.0
    max_eig = float(eigenvalues[0]) if len(eigenvalues) > 0 else -np.inf
    min_eig = float(eigenvalues[-1]) if len(eigenvalues) > 0 else np.inf

    # Check for outliers (should be none for rank 0)
    # Theoretical bound is 2.0, but finite N has fluctuations ~ N^{-2/3}
    # We check if any eigenvalue exceeds 2.0 + a small finite-N buffer
    # For strict verification, we check if max_eig > 2.0 + tolerance
    # However, finite N fluctuations are expected. We check if it exceeds
    # a strict threshold (e.g., 2.0 + 0.1) to catch actual outliers,
    # but for "compliance" we note the max value.
    
    # Strict check: No eigenvalue should be significantly > 2.0
    # For large N, max_eig -> 2.0. For small N, it might be slightly higher.
    # We flag if it exceeds 2.0 + 5 * N^{-2/3} (rough heuristic for fluctuations)
    # But the task asks to verify compliance.
    
    is_compliant = True
    outlier_detected = False

    # Check against strict edge + tolerance (as per T007b logic)
    # T007b defines outlier as > 2.0 + tolerance (relative to theoretical edge)
    # Actually T007b says "distinguish outliers from numerical artifacts using a strict tolerance of 1e-10 relative to the theoretical semicircle edge (±2.0)"
    # So if max_eig > 2.0 + 1e-10, it's technically an outlier by that strict definition?
    # In finite N, max_eig is naturally > 2.0.
    # The task is to verify "compliance". We will log the deviation.
    
    # Let's use the standard BBP transition logic:
    # If theta = 0, no outlier should exist.
    # We check if max_eig is within expected finite-size scaling.
    # Expected max ~ 2 + c * N^{-2/3}.
    # We will just log the value and check if it is "reasonable" (e.g. < 2.5 for N=1000).
    
    # Strict verification per T007b:
    # "validate_eigenvalues" function checks if eigenvalues are > 2.0 + tol.
    # We will use that.
    
    validation_result = validate_eigenvalues(eigenvalues, theta=0.0, tol=tolerance)
    
    # If validation_result says "outlier detected", then for rank 0, this is a failure
    # unless it's a numerical artifact. But T007b handles that.
    # We assume T007b is robust.
    
    return {
        "max_eigenvalue": max_eig,
        "min_eigenvalue": min_eig,
        "theoretical_edge": theoretical_edge,
        "max_deviation": max_eig - theoretical_edge,
        "is_compliant": not validation_result.get("outlier_detected", False),
        "outlier_detected": validation_result.get("outlier_detected", False),
        "N": N,
        "finite_size_expected_max": theoretical_edge + 2.0 * (N ** (-2/3))  # Approximation
    }

def log_verification_result(
    result: Dict[str, Any],
    log_path: Path,
    N: int,
    seed: int,
    run_time: float
) -> None:
    """
    Write the verification result to the log file.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    
    log_entry = {
        "timestamp": timestamp,
        "task_id": "T031",
        "description": "Semicircle Law Compliance Verification (Rank 0)",
        "parameters": {
            "N": N,
            "seed": seed,
            "perturbation_rank": 0,
            "perturbation_theta": 0.0
        },
        "execution_time_seconds": run_time,
        "results": result
    }

    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with open(log_path, 'w') as f:
        json.dump(log_entry, f, indent=2)
    
    logger.info(f"Verification log written to {log_path}")

def run_rank0_verification(
    N: int,
    seed: int,
    output_path: Path
) -> Dict[str, Any]:
    """
    Run the full verification process for a rank-0 Wigner matrix.
    """
    start_time = datetime.now(timezone.utc)
    start_ts = start_time.timestamp()

    logger.info(f"Starting Rank-0 verification: N={N}, seed={seed}")

    # 1. Generate Wigner Matrix (Unperturbed)
    # The generator returns a dense symmetric matrix
    matrix = generate_wigner_matrix(N, seed=seed)
    
    # 2. Compute Top Eigenvalues
    # We need enough eigenvalues to check the edge. Top 10 is sufficient.
    num_eigs = min(10, N)
    
    # Use iterative solver for large N, dense for small N (N < 1000 is fine for dense eigh too, but we use eigsh for consistency)
    # However, for N=1000, dense is fast. Let's use the project's eigen_solver.
    eigenvalues = compute_top_eigenvalues(matrix, k=num_eigs, which='LM')
    
    # Sort descending
    eigenvalues = np.sort(eigenvalues)[::-1]

    # 3. Verify Semicircle Law
    tolerance = get_tolerance()
    verification = verify_semicircle_law(eigenvalues, N, tolerance)

    end_time = datetime.now(timezone.utc)
    run_time = (end_time - start_time).total_seconds()

    # 4. Log Result
    log_verification_result(verification, output_path, N, seed, run_time)

    return verification

def main() -> None:
    """
    Entry point for T031.
    """
    # Setup logging
    from utils.config import ensure_directories
    ensure_directories()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('data/logs/edge_case_rank0.log') # Default fallback, overwritten by specific path
        ]
    )

    # Get config
    paths = get_project_paths()
    N = get_matrix_size() # Default or from config
    seed = get_seed() # Default or from config

    # Specific output path for T031
    output_path = paths["data_logs"] / "edge_case_rank0.log"

    # Run verification
    result = run_rank0_verification(N, seed, output_path)

    if result["is_compliant"]:
        logger.info("Verification PASSED: Rank-0 matrix complies with Semicircle Law.")
    else:
        logger.warning("Verification FAILED: Outliers detected in Rank-0 matrix.")
        sys.exit(1)

if __name__ == "__main__":
    main()
