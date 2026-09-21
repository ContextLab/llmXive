"""
US3: Correlation & Statistical Validation.
Computes Spearman correlation and applies Bonferroni correction.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
from scipy import stats

from .error_handler import safe_execute, ExecutionError, handle_pipeline_error
from .utils import setup_logging

logger = setup_logging(__name__)

def compute_spearman_correlation(x: List[float], y: List[float]) -> Dict[str, float]:
    """
    Compute Spearman rank correlation between two lists.
    """
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("Insufficient data for correlation")
    
    corr, p_value = stats.spearmanr(x, y)
    return {
        'correlation': corr,
        'p_value': p_value
    }

def apply_bonferroni_correction(p_value: float, n_tests: int) -> float:
    """
    Apply Bonferroni correction to a p-value.
    """
    corrected = p_value * n_tests
    return min(corrected, 1.0)

def run_sensitivity_analysis(correlations: List[float], p_values: List[float], alpha_range: List[float]) -> Dict[str, Any]:
    """
    Run sensitivity analysis across a range of alpha levels.
    """
    results = []
    for alpha in alpha_range:
        high_risk_count = sum(1 for p in p_values if p < alpha)
        results.append({
            'alpha': alpha,
            'high_risk_count': high_risk_count
        })
    return results

def flag_high_risk(p_value: float, threshold: float = 0.05) -> bool:
    """
    Flag if p-value is below threshold.
    """
    return p_value < threshold

@handle_pipeline_error(task_name="Correlation Analysis")
def run_correlation_analysis(
    textual_scores: List[float],
    fairness_slopes: List[float],
    output_path: Path
) -> Dict[str, Any]:
    """
    Main entry point for US3.
    """
    if len(textual_scores) != len(fairness_slopes):
        raise ValueError("Mismatched lengths for textual scores and fairness slopes")
    
    # Compute correlation
    result = compute_spearman_correlation(textual_scores, fairness_slopes)
    corr = result['correlation']
    p_raw = result['p_value']
    
    # Bonferroni correction (assuming 1 test for now, but generalized)
    n_tests = 1 # Could be number of metrics
    p_corrected = apply_bonferroni_correction(p_raw, n_tests)
    
    # Flag high risk
    is_high_risk = flag_high_risk(p_corrected)
    
    # Sensitivity analysis
    alpha_range = [0.01, 0.05, 0.10]
    sensitivity = run_sensitivity_analysis([corr], [p_corrected], alpha_range)
    
    final_report = {
        'correlation': corr,
        'p_value_raw': p_raw,
        'p_value_corrected': p_corrected,
        'is_high_risk': is_high_risk,
        'sensitivity_analysis': sensitivity
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(final_report, f, indent=2)
    
    logger.info(f"Analysis complete. Report saved to {output_path}")
    return final_report
