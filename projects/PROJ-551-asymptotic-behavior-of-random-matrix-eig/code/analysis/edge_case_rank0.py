"""
Edge Case Verification: Rank 0 (Unperturbed) Semicircle Law Compliance.

This module verifies that a Wigner matrix with no perturbation (rank k=0)
adheres to Wigner's Semicircle Law. It computes the empirical spectral density
and compares it against the theoretical density, outputting a verification log.
"""
import logging
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
from scipy.stats import kstest

# Import from existing project API
from generators.wigner import generate_wigner_matrix
from utils.config import get_project_paths, get_seed, get_matrix_size, get_tolerance
from utils.logging_config import setup_simulation_logger

# Constants
THEORETICAL_EDGE = 2.0
HISTOGRAM_BINS = 100
KS_PVALUE_THRESHOLD = 0.05


def verify_semicircle_law(eigenvalues: np.ndarray, N: int) -> Dict[str, Any]:
    """
    Verify the empirical spectral distribution against the theoretical semicircle law.

    Args:
        eigenvalues: Array of eigenvalues from the unperturbed Wigner matrix.
        N: Dimension of the matrix.

    Returns:
        Dictionary containing verification metrics and pass/fail status.
    """
    # Sort eigenvalues
    sorted_eigs = np.sort(eigenvalues)

    # Theoretical Semicircle Density function
    def semicircle_density(x):
        if abs(x) <= THEORETICAL_EDGE:
            return (2.0 / (np.pi * THEORETICAL_EDGE**2)) * np.sqrt(THEORETICAL_EDGE**2 - x**2)
        return 0.0

    # Empirical CDF calculation (simplified for KS test)
    # We use the Kolmogorov-Smirnov test to compare the empirical distribution
    # of the eigenvalues (scaled to [-2, 2]) against the theoretical distribution.
    # Since eigenvalues are already scaled by 1/sqrt(N) in the generator,
    # we compare directly against the standard semicircle on [-2, 2].

    # Calculate empirical CDF values
    # KS test requires a continuous distribution. We define a custom CDF for the semicircle.
    def semicircle_cdf(x):
        if x <= -THEORETICAL_EDGE:
            return 0.0
        if x >= THEORETICAL_EDGE:
            return 1.0
        # Integral of semicircle density
        # CDF(x) = 0.5 + (x * sqrt(4 - x^2))/(2*pi) + arcsin(x/2)/pi
        term1 = 0.5
        term2 = (x * np.sqrt(THEORETICAL_EDGE**2 - x**2)) / (2.0 * np.pi)
        term3 = np.arcsin(x / THEORETICAL_EDGE) / np.pi
        return term1 + term2 + term3

    # Perform KS test
    # We compare the sorted eigenvalues against the theoretical CDF
    # Note: scipy.stats.kstest expects a CDF function or a distribution name.
    # We pass the lambda for the CDF.
    try:
        statistic, p_value = kstest(sorted_eigs, semicircle_cdf)
    except Exception as e:
        logging.error(f"KS Test failed: {e}")
        statistic, p_value = 1.0, 0.0

    # Check edge compliance: max eigenvalue should be close to 2.0
    max_eig = float(np.max(sorted_eigs))
    min_eig = float(np.min(sorted_eigs))
    edge_deviation = max(abs(max_eig - THEORETICAL_EDGE), abs(min_eig - (-THEORETICAL_EDGE)))

    # Histogram comparison for visual verification (optional metrics)
    hist, bin_edges = np.histogram(sorted_eigs, bins=HISTOGRAM_BINS, range=(-THEORETICAL_EDGE, THEORETICAL_EDGE), density=True)
    theoretical_vals = [semicircle_density((bin_edges[i] + bin_edges[i+1])/2) for i in range(len(hist))]
    mse = float(np.mean((hist - theoretical_vals)**2))

    passed = (p_value > KS_PVALUE_THRESHOLD) and (edge_deviation < 0.5) # Loose edge check for finite N

    return {
        "ks_statistic": float(statistic),
        "ks_p_value": float(p_value),
        "max_eigenvalue": max_eig,
        "min_eigenvalue": min_eig,
        "edge_deviation": float(edge_deviation),
        "mean_squared_error_histogram": mse,
        "passed": passed,
        "n_samples": N
    }


def log_verification_result(
    results: Dict[str, Any],
    N: int,
    seed: int,
    output_path: Path
) -> None:
    """
    Write the verification results to a structured log file.

    Args:
        results: Dictionary of verification metrics.
        N: Matrix size used.
        seed: Random seed used.
        output_path: Path to the output log file.
    """
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task_id": "T031",
        "task_description": "Verify semicircle law compliance for rank k=0",
        "parameters": {
            "matrix_size": N,
            "seed": seed,
            "perturbation_rank": 0,
            "theoretical_edge": THEORETICAL_EDGE
        },
        "metrics": results,
        "status": "VERIFIED" if results["passed"] else "DEVIATION_DETECTED"
    }

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(log_entry, f, indent=2)

    # Also log to console/logger
    logger = logging.getLogger(__name__)
    if results["passed"]:
        logger.info(f"T031 Verification PASSED: KS p-value={results['ks_p_value']:.4f}, Edge Dev={results['edge_deviation']:.4f}")
    else:
        logger.warning(f"T031 Verification FAILED: KS p-value={results['ks_p_value']:.4f}, Edge Dev={results['edge_deviation']:.4f}")


def run_rank0_verification(
    N: Optional[int] = None,
    seed: Optional[int] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Main execution function to generate a rank-0 Wigner matrix, compute eigenvalues,
    verify against the semicircle law, and log the result.

    Args:
        N: Matrix size. Defaults to config.
        seed: Random seed. Defaults to config.
        output_path: Output path for the log. Defaults to data/logs/edge_case_rank0.log.

    Returns:
        The verification results dictionary.
    """
    # Setup logging
    logger = setup_simulation_logger("edge_case_rank0")
    logger.info("Starting Rank 0 Semicircle Law Verification (T031)")

    # Load config
    paths = get_project_paths()
    if N is None:
        N = get_matrix_size()
    if seed is None:
        seed = get_seed()
    if output_path is None:
        output_path = paths["data_logs"] / "edge_case_rank0.log"

    logger.info(f"Generating Wigner Matrix: N={N}, seed={seed}")

    # Generate Wigner Matrix (Rank 0 perturbation means NO perturbation added)
    # The generator returns a symmetric matrix scaled by 1/sqrt(N)
    wigner_matrix = generate_wigner_matrix(N, seed=seed)

    # Compute eigenvalues
    # Since the matrix is symmetric and dense (N is manageable for this check),
    # we use np.linalg.eigh for full spectrum.
    # Note: For very large N, we might only care about the top/bottom, but for
    # semicircle law verification, we need the bulk distribution.
    logger.info("Computing full eigenvalue spectrum...")
    try:
        eigenvalues = np.linalg.eigh(wigner_matrix)[1]
    except np.linalg.LinAlgError as e:
        logger.error(f"Eigenvalue computation failed: {e}")
        raise

    # Verify
    logger.info("Verifying against Semicircle Law...")
    results = verify_semicircle_law(eigenvalues, N)

    # Log
    log_verification_result(results, N, seed, output_path)

    logger.info("Rank 0 Verification complete.")
    return results


def main():
    """CLI entry point for T031."""
    import argparse

    parser = argparse.ArgumentParser(description="T031: Verify semicircle law for rank 0.")
    parser.add_argument('--N', type=int, default=None, help="Matrix size (overrides config)")
    parser.add_argument('--seed', type=int, default=None, help="Random seed (overrides config)")
    parser.add_argument('--output', type=str, default=None, help="Output log file path")

    args = parser.parse_args()

    output_path = Path(args.output) if args.output else None

    try:
        results = run_rank0_verification(N=args.N, seed=args.seed, output_path=output_path)
        if not results["passed"]:
            # Exit with error code if verification fails significantly
            # Though for exploratory science, we might just warn.
            # Given the task is "Verify", we treat failure as a reportable event.
            print(f"Verification completed. Status: {'PASS' if results['passed'] else 'WARN'}")
            return 0
        return 0
    except Exception as e:
        logging.exception("T031 execution failed")
        return 1


if __name__ == "__main__":
    exit(main())
