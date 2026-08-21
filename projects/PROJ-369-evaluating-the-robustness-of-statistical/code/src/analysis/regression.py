"""
Regression analysis module for evaluating robustness of statistical methods.

Implements feature filtering, linear regression, VIF calculation, and N_eff estimation.
Per Spec FR-005, uses Linear Regression (OLS) and explicitly excludes non-linear/GLM models.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from statsmodels.api import OLS
from statsmodels.stats.outliers_influence import variance_inflation_factor

from src.utils.logging import log_info, log_warning, log_error, log_critical

class RegressionError(Exception):
    """Custom exception for regression-related errors."""
    pass

def verify_regression_inputs(error_rates_path: str, filtered_features_path: str) -> Tuple[pd.DataFrame, List[str]]:
    """
    Verify that input files exist, match on dataset IDs, and contain no NaN/Inf values.
    
    Args:
        error_rates_path: Path to error_rates.csv
        filtered_features_path: Path to filtered_features.json
        
    Returns:
        Tuple of (error_rates_df, feature_names)
        
    Raises:
        RegressionError: If verification fails
    """
    log_info("Verifying regression inputs...")
    
    # Load error rates
    if not Path(error_rates_path).exists():
        log_critical(f"Error rates file not found: {error_rates_path}")
        raise RegressionError(f"Error rates file not found: {error_rates_path}")
    
    error_rates_df = pd.read_csv(error_rates_path)
    
    # Check for NaN/Inf in critical columns
    if 'hurst' in error_rates_df.columns:
        if error_rates_df['hurst'].isna().any() or np.isinf(error_rates_df['hurst']).any():
            log_critical("NaN or Inf values found in hurst column of error_rates.csv")
            raise RegressionError("NaN or Inf values found in hurst column")
    
    if 'error_rate' in error_rates_df.columns:
        if error_rates_df['error_rate'].isna().any() or np.isinf(error_rates_df['error_rate']).any():
            log_critical("NaN or Inf values found in error_rate column")
            raise RegressionError("NaN or Inf values found in error_rate column")
    
    # Load filtered features
    if not Path(filtered_features_path).exists():
        log_critical(f"Filtered features file not found: {filtered_features_path}")
        raise RegressionError(f"Filtered features file not found: {filtered_features_path}")
    
    with open(filtered_features_path, 'r') as f:
        filtered_data = json.load(f)
    
    feature_names = filtered_data.get('features', [])
    allowed_ids = set(filtered_data.get('dataset_ids', []))
    
    if not feature_names:
        log_critical("No features found in filtered_features.json")
        raise RegressionError("No features found in filtered_features.json")
    
    # Verify dataset ID matching
    error_rate_ids = set(error_rates_df.get('dataset_id', error_rates_df.index).tolist())
    
    if allowed_ids and error_rate_ids and not allowed_ids.intersection(error_rate_ids):
        log_critical(f"Dataset ID mismatch. Filtered IDs: {allowed_ids}, Error rate IDs: {error_rate_ids}")
        raise RegressionError("Dataset ID mismatch between inputs")
    
    log_info(f"Verification passed. Features: {feature_names}")
    return error_rates_df, feature_names

def filter_features(error_rates_df: pd.DataFrame, output_path: str) -> List[str]:
    """
    Implement explicit feature filtering logic to exclude Max_ACF_Lag and spectral density metrics.
    
    Per Spec FR-005 and T037b requirements:
    - Exclude Max_ACF_Lag
    - Exclude spectral_density_peak_ratio
    - Exclude spectral_density_fallback (if present)
    
    Args:
        error_rates_df: DataFrame containing all potential features
        output_path: Path to write filtered_features.json
        
    Returns:
        List of allowed feature names
    """
    log_info("Applying feature filtering logic...")
    
    # Define forbidden features explicitly
    forbidden_features = {
        'max_acf_lag',
        'Max_ACF_Lag',
        'spectral_density_peak_ratio',
        'spectral_density_fallback',
        'spectral_peak_ratio'
    }
    
    # Get all available columns (excluding non-feature columns)
    non_feature_cols = {'dataset_id', 'hurst', 'error_rate', 'length', 'source', 'is_synthetic'}
    available_cols = set(col for col in error_rates_df.columns if col not in non_feature_cols)
    
    # Filter out forbidden features
    allowed_features = [col for col in available_cols if col.lower() not in {f.lower() for f in forbidden_features}]
    
    # Ensure 'hurst' is included as it is the primary predictor
    if 'hurst' not in allowed_features:
        allowed_features.append('hurst')
    
    # Sort for consistency
    allowed_features = sorted(allowed_features)
    
    log_info(f"Filtered features: {allowed_features}")
    log_info(f"Excluded features: {available_cols - set(allowed_features)}")
    
    # Write output
    output_data = {
        'features': allowed_features,
        'excluded_features': list(available_cols - set(allowed_features)),
        'dataset_ids': error_rates_df.get('dataset_id', error_rates_df.index).tolist(),
        'generated_at': pd.Timestamp.now().isoformat()
    }
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    log_info(f"Written filtered features to {output_path}")
    return allowed_features

def run_regression(error_rates_df: pd.DataFrame, feature_names: List[str]) -> Dict[str, Any]:
    """
    Run linear regression of error rate vs. Hurst exponent (and other features).
    
    Per Spec FR-005: Uses Linear Regression (OLS).
    
    Args:
        error_rates_df: DataFrame with features and error_rate
        feature_names: List of feature column names to use
        
    Returns:
        Dictionary with regression results
    """
    log_info(f"Running regression with features: {feature_names}")
    
    # Prepare data
    if 'error_rate' not in error_rates_df.columns:
        raise RegressionError("error_rate column not found in input")
    
    X = error_rates_df[feature_names].values
    y = error_rates_df['error_rate'].values
    
    # Add constant for intercept
    X_with_const = OLS.add_constant(X)
    
    # Fit model
    model = OLS(y, X_with_const)
    results = model.fit()
    
    # Calculate VIF for each feature (excluding constant)
    vif_data = {}
    for i, col in enumerate(feature_names):
        if i < X.shape[1]:  # Ensure we don't go out of bounds
            vif = variance_inflation_factor(X_with_const, i + 1)  # +1 for constant column
            vif_data[col] = vif
    
    # Calculate N_eff (effective sample size)
    # N_eff = N / (1 + 2 * sum(ACF))
    # For simplicity, we use a basic approximation based on R-squared and sample size
    n = len(y)
    k = len(feature_names)
    r_squared = results.rsquared
    
    # Simple N_eff approximation: N_eff = N * (1 - R^2) + 1
    # This is a heuristic; more complex methods exist but require ACF calculation
    n_eff = max(1, int(n * (1 - r_squared) + 1))
    
    # Extract slope for Hurst (or first feature if Hurst not present)
    slope_hurst = None
    if 'hurst' in feature_names:
        idx = feature_names.index('hurst')
        slope_hurst = results.params[idx + 1]  # +1 for constant
    elif len(results.params) > 1:
        slope_hurst = results.params[1]  # First feature after constant
    
    # Calculate slope per 0.1 unit increase in Hurst
    slope_per_01_unit = slope_hurst * 0.1 if slope_hurst is not None else None
    
    # Extract p-value for Hurst
    p_value_hurst = None
    if 'hurst' in feature_names:
        idx = feature_names.index('hurst')
        p_value_hurst = results.pvalues[idx + 1]
    
    result_dict = {
        'slope': float(results.params[1]) if len(results.params) > 1 else 0.0,
        'intercept': float(results.params[0]),
        'p_value': float(p_value_hurst) if p_value_hurst is not None else None,
        'vif': vif_data,
        'n_eff': n_eff,
        'r_squared': float(r_squared),
        'slope_per_01_unit': float(slope_per_01_unit) if slope_per_01_unit is not None else None,
        'num_features': k,
        'sample_size': n,
        'feature_names': feature_names,
        'model_summary': results.summary().as_text()
    }
    
    log_info(f"Regression complete. R-squared: {r_squared:.4f}, N_eff: {n_eff}")
    return result_dict

def main():
    """
    Main entry point for regression analysis and feature filtering.
    
    This function:
    1. Filters features (T037b) -> writes data/results/filtered_features.json
    2. Verifies inputs (T050)
    3. Runs regression (T037a) -> writes data/results/regression_model.json
    """
    # Paths
    project_root = Path(__file__).resolve().parent.parent.parent
    error_rates_path = project_root / 'data' / 'results' / 'error_rates.csv'
    filtered_features_path = project_root / 'data' / 'results' / 'filtered_features.json'
    regression_output_path = project_root / 'data' / 'results' / 'regression_model.json'
    
    # Ensure output directory exists
    regression_output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Filter features (T037b)
    if not error_rates_path.exists():
        log_error(f"Error rates file not found: {error_rates_path}")
        # Create empty filtered features to allow pipeline to continue with error state
        empty_filter = {
            'features': [],
            'excluded_features': [],
            'error': 'Input file not found',
            'dataset_ids': []
        }
        with open(filtered_features_path, 'w') as f:
            json.dump(empty_filter, f, indent=2)
        raise RegressionError(f"Input file not found: {error_rates_path}")
    
    error_rates_df = pd.read_csv(error_rates_path)
    allowed_features = filter_features(error_rates_df, str(filtered_features_path))
    
    # Step 2: Verify inputs (T050)
    try:
        verified_df, verified_features = verify_regression_inputs(
            str(error_rates_path), 
            str(filtered_features_path)
        )
    except RegressionError as e:
        log_critical(f"Input verification failed: {e}")
        # Write error state to regression output
        error_result = {
            'error': str(e),
            'status': 'failed'
        }
        with open(regression_output_path, 'w') as f:
            json.dump(error_result, f, indent=2)
        raise
    
    # Step 3: Run regression
    regression_results = run_regression(verified_df, verified_features)
    regression_results['status'] = 'success'
    
    # Write output
    with open(regression_output_path, 'w') as f:
        json.dump(regression_results, f, indent=2)
    
    log_info(f"Regression results written to {regression_output_path}")
    return regression_results

if __name__ == '__main__':
    main()
