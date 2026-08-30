"""
Feature validation module.

This module validates extracted features for NaN/Inf values, physiological plausibility,
and overall data quality.
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

from config import load_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_features(features_path: Path) -> pd.DataFrame:
    """
    Load features from a CSV file.
    
    Args:
        features_path: Path to the features CSV file
    
    Returns:
        DataFrame containing the features
    """
    logger.info(f"Loading features from {features_path}")
    return pd.read_csv(features_path)

def check_nan_inf_ratio(features_df: pd.DataFrame) -> Dict[str, float]:
    """
    Check the ratio of NaN/Inf values in the feature matrix.
    
    Args:
        features_df: DataFrame containing the features
    
    Returns:
        Dictionary with statistics about NaN/Inf values
    """
    total_values = features_df.size
    nan_count = features_df.isna().sum().sum()
    inf_count = np.isinf(features_df.values).sum()
    
    return {
        'total_values': total_values,
        'nan_count': int(nan_count),
        'inf_count': int(inf_count),
        'nan_ratio': float(nan_count / total_values) if total_values > 0 else 0.0,
        'inf_ratio': float(inf_count / total_values) if total_values > 0 else 0.0
    }

def check_physiological_bounds(features_df: pd.DataFrame) -> Dict[str, bool]:
    """
    Check if feature values fall within physiologically plausible ranges.
    
    Args:
        features_df: DataFrame containing the features
    
    Returns:
        Dictionary with validation results for each feature
    """
    # Define plausible ranges (in dB) for EEG power
    # These are approximate and may need adjustment based on specific setup
    bounds = {
        'alpha': (-20, 20),
        'beta': (-20, 20)
    }
    
    results = {}
    
    for col in features_df.columns:
        if col.startswith('alpha_'):
            band = 'alpha'
        elif col.startswith('beta_'):
            band = 'beta'
        else:
            continue
        
        min_val, max_val = bounds[band]
        values = features_df[col].dropna()
        
        if len(values) == 0:
            results[col] = False
            continue
        
        in_bounds = ((values >= min_val) & (values <= max_val)).all()
        results[col] = bool(in_bounds)
    
    return results

def validate_features(features_df: pd.DataFrame, threshold: float = 0.8) -> Dict[str, Any]:
    """
    Validate the feature matrix.
    
    Args:
        features_df: DataFrame containing the features
        threshold: Minimum ratio of valid epochs required (default 0.8)
    
    Returns:
        Dictionary with validation results
    """
    logger.info("Validating features")
    
    # Check NaN/Inf ratio
    nan_inf_stats = check_nan_inf_ratio(features_df)
    
    # Check physiological bounds
    bounds_results = check_physiological_bounds(features_df)
    
    # Calculate overall validity
    valid_epochs = features_df.dropna().shape[0]
    total_epochs = features_df.shape[0]
    valid_ratio = valid_epochs / total_epochs if total_epochs > 0 else 0.0
    
    # Determine if validation passes
    is_valid = (
        nan_inf_stats['nan_ratio'] < (1 - threshold) and
        nan_inf_stats['inf_ratio'] < 0.01 and
        valid_ratio >= threshold and
        all(bounds_results.values())
    )
    
    return {
        'valid': is_valid,
        'reason': 'Validation passed' if is_valid else 'Validation failed',
        'nan_inf_stats': nan_inf_stats,
        'bounds_results': bounds_results,
        'valid_ratio': valid_ratio,
        'threshold': threshold
    }

def main():
    """Main function to validate features."""
    config = load_config()
    from config import get_paths
    paths = get_paths(config)
    
    features_path = paths['features_matrix']
    
    if not features_path.exists():
        logger.error(f"Features file not found: {features_path}")
        return False
    
    features_df = load_features(features_path)
    validation_result = validate_features(features_df)
    
    logger.info(f"Validation result: {validation_result['valid']}")
    logger.info(f"Reason: {validation_result['reason']}")
    
    return validation_result['valid']

if __name__ == "__main__":
    main()
