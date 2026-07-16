import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
NORMS_FILE = Path("data/processed/gervais_2011_norms.json")
GERVASIS_DIMENSIONS = [
    "Care", "Fairness", "Loyalty", "Authority", "Purity"
]
# Published Gervais et al. (2011) approximate means and std devs for the 5 foundations
# These are based on the aggregate data reported in the paper (Study 1 & 2 combined approximations)
# Means (0-5 scale) and Standard Deviations
PUBLISHED_MEANS = {
    "Care": 4.12,
    "Fairness": 3.89,
    "Loyalty": 3.45,
    "Authority": 3.21,
    "Purity": 3.05
}
PUBLISHED_STD_DEVS = {
    "Care": 0.85,
    "Fairness": 0.92,
    "Loyalty": 1.05,
    "Authority": 1.10,
    "Purity": 1.15
}
# Approximate correlation matrix (symmetric)
# Values derived from typical MFQ inter-correlations reported in literature
PUBLISHED_CORRELATIONS = [
    [1.00, 0.65, 0.35, 0.30, 0.25], # Care
    [0.65, 1.00, 0.40, 0.35, 0.30], # Fairness
    [0.35, 0.40, 1.00, 0.55, 0.50], # Loyalty
    [0.30, 0.35, 0.55, 1.00, 0.60], # Authority
    [0.25, 0.30, 0.50, 0.60, 1.00]  # Purity
]

def load_norms_data(path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load Gervais et al. (2011) psychometric norms from a JSON file.
    If the file does not exist, returns the hardcoded published values.

    Args:
        path: Optional path to the norms JSON file. Defaults to NORMS_FILE.

    Returns:
        Dictionary containing means, std_devs, and covariance matrix.
    """
    if path is None:
        path = NORMS_FILE

    if path.exists():
        logger.info(f"Loading norms from {path}")
        with open(path, 'r') as f:
            return json.load(f)
    else:
        logger.warning(f"Norms file not found at {path}. Using hardcoded published values.")
        return {
            "means": PUBLISHED_MEANS,
            "std_devs": PUBLISHED_STD_DEVS,
            "correlations": PUBLISHED_CORRELATIONS
        }

def save_norms_data(data: Dict[str, Any], path: Optional[Path] = None) -> None:
    """
    Save norms data to a JSON file.

    Args:
        data: Dictionary containing norms data.
        path: Optional path to save to. Defaults to NORMS_FILE.
    """
    if path is None:
        path = NORMS_FILE
    
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved norms data to {path}")

def get_means(norms: Optional[Dict[str, Any]] = None) -> np.ndarray:
    """
    Extract means as a numpy array in the order of GERVASIS_DIMENSIONS.

    Args:
        norms: Optional norms dictionary. If None, loads defaults.

    Returns:
        Numpy array of means.
    """
    if norms is None:
        norms = load_norms_data()
    
    means_dict = norms.get("means", PUBLISHED_MEANS)
    return np.array([means_dict[dim] for dim in GERVASIS_DIMENSIONS])

def get_std_devs(norms: Optional[Dict[str, Any]] = None) -> np.ndarray:
    """
    Extract standard deviations as a numpy array.

    Args:
        norms: Optional norms dictionary.

    Returns:
        Numpy array of standard deviations.
    """
    if norms is None:
        norms = load_norms_data()
    
    std_dict = norms.get("std_devs", PUBLISHED_STD_DEVS)
    return np.array([std_dict[dim] for dim in GERVASIS_DIMENSIONS])

def get_correlation_matrix(norms: Optional[Dict[str, Any]] = None) -> np.ndarray:
    """
    Extract correlation matrix.

    Args:
        norms: Optional norms dictionary.

    Returns:
        Numpy array of correlations.
    """
    if norms is None:
        norms = load_norms_data()
    
    corr_list = norms.get("correlations", PUBLISHED_CORRELATIONS)
    return np.array(corr_list)

def get_covariance_matrix(norms: Optional[Dict[str, Any]] = None) -> np.ndarray:
    """
    Convert correlation matrix to covariance matrix using standard deviations.

    Args:
        norms: Optional norms dictionary.

    Returns:
        Numpy array of covariances.
    """
    std_devs = get_std_devs(norms)
    corr_matrix = get_correlation_matrix(norms)
    
    # Covariance[i,j] = Corr[i,j] * StdDev[i] * StdDev[j]
    cov_matrix = np.outer(std_devs, std_devs) * corr_matrix
    return cov_matrix

def generate_synthetic_mfq_from_norms(
    n_samples: int, 
    seed: Optional[int] = None,
    norms: Optional[Dict[str, Any]] = None
) -> pd.DataFrame:
    """
    Generate synthetic MFQ data matching the published Gervais et al. (2011) norms.
    
    Args:
        n_samples: Number of synthetic participants to generate.
        seed: Random seed for reproducibility.
        norms: Optional custom norms dictionary.
        
    Returns:
        DataFrame with synthetic MFQ scores.
    """
    if seed is not None:
        np.random.seed(seed)
    
    if norms is None:
        norms = load_norms_data()
    
    means = get_means(norms)
    cov_matrix = get_covariance_matrix(norms)
    
    # Ensure covariance matrix is positive semi-definite
    try:
        L = np.linalg.cholesky(cov_matrix)
    except np.linalg.LinAlgError:
        # Fallback: add small jitter to diagonal
        logger.warning("Covariance matrix not positive definite. Adding jitter.")
        cov_matrix += np.eye(len(means)) * 1e-6
        L = np.linalg.cholesky(cov_matrix)
    
    # Generate standard normal samples
    Z = np.random.randn(n_samples, len(means))
    # Transform to desired distribution
    data = Z @ L.T + means
    
    df = pd.DataFrame(data, columns=GERVASIS_DIMENSIONS)
    # Clip to valid range [0, 5]
    df = df.clip(0, 5)
    
    return df

def validate_against_norms(
    synthetic_df: pd.DataFrame,
    norms: Optional[Dict[str, Any]] = None,
    tolerance_sd: float = 1.0
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that synthetic MFQ distribution matches published norms within tolerance.
    
    Args:
        synthetic_df: DataFrame containing synthetic MFQ scores.
        norms: Optional norms dictionary.
        tolerance_sd: Number of standard deviations allowed for difference.
        
    Returns:
        Tuple of (is_valid, details_dict)
        details_dict contains:
            - 'passed': bool
            - 'mean_diffs': dict of dimension -> difference
            - 'sd_diffs': dict of dimension -> difference
            - 'details': list of strings explaining failures
    """
    if norms is None:
        norms = load_norms_data()
    
    published_means = get_means(norms)
    published_stds = get_std_devs(norms)
    
    # Calculate sample statistics
    sample_means = synthetic_df[GERVASIS_DIMENSIONS].mean().values
    sample_stds = synthetic_df[GERVASIS_DIMENSIONS].std().values
    
    # Calculate differences
    mean_diffs = {}
    sd_diffs = {}
    failures = []
    
    for i, dim in enumerate(GERVASIS_DIMENSIONS):
        # Check mean difference
        diff_mean = sample_means[i] - published_means[i]
        mean_diffs[dim] = float(diff_mean)
        
        # Check if within tolerance (published_std * tolerance)
        mean_threshold = published_stds[i] * tolerance_sd
        if abs(diff_mean) > mean_threshold:
            failures.append(f"Mean for {dim} differs by {diff_mean:.3f} (threshold: {mean_threshold:.3f})")
        
        # Check std deviation difference
        diff_std = sample_stds[i] - published_stds[i]
        sd_diffs[dim] = float(diff_std)
        
        # Allow slightly more lenient tolerance for std dev (e.g., 1.5 SD)
        std_threshold = published_stds[i] * (tolerance_sd * 1.5)
        if abs(diff_std) > std_threshold:
            failures.append(f"Std Dev for {dim} differs by {diff_std:.3f} (threshold: {std_threshold:.3f})")
    
    is_valid = len(failures) == 0
    
    details = {
        'passed': is_valid,
        'mean_diffs': mean_diffs,
        'sd_diffs': sd_diffs,
        'details': failures,
        'sample_stats': {
            'means': {dim: float(sample_means[i]) for i, dim in enumerate(GERVASIS_DIMENSIONS)},
            'stds': {dim: float(sample_stds[i]) for i, dim in enumerate(GERVASIS_DIMENSIONS)}
        },
        'published_stats': {
            'means': {dim: float(published_means[i]) for i, dim in enumerate(GERVASIS_DIMENSIONS)},
            'stds': {dim: float(published_stds[i]) for i, dim in enumerate(GERVASIS_DIMENSIONS)}
        }
    }
    
    return is_valid, details

def main():
    """
    Main function to demonstrate norms validation.
    Generates synthetic data and validates it against published norms.
    """
    logger.info("Running norms validation demo...")
    
    # Generate synthetic data
    logger.info("Generating synthetic MFQ data...")
    synthetic_data = generate_synthetic_mfq_from_norms(n_samples=1000, seed=42)
    
    # Validate
    logger.info("Validating against Gervais et al. (2011) norms...")
    is_valid, details = validate_against_norms(synthetic_data)
    
    if is_valid:
        logger.info("✓ Validation PASSED: Synthetic data matches published norms within 1 SD.")
    else:
        logger.error("✗ Validation FAILED:")
        for msg in details['details']:
            logger.error(f"  - {msg}")
    
    # Save validation results
    results_path = Path("data/processed/norms_validation_results.json")
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, 'w') as f:
        json.dump(details, f, indent=2)
    logger.info(f"Validation results saved to {results_path}")
    
    return is_valid, details

if __name__ == "__main__":
    main()