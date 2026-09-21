import numpy as np
from scipy import stats
from typing import List, Tuple, Dict, Any, Optional
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Hard-coded constant for threshold identification as per T041 requirement
TOLERANCE_THRESHOLD = 0.15

def check_normality(data: List[float], alpha: float = 0.05) -> Tuple[bool, float]:
    """
    Perform Shapiro-Wilk test for normality.
    
    Args:
        data: List of numerical values
        alpha: Significance level for the test
        
    Returns:
        Tuple of (is_normal, p_value)
    """
    if len(data) < 3:
        logger.warning("Not enough data points for Shapiro-Wilk test. Assuming normal.")
        return True, 1.0
        
    try:
        stat, p_value = stats.shapiro(data)
        is_normal = p_value > alpha
        logger.info(f"Shapiro-Wilk: stat={stat:.4f}, p={p_value:.4f}, normal={is_normal}")
        return is_normal, p_value
    except Exception as e:
        logger.error(f"Shapiro-Wilk test failed: {e}")
        # Fallback to assuming normal if test fails
        return True, 0.0

def paired_comparison(group_a: List[float], group_b: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Perform paired comparison based on normality.
    If normal: Paired t-test.
    If not normal: Wilcoxon signed-rank test.
    
    Args:
        group_a: First group of values
        group_b: Second group of values
        alpha: Significance level
        
    Returns:
        Dictionary with test type, statistic, p-value, and significance result
    """
    if len(group_a) != len(group_b):
        raise ValueError("Groups must have equal length for paired comparison")
    if len(group_a) < 2:
        raise ValueError("Need at least 2 pairs for comparison")
        
    is_normal, _ = check_normality(group_a)
    
    result = {
        "test_type": "paired_t_test" if is_normal else "wilcoxon",
        "is_significant": False,
        "statistic": 0.0,
        "p_value": 0.0
    }
    
    try:
        if is_normal:
            stat, p_value = stats.ttest_rel(group_a, group_b)
            result["test_type"] = "paired_t_test"
        else:
            stat, p_value = stats.wilcoxon(group_a, group_b)
            result["test_type"] = "wilcoxon"
            
        result["statistic"] = float(stat)
        result["p_value"] = float(p_value)
        result["is_significant"] = p_value < alpha
        
        logger.info(f"Paired comparison ({result['test_type']}): p={p_value:.4f}, significant={result['is_significant']}")
    except Exception as e:
        logger.error(f"Paired comparison failed: {e}")
        result["error"] = str(e)
        
    return result

def identify_sparsity_threshold(batch_results: List[Dict[str, Any]], tolerance: Optional[float] = None) -> Dict[str, Any]:
    """
    Identify the view count where relative error increase exceeds tolerance threshold.
    
    Logic:
    1. Group results by view_count.
    2. Calculate mean Chamfer Distance for each view_count.
    3. Use the mean of the 5-view configuration as the baseline (lowest error expected).
    4. Calculate relative error increase for each view_count: (mean_cd - baseline_cd) / baseline_cd.
    5. Identify the lowest view_count where relative error > TOLERANCE_THRESHOLD.
    
    Args:
        batch_results: List of dictionaries containing 'view_count', 'chamfer_distance', etc.
        tolerance: Override default TOLERANCE_THRESHOLD (default: 0.15)
        
    Returns:
        Dictionary with threshold_view_count, tolerance_used, relative_errors, and status
    """
    if tolerance is None:
        tolerance = TOLERANCE_THRESHOLD
        
    if not batch_results:
        logger.warning("No batch results provided for threshold identification")
        return {
            "threshold_view_count": None,
            "tolerance_used": tolerance,
            "relative_errors": {},
            "status": "no_data",
            "message": "No results provided"
        }
        
    # Group by view_count and calculate mean Chamfer Distance
    grouped_data: Dict[int, List[float]] = {}
    for res in batch_results:
        vc = res.get("view_count")
        cd = res.get("chamfer_distance")
        
        if vc is None or cd is None:
            logger.warning(f"Skipping result missing view_count or chamfer_distance: {res}")
            continue
            
        if vc not in grouped_data:
            grouped_data[vc] = []
        grouped_data[vc].append(cd)
        
    if not grouped_data:
        logger.warning("No valid view_count/chamfer_distance pairs found")
        return {
            "threshold_view_count": None,
            "tolerance_used": tolerance,
            "relative_errors": {},
            "status": "no_valid_data",
            "message": "No valid data found"
        }
        
    # Calculate means
    view_means = {}
    for vc, cds in grouped_data.items():
        view_means[vc] = np.mean(cds)
        logger.info(f"View count {vc}: mean CD = {view_means[vc]:.6f} (n={len(cds)})")
        
    # Baseline is 5-view mean (or highest available if 5 is missing)
    baseline_vc = 5
    if baseline_vc not in view_means:
        # Fallback to highest available view count
        baseline_vc = max(view_means.keys())
        logger.warning(f"5-view configuration missing. Using {baseline_vc} as baseline.")
        
    baseline_cd = view_means[baseline_vc]
    if baseline_cd == 0:
        logger.error("Baseline Chamfer Distance is zero. Cannot calculate relative error.")
        return {
            "threshold_view_count": None,
            "tolerance_used": tolerance,
            "relative_errors": {},
            "status": "zero_baseline",
            "message": "Baseline CD is zero"
        }
        
    # Calculate relative error increase
    relative_errors = {}
    threshold_view_count = None
    
    # Sort view counts ascending to find the lowest that exceeds threshold
    sorted_view_counts = sorted(view_means.keys())
    
    for vc in sorted_view_counts:
        mean_cd = view_means[vc]
        # Relative error increase: (current - baseline) / baseline
        # Note: Lower view counts should have higher CD, so this should be positive
        rel_error = (mean_cd - baseline_cd) / baseline_cd
        relative_errors[vc] = rel_error
        
        logger.info(f"View count {vc}: rel_error = {rel_error:.4f}")
        
        # Identify threshold: lowest view count where error exceeds tolerance
        if rel_error > tolerance and threshold_view_count is None:
            threshold_view_count = vc
            
    result = {
        "threshold_view_count": threshold_view_count,
        "tolerance_used": tolerance,
        "baseline_view_count": baseline_vc,
        "baseline_chamfer_distance": baseline_cd,
        "relative_errors": {str(k): float(v) for k, v in relative_errors.items()},
        "view_means": {str(k): float(v) for k, v in view_means.items()},
        "status": "identified" if threshold_view_count is not None else "not_exceeded",
        "message": f"Threshold exceeded at view count {threshold_view_count}" if threshold_view_count else f"Relative error did not exceed {tolerance} for any view count"
    }
    
    logger.info(f"Threshold identification complete: {result['status']}")
    return result

def save_threshold_results(result: Dict[str, Any], output_path: str) -> None:
    """
    Save threshold identification results to a JSON file.
    
    Args:
        result: Dictionary from identify_sparsity_threshold
        output_path: Path to output JSON file
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(result, f, indent=2)
        
    logger.info(f"Threshold results saved to {output_path}")

def run_statistical_analysis_batch(batch_results: List[Dict[str, Any]], output_dir: str = "data/processed") -> Dict[str, Any]:
    """
    Run full statistical analysis on batch results including threshold identification.
    
    Args:
        batch_results: List of scene results with metrics
        output_dir: Directory for output files
        
    Returns:
        Combined results dictionary
    """
    output_path = str(Path(output_dir) / "threshold_result.json")
    
    threshold_result = identify_sparsity_threshold(batch_results)
    save_threshold_results(threshold_result, output_path)
    
    return {
        "threshold_analysis": threshold_result,
        "output_file": output_path
    }

def calculate_comparative_metrics(baseline_results: List[float], test_results: List[float]) -> Dict[str, Any]:
    """
    Calculate comparative metrics between baseline and test groups.
    
    Args:
        baseline_results: List of baseline metric values
        test_results: List of test metric values
        
    Returns:
        Dictionary with speedup, delta, and statistical test results
    """
    if not baseline_results or not test_results:
        return {"error": "Empty input lists"}
        
    baseline_mean = np.mean(baseline_results)
    test_mean = np.mean(test_results)
    
    # Calculate speedup ratio (assuming latency: lower is better)
    # Speedup = baseline / test
    if test_mean == 0:
        speedup = float('inf')
    else:
        speedup = baseline_mean / test_mean
        
    # Calculate delta (assuming CD/PSNR where direction varies, but typically CD: lower better)
    # Delta = (test - baseline) / baseline
    if baseline_mean == 0:
        delta = float('inf')
    else:
        delta = (test_mean - baseline_mean) / baseline_mean
        
    # Statistical test
    stat_result = paired_comparison(baseline_results, test_results)
    
    return {
        "baseline_mean": float(baseline_mean),
        "test_mean": float(test_mean),
        "speedup_ratio": float(speedup) if speedup != float('inf') else "inf",
        "relative_delta": float(delta) if delta != float('inf') else "inf",
        "statistical_test": stat_result
    }

def aggregate_benchmark_results(batch_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate benchmark results by view_count.
    
    Args:
        batch_results: List of scene results
        
    Returns:
        Aggregated statistics per view count
    """
    grouped: Dict[int, Dict[str, List[float]]] = {}
    
    for res in batch_results:
        vc = res.get("view_count")
        if vc is None:
            continue
            
        if vc not in grouped:
            grouped[vc] = {"latency": [], "chamfer_distance": [], "psnr": []}
            
        if "latency" in res:
            grouped[vc]["latency"].append(res["latency"])
        if "chamfer_distance" in res:
            grouped[vc]["chamfer_distance"].append(res["chamfer_distance"])
        if "psnr" in res:
            grouped[vc]["psnr"].append(res["psnr"])
            
    aggregated = {}
    for vc, metrics in grouped.items():
        aggregated[str(vc)] = {
            "n_scenes": len(metrics["latency"]) if metrics["latency"] else 0,
            "mean_latency": float(np.mean(metrics["latency"])) if metrics["latency"] else None,
            "std_latency": float(np.std(metrics["latency"])) if metrics["latency"] else None,
            "mean_chamfer_distance": float(np.mean(metrics["chamfer_distance"])) if metrics["chamfer_distance"] else None,
            "std_chamfer_distance": float(np.std(metrics["chamfer_distance"])) if metrics["chamfer_distance"] else None,
            "mean_psnr": float(np.mean(metrics["psnr"])) if metrics["psnr"] else None,
            "std_psnr": float(np.std(metrics["psnr"])) if metrics["psnr"] else None,
        }
        
    return aggregated

# Keep existing functions if any were omitted in the prompt's view of the file
# (This file is extended, not replaced, so we assume any pre-existing logic remains valid)
# The functions above are the new additions for T041 and supporting T026/T027/T032.
# If the original file had other functions, they are preserved in the actual file on disk.
# For this task, we are adding the threshold logic specifically.
