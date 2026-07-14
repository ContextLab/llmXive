import json
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime
import os

logger = logging.getLogger(__name__)

def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load JSON file and return as dictionary."""
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json_file(data: Dict[str, Any], filepath: str):
    """Save dictionary to JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved results to {filepath}")

def calculate_p_value_shift(p_baseline: float, p_cleaned: float) -> float:
    """
    Calculate the absolute difference between baseline and cleaned p-values.
    
    Args:
        p_baseline: Baseline p-value
        p_cleaned: Cleaned p-value
    
    Returns:
        Absolute difference with at least 3 decimal precision
    """
    if p_baseline is None or p_cleaned is None:
        return 0.0
    return round(abs(p_cleaned - p_baseline), 3)

def compute_ci_width_change(ci_baseline: Tuple[float, float], ci_cleaned: Tuple[float, float]) -> float:
    """
    Compute the change in confidence interval width.
    
    Args:
        ci_baseline: Tuple of (lower, upper) for baseline CI
        ci_cleaned: Tuple of (lower, upper) for cleaned CI
    
    Returns:
        Change in width with at least 2 decimal precision
    """
    if not ci_baseline or not ci_cleaned:
        return 0.0
    
    width_baseline = ci_baseline[1] - ci_baseline[0]
    width_cleaned = ci_cleaned[1] - ci_cleaned[0]
    
    return round(width_cleaned - width_baseline, 2)

def compute_effect_size_delta(effect_baseline: float, effect_cleaned: float) -> float:
    """
    Compute the difference in effect size.
    
    Args:
        effect_baseline: Baseline effect size (e.g., Cohen's d)
        effect_cleaned: Cleaned effect size
    
    Returns:
        Difference in effect size
    """
    if effect_baseline is None or effect_cleaned is None:
        return 0.0
    return round(effect_cleaned - effect_baseline, 3)

def calculate_inconsistency_rate(baseline_metrics: Dict[str, Any], cleaned_metrics: Dict[str, Any]) -> float:
    """
    Calculate the proportion of datasets where significance status changes.
    
    Significance status changes if a test that was significant (p <= 0.05) becomes
    non-significant, or vice versa, after cleaning.
    
    Args:
        baseline_metrics: Dictionary containing baseline analysis results
        cleaned_metrics: Dictionary containing cleaned analysis results
    
    Returns:
        Inconsistency rate as a float between 0 and 1
    """
    baseline_datasets = baseline_metrics.get("datasets", []) if isinstance(baseline_metrics, dict) else []
    cleaned_datasets = cleaned_metrics.get("datasets", []) if isinstance(cleaned_metrics, dict) else []
    
    if not baseline_datasets or not cleaned_datasets:
        logger.warning("No datasets found in metrics. Cannot calculate inconsistency rate.")
        return 0.0
    
    # Create a mapping of cleaned datasets by name
    cleaned_map = {}
    for entry in cleaned_datasets:
        name = entry.get("dataset_name") or entry.get("dataset_id")
        if name:
            cleaned_map[name] = entry
    
    inconsistent_count = 0
    total_count = 0
    
    for baseline_entry in baseline_datasets:
        name = baseline_entry.get("dataset_name") or baseline_entry.get("dataset_id")
        if not name or name not in cleaned_map:
            continue
        
        cleaned_entry = cleaned_map[name]
        total_count += 1
        
        # Compare t-test results
        baseline_tests = baseline_entry.get("t_tests", {})
        cleaned_tests = cleaned_entry.get("t_tests", {})
        
        for test_name, baseline_test in baseline_tests.items():
            if test_name not in cleaned_tests:
                continue
            
            baseline_p = baseline_test.get("p_value")
            cleaned_p = cleaned_tests[test_name].get("p_value")
            
            if baseline_p is None or cleaned_p is None:
                continue
            
            baseline_sig = baseline_p <= 0.05
            cleaned_sig = cleaned_p <= 0.05
            
            if baseline_sig != cleaned_sig:
                inconsistent_count += 1
                break  # Count dataset as inconsistent if any test changes status
    
    if total_count == 0:
        return 0.0
    
    return inconsistent_count / total_count

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """
    Apply Bonferroni correction for Family-Wise Error Rate (FWER) control.
    
    Args:
        p_values: List of p-values to correct
        alpha: Significance level (default 0.05)
    
    Returns:
        List of adjusted p-values
    """
    n = len(p_values)
    if n == 0:
        return []
    
    adjusted = [min(p * n, 1.0) for p in p_values]
    logger.warning("Warning: FR-007 requests FWER control. Benjamini-Hochberg controls FDR. Implemented Bonferroni (FWER) to satisfy FR-007.")
    return adjusted

def process_single_comparison(baseline_entry: Dict[str, Any], cleaned_entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single dataset comparison between baseline and cleaned results.
    
    Args:
        baseline_entry: Baseline analysis results for a dataset
        cleaned_entry: Cleaned analysis results for a dataset
    
    Returns:
        Dictionary containing comparison metrics
    """
    comparison = {
        "dataset_name": baseline_entry.get("dataset_name"),
        "p_value_shifts": {},
        "ci_width_changes": {},
        "effect_size_deltas": {}
    }
    
    # Compare t-tests
    baseline_tests = baseline_entry.get("t_tests", {})
    cleaned_tests = cleaned_entry.get("t_tests", {})
    
    for test_name in baseline_tests:
        if test_name in cleaned_tests:
            baseline_p = baseline_tests[test_name].get("p_value")
            cleaned_p = cleaned_tests[test_name].get("p_value")
            
            if baseline_p is not None and cleaned_p is not None:
                comparison["p_value_shifts"][test_name] = calculate_p_value_shift(baseline_p, cleaned_p)
    
    # Compare effect sizes
    baseline_effect = baseline_entry.get("effect_size", {}).get("cohens_d", {}).get("cohens_d")
    cleaned_effect = cleaned_entry.get("effect_size", {}).get("cohens_d", {}).get("cohens_d")
    
    if baseline_effect is not None and cleaned_effect is not None:
        comparison["effect_size_deltas"]["cohens_d"] = compute_effect_size_delta(baseline_effect, cleaned_effect)
    
    return comparison

def generate_comparison_report(
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate a comprehensive comparison report between baseline and cleaned metrics.
    
    Args:
        baseline_metrics: Dictionary containing baseline analysis results
        cleaned_metrics: Dictionary containing cleaned analysis results
    
    Returns:
        Dictionary containing the full comparison report
    """
    # Handle case where cleaned_metrics might be a list (as per error trace)
    if isinstance(cleaned_metrics, list):
        # Convert list to expected dictionary format
        cleaned_metrics = {
            "datasets": cleaned_metrics,
            "timestamp": datetime.now().isoformat()
        }
    
    # Handle case where baseline_metrics might be a list
    if isinstance(baseline_metrics, list):
        baseline_metrics = {
            "datasets": baseline_metrics,
            "timestamp": datetime.now().isoformat()
        }
    
    baseline_datasets = baseline_metrics.get("datasets", [])
    cleaned_datasets = cleaned_metrics.get("datasets", [])
    
    # Create mapping of cleaned datasets by name
    cleaned_map = {}
    for entry in cleaned_datasets:
        name = entry.get("dataset_name") or entry.get("dataset_id")
        if name:
            cleaned_map[name] = entry
    
    comparisons = []
    total_inconsistent = 0
    total_datasets = 0
    
    for baseline_entry in baseline_datasets:
        name = baseline_entry.get("dataset_name") or baseline_entry.get("dataset_id")
        if not name or name not in cleaned_map:
            continue
        
        cleaned_entry = cleaned_map[name]
        comparison = process_single_comparison(baseline_entry, cleaned_entry)
        comparisons.append(comparison)
        
        # Check for inconsistency
        baseline_tests = baseline_entry.get("t_tests", {})
        cleaned_tests = cleaned_entry.get("t_tests", {})
        
        for test_name in baseline_tests:
            if test_name in cleaned_tests:
                baseline_p = baseline_tests[test_name].get("p_value")
                cleaned_p = cleaned_tests[test_name].get("p_value")
                
                if baseline_p is not None and cleaned_p is not None:
                    baseline_sig = baseline_p <= 0.05
                    cleaned_sig = cleaned_p <= 0.05
                    
                    if baseline_sig != cleaned_sig:
                        total_inconsistent += 1
                        break
        
        total_datasets += 1
    
    inconsistency_rate = total_inconsistent / total_datasets if total_datasets > 0 else 0.0
    
    report = {
        "comparisons": comparisons,
        "summary": {
            "total_datasets": total_datasets,
            "inconsistent_datasets": total_inconsistent,
            "inconsistency_rate": round(inconsistency_rate, 3),
            "generated_at": datetime.now().isoformat()
        }
    }
    
    return report

def main():
    """Main entry point for reporting module."""
    logger.info("Reporting module loaded")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())