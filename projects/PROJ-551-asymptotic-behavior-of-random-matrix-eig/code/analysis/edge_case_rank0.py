"""
Edge Case Verification: Rank-0 (Unperturbed) Wigner Matrix
===========================================================

This module verifies semicircle law compliance for the unperturbed case (rank k=0).
It generates a Wigner matrix, computes its eigenvalues, and validates that the
spectral edge does not exceed the theoretical limit of 2.0 (for scaled matrices).
"""

import logging
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np

# Import from existing project API
from generators.wigner import generate_wigner_matrix
from analysis.eigen_solver import compute_top_eigenvalues, validate_eigenvalues
from utils.config import get_project_paths, get_seed, get_matrix_size, get_tolerance
from utils.logging_config import setup_simulation_logger

logger = logging.getLogger(__name__)

def verify_semicircle_law(
    eigenvalues: np.ndarray,
    n: int,
    expected_edge: float = 2.0,
    tolerance: Optional[float] = None
) -> Dict[str, Any]:
    """
    Verify that the computed eigenvalues comply with the Wigner Semicircle Law.
    
    For a Wigner matrix scaled by 1/sqrt(N), the eigenvalues should lie within
    [-2, 2] asymptotically. We check if the maximum eigenvalue is within
    a tolerance of the theoretical edge.
    
    Args:
        eigenvalues: Array of computed eigenvalues (sorted descending).
        n: Matrix dimension.
        expected_edge: Theoretical edge of the spectrum (default 2.0).
        tolerance: Acceptable deviation from the edge.
        
    Returns:
        Dictionary with verification results.
    """
    if tolerance is None:
        tolerance = get_tolerance()
        
    max_eig = float(eigenvalues[0])
    min_eig = float(eigenvalues[-1])
    
    # Check spectral radius
    spectral_radius = max(abs(max_eig), abs(min_eig))
    deviation = spectral_radius - expected_edge
    is_compliant = deviation <= tolerance
    
    # Calculate empirical spectral density moments (optional but informative)
    # Mean should be ~0, Variance should be ~1 (for standard Wigner)
    mean_eig = float(np.mean(eigenvalues))
    var_eig = float(np.var(eigenvalues))
    
    return {
        "n": n,
        "max_eigenvalue": max_eig,
        "min_eigenvalue": min_eig,
        "spectral_radius": spectral_radius,
        "theoretical_edge": expected_edge,
        "deviation_from_edge": deviation,
        "tolerance": tolerance,
        "is_compliant": is_compliant,
        "mean_eigenvalue": mean_eig,
        "variance_eigenvalue": var_eig,
        "compliance_message": "PASS" if is_compliant else "FAIL"
    }

def log_verification_result(
    result: Dict[str, Any],
    log_path: Path,
    seed: int
) -> None:
    """
    Write the verification result to a structured log file.
    
    Args:
        result: The verification dictionary.
        log_path: Path to the output log file.
        seed: The random seed used for generation.
    """
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task_id": "T031",
        "task_description": "Verify semicircle law compliance for rank k=0",
        "seed": seed,
        "verification_result": result
    }
    
    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log_entry, f, indent=2)
        
    logger.info(f"Verification log written to {log_path}")
    logger.info(f"Compliance Status: {result['compliance_message']}")

def run_rank0_verification(
    n: Optional[int] = None,
    seed: Optional[int] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Execute the full verification workflow for the rank-0 case.
    
    1. Generate a Wigner matrix of size N x N.
    2. Compute the top eigenvalues.
    3. Validate against the semicircle law edge (2.0).
    4. Log the result.
    
    Args:
        n: Matrix size (defaults to config).
        seed: Random seed (defaults to config).
        output_path: Path for the log file (defaults to config).
        
    Returns:
        The verification result dictionary.
    """
    if n is None:
        n = get_matrix_size()
    if seed is None:
        seed = get_seed()
    if output_path is None:
        paths = get_project_paths()
        output_path = paths["data_logs"] / "edge_case_rank0.log"
        
    logger.info(f"Starting Rank-0 Verification: N={n}, Seed={seed}")
    
    # 1. Generate Wigner Matrix (Rank-0 perturbation means just the Wigner matrix)
    # We use the standard generator which creates a symmetric matrix with
    # diagonal ~ N(0, 1/N) and off-diagonal ~ N(0, 1/(2N)) scaled by 1/sqrt(N)
    # effectively creating a matrix with spectral radius ~ 2.
    try:
        wigner_matrix = generate_wigner_matrix(n, seed=seed)
        logger.info(f"Generated Wigner matrix of shape {wigner_matrix.shape}")
    except Exception as e:
        logger.error(f"Failed to generate Wigner matrix: {e}")
        raise
        
    # 2. Compute Eigenvalues
    # We need all eigenvalues to check the full spectrum, not just top k
    # However, for large N, computing all is expensive. 
    # For verification of the edge, we can compute a sufficient number or all if N is small.
    # Given N=2000 is the max budget, computing all might be heavy but doable for verification.
    # We'll use numpy.linalg.eigh for dense symmetric matrices for accuracy in this edge case.
    try:
        # Since wigner_matrix is symmetric, eigh is efficient and accurate
        eigenvalues = np.linalg.eigh(wigner_matrix)[0]
        # Sort descending
        eigenvalues = np.sort(eigenvalues)[::-1]
        logger.info(f"Computed {len(eigenvalues)} eigenvalues.")
    except Exception as e:
        logger.error(f"Failed to compute eigenvalues: {e}")
        raise
        
    # 3. Validate against Semicircle Law
    tolerance = get_tolerance()
    verification_result = verify_semicircle_law(
        eigenvalues=eigenvalues,
        n=n,
        expected_edge=2.0,
        tolerance=tolerance
    )
    
    # 4. Log Result
    log_verification_result(verification_result, output_path, seed)
    
    return verification_result

def main() -> None:
    """
    Entry point for the Rank-0 Verification script.
    """
    # Setup logging
    log_path = get_project_paths()["data_logs"] / "edge_case_rank0.log"
    setup_simulation_logger("edge_case_rank0", log_file=log_path)
    
    try:
        result = run_rank0_verification()
        if result["is_compliant"]:
            logger.info("Verification PASSED: Semicircle law compliance confirmed.")
        else:
            logger.warning("Verification FAILED: Spectral edge exceeded theoretical limit.")
    except Exception as e:
        logger.critical(f"Verification process failed: {e}")
        raise

if __name__ == "__main__":
    main()
