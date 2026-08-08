"""
Regression analysis module.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy import stats as scipy_stats
from config import load_config, get_roughness_proxy

logger = logging.getLogger(__name__)

class RegressionError(Exception):
    """Custom exception for regression errors."""
    pass

def load_statistical_results_for_regression() -> List[Dict[str, Any]]:
    """Load statistical results for regression analysis."""
    path = 'artifacts/statistical_results.json'
    if not Path(path).exists():
        raise RegressionError(f"Statistical results file {path} not found.")
    with open(path, 'r') as f:
        return json.load(f)

def prepare_regression_data(results: List[Dict], config: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Prepare predictors and target for regression."""
    frequencies = []
    roughness = []
    deviations = []
    
    for r in results:
        # Extract frequency if available
        if 'group' in r and isinstance(r['group'], str) and ',' in r['group']:
          try:
              freq_str, mat_str = r['group'].split(',')
              freq = float(freq_str.strip())
              frequencies.append(freq)
              roughness.append(get_roughness_proxy(config, mat_str.strip()))
          except ValueError:
              continue
        elif 'frequency' in r:
            frequencies.append(r['frequency'])
            roughness.append(get_roughness_proxy(config, r.get('material', 'unknown')))
        else:
            continue
        
        # Deviation magnitude: 1 - p_value (simplified)
        # Or use KS statistic directly
        dev = r.get('ks_statistic', 0.0)
        deviations.append(dev)
    
    if not frequencies:
        raise RegressionError("No valid data points for regression.")
        
    return np.array(frequencies), np.array(roughness), np.array(deviations)

def fit_linear_regression(X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
    """Fit linear model y = mx + c."""
    slope, intercept, r_value, p_value, std_err = scipy_stats.linregress(X, y)
    return {
        'slope': slope,
        'intercept': intercept,
        'r_squared': r_value**2,
        'p_value_slope': p_value,
        'std_err': std_err
    }

def test_coefficient_significance(model_params: Dict[str, float], alpha: float = 0.05) -> Dict[str, Any]:
    """Test significance of coefficients."""
    return {
        'slope_significant': model_params['p_value_slope'] < alpha,
        'p_value_slope': model_params['p_value_slope']
    }

def check_multicollinearity(X: np.ndarray, feature_names: List[str], threshold: float = 5.0) -> Dict[str, Any]:
    """
    Calculate Variance Inflation Factor (VIF) for predictors.
    
    Args:
        X: Predictor matrix (n_samples, n_features)
        feature_names: List of feature names corresponding to columns in X
        threshold: VIF threshold above which a warning is issued (default 5.0)
        
    Returns:
        Dictionary containing VIF values, max VIF, and stability flag.
    """
    if X.shape[1] < 2:
        logger.warning("Multicollinearity check requires at least 2 predictors.")
        return {
            'vif_values': {},
            'max_vif': 0.0,
            'is_stable': True,
            'warning': "Insufficient predictors for VIF calculation."
        }

    # Add intercept column for VIF calculation (though VIF is usually for predictors)
    # VIF_i = 1 / (1 - R_i^2) where R_i^2 is R-squared of regressing X_i on all other X_j
    
    vif_values = {}
    
    for i, name in enumerate(feature_names):
        # Regress feature i against all other features
        y_i = X[:, i]
        X_others = np.delete(X, i, axis=1)
        
        # Fit linear regression
        try:
            # Add intercept to X_others for regression
            X_others_with_intercept = np.column_stack([np.ones(X_others.shape[0]), X_others])
            coeffs, _, _, _ = scipy_stats.linregress(X_others_with_intercept[:, 1:].flatten(), y_i.flatten()) if X_others.shape[1] == 1 else np.linalg.lstsq(X_others_with_intercept, y_i, rcond=None)[0], None, None, None
            
            # Calculate R-squared
            y_pred = X_others_with_intercept @ coeffs
            ss_res = np.sum((y_i - y_pred) ** 2)
            ss_tot = np.sum((y_i - np.mean(y_i)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            # Calculate VIF
            vif = 1 / (1 - r_squared) if r_squared < 1 else float('inf')
            vif_values[name] = vif
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {name}: {e}")
            vif_values[name] = float('inf')
    
    max_vif = max(vif_values.values()) if vif_values else 0.0
    is_stable = max_vif <= threshold
    
    result = {
        'vif_values': vif_values,
        'max_vif': float(max_vif),
        'is_stable': is_stable,
        'threshold': threshold
    }
    
    if not is_stable:
        logger.warning(f"Multicollinearity detected: max VIF ({max_vif:.2f}) exceeds threshold ({threshold}). Model fit may be unstable.")
        result['warning'] = f"Multicollinearity detected: max VIF ({max_vif:.2f}) exceeds threshold ({threshold})."
    
    return result

def run_regression_analysis(config: Dict[str, Any], alpha: float = 0.05):
    """Run full regression analysis."""
    results = load_statistical_results_for_regression()
    freq, rough, dev = prepare_regression_data(results, config)
    
    # Fit against frequency
    model = fit_linear_regression(freq, dev)
    sig = test_coefficient_significance(model, alpha)
    
    # Check multicollinearity
    # Stack predictors: frequency and roughness
    X = np.column_stack([freq, rough])
    feature_names = ['frequency', 'roughness']
    vif_result = check_multicollinearity(X, feature_names)
    
    analysis_result = {
        'model_parameters': model,
        'significance_test': sig,
        'n_samples': len(freq),
        'multicollinearity_check': vif_result
    }
    
    return analysis_result

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Regression Module')
    parser.add_argument('--config', type=str, default='data/config.yaml')
    args = parser.parse_args()
    
    config = load_config(args.config)
    report = run_regression_analysis(config)
    
    output_path = 'artifacts/regression_results.json'
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Also write diagnostics to regression_diagnostics.json as per task T066
    diag_output_path = 'artifacts/regression_diagnostics.json'
    with open(diag_output_path, 'w') as f:
        json.dump(report['multicollinearity_check'], f, indent=2)
    
    logger.info(f"Regression results written to {output_path}")
    logger.info(f"Regression diagnostics written to {diag_output_path}")

if __name__ == '__main__':
    main()
