"""
Regression analysis module for evaluating robustness of statistical methods.

This module implements feature filtering and regression logic to analyze
the relationship between Hurst exponent and Type I error rates.

Per Spec FR-005 and US3-AC2/AC3, this implements Linear Regression (OLS).

Features excluded per T037b: Max_ACF_Lag, spectral density metrics.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor
import statsmodels.api as sm

from src.utils.logging import log_info, log_warning, log_error, log_critical
from src.utils.config import get_path


class RegressionError(Exception):
    """Custom exception for regression-related errors."""
    pass


# Feature filtering configuration per T037b
EXCLUDED_FEATURES = [
    'Max_ACF_Lag',
    'spectral_density_peak_ratio',
    'spectral_peak_ratio'
]

INCLUDED_FEATURES = [
    'hurst',
    'length',
    'acf_mean',
    'acf_max',
    'variance',
    'skewness',
    'kurtosis'
]

def verify_regression_inputs(error_rates_path: str, features_path: str) -> Dict[str, Any]:
    """
    Verify that input files exist and contain valid data.
    
    Args:
        error_rates_path: Path to error_rates.csv
        features_path: Path to filtered_features.json
        
    Returns:
        Dict with verification status and details
        
    Raises:
        RegressionError: If inputs are invalid
    """
    error_rates_path = Path(error_rates_path)
    features_path = Path(features_path)
    
    # Check files exist
    if not error_rates_path.exists():
        raise RegressionError(f"Error rates file not found: {error_rates_path}")
    if not features_path.exists():
        raise RegressionError(f"Filtered features file not found: {features_path}")
    
    # Load and validate error rates
    try:
        error_rates_df = pd.read_csv(error_rates_path)
        if 'hurst' not in error_rates_df.columns or 'error_rate' not in error_rates_df.columns:
            raise RegressionError("Error rates CSV must contain 'hurst' and 'error_rate' columns")
        
        # Check for NaN/Inf
        if error_rates_df['hurst'].isna().any() or error_rates_df['error_rate'].isna().any():
            raise RegressionError("Error rates contain NaN values")
        if np.isinf(error_rates_df['hurst']).any() or np.isinf(error_rates_df['error_rate']).any():
            raise RegressionError("Error rates contain Inf values")
        
        log_info(f"Loaded error rates: {len(error_rates_df)} records")
    except Exception as e:
        raise RegressionError(f"Failed to load error rates: {e}")
    
    # Load and validate features
    try:
        with open(features_path, 'r') as f:
            features_data = json.load(f)
        
        if not isinstance(features_data, list) or len(features_data) == 0:
            raise RegressionError("Filtered features must be a non-empty list")
        
        log_info(f"Loaded filtered features: {len(features_data)} features")
    except Exception as e:
        raise RegressionError(f"Failed to load filtered features: {e}")
    
    return {
        'status': 'PASS',
        'error_rates_count': len(error_rates_df),
        'features_count': len(features_data),
        'error_rates_path': str(error_rates_path),
        'features_path': str(features_path)
    }

def check_regression_stability(error_rates_df: pd.DataFrame, threshold: float = 0.05) -> Dict[str, Any]:
    """
    Check for stability in the regression data.
    
    Args:
        error_rates_df: DataFrame with hurst and error_rate columns
        threshold: Maximum acceptable variance in error rates
        
    Returns:
        Dict with stability assessment
    """
    hurst_values = error_rates_df['hurst'].values
    error_rates = error_rates_df['error_rate'].values
    
    # Check for sufficient variation in Hurst
    if len(np.unique(hurst_values)) < 3:
        log_warning("Low variation in Hurst exponent values")
    
    # Check error rate distribution
    mean_error = np.mean(error_rates)
    std_error = np.std(error_rates)
    
    stability = {
        'hurst_range': [float(np.min(hurst_values)), float(np.max(hurst_values))],
        'error_rate_mean': float(mean_error),
        'error_rate_std': float(std_error),
        'data_points': len(error_rates),
        'stable': std_error < threshold
    }
    
    if stability['stable']:
        log_info(f"Regression data is stable: std={std_error:.4f}")
    else:
        log_warning(f"Regression data shows high variance: std={std_error:.4f}")
    
    return stability

def calculate_n_eff(hurst: float, n: int) -> float:
    """
    Calculate effective sample size for long-memory processes.
    
    Uses the approximation: N_eff ≈ N / VIF
    where VIF_theoretical ≈ N^(2H-1)
    
    Args:
        hurst: Hurst exponent (0.5 to 1.0)
        n: Actual sample size
        
    Returns:
        Effective sample size
    """
    if hurst <= 0.5:
        # For H <= 0.5, assume independence
        return float(n)
    
    # Theoretical VIF for long-memory processes
    vif_theoretical = n ** (2 * hurst - 1)
    n_eff = n / vif_theoretical
    
    return float(max(1, n_eff))  # Ensure at least 1

def run_regression(X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """
    Run OLS regression with VIF diagnostics.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        
    Returns:
        Dict with regression results
    """
    # Add constant for intercept
    X_with_const = sm.add_constant(X)
    
    # Fit OLS model
    model = sm.OLS(y, X_with_const)
    results = model.fit()
    
    # Calculate VIF for each feature
    vif_values = []
    for i in range(X_with_const.shape[1]):
        vif = variance_inflation_factor(X_with_const, i)
        vif_values.append(float(vif))
    
    return {
        'coefficients': results.params.tolist(),
        'p_values': results.pvalues.tolist(),
        'r_squared': float(results.rsquared),
        'adj_r_squared': float(results.rsquared_adj),
        'vif': vif_values,
        'n_obs': int(results.nobs),
        'summary': results.summary().as_text()
    }

def run_univariate_regression(hurst_values: np.ndarray, error_rates: np.ndarray) -> Dict[str, Any]:
    """
    Run univariate regression: error_rate ~ hurst.
    
    This is the primary analysis per US3-AC2.
    
    Args:
        hurst_values: Array of Hurst exponents
        error_rates: Array of Type I error rates
        
    Returns:
        Dict with regression results including slope_per_01_unit
    """
    X = hurst_values.reshape(-1, 1)
    y = error_rates
    
    # Add constant
    X_with_const = sm.add_constant(X)
    
    # Fit model
    model = sm.OLS(y, X_with_const)
    results = model.fit()
    
    # Extract key metrics
    slope = float(results.params[1])
    intercept = float(results.params[0])
    p_value = float(results.pvalues[1])
    r_squared = float(results.rsquared)
    
    # Calculate slope per 0.1 unit increase in H (per SC-002)
    slope_per_01_unit = slope * 0.1
    
    # Calculate VIF for single feature (should be 1.0 for univariate)
    vif = variance_inflation_factor(X_with_const, 1)
    
    # Calculate N_eff for typical sample size
    typical_n = int(np.mean([len(hurst_values)])) if len(hurst_values) > 0 else 1000
    avg_hurst = np.mean(hurst_values)
    n_eff = calculate_n_eff(avg_hurst, typical_n)
    
    return {
        'slope': slope,
        'intercept': intercept,
        'p_value': p_value,
        'r_squared': r_squared,
        'slope_per_01_unit': slope_per_01_unit,
        'vif': float(vif),
        'n_eff': n_eff,
        'n_obs': int(results.nobs),
        'model_type': 'univariate_ols'
    }

def filter_features(feature_list: List[str]) -> List[str]:
    """
    Filter features to exclude Max_ACF_Lag and spectral density metrics.
    
    Per T037b: Explicitly exclude features that could introduce
    multicollinearity or violate the analysis assumptions.
    
    Args:
        feature_list: List of feature names to filter
        
    Returns:
        List of filtered feature names
    """
    filtered = [f for f in feature_list if f not in EXCLUDED_FEATURES]
    
    excluded_count = len(feature_list) - len(filtered)
    if excluded_count > 0:
        log_info(f"Filtered out {excluded_count} features: {EXCLUDED_FEATURES}")
    
    return filtered

def write_filtered_features(output_path: str, features: List[str]) -> None:
    """
    Write filtered feature list to JSON file.
    
    Args:
        output_path: Path to output JSON file
        features: List of feature names to write
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        'filtered_features': features,
        'excluded_features': EXCLUDED_FEATURES,
        'total_features_before': len(features) + len(EXCLUDED_FEATURES),
        'total_features_after': len(features),
        'timestamp': pd.Timestamp.now().isoformat()
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    log_info(f"Written filtered features to {output_path}")

def main() -> int:
    """
    Main entry point for feature filtering and regression analysis.
    
    This function:
    1. Filters features to exclude Max_ACF_Lag and spectral metrics
    2. Writes filtered_features.json
    3. Runs regression analysis if inputs are available
    4. Writes regression_model.json
    
    Returns:
        0 on success, 1 on failure
    """
    try:
        # Initialize logging
        log_info("Starting regression analysis (T037b)")
        
        # Define paths
        project_root = get_path('root')
        features_output = project_root / 'data' / 'results' / 'filtered_features.json'
        regression_output = project_root / 'data' / 'results' / 'regression_model.json'
        error_rates_path = project_root / 'data' / 'results' / 'error_rates.csv'
        
        # Step 1: Filter features
        # Start with a comprehensive list of potential features
        all_features = [
            'hurst',
            'length',
            'acf_mean',
            'acf_max',
            'Max_ACF_Lag',  # Will be excluded
            'spectral_density_peak_ratio',  # Will be excluded
            'spectral_peak_ratio',  # Will be excluded
            'variance',
            'skewness',
            'kurtosis'
        ]
        
        filtered_features = filter_features(all_features)
        
        # Write filtered features
        write_filtered_features(str(features_output), filtered_features)
        
        # Step 2: Check if we can run regression
        if error_rates_path.exists():
            log_info("Error rates file found, running regression analysis")
            
            # Verify inputs
            verification = verify_regression_inputs(str(error_rates_path), str(features_output))
            
            # Load error rates
            error_rates_df = pd.read_csv(error_rates_path)
            
            # Check stability
            stability = check_regression_stability(error_rates_df)
            
            # Run univariate regression
            hurst_vals = error_rates_df['hurst'].values
            error_vals = error_rates_df['error_rate'].values
            
            regression_results = run_univariate_regression(hurst_vals, error_vals)
            
            # Add metadata
            regression_results['verification'] = verification
            regression_results['stability'] = stability
            regression_results['filtered_features'] = filtered_features
            regression_results['excluded_features'] = EXCLUDED_FEATURES
            regression_results['timestamp'] = pd.Timestamp.now().isoformat()
            
            # Write regression results
            regression_output.parent.mkdir(parents=True, exist_ok=True)
            with open(regression_output, 'w') as f:
                json.dump(regression_results, f, indent=2)
            
            log_info(f"Written regression results to {regression_output}")
            log_info(f"Slope per 0.1 H: {regression_results['slope_per_01_unit']:.6f}")
        else:
            log_warning("Error rates file not found, skipping regression analysis")
            log_info("Only filtered_features.json will be written")
        
        log_info("Regression analysis completed successfully")
        return 0
        
    except Exception as e:
        log_critical(f"Regression analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
