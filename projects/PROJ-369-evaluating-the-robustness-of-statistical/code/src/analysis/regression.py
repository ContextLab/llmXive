"""
Regression analysis module for evaluating the robustness of statistical methods.
Implements linear regression of error rate vs. Hurst exponent with stability checks.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

from src.utils.logging import log_info, log_warning, log_error, log_critical
from src.utils.config import get_path

class RegressionError(Exception):
    """Custom exception for regression-related errors."""
    pass

def verify_regression_inputs(error_rates_path: Path, filtered_features_path: Path) -> bool:
    """
    Verify that input files exist, are non-empty, and contain valid data.
    
    Args:
        error_rates_path: Path to error_rates.csv
        filtered_features_path: Path to filtered_features.json
        
    Returns:
        True if inputs are valid, False otherwise.
    """
    log_info("Verifying regression inputs...")
    
    # Check file existence
    if not error_rates_path.exists():
        log_critical(f"Error rates file not found: {error_rates_path}")
        return False
        
    if not filtered_features_path.exists():
        log_critical(f"Filtered features file not found: {filtered_features_path}")
        return False
        
    # Load and validate error rates
    try:
        error_rates_df = pd.read_csv(error_rates_path)
        if error_rates_df.empty:
            log_critical("Error rates file is empty")
            return False
            
        required_cols = ['hurst', 'error_rate']
        if not all(col in error_rates_df.columns for col in required_cols):
            log_critical(f"Error rates file missing required columns: {required_cols}")
            return False
            
        # Check for NaN/Inf
        if error_rates_df['hurst'].isna().any() or np.isinf(error_rates_df['hurst']).any():
            log_critical("Error rates file contains NaN or Inf in hurst column")
            return False
            
        if error_rates_df['error_rate'].isna().any() or np.isinf(error_rates_df['error_rate']).any():
            log_critical("Error rates file contains NaN or Inf in error_rate column")
            return False
            
        log_info(f"Error rates loaded: {len(error_rates_df)} records")
        
    except Exception as e:
        log_critical(f"Failed to load error rates: {e}")
        return False
        
    # Load and validate filtered features
    try:
        with open(filtered_features_path, 'r') as f:
            filtered_features = json.load(f)
            
        if not filtered_features or 'features' not in filtered_features:
            log_critical("Filtered features file invalid or missing 'features' key")
            return False
            
        log_info(f"Filtered features loaded: {len(filtered_features['features'])} features")
        
    except Exception as e:
        log_critical(f"Failed to load filtered features: {e}")
        return False
        
    return True

def check_regression_stability(X: np.ndarray, y: np.ndarray) -> Tuple[bool, Dict[str, Any]]:
    """
    Check for multicollinearity and singular matrices before running OLS regression.
    
    This implements the stability check required by T065.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        
    Returns:
        Tuple of (is_stable, stability_info) where:
        - is_stable: True if regression can proceed safely
        - stability_info: Dictionary with VIF values, condition number, and recommendations
    """
    log_info("Checking regression stability...")
    
    stability_info = {
        'is_singular': False,
        'condition_number': None,
        'vif_values': {},
        'max_vif': None,
        'recommendation': 'proceed',
        'warnings': []
    }
    
    n_samples, n_features = X.shape
    
    # Check for singular matrix (rank deficiency)
    try:
        # Add constant for intercept
        X_with_const = sm.add_constant(X)
        XtX = X_with_const.T @ X_with_const
        
        # Calculate condition number
        eigenvalues = np.linalg.eigvalsh(XtX)
        if np.any(eigenvalues <= 0):
            stability_info['is_singular'] = True
            stability_info['warnings'].append("Matrix is singular or near-singular (non-positive eigenvalues)")
        else:
            stability_info['condition_number'] = np.sqrt(eigenvalues.max() / eigenvalues.min())
            
            # Flag if condition number is very high (> 30 is often problematic)
            if stability_info['condition_number'] > 30:
                stability_info['warnings'].append(f"High condition number detected: {stability_info['condition_number']:.2f}")
                
    except np.linalg.LinAlgError as e:
        stability_info['is_singular'] = True
        stability_info['warnings'].append(f"Matrix singularity detected: {e}")
        
    # Calculate VIF for each feature (excluding constant)
    if n_features > 0 and not stability_info['is_singular']:
        try:
            vif_values = []
            for i in range(n_features):
                vif = variance_inflation_factor(X_with_const, i + 1)  # +1 to skip constant
                feature_name = f"feature_{i}"
                stability_info['vif_values'][feature_name] = vif
                vif_values.append(vif)
                
            stability_info['max_vif'] = max(vif_values) if vif_values else None
            
            # Flag high VIF (> 10 is often considered problematic)
            if stability_info['max_vif'] and stability_info['max_vif'] > 10:
                stability_info['warnings'].append(f"High VIF detected: {stability_info['max_vif']:.2f}")
                
        except Exception as e:
            log_warning(f"Could not calculate VIF: {e}")
            stability_info['warnings'].append(f"VIF calculation failed: {e}")
    
    # Determine stability and recommendation
    is_stable = True
    if stability_info['is_singular']:
        is_stable = False
        stability_info['recommendation'] = 'skip'
        log_critical("Regression matrix is singular. Skipping regression for this configuration.")
    elif stability_info['max_vif'] and stability_info['max_vif'] > 10:
        is_stable = False
        stability_info['recommendation'] = 'fallback'
        log_warning(f"High multicollinearity detected (max VIF={stability_info['max_vif']:.2f}). "
                   "Falling back to univariate regression.")
    elif stability_info['condition_number'] and stability_info['condition_number'] > 100:
        stability_info['recommendation'] = 'warn'
        log_warning(f"Very high condition number ({stability_info['condition_number']:.2f}). "
                   "Proceed with caution.")
    else:
        log_info("Regression stability check passed.")
        
    stability_info['is_stable'] = is_stable
    return is_stable, stability_info

def run_regression(X: np.ndarray, y: np.ndarray, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run linear regression with stability checks.
    
    Implements the fallback logic for T065:
    - If matrix is singular, skip regression
    - If high multicollinearity, fall back to univariate regression
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        config: Configuration dictionary with regression parameters
        
    Returns:
        Dictionary with regression results
    """
    log_info(f"Running regression with {X.shape[0]} samples, {X.shape[1]} features")
    
    # Check stability first
    is_stable, stability_info = check_regression_stability(X, y)
    
    result = {
        'config': config,
        'stability_info': stability_info,
        'success': False,
        'model_type': None,
        'coefficients': None,
        'p_values': None,
        'r_squared': None,
        'slope': None,
        'intercept': None,
        'slope_per_01_unit': None,
        'vif': None,
        'n_eff': None,
        'error_message': None
    }
    
    if not is_stable:
        if stability_info['recommendation'] == 'skip':
            result['error_message'] = "Regression skipped due to singular matrix"
            log_critical(result['error_message'])
            return result
            
        elif stability_info['recommendation'] == 'fallback':
            log_info("Falling back to univariate regression due to multicollinearity")
            # Use only the first feature (Hurst exponent) for univariate regression
            X_uni = X[:, 0:1]
            y_uni = y
            return run_univariate_regression(X_uni, y_uni, config, stability_info)
    
    # Standard multivariate regression
    try:
        X_with_const = sm.add_constant(X)
        model = sm.OLS(y, X_with_const).fit()
        
        result['model_type'] = 'multivariate_ols'
        result['success'] = True
        result['coefficients'] = model.params.tolist()
        result['p_values'] = model.pvalues.tolist()
        result['r_squared'] = float(model.rsquared)
        result['intercept'] = float(model.params[0])
        result['slope'] = float(model.params[1]) if len(model.params) > 1 else None
        
        # Calculate slope per 0.1 unit increase in Hurst
        if result['slope'] is not None:
            result['slope_per_01_unit'] = result['slope'] * 0.1
            
        # Calculate VIF for the model
        if X.shape[1] > 0:
            vif_values = []
            for i in range(X.shape[1]):
                vif = variance_inflation_factor(X_with_const, i + 1)
                vif_values.append(vif)
            result['vif'] = max(vif_values) if vif_values else None
            
        # Calculate effective sample size
        n_eff = calculate_n_eff(len(y), result.get('r_squared', 0), X.shape[1])
        result['n_eff'] = n_eff
        
        log_info(f"Regression completed: R²={result['r_squared']:.4f}, "
                f"slope={result['slope']:.4f}, slope_per_0.1={result['slope_per_01_unit']:.4f}")
                
    except Exception as e:
        result['error_message'] = str(e)
        log_error(f"Regression failed: {e}")
        
    return result

def run_univariate_regression(X: np.ndarray, y: np.ndarray, config: Dict[str, Any], 
                             stability_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run univariate regression as fallback for high multicollinearity.
    
    Args:
        X: Feature matrix (n_samples, 1) - should contain only Hurst exponent
        y: Target vector (n_samples,)
        config: Configuration dictionary
        stability_info: Stability information from check_regression_stability
        
    Returns:
        Dictionary with univariate regression results
    """
    log_info("Running univariate regression fallback")
    
    result = {
        'config': config,
        'stability_info': stability_info,
        'success': False,
        'model_type': 'univariate_ols',
        'coefficients': None,
        'p_values': None,
        'r_squared': None,
        'slope': None,
        'intercept': None,
        'slope_per_01_unit': None,
        'vif': None,
        'n_eff': None,
        'error_message': None,
        'fallback_reason': 'high_multicollinearity'
    }
    
    try:
        X_with_const = sm.add_constant(X)
        model = sm.OLS(y, X_with_const).fit()
        
        result['success'] = True
        result['coefficients'] = model.params.tolist()
        result['p_values'] = model.pvalues.tolist()
        result['r_squared'] = float(model.rsquared)
        result['intercept'] = float(model.params[0])
        result['slope'] = float(model.params[1]) if len(model.params) > 1 else None
        
        if result['slope'] is not None:
            result['slope_per_01_unit'] = result['slope'] * 0.1
            
        # VIF for univariate is typically 1.0 (no multicollinearity)
        result['vif'] = 1.0
        
        n_eff = calculate_n_eff(len(y), result.get('r_squared', 0), 1)
        result['n_eff'] = n_eff
        
        log_info(f"Univariate regression completed: R²={result['r_squared']:.4f}, "
                f"slope={result['slope']:.4f}")
                
    except Exception as e:
        result['error_message'] = str(e)
        log_error(f"Univariate regression failed: {e}")
        
    return result

def calculate_n_eff(n: int, r_squared: float, n_features: int) -> float:
    """
    Calculate effective sample size based on autocorrelation and model complexity.
    
    Args:
        n: Original sample size
        r_squared: R-squared value from regression
        n_features: Number of features in the model
        
    Returns:
        Effective sample size
    """
    # Simplified approximation: n_eff = n * (1 - r_squared) / (1 + r_squared)
    # This accounts for the reduction in independent information due to dependence
    if r_squared >= 1.0:
        return n / (n_features + 1)
        
    n_eff = n * (1 - r_squared) / (1 + r_squared)
    return max(n_eff, 1.0)  # Ensure at least 1

def main():
    """Main entry point for regression analysis."""
    log_info("Starting regression analysis...")
    
    try:
        # Get paths
        project_root = get_path()
        error_rates_path = project_root / "data" / "results" / "error_rates.csv"
        filtered_features_path = project_root / "data" / "results" / "filtered_features.json"
        output_path = project_root / "data" / "results" / "regression_model.json"
        
        # Verify inputs
        if not verify_regression_inputs(error_rates_path, filtered_features_path):
            log_critical("Input verification failed. Exiting.")
            sys.exit(1)
            
        # Load data
        error_rates_df = pd.read_csv(error_rates_path)
        
        with open(filtered_features_path, 'r') as f:
            filtered_features = json.load(f)
            
        # Prepare features and target
        X = error_rates_df['hurst'].values.reshape(-1, 1)
        y = error_rates_df['error_rate'].values
        
        # Configuration
        config = {
            'model_type': 'linear_regression',
            'features': filtered_features['features'],
            'alpha': 0.05,
            'seed': 42
        }
        
        # Run regression
        result = run_regression(X, y, config)
        
        # Save results
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2, default=str)
            
        log_info(f"Regression results saved to {output_path}")
        
        if result['success']:
            log_info(f"Final slope: {result['slope']:.4f}")
            log_info(f"Slope per 0.1 unit Hurst: {result['slope_per_01_unit']:.4f}")
            log_info(f"R-squared: {result['r_squared']:.4f}")
        else:
            log_warning(f"Regression did not complete successfully: {result.get('error_message')}")
            
    except Exception as e:
        log_critical(f"Regression analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
