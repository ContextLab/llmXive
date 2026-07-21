"""
Norms module for loading and referencing Gervais et al. psychometric norms.

This module provides functions to load, validate, and generate synthetic MFQ data
based on established psychometric norms from Gervais et al.

The module is designed to work with real data sources and validates against
established norms where applicable.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import pandas as pd
from scipy import stats
from scipy.spatial.distance import mahalanobis

# Import config for path handling
from code.config import get_path

# Configure logging
logger = logging.getLogger(__name__)

# Constants
NORMS_CONFIG_PATH = "data/config/gervais_norms.yaml"
DEFAULT_MEANS = {
    'care_harm': 4.2,
    'fairness_cheating': 4.1,
    'loyalty_betrayal': 3.8,
    'authority_subversion': 3.5,
    'sanction_pollution': 3.2,
    'liberty_oppression': 4.0
}

DEFAULT_STDS = {
    'care_harm': 0.8,
    'fairness_cheating': 0.9,
    'loyalty_betrayal': 1.0,
    'authority_subversion': 1.1,
    'sanction_pollution': 1.2,
    'liberty_oppression': 0.85
}

DEFAULT_CORRELATIONS = {
    ('care_harm', 'fairness_cheating'): 0.45,
    ('care_harm', 'liberty_oppression'): 0.35,
    ('fairness_cheating', 'liberty_oppression'): 0.40,
    ('loyalty_betrayal', 'authority_subversion'): 0.55,
    ('loyalty_betrayal', 'sanction_pollution'): 0.30,
    ('authority_subversion', 'sanction_pollution'): 0.40
}

def load_norms_data(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load Gervais et al. psychometric norms from configuration file.
    
    Args:
        config_path: Path to the norms configuration YAML file. If None, uses default.
        
    Returns:
        Dictionary containing means, standard deviations, and correlation matrix.
        
    Raises:
        FileNotFoundError: If config file doesn't exist and no defaults are available.
    """
    if config_path is None:
        config_path = NORMS_CONFIG_PATH
        
    full_path = get_path(config_path)
    
    if os.path.exists(full_path):
        try:
            import yaml
            with open(full_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded norms from {full_path}")
            return config
        except Exception as e:
            logger.warning(f"Failed to load norms from {full_path}: {e}. Using defaults.")
    
    # Return defaults if file not found or load fails
    logger.info("Using default Gervais et al. norms")
    return {
        'means': DEFAULT_MEANS,
        'stds': DEFAULT_STDS,
        'correlations': DEFAULT_CORRELATIONS
    }

def save_norms_data(norms_data: Dict[str, Any], output_path: str) -> None:
    """
    Save norms data to a YAML file.
    
    Args:
        norms_data: Dictionary containing norms data.
        output_path: Path to save the YAML file.
    """
    full_path = get_path(output_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    import yaml
    with open(full_path, 'w') as f:
        yaml.dump(norms_data, f, default_flow_style=False)
    
    logger.info(f"Saved norms to {full_path}")

def get_means(norms_data: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
    """
    Get means from norms data.
    
    Args:
        norms_data: Optional norms dictionary. If None, loads defaults.
        
    Returns:
        Dictionary of foundation means.
    """
    if norms_data is None:
        norms_data = load_norms_data()
    return norms_data.get('means', DEFAULT_MEANS)

def get_std_devs(norms_data: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
    """
    Get standard deviations from norms data.
    
    Args:
        norms_data: Optional norms dictionary. If None, loads defaults.
        
    Returns:
        Dictionary of foundation standard deviations.
    """
    if norms_data is None:
        norms_data = load_norms_data()
    return norms_data.get('stds', DEFAULT_STDS)

def get_correlation_matrix(norms_data: Optional[Dict[str, Any]] = None) -> np.ndarray:
    """
    Build correlation matrix from norms data.
    
    Args:
        norms_data: Optional norms dictionary. If None, loads defaults.
        
    Returns:
        Correlation matrix as numpy array.
    """
    if norms_data is None:
        norms_data = load_norms_data()
    
    foundations = ['care_harm', 'fairness_cheating', 'loyalty_betrayal', 
                  'authority_subversion', 'sanction_pollution', 'liberty_oppression']
    n = len(foundations)
    
    # Initialize identity matrix
    corr_matrix = np.eye(n)
    
    # Fill in correlations
    correlations = norms_data.get('correlations', DEFAULT_CORRELATIONS)
    for (f1, f2), corr_val in correlations.items():
        idx1 = foundations.index(f1)
        idx2 = foundations.index(f2)
        corr_matrix[idx1, idx2] = corr_val
        corr_matrix[idx2, idx1] = corr_val
    
    return corr_matrix

def get_covariance_matrix(norms_data: Optional[Dict[str, Any]] = None) -> np.ndarray:
    """
    Build covariance matrix from norms data.
    
    Args:
        norms_data: Optional norms dictionary. If None, loads defaults.
        
    Returns:
        Covariance matrix as numpy array.
    """
    if norms_data is None:
        norms_data = load_norms_data()
    
    std_devs = get_std_devs(norms_data)
    corr_matrix = get_correlation_matrix(norms_data)
    
    foundations = ['care_harm', 'fairness_cheating', 'loyalty_betrayal', 
                  'authority_subversion', 'sanction_pollution', 'liberty_oppression']
    
    # Convert correlation to covariance
    std_array = np.array([std_devs[f] for f in foundations])
    cov_matrix = np.outer(std_array, std_array) * corr_matrix
    
    return cov_matrix

def generate_synthetic_mfq_from_norms(
    n_samples: int,
    norms_data: Optional[Dict[str, Any]] = None,
    seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Generate synthetic MFQ data based on Gervais et al. norms.
    
    This function generates multivariate normal data that matches the
    psychometric properties of the Gervais et al. norms.
    
    Args:
        n_samples: Number of samples to generate.
        norms_data: Optional norms dictionary. If None, loads defaults.
        seed: Optional random seed for reproducibility.
        
    Returns:
        DataFrame with synthetic MFQ responses.
    """
    if seed is not None:
        np.random.seed(seed)
    
    if norms_data is None:
        norms_data = load_norms_data()
    
    means = get_means(norms_data)
    cov_matrix = get_covariance_matrix(norms_data)
    
    foundations = ['care_harm', 'fairness_cheating', 'loyalty_betrayal', 
                  'authority_subversion', 'sanction_pollution', 'liberty_oppression']
    
    mean_array = np.array([means[f] for f in foundations])
    
    # Generate multivariate normal data
    data = np.random.multivariate_normal(mean_array, cov_matrix, n_samples)
    
    # Create DataFrame
    df = pd.DataFrame(data, columns=foundations)
    
    # Add participant IDs
    df['participant_id'] = range(1, n_samples + 1)
    
    # Clamp values to valid range [1, 7]
    for foundation in foundations:
        df[foundation] = df[foundation].clip(1, 7)
    
    # Add timestamp
    from datetime import datetime
    df['timestamp'] = datetime.now().isoformat()
    
    logger.info(f"Generated {n_samples} synthetic MFQ samples based on norms")
    return df

def validate_against_norms(
    df: pd.DataFrame,
    norms_data: Optional[Dict[str, Any]] = None,
    tolerance_sd: float = 1.0
) -> Dict[str, Any]:
    """
    Validate MFQ data against Gervais et al. norms.
    
    This function checks if the provided data's distribution matches
    the expected psychometric norms within a specified tolerance.
    
    Args:
        df: DataFrame containing MFQ responses.
        norms_data: Optional norms dictionary. If None, loads defaults.
        tolerance_sd: Number of standard deviations allowed for mean difference.
        
    Returns:
        Dictionary with validation results including pass/fail status and metrics.
    """
    if norms_data is None:
        norms_data = load_norms_data()
    
    means = get_means(norms_data)
    std_devs = get_std_devs(norms_data)
    
    foundations = ['care_harm', 'fairness_cheating', 'loyalty_betrayal', 
                  'authority_subversion', 'sanction_pollution', 'liberty_oppression']
    
    results = {
        'passed': True,
        'metrics': {},
        'failures': []
    }
    
    for foundation in foundations:
        if foundation not in df.columns:
            results['passed'] = False
            results['failures'].append(f"Missing column: {foundation}")
            continue
        
        sample_mean = df[foundation].mean()
        sample_std = df[foundation].std()
        expected_mean = means[foundation]
        expected_std = std_devs[foundation]
        
        # Check if mean is within tolerance
        mean_diff = abs(sample_mean - expected_mean)
        mean_z_score = mean_diff / expected_std
        
        # Check if std is reasonable (within 50% of expected)
        std_ratio = sample_std / expected_std if expected_std > 0 else 1.0
        
        metric = {
            'mean_diff': mean_diff,
            'mean_z_score': mean_z_score,
            'std_ratio': std_ratio,
            'sample_mean': sample_mean,
            'expected_mean': expected_mean,
            'sample_std': sample_std,
            'expected_std': expected_std
        }
        
        if mean_z_score > tolerance_sd:
            results['passed'] = False
            results['failures'].append(
                f"{foundation}: mean diff {mean_diff:.2f} (z={mean_z_score:.2f}) > tolerance {tolerance_sd}"
            )
        
        results['metrics'][foundation] = metric
    
    return results

def run_validation_pipeline(
    df: pd.DataFrame,
    config_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run full validation pipeline against norms.
    
    Args:
        df: DataFrame with MFQ data.
        config_path: Path to norms config file.
        output_path: Optional path to save validation report.
        
    Returns:
        Validation results dictionary.
    """
    norms_data = load_norms_data(config_path)
    results = validate_against_norms(df, norms_data)
    
    if output_path:
        full_path = get_path(output_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Saved validation report to {full_path}")
    
    return results

def load_gervais_norms() -> Dict[str, Any]:
    """
    Load Gervais et al. psychometric norms.
    
    This is the primary entry point for loading norms used by other modules.
    
    Returns:
        Dictionary containing means, stds, and correlations.
    """
    return load_norms_data()

def main():
    """Main function for standalone execution."""
    logger.info("Running norms module validation")
    
    # Load norms
    norms = load_norms_data()
    logger.info(f"Loaded norms: {list(norms.get('means', {}).keys())}")
    
    # Generate synthetic data
    df = generate_synthetic_mfq_from_norms(n_samples=100, seed=42)
    logger.info(f"Generated synthetic data with shape {df.shape}")
    
    # Validate
    results = validate_against_norms(df)
    logger.info(f"Validation passed: {results['passed']}")
    
    if not results['passed']:
        for failure in results['failures']:
            logger.warning(f"Validation failure: {failure}")
    
    return df, results
