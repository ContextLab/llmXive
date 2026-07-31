import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np

from config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_scaling_fits(input_path: str) -> List[Dict[str, Any]]:
    """
    Load scaling fits from JSON.
    
    The input file MUST be a list of objects containing:
    - disorder_width (float)
    - xi (float)
    - uncertainty (float)
    - p_value (float)
    
    If the file is a dict (legacy format) or missing keys, raise an error.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Scaling fits file not found: {input_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Validate format: must be a list
    if not isinstance(data, list):
        raise ValueError(
            f"Schema violation: {input_path} must be a JSON list of objects. "
            f"Found: {type(data).__name__}. "
            "Ensure T013a/T013b produced the correct list format."
        )
    
    if len(data) == 0:
        raise ValueError(f"Schema violation: {input_path} is an empty list.")
    
    # Validate keys in each object
    required_keys = {'disorder_width', 'xi', 'uncertainty', 'p_value'}
    valid_data = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"Item {i} in {input_path} is not a dict.")
        
        missing = required_keys - set(item.keys())
        if missing:
            raise ValueError(
                f"Item {i} in {input_path} is missing required keys: {missing}. "
                f"Found keys: {list(item.keys())}"
            )
        
        # Ensure numeric types
        try:
            item['disorder_width'] = float(item['disorder_width'])
            item['xi'] = float(item['xi'])
            item['uncertainty'] = float(item['uncertainty'])
            item['p_value'] = float(item['p_value'])
        except (TypeError, ValueError) as e:
            raise ValueError(f"Item {i} in {input_path} contains non-numeric values: {e}")
        
        valid_data.append(item)
    
    logger.info(f"Loaded {len(valid_data)} valid scaling fit records from {input_path}")
    return valid_data

def apply_bonferroni_correction(
    results: List[Dict[str, Any]],
    alpha: float = 0.05
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Apply Bonferroni correction to control Family-Wise Error Rate (FWER).
    
    Correction Factor = alpha / len(results)
    
    Returns:
      - corrected_results: List of dicts with 'adjusted_p_value' and 'significant'
      - summary: Dict with correction details
    """
    n_tests = len(results)
    if n_tests == 0:
        raise ValueError("Cannot apply Bonferroni correction to an empty list of results.")
    
    corrected_alpha = alpha / n_tests
    logger.info(f"Applying Bonferroni correction: alpha={alpha}, n_tests={n_tests}, "
                f"corrected_alpha={corrected_alpha:.6f}")
    
    corrected_results = []
    significant_count = 0
    
    for item in results:
        original_p = item['p_value']
        adjusted_p = min(original_p * n_tests, 1.0)
        is_significant = adjusted_p < corrected_alpha
        
        if is_significant:
            significant_count += 1
        
        corrected_item = item.copy()
        corrected_item['adjusted_p_value'] = adjusted_p
        corrected_item['significant'] = is_significant
        corrected_item['bonferroni_threshold'] = corrected_alpha
        corrected_results.append(corrected_item)
    
    summary = {
        'alpha': alpha,
        'n_tests': n_tests,
        'corrected_alpha': corrected_alpha,
        'significant_count': significant_count,
        'correction_method': 'Bonferroni',
        'decision_record': 'SC-005 (FWER across full family of widths)'
    }
    
    logger.info(f"Bonferroni correction complete. Significant results: {significant_count}/{n_tests}")
    return corrected_results, summary

def analyze_scaling_slopes(
    results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Analyze the scaling of localization length with disorder width.
    
    Expects results to contain 'disorder_width' and 'xi'.
    Performs a linear regression on log(xi) vs log(W) to check the slope.
    """
    if not results:
        return {'error': 'No data to analyze'}
    
    widths = np.array([r['disorder_width'] for r in results])
    xis = np.array([r['xi'] for r in results])
    
    # Filter out zero or negative values for log
    mask = (widths > 0) & (xis > 0)
    if np.sum(mask) < 2:
        return {'error': 'Insufficient valid data points for regression'}
    
    log_w = np.log(widths[mask])
    log_xi = np.log(xis[mask])
    
    # Simple linear regression
    slope, intercept = np.polyfit(log_w, log_xi, 1)
    
    # Calculate R-squared
    y_pred = slope * log_w + intercept
    ss_res = np.sum((log_xi - y_pred) ** 2)
    ss_tot = np.sum((log_xi - np.mean(log_xi)) ** 2)
    r_squared = 1 - (ss_res / ss_tot)
    
    return {
        'slope': slope,
        'intercept': intercept,
        'r_squared': r_squared,
        'n_points': int(np.sum(mask)),
        'expected_slope': -2.0,
        'deviation_from_theory': abs(slope - (-2.0))
    }

def main():
    config = get_config()
    input_path = str(config.DATA_PROCESSED_DIR / 'scaling_fits.json')
    output_path = str(config.DATA_PROCESSED_DIR / 'bonferroni_results.json')
    
    logger.info(f"Starting Bonferroni correction task (T015)")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    
    try:
        # 1. Load and validate data
        results = load_scaling_fits(input_path)
        
        # 2. Apply correction
        corrected_results, summary = apply_bonferroni_correction(results)
        
        # 3. Analyze slopes
        slope_analysis = analyze_scaling_slopes(corrected_results)
        
        # 4. Assemble final output
        output_data = {
            'summary': summary,
            'slope_analysis': slope_analysis,
            'results': corrected_results
        }
        
        # 5. Write output
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Successfully wrote results to {output_path}")
        print(f"Bonferroni correction complete. Output: {output_path}")
        print(f"Significant findings: {summary['significant_count']} / {summary['n_tests']}")
        
    except FileNotFoundError as e:
        logger.error(f"Input file missing: {e}")
        raise
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during Bonferroni correction: {e}")
        raise

if __name__ == '__main__':
    main()
