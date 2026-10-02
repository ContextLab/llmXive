"""
Systematic Uncertainty Inflation Test (T031)

Implements the systematic uncertainty inflation test as described in User Story 3.
Reads the inflation factor from data/processed/inflation_factor.json, applies it
multiplicatively to the covariance matrix, and verifies the impact on the Bayes factor.

Dependency: T023-MCMC (requires Bayes factor output), T030-DEFERRED-FORMULA (requires inflation factor)
"""

import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

import numpy as np
from scipy.linalg import cholesky, cho_solve, LinAlgError

# Project imports based on provided API surface
from config import get_logger, ProjectConfig
from data.loaders import load_harmonized_data
from models.likelihood import load_covariance_matrix, compute_cholesky_decomposition
from inference.nested import run_nested_sampling, log_prior_yukawa, log_likelihood_yukawa, log_prior_newtonian, log_likelihood_newtonian

logger = get_logger(__name__)

def inflate_covariance(
    covariance_matrix: np.ndarray,
    inflation_factor: float
) -> np.ndarray:
    """
    Apply multiplicative inflation to the covariance matrix.

    Args:
        covariance_matrix: The original covariance matrix (N, N).
        inflation_factor: The scalar factor to multiply the matrix by.

    Returns:
        The inflated covariance matrix.
    """
    if inflation_factor <= 0:
        raise ValueError(f"Inflation factor must be positive, got {inflation_factor}")
    
    logger.info(f"Inflating covariance matrix by factor: {inflation_factor}")
    inflated_cov = covariance_matrix * inflation_factor
    
    # Verify positive definiteness after inflation
    try:
        cholesky(inflated_cov, check_finite=False)
        logger.debug("Inflated covariance matrix is positive definite.")
    except LinAlgError as e:
        logger.error(f"Inflated covariance matrix is not positive definite: {e}")
        raise
    
    return inflated_cov

def compute_bayes_factor(
    data_path: Path,
    covariance_path: Path,
    output_dir: Path,
    seed: int = 42
) -> Tuple[float, Dict[str, Any], Dict[str, Any]]:
    """
    Run nested sampling for both Newtonian and Yukawa models and compute Bayes factor.

    Args:
        data_path: Path to the harmonized dataset (JSON/CSV).
        covariance_path: Path to the covariance matrix (.npy).
        output_dir: Directory to save intermediate results.
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (Bayes Factor K, Yukawa results dict, Newtonian results dict).
    """
    logger.info(f"Computing Bayes factor using data: {data_path}, cov: {covariance_path}")
    
    # Load data
    dataset = load_harmonized_data(data_path)
    separation = dataset.separation_m
    force = dataset.force_n
    
    # Load covariance
    cov_matrix = load_covariance_matrix(covariance_path)
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run Nested Sampling for Newtonian Model (H0)
    logger.info("Running nested sampling for Newtonian model (H0)...")
    try:
        result_newtonian = run_nested_sampling(
            separation=separation,
            force=force,
            covariance=cov_matrix,
            model="newtonian",
            output_path=output_dir / "newtonian_evidence.json",
            seed=seed,
            max_iter=10000 # Reduced for robustness test speed
        )
        log_evidence_newtonian = result_newtonian['log_evidence']
    except Exception as e:
        logger.error(f"Newtonian sampling failed: {e}")
        raise

    # Run Nested Sampling for Yukawa Model (H1)
    logger.info("Running nested sampling for Yukawa model (H1)...")
    try:
        result_yukawa = run_nested_sampling(
            separation=separation,
            force=force,
            covariance=cov_matrix,
            model="yukawa",
            output_path=output_dir / "yukawa_evidence.json",
            seed=seed,
            max_iter=10000
        )
        log_evidence_yukawa = result_yukawa['log_evidence']
    except Exception as e:
        logger.error(f"Yukawa sampling failed: {e}")
        raise

    # Compute Bayes Factor K = P(D|H1) / P(D|H0) = exp(log_evidence_yukawa - log_evidence_newtonian)
    log_bayes_factor = log_evidence_yukawa - log_evidence_newtonian
    bayes_factor = np.exp(log_bayes_factor)

    logger.info(f"Log Evidence (Newtonian): {log_evidence_newtonian:.4f}")
    logger.info(f"Log Evidence (Yukawa): {log_evidence_yukawa:.4f}")
    logger.info(f"Log Bayes Factor: {log_bayes_factor:.4f}")
    logger.info(f"Bayes Factor K: {bayes_factor:.4f}")

    return bayes_factor, result_yukawa, result_newtonian

def main():
    """
    Main entry point for the systematic uncertainty inflation test.
    1. Load inflation factor from data/processed/inflation_factor.json.
    2. Load original harmonized data and covariance matrix.
    3. Compute baseline Bayes factor.
    4. Inflate covariance matrix.
    5. Compute inflated Bayes factor.
    6. Compare and log results.
    """
    config = ProjectConfig()
    logger.info("Starting Systematic Uncertainty Inflation Test (T031)")

    # Paths
    project_root = config.project_root
    inflation_factor_path = project_root / "data" / "processed" / "inflation_factor.json"
    harmonized_data_path = project_root / "data" / "processed" / "harmonized_dataset.json"
    original_cov_path = project_root / "data" / "processed" / "covariance_matrix.npy"
    results_dir = project_root / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load Inflation Factor
    if not inflation_factor_path.exists():
        logger.error(f"Inflation factor file not found: {inflation_factor_path}")
        logger.error("Please ensure T030-DEFERRED-FORMULA has been completed.")
        sys.exit(1)

    with open(inflation_factor_path, 'r') as f:
        inflation_config = json.load(f)
    
    inflation_factor = float(inflation_config.get('inflation_factor', 1.1))
    logger.info(f"Loaded inflation factor: {inflation_factor}")

    # 2. Load Data and Covariance
    if not harmonized_data_path.exists():
        logger.error(f"Harmonized dataset not found: {harmonized_data_path}")
        sys.exit(1)
    
    if not original_cov_path.exists():
        logger.error(f"Original covariance matrix not found: {original_cov_path}")
        sys.exit(1)

    # 3. Compute Baseline Bayes Factor
    logger.info("Computing baseline Bayes factor...")
    start_time = time.time()
    try:
        bf_baseline, _, _ = compute_bayes_factor(
            data_path=harmonized_data_path,
            covariance_path=original_cov_path,
            output_dir=results_dir / "baseline",
            seed=42
        )
    except Exception as e:
        logger.error(f"Baseline Bayes factor computation failed: {e}")
        sys.exit(1)
    baseline_time = time.time() - start_time

    # 4. Inflate Covariance
    logger.info(f"Inflating covariance matrix by factor {inflation_factor}...")
    original_cov = np.load(original_cov_path)
    inflated_cov = inflate_covariance(original_cov, inflation_factor)
    inflated_cov_path = results_dir / "covariance_inflated.npy"
    np.save(inflated_cov_path, inflated_cov)
    logger.info(f"Saved inflated covariance to {inflated_cov_path}")

    # 5. Compute Inflated Bayes Factor
    logger.info("Computing inflated Bayes factor...")
    start_time = time.time()
    try:
        bf_inflated, _, _ = compute_bayes_factor(
            data_path=harmonized_data_path,
            covariance_path=inflated_cov_path,
            output_dir=results_dir / "inflated",
            seed=42
        )
    except Exception as e:
        logger.error(f"Inflated Bayes factor computation failed: {e}")
        sys.exit(1)
    inflated_time = time.time() - start_time

    # 6. Compare and Log Results
    relative_shift = abs(bf_inflated - bf_baseline) / bf_baseline if bf_baseline != 0 else 0.0
    percent_shift = relative_shift * 100

    logger.info("=" * 60)
    logger.info("SYSTEMATIC UNCERTAINTY INFLATION TEST RESULTS")
    logger.info("=" * 60)
    logger.info(f"Baseline Bayes Factor (K): {bf_baseline:.6f}")
    logger.info(f"Inflated Bayes Factor (K): {bf_inflated:.6f}")
    logger.info(f"Relative Shift: {relative_shift:.6f} ({percent_shift:.2f}%)")
    logger.info(f"Baseline Time: {baseline_time:.2f}s")
    logger.info(f"Inflated Time: {inflated_time:.2f}s")
    logger.info("=" * 60)

    # Determine pass/fail based on "negligible amount" (spec implies < 15% or similar stability)
    # We will log the result and save a report.
    # The task says "Verify that the Bayes factor changes by a negligible amount".
    # We define negligible as < 15% relative shift, consistent with SC-003.
    negligible_threshold = 0.15
    is_stable = relative_shift < negligible_threshold

    logger.info(f"Stability Check (Shift < {negligible_threshold*100}%): {'PASS' if is_stable else 'FAIL'}")

    report = {
        "inflation_factor": inflation_factor,
        "bayes_factor_baseline": float(bf_baseline),
        "bayes_factor_inflated": float(bf_inflated),
        "relative_shift": float(relative_shift),
        "percent_shift": float(percent_shift),
        "negligible_threshold": negligible_threshold,
        "is_stable": is_stable,
        "baseline_runtime_seconds": baseline_time,
        "inflated_runtime_seconds": inflated_time
    }

    report_path = results_dir / "uncertainty_inflation_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Report saved to {report_path}")

    if not is_stable:
        logger.warning("Bayes factor shift is significant. Results may be sensitive to systematic uncertainty inflation.")

    return report

if __name__ == "__main__":
    main()