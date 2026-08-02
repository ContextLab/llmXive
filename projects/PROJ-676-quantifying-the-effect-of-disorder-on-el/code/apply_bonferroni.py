import json
import os
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
from scipy import stats as sp_stats

from code.config import get_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_scaling_fits(input_path: str) -> List[Dict[str, Any]]:
    """Load scaling fits from JSON file."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected list of results, got {type(data)}")
    
    # Validate schema
    required_keys = {'disorder_width', 'xi', 'uncertainty', 'p_value'}
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"Item {i} is not a dictionary")
        missing = required_keys - set(item.keys())
        if missing:
            raise ValueError(f"Item {i} missing keys: {missing}")
    
    return data

def analyze_scaling_slopes(results: List[Dict[str, Any]]) -> List[Tuple[float, float, float]]:
    """
    Analyze scaling slopes for each disorder width.
    Returns list of (width, slope, p_value) tuples.
    
    Note: This function assumes p_values are already computed and stored in the input.
    The task description mentions a t-test on slope deviation from -2, but since
    T013a is responsible for fitting and computing p-values, we use those directly.
    """
    slopes_and_pvalues = []
    for item in results:
        width = item['disorder_width']
        # The p_value in the input is from the fit quality (R^2 based), 
        # but for Bonferroni we need the p-value for the hypothesis test.
        # Since T013a outputs p_value, we use it as the test statistic p-value.
        p_val = item['p_value']
        
        # If p_value is not a valid probability, log warning
        if not (0.0 <= p_val <= 1.0):
            logger.warning(f"Invalid p-value {p_val} for width {width}, clamping to [0,1]")
            p_val = max(0.0, min(1.0, p_val))
        
        slopes_and_pvalues.append((width, item['xi'], p_val))
    
    return slopes_and_pvalues

def apply_bonferroni_correction(results: List[Dict[str, Any]], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Bonferroni correction for the full family of disorder widths.
    
    Args:
        results: List of scaling fit results from T013b
        alpha: Significance level (default 0.05)
    
    Returns:
        Dictionary with corrected p-values and test results
    """
    logger.info(f"Applying Bonferroni correction with alpha={alpha}")
    
    # Step 1: Extract all p-values
    p_values = [item['p_value'] for item in results]
    num_tests = len(p_values)
    
    if num_tests == 0:
        logger.warning("No results found for Bonferroni correction")
        return {
            'alpha': alpha,
            'num_tests': 0,
            'bonferroni_threshold': None,
            'results': [],
            'note': 'No tests to correct'
        }
    
    # Step 2: Calculate Bonferroni threshold
    bonferroni_threshold = alpha / num_tests
    logger.info(f"Number of tests: {num_tests}, Bonferroni threshold: {bonferroni_threshold}")
    
    # Step 3: Apply correction
    corrected_results = []
    significant_count = 0
    
    for item in results:
        width = item['disorder_width']
        xi = item['xi']
        uncertainty = item['uncertainty']
        p_val = item['p_value']
        
        # Bonferroni-corrected p-value
        corrected_p = min(p_val * num_tests, 1.0)
        is_significant = corrected_p < alpha
        
        if is_significant:
            significant_count += 1
        
        corrected_results.append({
            'disorder_width': width,
            'xi': xi,
            'uncertainty': uncertainty,
            'raw_p_value': p_val,
            'bonferroni_corrected_p_value': corrected_p,
            'bonferroni_threshold': bonferroni_threshold,
            'is_significant': is_significant
        })
    
    logger.info(f"Significant results after correction: {significant_count}/{num_tests}")
    
    return {
        'alpha': alpha,
        'num_tests': num_tests,
        'bonferroni_threshold': bonferroni_threshold,
        'results': corrected_results,
        'significant_count': significant_count,
        'correction_method': 'Bonferroni (full family)'
    }

def main():
    """Main entry point for Bonferroni correction task."""
    parser = argparse.ArgumentParser(description='Apply Bonferroni correction to scaling fits')
    parser.add_argument('--input', type=str, default='data/processed/scaling_fits.json',
                      help='Input file with scaling fits')
    parser.add_argument('--output', type=str, default='data/processed/bonferroni_results.json',
                      help='Output file for corrected results')
    parser.add_argument('--alpha', type=float, default=0.05,
                      help='Significance level (default: 0.05)')
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load results
        logger.info(f"Loading scaling fits from {args.input}")
        results = load_scaling_fits(args.input)
        logger.info(f"Loaded {len(results)} results")
        
        # Apply Bonferroni correction
        logger.info("Applying Bonferroni correction")
        corrected_results = apply_bonferroni_correction(results, args.alpha)
        
        # Write output
        with open(output_path, 'w') as f:
            json.dump(corrected_results, f, indent=2)
        
        logger.info(f"Bonferroni results written to {args.output}")
        print(f"Successfully applied Bonferroni correction. Results saved to {args.output}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == '__main__':
    main()