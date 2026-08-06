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

def run_regression_analysis(config: Dict[str, Any], alpha: float = 0.05):
    """Run full regression analysis."""
    results = load_statistical_results_for_regression()
    freq, rough, dev = prepare_regression_data(results, config)
    
    # Fit against frequency
    model = fit_linear_regression(freq, dev)
    sig = test_coefficient_significance(model, alpha)
    
    return {
        'model_parameters': model,
        'significance_test': sig,
        'n_samples': len(freq)
    }

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
    logger.info(f"Regression results written to {output_path}")
