"""
Aggregate results from T014 for all disorder widths and apply Bonferroni correction
for Family-Wise Error Rate (FWER) across the full family of tests.

This implements FR-010 and SC-005. The correction scope is global to satisfy
the requirement for controlling FWER across all widths, not just pairwise.

Input: data/processed/localization_lengths.json (aggregated from T014)
Output: data/processed/bonferroni_corrected_results.json
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
from scipy import stats

# Import from existing modules
from config import get_config
from stats import perform_linear_regression, aggregate_localization_lengths

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_aggregated_results(input_path: str) -> Dict[str, Any]:
    """Load the aggregated localization lengths from T014 output."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    return data

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Bonferroni correction for FWER across the full family of tests.
    
    The Bonferroni correction divides the alpha level by the number of tests (m)
    to control the family-wise error rate.
    
    Args:
        p_values: List of p-values from individual tests
        alpha: Significance level (default 0.05)
    
    Returns:
        Dictionary with corrected results
    """
    m = len(p_values)
    if m == 0:
        return {
            'corrected_alpha': 1.0,
            'significant_results': [],
            'non_significant_results': [],
            'family_size': 0,
            'correction_method': 'bonferroni'
        }
    
    corrected_alpha = alpha / m
    
    significant_indices = []
    non_significant_indices = []
    
    for i, p_val in enumerate(p_values):
        if p_val < corrected_alpha:
            significant_indices.append(i)
        else:
            non_significant_indices.append(i)
    
    return {
        'corrected_alpha': corrected_alpha,
        'original_alpha': alpha,
        'family_size': m,
        'significant_indices': significant_indices,
        'non_significant_indices': non_significant_indices,
        'significant_results': [p_values[i] for i in significant_indices],
        'non_significant_results': [p_values[i] for i in non_significant_indices],
        'correction_method': 'bonferroni'
    }

def analyze_scaling_slopes(results: Dict[str, Any]) -> Tuple[List[float], List[float], List[str]]:
    """
    Extract p-values for slope deviation from -2 across all disorder widths.
    
    This performs a t-test for each width to determine if the slope significantly
    deviates from the theoretical value of -2.
    
    Args:
        results: Aggregated results from T014 containing scaling analysis for each width
    
    Returns:
        Tuple of (p_values, slopes, width_labels)
    """
    p_values = []
    slopes = []
    width_labels = []
    
    # Expected theoretical slope for 1D Anderson localization
    theoretical_slope = -2.0
    
    for width_key, width_data in results.items():
        if 'scaling_analysis' not in width_data:
            logger.warning(f"Skipping {width_key}: no scaling analysis found")
            continue
        
        scaling = width_data['scaling_analysis']
        
        # Extract slope and standard error
        slope = scaling.get('slope', None)
        slope_stderr = scaling.get('slope_stderr', None)
        
        if slope is None or slope_stderr is None or slope_stderr == 0:
            logger.warning(f"Skipping {width_key}: invalid slope statistics")
            continue
        
        # Calculate t-statistic for deviation from theoretical slope
        t_stat = (slope - theoretical_slope) / slope_stderr
        
        # Two-tailed p-value
        p_val = 2 * (1 - stats.t.cdf(abs(t_stat), df=scaling.get('degrees_of_freedom', 10)))
        
        p_values.append(p_val)
        slopes.append(slope)
        width_labels.append(width_key)
        
        logger.info(f"Width {width_key}: slope={slope:.4f} (SE={slope_stderr:.4f}), "
                   f"t={t_stat:.4f}, p={p_val:.6f}")
    
    return p_values, slopes, width_labels

def main():
    """Main entry point for Bonferroni correction analysis."""
    config = get_config()
    
    # Define paths
    input_path = config['paths']['processed'] / 'localization_lengths.json'
    output_path = config['paths']['processed'] / 'bonferroni_corrected_results.json'
    
    logger.info(f"Loading aggregated results from {input_path}")
    
    try:
        results = load_aggregated_results(str(input_path))
    except FileNotFoundError as e:
        logger.error(str(e))
        return 1
    
    # Extract p-values for slope deviation tests
    p_values, slopes, width_labels = analyze_scaling_slopes(results)
    
    if len(p_values) == 0:
        logger.error("No valid p-values found for correction")
        return 1
    
    logger.info(f"Found {len(p_values)} tests to correct")
    
    # Apply Bonferroni correction
    correction_result = apply_bonferroni_correction(p_values, alpha=0.05)
    
    # Prepare output
    output_data = {
        'analysis_metadata': {
            'method': 'Bonferroni correction for FWER',
            'reference': 'FR-010, SC-005',
            'theoretical_slope': -2.0,
            'original_alpha': 0.05,
            'timestamp': str(config.get('timestamp', 'N/A'))
        },
        'correction_results': correction_result,
        'individual_tests': []
    }
    
    # Add detailed results for each test
    for i, width_label in enumerate(width_labels):
        test_result = {
            'width': width_label,
            'slope': slopes[i],
            'p_value': p_values[i],
            'is_significant': i in correction_result['significant_indices'],
            'corrected_alpha': correction_result['corrected_alpha']
        }
        output_data['individual_tests'].append(test_result)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write results
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Bonferroni correction results written to {output_path}")
    logger.info(f"Family size: {correction_result['family_size']}")
    logger.info(f"Corrected alpha: {correction_result['corrected_alpha']:.6f}")
    logger.info(f"Significant results: {len(correction_result['significant_indices'])}")
    
    return 0

if __name__ == '__main__':
    exit(main())
