"""
Systematic uncertainty inflation test module.

This module implements the systematic uncertainty inflation test as described in T031.
It reads the inflation factor from config, applies it to the covariance matrix,
re-runs inference, and verifies that the Bayes factor changes negligibly.
"""
import os
import sys
import json
import logging
import time
from pathlib import Path
import numpy as np
from scipy.linalg import cholesky, cho_solve, LinAlgError

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(project_root))

from config import get_logger, ProjectConfig
from data.models import HarmonizedDataset
from data.loaders import load_harmonized_data, save_harmonized_data
from models.likelihood import log_likelihood_yukawa, compute_cholesky_decomposition
from models.physics import yukawa_force, newtonian_force
from inference.mcmc import run_mcmc
from inference.nested import run_nested_sampling, log_prior_yukawa, log_prior_newtonian

logger = get_logger(__name__)

# Constants
DEFAULT_INFLATION_FACTOR = 1.5
BAYES_FACTOR_TOLERANCE = 0.10  # 10% change is considered negligible
MAX_STEPS = 1000  # Reduced steps for robustness check
N_WALKERS = 32

def load_inflation_factor(config_path: Path = None) -> float:
    """
    Load the systematic uncertainty inflation factor from config.

    Args:
        config_path: Path to the config.json file. Defaults to data/processed/config.json.

    Returns:
        float: The inflation factor value.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        KeyError: If inflation_factor key is missing.
        ValueError: If inflation_factor is not a positive number.
    """
    if config_path is None:
        config_path = Path("data/processed/config.json")

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'r') as f:
        config = json.load(f)

    if 'inflation_factor' not in config:
        raise KeyError("Missing inflation_factor in config. Please define in data/processed/config.json.")

    factor = float(config['inflation_factor'])
    if factor <= 0:
        raise ValueError(f"Inflation factor must be positive, got: {factor}")

    logger.info(f"Loaded inflation factor: {factor}")
    return factor

def inflate_covariance(covariance_matrix: np.ndarray, inflation_factor: float) -> np.ndarray:
    """
    Apply inflation factor to the covariance matrix.

    The inflation is applied multiplicatively to the diagonal elements (systematic errors).
    For a full covariance matrix, we scale the entire matrix to account for correlated
    systematic uncertainties.

    Args:
        covariance_matrix: The original covariance matrix (N x N).
        inflation_factor: The factor by which to inflate uncertainties.

    Returns:
        np.ndarray: The inflated covariance matrix.
    """
    if inflation_factor <= 1.0:
        logger.warning(f"Inflation factor {inflation_factor} <= 1.0, no inflation applied.")
        return covariance_matrix.copy()

    # Scale the entire covariance matrix by the square of the inflation factor
    # This is because variance scales with the square of the uncertainty multiplier
    inflated_cov = covariance_matrix * (inflation_factor ** 2)

    logger.info(f"Covariance matrix inflated by factor {inflation_factor} (variance scaled by {inflation_factor**2})")
    return inflated_cov

def compute_bayes_factor(log_evidence_yukawa: float, log_evidence_newtonian: float) -> float:
    """
    Compute the Bayes factor K = P(Data | Yukawa) / P(Data | Newtonian).

    Args:
        log_evidence_yukawa: Log evidence for the Yukawa model.
        log_evidence_newtonian: Log evidence for the Newtonian model.

    Returns:
        float: The Bayes factor K.
    """
    log_k = log_evidence_yukawa - log_evidence_newtonian
    return np.exp(log_k)

def run_single_inference(harmonized_data: HarmonizedDataset, covariance_matrix: np.ndarray, max_steps: int = None) -> dict:
    """
    Run a single inference pass with the given covariance matrix.

    Args:
        harmonized_data: The harmonized dataset.
        covariance_matrix: The covariance matrix to use.
        max_steps: Maximum number of MCMC steps.

    Returns:
        dict: Inference results including log evidence and Bayes factor.
    """
    if max_steps is None:
        max_steps = MAX_STEPS

    logger.info(f"Running inference with {max_steps} steps...")

    # Prepare data
    separation = harmonized_data.separation_m
    force = harmonized_data.force_n

    # Run nested sampling for both models
    try:
        # Newtonian model
        result_newton = run_nested_sampling(
            separation=separation,
            force=force,
            covariance=covariance_matrix,
            model='newtonian',
            log_prior=log_prior_newtonian,
            log_likelihood_func=log_likelihood_yukawa,  # Using yukawa likelihood with alpha=0
            n_steps=max_steps // 2
        )
        log_evidence_newton = result_newton.get('log_evidence', -np.inf)

        # Yukawa model
        result_yukawa = run_nested_sampling(
            separation=separation,
            force=force,
            covariance=covariance_matrix,
            model='yukawa',
            log_prior=log_prior_yukawa,
            log_likelihood_func=log_likelihood_yukawa,
            n_steps=max_steps // 2
        )
        log_evidence_yukawa = result_yukawa.get('log_evidence', -np.inf)

        bayes_factor = compute_bayes_factor(log_evidence_yukawa, log_evidence_newton)

        logger.info(f"Newtonian log evidence: {log_evidence_newton:.4f}")
        logger.info(f"Yukawa log evidence: {log_evidence_yukawa:.4f}")
        logger.info(f"Bayes factor K: {bayes_factor:.4f}")

        return {
            'log_evidence_newtonian': log_evidence_newton,
            'log_evidence_yukawa': log_evidence_yukawa,
            'bayes_factor': bayes_factor,
            'inference_success': True
        }

    except Exception as e:
        logger.error(f"Inference failed: {e}")
        return {
            'log_evidence_newtonian': -np.inf,
            'log_evidence_yukawa': -np.inf,
            'bayes_factor': -np.inf,
            'inference_success': False,
            'error': str(e)
        }

def run_inflation_test(
    config_path: Path = None,
    data_path: Path = None,
    output_path: Path = None,
    max_steps: int = None
) -> dict:
    """
    Run the systematic uncertainty inflation test.

    This function:
    1. Loads the inflation factor from config.
    2. Loads the harmonized dataset and its covariance matrix.
    3. Runs inference with the original covariance.
    4. Inflates the covariance matrix.
    5. Runs inference again with the inflated covariance.
    6. Compares the Bayes factors and determines if the change is negligible.

    Args:
        config_path: Path to config.json.
        data_path: Path to harmonized dataset.
        output_path: Path for the output report.
        max_steps: Maximum steps for inference.

    Returns:
        dict: The test results.
    """
    # Load configuration
    logger.info("Loading inflation factor...")
    try:
        inflation_factor = load_inflation_factor(config_path)
    except (FileNotFoundError, KeyError, ValueError) as e:
        logger.error(f"Failed to load inflation factor: {e}")
        return {
            'success': False,
            'error': f"Config error: {str(e)}",
            'inflation_factor': None,
            'original_bayes_factor': None,
            'inflated_bayes_factor': None,
            'relative_change': None,
            'negligible_change': None
        }

    # Load data
    if data_path is None:
        data_path = Path("data/processed/harmonized_dataset.json")

    logger.info(f"Loading harmonized dataset from {data_path}...")
    try:
        harmonized_data = load_harmonized_data(data_path)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return {
            'success': False,
            'error': f"Data loading error: {str(e)}",
            'inflation_factor': inflation_factor,
            'original_bayes_factor': None,
            'inflated_bayes_factor': None,
            'relative_change': None,
            'negligible_change': None
        }

    # Load original covariance matrix
    cov_path = Path("data/processed/covariance_matrix_diagonal.npy")
    if not cov_path.exists():
        logger.error(f"Covariance matrix not found at {cov_path}")
        return {
            'success': False,
            'error': f"Covariance matrix not found: {cov_path}",
            'inflation_factor': inflation_factor,
            'original_bayes_factor': None,
            'inflated_bayes_factor': None,
            'relative_change': None,
            'negligible_change': None
        }

    original_cov = np.load(cov_path)
    logger.info(f"Loaded covariance matrix with shape {original_cov.shape}")

    # Run inference with original covariance
    logger.info("Running inference with original covariance...")
    original_results = run_single_inference(harmonized_data, original_cov, max_steps)

    if not original_results['inference_success']:
        logger.error("Original inference failed, cannot proceed with inflation test.")
        return {
            'success': False,
            'error': "Original inference failed",
            'inflation_factor': inflation_factor,
            'original_bayes_factor': original_results['bayes_factor'],
            'inflated_bayes_factor': None,
            'relative_change': None,
            'negligible_change': None
        }

    original_bayes = original_results['bayes_factor']

    # Inflate covariance
    logger.info("Inflating covariance matrix...")
    inflated_cov = inflate_covariance(original_cov, inflation_factor)

    # Run inference with inflated covariance
    logger.info("Running inference with inflated covariance...")
    inflated_results = run_single_inference(harmonized_data, inflated_cov, max_steps)

    if not inflated_results['inference_success']:
        logger.error("Inflated inference failed.")
        return {
            'success': False,
            'error': "Inflated inference failed",
            'inflation_factor': inflation_factor,
            'original_bayes_factor': original_bayes,
            'inflated_bayes_factor': inflated_results['bayes_factor'],
            'relative_change': None,
            'negligible_change': None
        }

    inflated_bayes = inflated_results['bayes_factor']

    # Calculate relative change
    if original_bayes > 0:
        relative_change = abs(inflated_bayes - original_bayes) / original_bayes
    else:
        relative_change = float('inf') if inflated_bayes != 0 else 0.0

    # Determine if change is negligible
    negligible_change = relative_change <= BAYES_FACTOR_TOLERANCE

    logger.info(f"Original Bayes factor: {original_bayes:.4f}")
    logger.info(f"Inflated Bayes factor: {inflated_bayes:.4f}")
    logger.info(f"Relative change: {relative_change:.4f} ({relative_change*100:.2f}%)")
    logger.info(f"Change negligible (threshold {BAYES_FACTOR_TOLERANCE}): {negligible_change}")

    # Prepare report
    report = {
        'success': True,
        'inflation_factor': inflation_factor,
        'original_bayes_factor': float(original_bayes),
        'inflated_bayes_factor': float(inflated_bayes),
        'relative_change': float(relative_change) if not np.isinf(relative_change) else None,
        'negligible_change': negligible_change,
        'threshold': BAYES_FACTOR_TOLERANCE,
        'original_log_evidence_newtonian': float(original_results['log_evidence_newtonian']),
        'original_log_evidence_yukawa': float(original_results['log_evidence_yukawa']),
        'inflated_log_evidence_newtonian': float(inflated_results['log_evidence_newtonian']),
        'inflated_log_evidence_yukawa': float(inflated_results['log_evidence_yukawa']),
        'test_passed': negligible_change
    }

    # Save report
    if output_path is None:
        output_path = Path("data/results/uncertainty_inflation_report.json")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Report saved to {output_path}")

    return report

def main():
    """Main entry point for the uncertainty inflation test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting systematic uncertainty inflation test (T031)...")

    try:
        result = run_inflation_test()

        if result['success']:
            logger.info(f"Test completed. Bayes factor change: {result['relative_change']*100:.2f}%")
            logger.info(f"Result: {'PASSED' if result['test_passed'] else 'FAILED'}")
            sys.exit(0 if result['test_passed'] else 1)
        else:
            logger.error(f"Test failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)

    except Exception as e:
        logger.exception(f"Unexpected error during test: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
