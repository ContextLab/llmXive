"""
Norms module for loading and referencing Gervais et al. (2011) psychometric norms.
This module provides functions to load the pre-defined norms and validate data against them.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import yaml
import numpy as np
from scipy import stats

# Configure logging
logger = logging.getLogger(__name__)

def load_norms() -> Dict[str, Dict[str, float]]:
    """
    Load and reference Gervais et al. (2011) psychometric norms.

    Returns:
        dict: A dictionary containing the norms for each foundation.
              Keys are foundation names (e.g., 'Care', 'Fairness'),
              values are dictionaries with 'mean' and 'std' keys.
    """
    config_path = Path("data/config/gervais_norms.yaml")
    if not config_path.exists():
        raise FileNotFoundError(
            f"Norms configuration file not found at {config_path}. "
            "Ensure T007b (gervais_norms.yaml) is complete."
        )

    try:
        with open(config_path, 'r') as f:
            norms = yaml.safe_load(f)
        logger.info(f"Successfully loaded norms from {config_path}")
        return norms
    except yaml.YAMLError as e:
        logger.error(f"Error parsing norms YAML: {e}")
        raise
    except Exception as e:
        logger.error(f"Error loading norms: {e}")
        raise

def load_norms_data() -> Dict[str, Dict[str, float]]:
    """
    Alias for load_norms() for backward compatibility.
    """
    return load_norms()

def load_gervais_norms() -> Dict[str, Dict[str, float]]:
    """
    Alias for load_norms() for backward compatibility.
    """
    return load_norms()

def get_means(norms: Optional[Dict[str, Dict[str, float]]] = None) -> Dict[str, float]:
    """
    Extract mean values from the norms dictionary.

    Args:
        norms: Optional norms dictionary. If None, loads from file.

    Returns:
        dict: A dictionary mapping foundation names to their mean values.
    """
    if norms is None:
        norms = load_norms()

    return {k: v['mean'] for k, v in norms.items()}

def get_std_devs(norms: Optional[Dict[str, Dict[str, float]]] = None) -> Dict[str, float]:
    """
    Extract standard deviation values from the norms dictionary.

    Args:
        norms: Optional norms dictionary. If None, loads from file.

    Returns:
        dict: A dictionary mapping foundation names to their std values.
    """
    if norms is None:
        norms = load_norms()

    return {k: v['std'] for k, v in norms.items()}

def get_correlation_matrix(norms: Optional[Dict[str, Dict[str, float]]] = None) -> np.ndarray:
    """
    Get the correlation matrix for the foundations.
    Note: The Gervais norms typically provide marginal statistics (mean, std).
    If a correlation matrix is not explicitly stored in the YAML, we assume
    a simple identity matrix or a placeholder structure for simulation purposes.
    In a real-world scenario, this would be populated from the published paper's data.

    Args:
        norms: Optional norms dictionary.

    Returns:
        np.ndarray: A correlation matrix (identity matrix if not specified).
    """
    if norms is None:
        norms = load_norms()

    foundations = list(norms.keys())
    n = len(foundations)

    # Default to identity matrix if no correlation data is provided
    # This is a safe assumption for independent generation unless specified otherwise
    corr_matrix = np.eye(n)

    # If the YAML contains a 'correlation' key, use it
    if 'correlation' in norms:
        corr_data = norms['correlation']
        # Attempt to reconstruct matrix from flat list or nested structure
        if isinstance(corr_data, list) and len(corr_data) == n * n:
            corr_matrix = np.array(corr_data).reshape(n, n)
        elif isinstance(corr_data, dict):
            # Flatten dict to matrix if keys are (row, col) tuples as strings
            # This is a heuristic; specific format depends on YAML structure
            pass

    return corr_matrix

def get_covariance_matrix(norms: Optional[Dict[str, Dict[str, float]]] = None) -> np.ndarray:
    """
    Compute the covariance matrix from means, stds, and correlation matrix.

    Args:
        norms: Optional norms dictionary.

    Returns:
        np.ndarray: The covariance matrix.
    """
    if norms is None:
        norms = load_norms()

    stds = list(get_std_devs(norms).values())
    corr_matrix = get_correlation_matrix(norms)

    std_matrix = np.diag(stds)
    cov_matrix = std_matrix @ corr_matrix @ std_matrix

    return cov_matrix

def generate_synthetic_mfq_from_norms(n: int, seed: int = 42) -> np.ndarray:
    """
    Generate synthetic MFQ data based on the Gervais norms.

    Args:
        n: Number of samples to generate.
        seed: Random seed for reproducibility.

    Returns:
        np.ndarray: Generated data array of shape (n, num_foundations).
    """
    norms = load_norms()
    means = list(get_means(norms).values())
    cov_matrix = get_covariance_matrix(norms)

    np.random.seed(seed)
    data = np.random.multivariate_normal(means, cov_matrix, size=n)
    return data

def validate_against_norms(
    data: np.ndarray,
    norms: Optional[Dict[str, Dict[str, float]]] = None,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Validate a dataset against the Gervais norms using Kolmogorov-Smirnov tests.

    Args:
        data: Array of shape (n_samples, n_foundations).
        norms: Optional norms dictionary.
        alpha: Significance level for the KS test.

    Returns:
        dict: Validation results including p-values and pass/fail status per foundation.
    """
    if norms is None:
        norms = load_norms()

    foundations = list(norms.keys())
    results = {
        'valid': True,
        'details': {}
    }

    if data.shape[1] != len(foundations):
        raise ValueError(f"Data has {data.shape[1]} columns, expected {len(foundations)}")

    for i, foundation in enumerate(foundations):
        col_data = data[:, i]
        expected_mean = norms[foundation]['mean']
        expected_std = norms[foundation]['std']

        # Perform KS test against the theoretical distribution
        # Note: KS test compares against a continuous distribution.
        # Here we compare the empirical CDF of the sample to the theoretical CDF
        # defined by the norm's mean and std (assuming Normal distribution).
        ks_stat, p_value = stats.kstest(
            col_data,
            'norm',
            args=(expected_mean, expected_std)
        )

        passed = p_value > alpha
        results['details'][foundation] = {
            'ks_statistic': float(ks_stat),
            'p_value': float(p_value),
            'passed': passed,
            'observed_mean': float(np.mean(col_data)),
            'observed_std': float(np.std(col_data))
        }

        if not passed:
            results['valid'] = False
            logger.warning(f"Validation failed for {foundation}: p-value {p_value:.4f} <= {alpha}")

    return results

def run_validation_pipeline(
    data: np.ndarray,
    norms: Optional[Dict[str, Dict[str, float]]] = None,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Run the full validation pipeline against norms.

    Args:
        data: Data to validate.
        norms: Optional norms dictionary.
        alpha: Significance level.

    Returns:
        dict: Validation report.
    """
    return validate_against_norms(data, norms, alpha)

def main():
    """
    Main entry point for testing the norms module.
    """
    print("Loading Gervais norms...")
    norms = load_norms()
    print(f"Loaded norms: {list(norms.keys())}")

    print("\nGenerating synthetic data...")
    data = generate_synthetic_mfq_from_norms(n=100, seed=42)
    print(f"Generated data shape: {data.shape}")

    print("\nValidating against norms...")
    results = validate_against_norms(data, norms)
    print(f"Validation passed: {results['valid']}")
    for foundation, detail in results['details'].items():
        print(f"  {foundation}: p={detail['p_value']:.4f}, passed={detail['passed']}")

if __name__ == "__main__":
    main()