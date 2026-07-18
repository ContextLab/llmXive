"""
Norms module for loading, managing, and validating against psychometric norms.

This module handles the Gervais et al. psychometric norms for Moral Foundations
Questionnaire (MFQ) data, providing utilities to load reference data, calculate
statistics, and validate synthetic or real data against published norms.
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

# Configure logging for this module
logger = logging.getLogger(__name__)

# Default path for norms data (relative to project root)
NORMS_DATA_PATH = Path("data/config/mfq_norms.json")
NORMS_OUTPUT_PATH = Path("data/processed/norms_validation_report.json")

# Standard deviation threshold for validation (1 SD as per task requirement)
VALIDATION_SD_THRESHOLD = 1.0

def load_norms_data(norms_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the Gervais et al. MFQ norms from a JSON file.
    
    Args:
        norms_path: Path to the norms JSON file. Defaults to NORMS_DATA_PATH.
        
    Returns:
        Dictionary containing means, standard deviations, and correlation matrix.
        
    Raises:
        FileNotFoundError: If the norms file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    if norms_path is None:
        norms_path = NORMS_DATA_PATH
        
    if not norms_path.exists():
        raise FileNotFoundError(f"Norms data file not found: {norms_path}")
        
    with open(norms_path, 'r') as f:
        data = json.load(f)
        
    logger.info(f"Loaded norms data from {norms_path}")
    return data

def save_norms_data(data: Dict[str, Any], norms_path: Optional[Path] = None) -> None:
    """
    Save norms data to a JSON file.
    
    Args:
        data: Dictionary containing norms data.
        norms_path: Path to save the file. Defaults to NORMS_DATA_PATH.
    """
    if norms_path is None:
        norms_path = NORMS_DATA_PATH
        
    norms_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(norms_path, 'w') as f:
        json.dump(data, f, indent=2)
        
    logger.info(f"Saved norms data to {norms_path}")

def get_means(norms_data: Dict[str, Any]) -> np.ndarray:
    """
    Extract means from norms data.
    
    Args:
        norms_data: Dictionary containing norms data.
        
    Returns:
        Array of means for each moral foundation.
    """
    return np.array(norms_data['means'])

def get_std_devs(norms_data: Dict[str, Any]) -> np.ndarray:
    """
    Extract standard deviations from norms data.
    
    Args:
        norms_data: Dictionary containing norms data.
        
    Returns:
        Array of standard deviations for each moral foundation.
    """
    return np.array(norms_data['std_devs'])

def get_correlation_matrix(norms_data: Dict[str, Any]) -> np.ndarray:
    """
    Extract correlation matrix from norms data.
    
    Args:
        norms_data: Dictionary containing norms data.
        
    Returns:
        Correlation matrix as a 2D numpy array.
    """
    return np.array(norms_data['correlation_matrix'])

def get_covariance_matrix(norms_data: Dict[str, Any]) -> np.ndarray:
    """
    Calculate covariance matrix from correlation matrix and standard deviations.
    
    Args:
        norms_data: Dictionary containing norms data.
        
    Returns:
        Covariance matrix as a 2D numpy array.
    """
    std_devs = get_std_devs(norms_data)
    corr_matrix = get_correlation_matrix(norms_data)
    
    # Covariance = correlation * std_dev_i * std_dev_j
    std_devs_matrix = np.outer(std_devs, std_devs)
    cov_matrix = corr_matrix * std_devs_matrix
    
    return cov_matrix

def generate_synthetic_mfq_from_norms(
    norms_data: Dict[str, Any],
    n_samples: int,
    random_seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Generate synthetic MFQ data based on the provided norms.
    
    Args:
        norms_data: Dictionary containing norms data.
        n_samples: Number of samples to generate.
        random_seed: Random seed for reproducibility.
        
    Returns:
        DataFrame with synthetic MFQ data.
    """
    if random_seed is not None:
        np.random.seed(random_seed)
        
    means = get_means(norms_data)
    cov_matrix = get_covariance_matrix(norms_data)
    
    # Generate multivariate normal samples
    samples = np.random.multivariate_normal(means, cov_matrix, n_samples)
    
    # Create DataFrame with foundation names
    foundation_names = ['Care', 'Fairness', 'Loyalty', 'Authority', 'Purity']
    df = pd.DataFrame(samples, columns=foundation_names)
    
    logger.info(f"Generated {n_samples} synthetic MFQ samples from norms")
    return df

def validate_against_norms(
    synthetic_data: pd.DataFrame,
    norms_data: Dict[str, Any],
    sd_threshold: float = VALIDATION_SD_THRESHOLD,
    foundation_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Validate synthetic MFQ data against published norms.
    
    This function compares the mean and standard deviation of each moral foundation
    in the synthetic data against the published norms, checking if they fall within
    the specified standard deviation threshold.
    
    Args:
        synthetic_data: DataFrame containing synthetic MFQ data.
        norms_data: Dictionary containing published norms.
        sd_threshold: Number of standard deviations to allow for validation.
        foundation_names: Optional list of foundation column names. If None,
            will infer from norms data keys.
            
    Returns:
        Dictionary containing validation results with:
            - 'passed': Boolean indicating if all foundations passed
            - 'details': List of detailed results for each foundation
            - 'summary': Summary statistics
    """
    if foundation_names is None:
        # Infer foundation names from norms data keys (excluding metadata)
        foundation_names = [k for k in norms_data.keys() if k not in ['means', 'std_devs', 'correlation_matrix']]
        
    means = get_means(norms_data)
    std_devs = get_std_devs(norms_data)
    
    results = {
        'passed': True,
        'details': [],
        'summary': {}
    }
    
    for i, foundation in enumerate(foundation_names):
        if foundation not in synthetic_data.columns:
            logger.warning(f"Foundation '{foundation}' not found in synthetic data")
            results['passed'] = False
            results['details'].append({
                'foundation': foundation,
                'passed': False,
                'reason': 'Column not found in data'
            })
            continue
            
        synthetic_mean = synthetic_data[foundation].mean()
        synthetic_std = synthetic_data[foundation].std()
        norm_mean = means[i]
        norm_std = std_devs[i]
        
        # Check if mean is within threshold * std_dev of norm mean
        mean_diff = abs(synthetic_mean - norm_mean)
        mean_z_score = mean_diff / norm_std if norm_std > 0 else float('inf')
        mean_passed = mean_z_score <= sd_threshold
        
        # Check if std is within threshold * std_dev of norm std
        std_diff = abs(synthetic_std - norm_std)
        std_z_score = std_diff / norm_std if norm_std > 0 else float('inf')
        std_passed = std_z_score <= sd_threshold
        
        foundation_passed = mean_passed and std_passed
        
        if not foundation_passed:
            results['passed'] = False
            
        detail = {
            'foundation': foundation,
            'passed': foundation_passed,
            'synthetic_mean': float(synthetic_mean),
            'norm_mean': float(norm_mean),
            'mean_diff': float(mean_diff),
            'mean_z_score': float(mean_z_score),
            'synthetic_std': float(synthetic_std),
            'norm_std': float(norm_std),
            'std_diff': float(std_diff),
            'std_z_score': float(std_z_score),
            'threshold': sd_threshold
        }
        
        results['details'].append(detail)
        
        logger.info(f"Foundation {foundation}: mean_diff={mean_diff:.4f}, "
                   f"mean_z_score={mean_z_score:.4f}, passed={mean_passed}")
    
    # Calculate summary statistics
    passed_count = sum(1 for d in results['details'] if d['passed'])
    total_count = len(results['details'])
    results['summary'] = {
        'total_foundations': total_count,
        'passed_foundations': passed_count,
        'overall_pass_rate': passed_count / total_count if total_count > 0 else 0.0
    }
    
    return results

def run_validation_pipeline(
    synthetic_data_path: Path,
    norms_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    sd_threshold: float = VALIDATION_SD_THRESHOLD
) -> Dict[str, Any]:
    """
    Run the full validation pipeline: load data, validate against norms, save results.
    
    Args:
        synthetic_data_path: Path to the synthetic MFQ data CSV file.
        norms_path: Path to the norms JSON file. Defaults to NORMS_DATA_PATH.
        output_path: Path to save the validation report. Defaults to NORMS_OUTPUT_PATH.
        sd_threshold: Number of standard deviations to allow for validation.
        
    Returns:
        Dictionary containing validation results.
    """
    # Load norms data
    logger.info(f"Loading norms data from {norms_path or NORMS_DATA_PATH}")
    norms_data = load_norms_data(norms_path)
    
    # Load synthetic data
    logger.info(f"Loading synthetic data from {synthetic_data_path}")
    if not synthetic_data_path.exists():
        raise FileNotFoundError(f"Synthetic data file not found: {synthetic_data_path}")
        
    synthetic_data = pd.read_csv(synthetic_data_path)
    
    # Validate against norms
    logger.info("Validating synthetic data against norms")
    validation_results = validate_against_norms(
        synthetic_data, norms_data, sd_threshold
    )
    
    # Add metadata to results
    validation_results['metadata'] = {
        'synthetic_data_path': str(synthetic_data_path),
        'norms_path': str(norms_path or NORMS_DATA_PATH),
        'sd_threshold': sd_threshold,
        'sample_size': len(synthetic_data)
    }
    
    # Save results
    if output_path is None:
        output_path = NORMS_OUTPUT_PATH
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(validation_results, f, indent=2)
        
    logger.info(f"Validation report saved to {output_path}")
    logger.info(f"Overall validation passed: {validation_results['passed']}")
    
    return validation_results

def main():
    """
    Main entry point for the norms validation script.
    
    This function demonstrates the usage of the norms validation pipeline
    by loading sample data and validating it against the Gervais et al. norms.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Define paths
    synthetic_data_path = Path("data/processed/synthetic_mfq.csv")
    norms_path = Path("data/config/mfq_norms.json")
    output_path = Path("data/processed/norms_validation_report.json")
    
    # Check if synthetic data exists
    if not synthetic_data_path.exists():
        logger.error(f"Synthetic data file not found: {synthetic_data_path}")
        logger.info("Please run simulation_mfq.py first to generate synthetic data")
        sys.exit(1)
        
    # Run validation pipeline
    try:
        results = run_validation_pipeline(
            synthetic_data_path=synthetic_data_path,
            norms_path=norms_path,
            output_path=output_path
        )
        
        # Print summary
        print("\n=== Norms Validation Summary ===")
        print(f"Overall Passed: {results['passed']}")
        print(f"Foundations Passed: {results['summary']['passed_foundations']}/{results['summary']['total_foundations']}")
        print(f"Pass Rate: {results['summary']['overall_pass_rate']:.2%}")
        
        print("\nDetailed Results:")
        for detail in results['details']:
            status = "PASS" if detail['passed'] else "FAIL"
            print(f"  {detail['foundation']}: {status} "
                 f"(mean_z={detail['mean_z_score']:.3f}, std_z={detail['std_z_score']:.3f})")
                 
    except Exception as e:
        logger.error(f"Validation pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()