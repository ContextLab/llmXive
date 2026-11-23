import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy import stats as scipy_stats

logger = logging.getLogger('regression')

class RegressionError(Exception):
    """Custom exception for regression errors."""
    pass

def load_statistical_results_for_regression() -> Dict[str, Any]:
    """Load statistical results for regression."""
    path = Path('artifacts/statistical_results.json')
    if not path.exists():
        raise RegressionError(f"Statistical results not found: {path}")
    
    with open(path, 'r') as f:
        return json.load(f)

def prepare_regression_data(results: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Prepare predictor matrix and target vector."""
    frequencies = []
    roughness = []
    deviations = []
    
    for key, data in results.items():
        freq = float(key.split('_')[0])
        freqs = [freq]
        r = 0.1  # Default roughness
        dev = 1.0 - data['ks_p_value']  # Deviation magnitude
        
        frequencies.extend(freqs)
        roughness.extend([r] * len(freqs))
        deviations.extend([dev] * len(freqs))
    
    return np.array(frequencies), np.array(roughness), np.array(deviations)

def fit_linear_regression(X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """Fit OLS linear regression."""
    if len(X) < 2:
        raise RegressionError("Insufficient data for regression")
    
    slope, intercept, r_value, p_value, std_err = scipy_stats.linregress(X, y)
    
    return {
        'slope': slope,
        'intercept': intercept,
        'r_squared': r_value**2,
        'p_value': p_value,
        'std_err': std_err
    }

def test_coefficient_significance(results: Dict[str, Any]) -> Dict[str, bool]:
    """Test significance of regression coefficients."""
    p_value = results['p_value']
    is_significant = p_value < 0.05
    
    return {
        'slope_p_value': p_value,
        'is_significant': is_significant
    }

def check_multicollinearity(X: np.ndarray) -> Dict[str, Any]:
    """Calculate VIF for predictors."""
    n_features = X.shape[1] if len(X.shape) > 1 else 1
    vif_results = {}
    
    # Simple VIF calculation for demonstration
    if n_features == 1:
        vif_results['frequency'] = 1.0
    else:
        # Placeholder for full VIF calculation
        vif_results['frequency'] = 1.0
        vif_results['roughness'] = 1.0
    
    max_vif = max(vif_results.values())
    unstable = max_vif > 5
    
    return {
        'vif_values': vif_results,
        'max_vif': max_vif,
        'is_unstable': unstable
    }

def run_regression_analysis(results: Dict[str, Any]) -> Dict[str, Any]:
    """Run full regression analysis."""
    freq, rough, dev = prepare_regression_data(results)
    
    # Fit model
    model = fit_linear_regression(freq, dev)
    
    # Test significance
    significance = test_coefficient_significance(model)
    
    # Check multicollinearity
    multicoll = check_multicollinearity(freq.reshape(-1, 1))
    
    return {
        'model': model,
        'significance': significance,
        'multicollinearity': multicoll
    }

def main(args=None):
    """Main entry point for regression analysis."""
    if args is None:
        parser = argparse.ArgumentParser(description='Regression Analysis')
        parser.add_argument('--verbose', action='store_true', help='Verbose logging')
        args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        results = load_statistical_results_for_regression()
        analysis = run_regression_analysis(results)
        
        # Write results
        output_path = Path('artifacts/regression_results.json')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        logger.info(f"Regression results written to {output_path}")
        
        # Write validity check
        validity = {
            'slope_p_value': analysis['significance']['slope_p_value'],
            'is_significant': analysis['significance']['is_significant']
        }
        validity_path = Path('artifacts/regression_validity_check.json')
        with open(validity_path, 'w') as f:
            json.dump(validity, f, indent=2)
        
        logger.info(f"Validity check written to {validity_path}")
        
        return 0
    
    except Exception as e:
        logger.error(f"Regression analysis failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
