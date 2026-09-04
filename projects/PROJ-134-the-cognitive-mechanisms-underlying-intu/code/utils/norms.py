"""
Norms handling for Moral Foundations Questionnaire (MFQ) data.
Loads Gervais et al. psychometric norms and provides validation utilities.
"""
from __future__ import annotations

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import pandas as pd
from scipy import stats

from code.config import get_path

# Setup logging
logger = logging.getLogger(__name__)

def load_norms() -> Dict[str, Any]:
    """
    Load Gervais et al. psychometric norms from configuration.

    Returns:
        Dictionary containing mean and std for each foundation.
    """
    norms_path = get_path("data/config/gervais_norms.yaml")
    if not os.path.exists(norms_path):
        raise FileNotFoundError(f"Norms file not found at {norms_path}")

    import yaml
    with open(norms_path, 'r') as f:
        return yaml.safe_load(f)

def load_norms_data() -> Dict[str, Any]:
    """
    Load and return the full norms data structure.
    Alias for load_norms() for backward compatibility.
    """
    return load_norms()

def load_gervais_norms() -> Dict[str, Any]:
    """
    Load Gervais et al. norms.
    Alias for load_norms() for backward compatibility.
    """
    return load_norms()

def get_means(norms: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
    """
    Extract mean values from norms.

    Args:
        norms: Optional norms dictionary. If None, loads from file.

    Returns:
        Dictionary mapping foundation names to mean values.
    """
    if norms is None:
        norms = load_norms()

    means = {}
    for foundation in ['care', 'fairness', 'loyalty', 'authority', 'purity']:
        if foundation in norms:
            means[foundation] = norms[foundation].get('mean', 0.0)
        else:
            logger.warning(f"Foundation {foundation} not found in norms")
            means[foundation] = 0.0
    return means

def get_std_devs(norms: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
    """
    Extract standard deviation values from norms.

    Args:
        norms: Optional norms dictionary. If None, loads from file.

    Returns:
        Dictionary mapping foundation names to std values.
    """
    if norms is None:
        norms = load_norms()

    stds = {}
    for foundation in ['care', 'fairness', 'loyalty', 'authority', 'purity']:
        if foundation in norms:
            stds[foundation] = norms[foundation].get('std', 1.0)
        else:
            logger.warning(f"Foundation {foundation} not found in norms")
            stds[foundation] = 1.0
    return stds

def get_correlation_matrix(norms: Optional[Dict[str, Any]] = None) -> np.ndarray:
    """
    Extract correlation matrix from norms.

    Args:
        norms: Optional norms dictionary. If None, loads from file.

    Returns:
        Correlation matrix as numpy array.
    """
    if norms is None:
        norms = load_norms()

    # Default correlation matrix if not specified
    # Based on typical MFQ correlations (positive inter-foundation correlations)
    if 'correlation_matrix' in norms:
        corr_data = norms['correlation_matrix']
        return np.array(corr_data)
    else:
        # Default: identity matrix with slight positive off-diagonals
        foundations = ['care', 'fairness', 'loyalty', 'authority', 'purity']
        n = len(foundations)
        corr = np.eye(n)
        for i in range(n):
            for j in range(i+1, n):
                corr[i, j] = 0.3  # Typical moderate positive correlation
                corr[j, i] = 0.3
        return corr

def get_covariance_matrix(norms: Optional[Dict[str, Any]] = None) -> np.ndarray:
    """
    Compute covariance matrix from means, stds, and correlation.

    Args:
        norms: Optional norms dictionary. If None, loads from file.

    Returns:
        Covariance matrix as numpy array.
    """
    if norms is None:
        norms = load_norms()

    stds = list(get_std_devs(norms).values())
    corr = get_correlation_matrix(norms)

    # Convert correlation to covariance: Cov = D * Corr * D
    # where D is diagonal matrix of stds
    D = np.diag(stds)
    cov = D @ corr @ D
    return cov

def generate_synthetic_mfq_from_norms(n_samples: int, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic MFQ data matching Gervais et al. norms.

    Args:
        n_samples: Number of samples to generate.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with synthetic MFQ responses.
    """
    np.random.seed(seed)
    norms = load_norms()
    means = list(get_means(norms).values())
    cov = get_covariance_matrix(norms)

    # Generate multivariate normal samples
    data = np.random.multivariate_normal(means, cov, size=n_samples)

    # Create DataFrame
    columns = ['care', 'fairness', 'loyalty', 'authority', 'purity']
    df = pd.DataFrame(data, columns=columns)

    # Add participant IDs
    df.insert(0, 'participant_id', [f'P{i:04d}' for i in range(n_samples)])

    # Calculate total score
    df['total_score'] = df[['care', 'fairness', 'loyalty', 'authority', 'purity']].sum(axis=1)

    return df

def validate_against_norms(df: pd.DataFrame, norms: Optional[Dict[str, Any]] = None, 
                           max_sd_threshold: float = 1.0) -> Dict[str, Any]:
    """
    Validate that synthetic MFQ distribution matches published norms.
    
    Checks if the mean and std of each foundation in the data are within
    max_sd_threshold standard deviations of the published norms.
    
    Args:
        df: DataFrame containing MFQ data with columns: care, fairness, 
            loyalty, authority, purity.
        norms: Optional norms dictionary. If None, loads from file.
        max_sd_threshold: Maximum allowed deviation in standard deviations.
                        
    Returns:
        Dictionary with validation results for each foundation.
        Keys: foundation names, values: dict with 'mean_diff', 'std_diff', 
              'mean_within_threshold', 'std_within_threshold', 'pass'.
    """
    if norms is None:
        norms = load_norms()

    results = {}
    all_pass = True

    foundations = ['care', 'fairness', 'loyalty', 'authority', 'purity']
    
    for foundation in foundations:
        if foundation not in df.columns:
            results[foundation] = {
                'mean_diff': None,
                'std_diff': None,
                'mean_within_threshold': False,
                'std_within_threshold': False,
                'pass': False,
                'error': f"Column {foundation} not found in data"
            }
            all_pass = False
            continue

        if foundation not in norms:
            results[foundation] = {
                'mean_diff': None,
                'std_diff': None,
                'mean_within_threshold': False,
                'std_within_threshold': False,
                'pass': False,
                'error': f"Foundation {foundation} not found in norms"
            }
            all_pass = False
            continue

        # Calculate statistics
        data_mean = df[foundation].mean()
        data_std = df[foundation].std()
        norm_mean = norms[foundation].get('mean', 0.0)
        norm_std = norms[foundation].get('std', 1.0)

        # Calculate differences in standard deviations
        mean_diff = (data_mean - norm_mean) / norm_std if norm_std > 0 else 0.0
        std_diff = (data_std - norm_std) / norm_std if norm_std > 0 else 0.0

        # Check thresholds
        mean_within = abs(mean_diff) <= max_sd_threshold
        std_within = abs(std_diff) <= max_sd_threshold
        foundation_pass = mean_within and std_within

        if not foundation_pass:
            all_pass = False

        results[foundation] = {
            'data_mean': float(data_mean),
            'data_std': float(data_std),
            'norm_mean': float(norm_mean),
            'norm_std': float(norm_std),
            'mean_diff': float(mean_diff),
            'std_diff': float(std_diff),
            'mean_within_threshold': mean_within,
            'std_within_threshold': std_within,
            'pass': foundation_pass
        }

    # Add overall summary
    results['summary'] = {
        'all_foundations_pass': all_pass,
        'max_sd_threshold': max_sd_threshold,
        'foundations_checked': len(foundations),
        'foundations_passed': sum(1 for f in foundations if results.get(f, {}).get('pass', False))
    }

    return results

def run_validation_pipeline(data_path: Optional[str] = None, 
                            output_path: Optional[str] = None,
                            max_sd_threshold: float = 1.0) -> Dict[str, Any]:
    """
    Run the full validation pipeline on MFQ data.
    
    Args:
        data_path: Path to CSV file with MFQ data. If None, expects 
                   'data/processed/synthetic_mfq.csv'.
        output_path: Path to write JSON results. If None, writes to 
                    'state/norm_validation_results.json'.
        max_sd_threshold: Maximum allowed deviation in standard deviations.
                        
    Returns:
        Validation results dictionary.
    """
    if data_path is None:
        data_path = get_path("data/processed/synthetic_mfq.csv")
    if output_path is None:
        output_path = get_path("state/norm_validation_results.json")

    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)

    logger.info("Validating against norms")
    results = validate_against_norms(df, max_sd_threshold=max_sd_threshold)

    logger.info(f"Writing results to {output_path}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    return results

def main():
    """Main entry point for norms validation."""
    logging.basicConfig(level=logging.INFO)
    
    logger.info("Starting MFQ norms validation pipeline (T017)")
    
    try:
        results = run_validation_pipeline()
        
        if results['summary']['all_foundations_pass']:
            logger.info("SUCCESS: All foundations within threshold")
            logger.info(f"Foundations passed: {results['summary']['foundations_passed']}/{results['summary']['foundations_checked']}")
        else:
            logger.warning("WARNING: Some foundations outside threshold")
            logger.warning(f"Foundations passed: {results['summary']['foundations_passed']}/{results['summary']['foundations_checked']}")
            
        for foundation in ['care', 'fairness', 'loyalty', 'authority', 'purity']:
            if foundation in results:
                status = "PASS" if results[foundation].get('pass', False) else "FAIL"
                logger.info(f"{foundation}: {status} (mean_diff={results[foundation].get('mean_diff'):.2f}, std_diff={results[foundation].get('std_diff'):.2f})")
                
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()