import numpy as np
from scipy import stats
from typing import List, Tuple, Dict, Any, Optional
import json
from pathlib import Path
import logging
import warnings

# Suppress specific warnings for cleaner logs if needed
warnings.filterwarnings('ignore', category=RuntimeWarning)

logger = logging.getLogger(__name__)

def boxcox_transform(data: np.ndarray, lmbda: Optional[float] = None) -> Tuple[np.ndarray, float]:
    """
    Apply Box-Cox transformation to stabilize variance.
    Returns transformed data and the optimal lambda parameter.
    """
    if np.all(data == data[0]):
        logger.warning("Constant data detected. Box-Cox not applicable. Returning original data.")
        return data, 0.0

    try:
        transformed_data, lmbda_opt = stats.boxcox(data)
        return transformed_data, lmbda_opt
    except Exception as e:
        logger.warning(f"Box-Cox transformation failed: {e}. Reverting to log transform.")
        # Fallback to log transform if Box-Cox fails (common for strictly positive data)
        # Ensure data is strictly positive for log transform
        min_val = np.min(data)
        if min_val <= 0:
            shift = abs(min_val) + 1e-6
            data_shifted = data + shift
        else:
            data_shifted = data

        log_transformed = np.log(data_shifted)
        return log_transformed, 0.0  # Lambda=0 corresponds to log transform

def check_normality(data: np.ndarray, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Check normality using Shapiro-Wilk test.
    Returns dict with p-value and boolean result.
    """
    if len(data) < 3:
        logger.warning("Insufficient data points for Shapiro-Wilk test (<3).")
        return {"is_normal": False, "p_value": 0.0, "statistic": 0.0}

    try:
        stat, p_value = stats.shapiro(data)
        is_normal = p_value >= alpha
        return {"is_normal": is_normal, "p_value": p_value, "statistic": stat}
    except Exception as e:
        logger.error(f"Shapiro-Wilk test failed: {e}")
        return {"is_normal": False, "p_value": 0.0, "statistic": 0.0}

def apply_variance_stabilization(data: np.ndarray, method: str = "auto") -> Tuple[np.ndarray, str, Dict[str, Any]]:
    """
    Apply a variance-stabilizing transformation to latency data if normality is violated.
    
    Args:
        data: Array of latency measurements.
        method: 'auto' (check normality first), 'boxcox', 'log', or 'none'.
    
    Returns:
        Tuple of (transformed_data, method_used, diagnostics).
    """
    diagnostics = {"original_mean": float(np.mean(data)), "original_std": float(np.std(data))}
    diagnostics["original_min"] = float(np.min(data))
    diagnostics["original_max"] = float(np.max(data))

    if method == "none":
        logger.info("Variance stabilization skipped (method='none').")
        return data, "none", diagnostics

    # Check normality if method is auto or if we need to decide
    should_transform = False
    if method == "auto":
        normality_result = check_normality(data)
        diagnostics["normality_p_value"] = normality_result["p_value"]
        diagnostics["normality_statistic"] = normality_result["statistic"]
        should_transform = not normality_result["is_normal"]
        logger.info(f"Normality check (Shapiro-Wilk): p={normality_result['p_value']:.4f}, is_normal={normality_result['is_normal']}")
    else:
        should_transform = True

    if not should_transform:
        logger.info("Data appears normal. Skipping variance stabilization.")
        return data, "none", diagnostics

    transformed_data = data
    applied_method = "none"

    try:
        if method == "boxcox" or (method == "auto" and np.all(data > 0)):
            # Box-Cox requires strictly positive data
            if np.all(data > 0):
                transformed_data, lmbda = boxcox_transform(data)
                applied_method = "boxcox"
                diagnostics["boxcox_lambda"] = lmbda
                logger.info(f"Applied Box-Cox transformation with lambda={lmbda:.4f}")
            else:
                logger.warning("Data contains non-positive values. Cannot apply Box-Cox. Falling back to log transform.")
                # Fallback to log
                shift = abs(np.min(data)) + 1e-6
                transformed_data = np.log(data + shift)
                applied_method = "log"
                diagnostics["log_shift"] = shift
        elif method == "log" or method == "auto":
            # Log transform: requires positive data, shift if necessary
            min_val = np.min(data)
            if min_val <= 0:
                shift = abs(min_val) + 1e-6
                transformed_data = np.log(data + shift)
                diagnostics["log_shift"] = shift
                logger.info(f"Applied log transformation with shift={shift:.6f}")
            else:
                transformed_data = np.log(data)
                logger.info("Applied log transformation (no shift needed).")
            applied_method = "log"
        else:
            logger.warning(f"Unknown method '{method}'. Returning original data.")
            applied_method = "none"

        # Verify transformation reduced skewness (optional diagnostic)
        if applied_method != "none":
            diagnostics["transformed_mean"] = float(np.mean(transformed_data))
            diagnostics["transformed_std"] = float(np.std(transformed_data))
            # Check normality of transformed data
            new_normality = check_normality(transformed_data)
            diagnostics["transformed_normality_p_value"] = new_normality["p_value"]
            diagnostics["transformed_normality_is_normal"] = new_normality["is_normal"]
            logger.info(f"Transformed data normality: p={new_normality['p_value']:.4f}, is_normal={new_normality['is_normal']}")

    except Exception as e:
        logger.error(f"Variance stabilization failed: {e}. Returning original data.")
        applied_method = "none"
        transformed_data = data

    diagnostics["method_applied"] = applied_method
    return transformed_data, applied_method, diagnostics

def paired_comparison(data1: np.ndarray, data2: np.ndarray, method: str = "auto") -> Dict[str, Any]:
    """
    Perform paired comparison (t-test or Wilcoxon) based on normality.
    """
    if len(data1) != len(data2) or len(data1) < 3:
        logger.error("Insufficient or mismatched data for paired comparison.")
        return {"p_value": 1.0, "statistic": 0.0, "test_used": "none", "message": "Insufficient data"}

    # Check normality of differences
    diff = data1 - data2
    normality_result = check_normality(diff)
    test_used = "unknown"
    p_value = 1.0
    statistic = 0.0

    if normality_result["is_normal"]:
        try:
            statistic, p_value = stats.ttest_rel(data1, data2)
            test_used = "paired_ttest"
            logger.info(f"Normality passed. Using paired t-test. p={p_value:.4f}")
        except Exception as e:
            logger.error(f"T-test failed: {e}. Falling back to Wilcoxon.")
            test_used = "wilcoxon"
            statistic, p_value = stats.wilcoxon(data1, data2)
            logger.info(f"Fallback to Wilcoxon. p={p_value:.4f}")
    else:
        try:
            statistic, p_value = stats.wilcoxon(data1, data2)
            test_used = "wilcoxon"
            logger.info(f"Normality failed. Using Wilcoxon signed-rank test. p={p_value:.4f}")
        except Exception as e:
            logger.error(f"Wilcoxon failed: {e}.")
            test_used = "none"
            p_value = 1.0

    return {
        "p_value": p_value,
        "statistic": statistic,
        "test_used": test_used,
        "normality_check": normality_result
    }

def calculate_convergence_rate(iteration_errors: List[float]) -> float:
    """
    Calculate the rate of convergence based on error reduction.
    Simple metric: (error_start - error_end) / error_start
    """
    if len(iteration_errors) < 2:
        return 0.0
    start_err = iteration_errors[0]
    end_err = iteration_errors[-1]
    if start_err == 0:
        return 0.0
    return (start_err - end_err) / start_err

def identify_sparsity_threshold(view_counts: List[int], errors: List[float], tolerance: float = 0.1) -> Dict[str, Any]:
    """
    Identify the view count where relative error increase exceeds tolerance.
    """
    if not view_counts or not errors:
        return {"threshold_view_count": None, "reason": "No data"}

    baseline_error = errors[0]
    if baseline_error == 0:
        return {"threshold_view_count": None, "reason": "Baseline error is zero"}

    threshold_view_count = None
    for i, err in enumerate(errors):
        relative_increase = (err - baseline_error) / baseline_error
        if relative_increase > tolerance:
            threshold_view_count = view_counts[i]
            break

    return {
        "threshold_view_count": threshold_view_count,
        "tolerance": tolerance,
        "baseline_error": baseline_error
    }

def calculate_bootstrap_confidence_interval(data: np.ndarray, n_iterations: int = 1000, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate bootstrap confidence interval for the mean.
    """
    if len(data) < 2:
        return (float(np.mean(data)), float(np.mean(data)))

    bootstrap_means = []
    rng = np.random.default_rng(42)
    for _ in range(n_iterations):
        sample = rng.choice(data, size=len(data), replace=True)
        bootstrap_means.append(np.mean(sample))

    lower = np.percentile(bootstrap_means, (1 - confidence) / 2 * 100)
    upper = np.percentile(bootstrap_means, (1 + confidence) / 2 * 100)
    return float(lower), float(upper)

def save_threshold_results(results: Dict[str, Any], output_path: Path) -> None:
    """
    Save threshold results to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Threshold results saved to {output_path}")

def run_statistical_analysis_batch(data_dict: Dict[str, np.ndarray], tolerance: float = 0.1) -> Dict[str, Any]:
    """
    Run statistical analysis on a batch of data grouped by view count.
    """
    view_counts = sorted(data_dict.keys())
    if not view_counts:
        return {}

    errors = [np.mean(data_dict[v]) for v in view_counts]
    threshold_result = identify_sparsity_threshold(view_counts, errors, tolerance)

    # Run paired comparisons between consecutive view counts
    comparisons = []
    for i in range(len(view_counts) - 1):
        v1, v2 = view_counts[i], view_counts[i+1]
        d1, d2 = data_dict[v1], data_dict[v2]
        # Ensure same length for paired test (pad or truncate if necessary, here we assume equal or truncate)
        min_len = min(len(d1), len(d2))
        if min_len < 3:
            logger.warning(f"Insufficient data for paired comparison between {v1} and {v2} views.")
            continue
        res = paired_comparison(d1[:min_len], d2[:min_len])
        comparisons.append({
            "view_count_1": v1,
            "view_count_2": v2,
            "p_value": res["p_value"],
            "test_used": res["test_used"]
        })

    return {
        "threshold_result": threshold_result,
        "pairwise_comparisons": comparisons
    }

def calculate_comparative_metrics(baseline_latencies: np.ndarray, new_latencies: np.ndarray) -> Dict[str, float]:
    """
    Calculate speedup ratio and latency delta.
    """
    if len(baseline_latencies) == 0 or len(new_latencies) == 0:
        return {"speedup_ratio": 0.0, "psnr_delta": 0.0} # Placeholder for PSNR delta if needed

    mean_base = np.mean(baseline_latencies)
    mean_new = np.mean(new_latencies)

    speedup = mean_base / mean_new if mean_new > 0 else 0.0
    delta = mean_base - mean_new

    return {
        "mean_baseline_latency": float(mean_base),
        "mean_new_latency": float(mean_new),
        "speedup_ratio": float(speedup),
        "latency_delta": float(delta)
    }

def aggregate_benchmark_results(results_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate benchmark results from multiple scenes.
    """
    if not results_list:
        return {}

    # Example aggregation: mean and std for key metrics
    aggregated = {}
    for key in results_list[0].keys():
        if isinstance(results_list[0][key], (int, float)):
            values = [r[key] for r in results_list if isinstance(r.get(key), (int, float))]
            if values:
                aggregated[f"mean_{key}"] = float(np.mean(values))
                aggregated[f"std_{key}"] = float(np.std(values))
    return aggregated

# T053 Implementation: Variance Stabilization for Latency Data
# This function is explicitly added to satisfy T053.
# It applies a variance-stabilizing transformation (Box-Cox or Log)
# to latency measurements if a normality check (Shapiro-Wilk) fails.
# This ensures that subsequent t-tests on latency data are valid.
def apply_variance_stabilization_to_latency(latency_data: List[float], output_log_path: Optional[Path] = None) -> Tuple[List[float], Dict[str, Any]]:
    """
    Main entry point for T053.
    Checks normality of latency data. If non-normal, applies Box-Cox or Log transform.
    Returns transformed data and a diagnostics dictionary.
    
    Args:
        latency_data: List of latency measurements (floats).
        output_log_path: Optional path to write detailed diagnostics.
    
    Returns:
        Tuple of (transformed_latency_list, diagnostics_dict)
    """
    if not latency_data:
        logger.warning("Empty latency data provided to variance stabilization.")
        return [], {"method": "none", "message": "Empty data"}

    data_array = np.array(latency_data, dtype=float)

    # Apply variance stabilization
    transformed_array, method_applied, diagnostics = apply_variance_stabilization(data_array, method="auto")

    diagnostics["original_count"] = len(latency_data)
    diagnostics["transformed_count"] = len(transformed_array)

    # Log the result
    if method_applied != "none":
        logger.info(f"Variance stabilization applied to latency data. Method: {method_applied}")
    else:
        logger.info("Variance stabilization not needed for latency data (normal distribution).")

    # Save diagnostics if path provided
    if output_log_path:
        try:
            output_log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_log_path, 'w') as f:
                json.dump(diagnostics, f, indent=2)
            logger.info(f"Variance stabilization diagnostics saved to {output_log_path}")
        except Exception as e:
            logger.error(f"Failed to save diagnostics to {output_log_path}: {e}")

    return transformed_array.tolist(), diagnostics