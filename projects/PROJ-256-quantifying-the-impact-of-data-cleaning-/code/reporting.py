import json
import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

def calculate_p_value_shift(p_baseline: float, p_cleaned: float) -> float:
    """Calculate the absolute difference between baseline and cleaned p-values."""
    shift = abs(p_cleaned - p_baseline)
    return round(shift, 3)

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool]]:
    """
    Apply Bonferroni correction for Family-Wise Error Rate (FWER) control.
    
    Args:
        p_values: List of raw p-values from multiple hypothesis tests.
        alpha: Significance level (default 0.05).
        
    Returns:
        Tuple of (adjusted_p_values, is_significant_list).
    """
    if not p_values:
        return [], []
    
    n_tests = len(p_values)
    adjusted_alpha = alpha / n_tests
    
    adjusted_p_values = []
    is_significant = []
    
    for p in p_values:
        # Bonferroni adjusted p-value is min(p * n, 1.0)
        adj_p = min(p * n_tests, 1.0)
        adjusted_p_values.append(round(adj_p, 6))
        is_significant.append(adj_p < alpha)
    
    logger.warning("Warning: FR-007 requests FWER control. Benjamini-Hochberg controls FDR. Implemented Bonferroni (FWER) to satisfy FR-007.")
    
    return adjusted_p_values, is_significant

def compute_ci_width_change(ci_baseline: Tuple[float, float], ci_cleaned: Tuple[float, float]) -> float:
    """Compute the change in confidence interval width."""
    width_baseline = ci_baseline[1] - ci_baseline[0]
    width_cleaned = ci_cleaned[1] - ci_cleaned[0]
    change = width_cleaned - width_baseline
    return round(change, 2)

def compute_effect_size_delta(es_baseline: float, es_cleaned: float) -> float:
    """Compute the difference in effect size."""
    delta = es_cleaned - es_baseline
    return round(delta, 3)

def calculate_inconsistency_rate(baseline_significant: List[bool], cleaned_significant: List[bool]) -> float:
    """
    Calculate the proportion of tests where significance status changes.
    
    Args:
        baseline_significant: List of booleans indicating significance in baseline.
        cleaned_significant: List of booleans indicating significance in cleaned data.
        
    Returns:
        Inconsistency rate as a float between 0 and 1.
    """
    if len(baseline_significant) != len(cleaned_significant):
        raise ValueError("Lists must be of equal length")
    
    if not baseline_significant:
        return 0.0
        
    inconsistencies = sum(1 for b, c in zip(baseline_significant, cleaned_significant) if b != c)
    return round(inconsistencies / len(baseline_significant), 3)

def generate_comparison_report(
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Generate a comprehensive comparison report between baseline and cleaned metrics.
    
    Args:
        baseline_metrics: Dictionary containing baseline analysis results.
        cleaned_metrics: Dictionary containing cleaned analysis results.
        alpha: Significance level for statistical tests.
        
    Returns:
        Dictionary containing the comparison report with all computed metrics.
    """
    report = {
        "baseline_metrics": baseline_metrics,
        "cleaned_metrics": cleaned_metrics,
        "p_value_shifts": [],
        "ci_width_changes": [],
        "effect_size_deltas": [],
        "inconsistency_rate": 0.0,
        "bonferroni_adjusted": {
            "adjusted_p_values": [],
            "is_significant": []
        }
    }
    
    # Ensure we have lists of p-values for comparison
    baseline_p_values = [m.get("p_value") for m in baseline_metrics.get("results", []) if m.get("p_value") is not None]
    cleaned_p_values = [m.get("p_value") for m in cleaned_metrics.get("results", []) if m.get("p_value") is not None]
    
    if len(baseline_p_values) != len(cleaned_p_values):
        logger.warning(f"Mismatch in number of p-values: baseline={len(baseline_p_values)}, cleaned={len(cleaned_p_values)}. Skipping shift calculations.")
        return report
    
    # Calculate p-value shifts
    for b_p, c_p in zip(baseline_p_values, cleaned_p_values):
        shift = calculate_p_value_shift(b_p, c_p)
        report["p_value_shifts"].append(shift)
    
    # Calculate CI width changes
    baseline_cis = [m.get("ci_bounds") for m in baseline_metrics.get("results", []) if m.get("ci_bounds")]
    cleaned_cis = [m.get("ci_bounds") for m in cleaned_metrics.get("results", []) if m.get("ci_bounds")]
    
    if len(baseline_cis) == len(cleaned_cis):
        for b_ci, c_ci in zip(baseline_cis, cleaned_cis):
            if b_ci and c_ci:
                change = compute_ci_width_change(b_ci, c_ci)
                report["ci_width_changes"].append(change)
    
    # Calculate effect size deltas
    baseline_es = [m.get("effect_size") for m in baseline_metrics.get("results", []) if m.get("effect_size") is not None]
    cleaned_es = [m.get("effect_size") for m in cleaned_metrics.get("results", []) if m.get("effect_size") is not None]
    
    if len(baseline_es) == len(cleaned_es):
        for b_es, c_es in zip(baseline_es, cleaned_es):
            delta = compute_effect_size_delta(b_es, c_es)
            report["effect_size_deltas"].append(delta)
    
    # Determine significance for inconsistency rate
    baseline_sig = [p <= alpha for p in baseline_p_values]
    cleaned_sig = [p <= alpha for p in cleaned_p_values]
    
    if baseline_sig and cleaned_sig:
        report["inconsistency_rate"] = calculate_inconsistency_rate(baseline_sig, cleaned_sig)
    
    # Apply Bonferroni correction
    if cleaned_p_values:
        adj_p, sig_list = apply_bonferroni_correction(cleaned_p_values, alpha)
        report["bonferroni_adjusted"]["adjusted_p_values"] = adj_p
        report["bonferroni_adjusted"]["is_significant"] = sig_list
    
    return report