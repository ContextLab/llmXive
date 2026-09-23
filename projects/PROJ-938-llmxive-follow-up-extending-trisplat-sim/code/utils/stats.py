"""
Statistical analysis utilities.
Implements T007, T026, T027, T041.
"""
import numpy as np
from scipy import stats
from typing import List, Tuple, Dict, Any, Optional
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def check_normality(data: List[float]) -> Tuple[bool, float]:
    """
    T027: Shapiro-Wilk test for normality.
    Returns (is_normal, p_value).
    """
    if len(data) < 3:
        return False, 0.0
    stat, p_value = stats.shapiro(data)
    return p_value > 0.05, p_value

def paired_comparison(data1: List[float], data2: List[float]) -> Dict[str, float]:
    """
    T007: Paired t-test or Wilcoxon signed-rank test.
    """
    if len(data1) != len(data2):
        raise ValueError("Data lengths must match for paired test.")
    
    is_normal, _ = check_normality([a-b for a, b in zip(data1, data2)])
    
    if is_normal:
        stat, p_value = stats.ttest_rel(data1, data2)
        method = "paired_t_test"
    else:
        stat, p_value = stats.wilcoxon(data1, data2)
        method = "wilcoxon_signed_rank"
        
    return {"method": method, "statistic": float(stat), "p_value": float(p_value)}

def identify_sparsity_threshold(results: List[Dict[str, Any]], tolerance: float = 0.15) -> Dict[str, Any]:
    """
    T041: Identify view count where error exceeds tolerance.
    """
    # Group by view count
    view_errors = {}
    for r in results:
        vc = r.get('view_count')
        cd = r.get('chamfer_distance')
        if cd is not None:
            if vc not in view_errors:
                view_errors[vc] = []
            view_errors[vc].append(cd)
    
    if not view_errors:
        return {"error": "No valid data"}

    # Baseline: lowest view count with data
    sorted_views = sorted(view_errors.keys())
    baseline_view = sorted_views[0]
    baseline_error = np.mean(view_errors[baseline_view])
    
    threshold_result = {}
    for vc in sorted_views:
        avg_error = np.mean(view_errors[vc])
        relative_increase = (avg_error - baseline_error) / baseline_error if baseline_error != 0 else 0
        threshold_result[vc] = {
            "avg_error": avg_error,
            "relative_increase": relative_increase,
            "exceeds_tolerance": relative_increase > tolerance
        }
        
        if relative_increase > tolerance and "threshold" not in threshold_result:
            threshold_result["threshold_view_count"] = vc
            break
    
    return threshold_result

def save_threshold_results(results: Dict[str, Any], path: str):
    """Save threshold results to JSON."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Threshold results saved to {path}")

def run_statistical_analysis_batch(results: List[Dict[str, Any]]):
    """Orchestrate batch statistical analysis."""
    logger.info("Running batch statistical analysis...")
    # Group by view count for comparison
    # Simplified: just calculate threshold
    threshold_data = identify_sparsity_threshold(results)
    save_threshold_results(threshold_data, "data/processed/threshold_result.json")

def calculate_comparative_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate speedup and fidelity delta."""
    # Placeholder
    return {}

def aggregate_benchmark_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate results for benchmark report."""
    return results
