"""
Regression analysis module for User Story 4.

Implements linear regression to relate deviation magnitude to driving frequency
and material roughness, and tests the significance of coefficients.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

from config import get_material_properties, get_roughness_proxy, load_config
from stats import StatsError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RegressionError(Exception):
    """Custom exception for regression-related errors."""
    pass

def load_statistical_results_for_regression(input_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load statistical results from JSON and convert to a DataFrame suitable for regression.
    
    Args:
        input_path: Path to the statistical_results.json file. If None, uses default path.
        
    Returns:
        DataFrame with columns: frequency, roughness_proxy, deviation_magnitude, bin_id
        
    Raises:
        RegressionError: If the file cannot be loaded or parsed correctly.
    """
    if input_path is None:
        input_path = "artifacts/statistical_results.json"
    
    path = Path(input_path)
    if not path.exists():
        raise RegressionError(f"Statistical results file not found: {input_path}")
    
    try:
        with open(path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise RegressionError(f"Failed to parse JSON: {e}")
    
    # Expected structure: {'bins': [{'bin_id': ..., 'frequency': ..., 'ks_test': {...}, ...}, ...]}
    if 'bins' not in data:
        raise RegressionError("Invalid JSON structure: missing 'bins' key")
    
    records = []
    for bin_data in data['bins']:
        bin_id = bin_data.get('bin_id')
        frequency = bin_data.get('frequency')
        
        # Extract deviation magnitude from KS test results
        # The deviation magnitude is typically 1 - p-value or the KS statistic itself
        # Using KS statistic as the deviation magnitude (larger = more deviation from MB)
        ks_result = bin_data.get('ks_test', {})
        ks_statistic = ks_result.get('statistic')
        ks_pvalue = ks_result.get('pvalue')
        
        # Define deviation magnitude as the KS statistic (distance from MB distribution)
        deviation_magnitude = ks_statistic if ks_statistic is not None else 0.0
        
        # Get material type and map to roughness proxy
        material_type = bin_data.get('material_type', 'unknown')
        roughness_proxy = get_roughness_proxy(material_type)
        
        records.append({
            'bin_id': bin_id,
            'frequency': frequency,
            'roughness_proxy': roughness_proxy,
            'deviation_magnitude': deviation_magnitude,
            'ks_pvalue': ks_pvalue,
            'material_type': material_type
        })
    
    df = pd.DataFrame(records)
    
    if df.empty:
        raise RegressionError("No valid data extracted from statistical results")
    
    logger.info(f"Loaded {len(df)} bins for regression analysis")
    return df

def prepare_regression_data(
    df: pd.DataFrame, 
    config_path: Optional[str] = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, List[str]]:
    """
    Prepare predictors and target for linear regression.
    
    Maps material types to roughness proxies and prepares the design matrix.
    
    Args:
        df: DataFrame with frequency, material_type, and deviation_magnitude.
        config_path: Optional path to config.yaml. If None, uses default.
        
    Returns:
        Tuple of (X, y, frequencies, feature_names) where:
        - X: 2D numpy array of predictors [frequency, roughness_proxy]
        - y: 1D numpy array of target (deviation_magnitude)
        - frequencies: 1D array of frequency values
        - feature_names: List of feature names ['frequency', 'roughness_proxy']
        
    Raises:
        RegressionError: If data preparation fails.
    """
    if config_path is None:
        config_path = "data/config.yaml"
    
    # Validate required columns
    required_cols = ['frequency', 'deviation_magnitude', 'material_type']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise RegressionError(f"Missing required columns: {missing}")
    
    # Filter out rows with missing data
    valid_df = df.dropna(subset=required_cols + ['roughness_proxy'] if 'roughness_proxy' in df.columns else required_cols)
    
    if valid_df.empty:
        raise RegressionError("No valid data after filtering missing values")
    
    # Map material types to roughness proxies if not already present
    if 'roughness_proxy' not in valid_df.columns:
        roughness_list = []
        for mat in valid_df['material_type']:
            roughness_list.append(get_roughness_proxy(mat))
        valid_df['roughness_proxy'] = roughness_list
    
    # Prepare predictors: frequency and roughness proxy
    X_freq = valid_df['frequency'].values.reshape(-1, 1)
    X_roughness = valid_df['roughness_proxy'].values.reshape(-1, 1)
    
    # Combine into design matrix
    X = np.hstack([X_freq, X_roughness])
    y = valid_df['deviation_magnitude'].values
    frequencies = valid_df['frequency'].values
    
    feature_names = ['frequency', 'roughness_proxy']
    
    logger.info(f"Prepared regression data: {X.shape[0]} samples, {X.shape[1]} features")
    return X, y, frequencies, feature_names

def fit_linear_regression(X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """
    Fit a linear regression model and calculate statistics.
    
    Args:
        X: 2D numpy array of predictors.
        y: 1D numpy array of target.
        
    Returns:
        Dictionary containing:
        - coefficients: array of [intercept, slope_freq, slope_roughness]
        - r_squared: R^2 value
        - residuals: array of residuals
        - predictions: array of predicted values
        
    Raises:
        RegressionError: If regression fails.
    """
    try:
        # Add intercept term
        X_with_intercept = np.hstack([np.ones((X.shape[0], 1)), X])
        
        # Fit using least squares
        # beta = (X'X)^-1 X'y
        XtX = X_with_intercept.T @ X_with_intercept
        if np.linalg.cond(XtX) > 1e10:
            logger.warning("Design matrix is ill-conditioned. Results may be unreliable.")
        
        beta = np.linalg.solve(XtX, X_with_intercept.T @ y)
        
        # Calculate predictions
        y_pred = X_with_intercept @ beta
        
        # Calculate residuals
        residuals = y - y_pred
        
        # Calculate R^2
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y - np.mean(y))**2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        return {
            'coefficients': beta.tolist(),
            'r_squared': float(r_squared),
            'residuals': residuals.tolist(),
            'predictions': y_pred.tolist()
        }
        
    except np.linalg.LinAlgError as e:
        raise RegressionError(f"Linear algebra error during regression: {e}")
    except Exception as e:
        raise RegressionError(f"Regression fitting failed: {e}")

def test_coefficient_significance(
    X: np.ndarray, 
    y: np.ndarray, 
    model_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Perform t-tests on regression coefficients to assess significance.
    
    Args:
        X: 2D numpy array of predictors (without intercept).
        y: 1D numpy array of target.
        model_results: Dictionary from fit_linear_regression.
        
    Returns:
        Dictionary containing:
        - p_values: list of p-values for [intercept, freq, roughness]
        - t_statistics: list of t-statistics
        - standard_errors: list of standard errors
        - significant: dict mapping feature name to boolean
        
    Raises:
        RegressionError: If significance testing fails.
    """
    try:
        # Add intercept term
        n = len(y)
        p = X.shape[1] + 1  # +1 for intercept
        
        X_with_intercept = np.hstack([np.ones((n, 1)), X])
        
        # Residuals
        y_pred = np.array(model_results['predictions'])
        residuals = y - y_pred
        
        # Mean squared error
        mse = np.sum(residuals**2) / (n - p)
        
        # Covariance matrix of coefficients: sigma^2 * (X'X)^-1
        XtX = X_with_intercept.T @ X_with_intercept
        try:
            XtX_inv = np.linalg.inv(XtX)
        except np.linalg.LinAlgError:
            raise RegressionError("Cannot invert X'X matrix. Features may be collinear.")
        
        cov_beta = mse * XtX_inv
        se_beta = np.sqrt(np.diag(cov_beta))
        
        # t-statistics: beta / SE(beta)
        beta = np.array(model_results['coefficients'])
        t_stats = beta / se_beta
        
        # p-values (two-tailed)
        df = n - p
        p_values = 2 * (1 - scipy_stats.t.cdf(np.abs(t_stats), df))
        
        # Significance at alpha=0.05
        significant = {
            'intercept': p_values[0] < 0.05,
            'frequency': p_values[1] < 0.05,
            'roughness_proxy': p_values[2] < 0.05
        }
        
        return {
            'p_values': p_values.tolist(),
            't_statistics': t_stats.tolist(),
            'standard_errors': se_beta.tolist(),
            'significant': significant,
            'degrees_of_freedom': int(df)
        }
        
    except Exception as e:
        raise RegressionError(f"Significance testing failed: {e}")

def run_regression_analysis(
    input_json_path: str = "artifacts/statistical_results.json",
    config_path: str = "data/config.yaml",
    output_path: str = "artifacts/regression_results.json"
) -> Dict[str, Any]:
    """
    Main function to run the full regression analysis pipeline.
    
    1. Load statistical results
    2. Prepare predictors (frequency, roughness) and target (deviation)
    3. Fit linear regression
    4. Test coefficient significance
    5. Save results to JSON
    
    Args:
        input_json_path: Path to statistical_results.json
        config_path: Path to config.yaml
        output_path: Path for output regression_results.json
        
    Returns:
        Dictionary with all regression results.
        
    Raises:
        RegressionError: If any step fails.
    """
    logger.info("Starting regression analysis...")
    
    # Step 1: Load data
    df = load_statistical_results_for_regression(input_json_path)
    
    # Step 2: Prepare data
    X, y, frequencies, feature_names = prepare_regression_data(df, config_path)
    
    # Step 3: Fit model
    model_results = fit_linear_regression(X, y)
    
    # Step 4: Test significance
    significance_results = test_coefficient_significance(X, y, model_results)
    
    # Compile full results
    results = {
        'metadata': {
            'n_samples': int(len(y)),
            'n_features': int(X.shape[1]),
            'feature_names': feature_names,
            'input_file': input_json_path
        },
        'model': {
            'coefficients': model_results['coefficients'],
            'coefficient_names': ['intercept', 'frequency', 'roughness_proxy'],
            'r_squared': model_results['r_squared']
        },
        'significance': significance_results,
        'validation': {
            'frequency_significant': significance_results['significant']['frequency'],
            'frequency_p_value': significance_results['p_values'][1],
            'meets_success_criterion_sc005': significance_results['significant']['frequency']
        }
    }
    
    # Save to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Regression results saved to {output_path}")
    logger.info(f"R^2 = {model_results['r_squared']:.4f}")
    logger.info(f"Frequency p-value = {significance_results['p_values'][1]:.4f}")
    
    return results

def main():
    """CLI entry point for regression analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run regression analysis on statistical results")
    parser.add_argument(
        '--input', 
        type=str, 
        default="artifacts/statistical_results.json",
        help="Path to statistical_results.json"
    )
    parser.add_argument(
        '--config', 
        type=str, 
        default="data/config.yaml",
        help="Path to config.yaml"
    )
    parser.add_argument(
        '--output', 
        type=str, 
        default="artifacts/regression_results.json",
        help="Path for output regression_results.json"
    )
    
    args = parser.parse_args()
    
    try:
        results = run_regression_analysis(
            input_json_path=args.input,
            config_path=args.config,
            output_path=args.output
        )
        print(f"Analysis complete. Results saved to {args.output}")
        sys.exit(0)
    except RegressionError as e:
        logger.error(f"Regression analysis failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
