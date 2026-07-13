"""
Statistical analysis module for comparing human-written vs LLM-generated code metrics.
Implements Mann-Whitney U tests, Cliff's delta, and Benjamini-Hochberg correction.
"""
import os
import sys
import logging
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import pandas as pd
import numpy as np
from scipy.stats import mannwhitneyu, norm

# Import logging utilities
from logging_config import setup_logger, get_logger

@dataclass
class PowerAnalysisResult:
    """Result container for power analysis."""
    metric_name: str
    effect_size: float
    sample_size: int
    power: float
    alpha: float

def compute_effect_size_cohen_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """Compute Cohen's d effect size."""
    mean1, mean2 = np.mean(group1), np.mean(group2)
    std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)
    n1, n2 = len(group1), len(group2)
    
    pooled_std = math.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
    
    return (mean1 - mean2) / pooled_std

def compute_power_cohen_d(effect_size: float, n1: int, n2: int, alpha: float = 0.05) -> float:
    """Compute statistical power given effect size and sample sizes."""
    n_total = n1 + n2
    # Approximation using non-central t-distribution parameters
    # Simplified formula for power calculation
    if effect_size == 0:
        return alpha
    
    # Using standard normal approximation for large samples
    delta = effect_size * math.sqrt((n1 * n2) / (n1 + n2))
    z_alpha = norm.ppf(1 - alpha / 2)
    power = norm.cdf(delta - z_alpha) + norm.cdf(-delta - z_alpha)
    return max(0.0, min(1.0, power))

def compute_cliffs_delta(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Compute Cliff's Delta effect size.
    Returns value in range [-1, 1].
    """
    n1, n2 = len(group1), len(group2)
    if n1 == 0 or n2 == 0:
        return 0.0
    
    count_greater = 0
    count_less = 0
    
    for x in group1:
        for y in group2:
            if x > y:
                count_greater += 1
            elif x < y:
                count_less += 1
    
    delta = (count_greater - count_less) / (n1 * n2)
    return delta

def get_effect_size_magnitude(delta: float) -> str:
    """
    Classify effect size magnitude based on Cliff's Delta thresholds.
    |delta| < 0.147: negligible
    0.147 <= |delta| < 0.33: small
    0.33 <= |delta| < 0.474: medium
    |delta| >= 0.474: large
    """
    abs_delta = abs(delta)
    if abs_delta < 0.147:
        return "negligible"
    elif abs_delta < 0.33:
        return "small"
    elif abs_delta < 0.474:
        return "medium"
    else:
        return "large"

def run_mann_whitney_u_test(group1: np.ndarray, group2: np.ndarray, alternative: str = 'two-sided') -> Tuple[float, float]:
    """
    Run Mann-Whitney U test between two groups.
    Returns (statistic, p_value).
    """
    if len(group1) == 0 or len(group2) == 0:
        return 0.0, 1.0
    
    try:
        result = mannwhitneyu(group1, group2, alternative=alternative)
        return result.statistic, result.pvalue
    except Exception as e:
        logging.error(f"Mann-Whitney U test failed: {e}")
        return 0.0, 1.0

def run_power_analysis_for_metric(effect_size: float, n1: int, n2: int, alpha: float = 0.05) -> PowerAnalysisResult:
    """Compute power for a specific metric comparison."""
    power = compute_power_cohen_d(effect_size, n1, n2, alpha)
    return PowerAnalysisResult(
        metric_name="unknown",
        effect_size=effect_size,
        sample_size=n1 + n2,
        power=power,
        alpha=alpha
    )

def run_power_analysis_on_metrics(metrics_data: Dict[str, Dict[str, np.ndarray]], alpha: float = 0.05) -> Dict[str, PowerAnalysisResult]:
    """Run power analysis for all metrics."""
    results = {}
    for metric_name, groups in metrics_data.items():
        g1 = groups.get('human', np.array([]))
        g2 = groups.get('llm', np.array([]))
        
        if len(g1) > 0 and len(g2) > 0:
            d = compute_effect_size_cohen_d(g1, g2)
            power = compute_power_cohen_d(d, len(g1), len(g2), alpha)
            results[metric_name] = PowerAnalysisResult(
                metric_name=metric_name,
                effect_size=d,
                sample_size=len(g1) + len(g2),
                power=power,
                alpha=alpha
            )
    return results

def run_mann_whitney_u_analysis(metrics_data: Dict[str, Dict[str, np.ndarray]], alpha: float = 0.05) -> Dict[str, Dict[str, Any]]:
    """
    Run Mann-Whitney U test for all metrics.
    Returns dictionary with raw p-values and statistics.
    """
    results = {}
    for metric_name, groups in metrics_data.items():
        g1 = groups.get('human', np.array([]))
        g2 = groups.get('llm', np.array([]))
        
        if len(g1) > 0 and len(g2) > 0:
            stat, pval = run_mann_whitney_u_test(g1, g2)
            results[metric_name] = {
                'statistic': stat,
                'p_value_raw': pval,
                'n_human': len(g1),
                'n_llm': len(g2)
            }
        else:
            results[metric_name] = {
                'statistic': 0.0,
                'p_value_raw': 1.0,
                'n_human': len(g1),
                'n_llm': len(g2),
                'error': 'Insufficient data'
            }
    return results

def run_cliffs_delta_analysis(metrics_data: Dict[str, Dict[str, np.ndarray]]) -> Dict[str, Dict[str, Any]]:
    """
    Compute Cliff's Delta for all metrics.
    Returns dictionary with delta values and magnitude labels.
    """
    results = {}
    for metric_name, groups in metrics_data.items():
        g1 = groups.get('human', np.array([]))
        g2 = groups.get('llm', np.array([]))
        
        if len(g1) > 0 and len(g2) > 0:
            delta = compute_cliffs_delta(g1, g2)
            magnitude = get_effect_size_magnitude(delta)
            results[metric_name] = {
                'cliffs_delta': delta,
                'magnitude': magnitude
            }
        else:
            results[metric_name] = {
                'cliffs_delta': 0.0,
                'magnitude': 'negligible',
                'error': 'Insufficient data'
            }
    return results

def apply_benjamini_hochberg_correction(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg procedure for multiple comparison correction.
    
    Args:
        p_values: List of raw p-values (must be non-negative)
        
    Returns:
        List of adjusted p-values (q-values)
    """
    if not p_values or len(p_values) == 0:
        return []
    
    n = len(p_values)
    # Create list of (original_index, p_value)
    indexed_pvals = [(i, p) for i, p in enumerate(p_values) if not math.isnan(p) and not math.isinf(p)]
    
    if len(indexed_pvals) == 0:
        return [1.0] * n
    
    # Sort by p-value
    indexed_pvals.sort(key=lambda x: x[1])
    
    # Compute adjusted p-values
    # BH procedure: q_i = min( (n/i) * p_i, q_{i+1} ) working backwards
    adjusted = [0.0] * len(indexed_pvals)
    current_min = 1.0
    
    for i in reversed(range(len(indexed_pvals))):
        idx, p = indexed_pvals[i]
        rank = i + 1  # 1-based rank
        # BH adjusted p-value formula
        q = (n / rank) * p
        # Ensure monotonicity: adjusted p-value for rank i cannot be less than rank i+1
        q = min(q, current_min)
        # Clamp to [0, 1]
        q = max(0.0, min(1.0, q))
        adjusted[i] = q
        current_min = q
    
    # Map back to original order
    final_adjusted = [1.0] * n
    for i, (orig_idx, _) in enumerate(indexed_pvals):
        final_adjusted[orig_idx] = adjusted[i]
    
    return final_adjusted

def run_benjamini_hochberg_correction_on_metrics(raw_results: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Apply Benjamini-Hochberg correction to all raw p-values.
    
    Args:
        raw_results: Dictionary from run_mann_whitney_u_analysis
        
    Returns:
        Updated dictionary with 'p_value_adjusted' added to each metric
    """
    # Extract p-values in order
    metrics_list = list(raw_results.keys())
    p_values = []
    
    for metric in metrics_list:
        if 'p_value_raw' in raw_results[metric]:
            p_values.append(raw_results[metric]['p_value_raw'])
        else:
            p_values.append(1.0)  # Default if missing
    
    adjusted_p_values = apply_benjamini_hochberg_correction(p_values)
    
    # Add adjusted p-values to results
    for i, metric in enumerate(metrics_list):
        if 'p_value_raw' in raw_results[metric]:
            raw_results[metric]['p_value_adjusted'] = adjusted_p_values[i]
        else:
            raw_results[metric]['p_value_adjusted'] = adjusted_p_values[i]
    
    return raw_results

def main():
    """Main entry point for statistical analysis."""
    logger = setup_logger("statistical_analysis")
    logger.info("Starting statistical analysis module")
    
    # Example usage (would be populated with real data in pipeline)
    # This is a placeholder for the actual pipeline integration
    logger.info("Module loaded successfully. Use run_mann_whitney_u_analysis, run_cliffs_delta_analysis, and run_benjamini_hochberg_correction_on_metrics for analysis.")
    
    return True

if __name__ == "__main__":
    main()
