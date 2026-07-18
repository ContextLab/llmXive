import numpy as np
from typing import List, Dict, Tuple, Optional, Union
from scipy import stats
import warnings

def paired_ttest_heuristic_vs_fullbatch(
    heuristic_variances: Union[List[float], np.ndarray],
    fullbatch_variances: Union[List[float], np.ndarray]
) -> Dict[str, float]:
    """
    Perform a paired t-test comparing Heuristic variance vs. Full-Batch Empirical variance.
    
    This is the PRIMARY validation method per Plan (FR-006).
    One-sample t-test against theoretical bound is FORBIDDEN.
    
    Args:
        heuristic_variances: List or array of variance estimates from the moving-window heuristic.
        fullbatch_variances: List or array of variance estimates from full-batch calculation.
        
    Returns:
        Dictionary containing:
            - 't_statistic': The t-statistic from the test.
            - 'p_value': The p-value for the two-sided test.
            - 'mean_diff': Mean of the differences (heuristic - fullbatch).
    """
    h_arr = np.array(heuristic_variances)
    f_arr = np.array(fullbatch_variances)
    
    if h_arr.shape != f_arr.shape:
        raise ValueError(f"Input arrays must have the same shape. Got {h_arr.shape} and {f_arr.shape}")
    
    if len(h_arr) < 2:
        raise ValueError("Paired t-test requires at least 2 samples.")
        
    t_stat, p_val = stats.ttest_rel(h_arr, f_arr)
    
    return {
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "mean_diff": float(np.mean(h_arr - f_arr))
    }

def check_stability(
    heuristic_variances: Union[List[float], np.ndarray],
    fullbatch_variances: Union[List[float], np.ndarray],
    tolerance_lower: float = 0.9,
    tolerance_upper: float = 1.1,
    stability_threshold: float = 0.95
) -> Dict[str, Union[bool, float, int]]:
    """
    Implement stability check: ratio of heuristic/full-batch variance must remain 
    within [tolerance_lower, tolerance_upper] for >= stability_threshold of steps.
    
    This addresses T039: "Implement stability check: ratio of heuristic/full-batch 
    variance must remain within [0.9, 1.1] for ≥ 95% of steps".
    
    Args:
        heuristic_variances: List or array of variance estimates from the moving-window heuristic.
        fullbatch_variances: List or array of variance estimates from full-batch calculation.
        tolerance_lower: Lower bound for the ratio (default 0.9).
        tolerance_upper: Upper bound for the ratio (default 1.1).
        stability_threshold: Minimum fraction of steps required to be stable (default 0.95).
        
    Returns:
        Dictionary containing:
            - 'is_stable': Boolean indicating if the stability threshold was met.
            - 'stability_ratio': The actual fraction of steps within tolerance.
            - 'stable_count': Number of steps within tolerance.
            - 'total_count': Total number of steps.
            - 'outlier_indices': List of indices where the ratio was outside tolerance.
    """
    h_arr = np.array(heuristic_variances)
    f_arr = np.array(fullbatch_variances)
    
    if h_arr.shape != f_arr.shape:
        raise ValueError(f"Input arrays must have the same shape. Got {h_arr.shape} and {f_arr.shape}")
    
    if len(h_arr) == 0:
        return {
            "is_stable": False,
            "stability_ratio": 0.0,
            "stable_count": 0,
            "total_count": 0,
            "outlier_indices": []
        }
    
    # Avoid division by zero; if fullbatch variance is 0, we cannot compute a meaningful ratio.
    # In such cases, we treat it as unstable unless heuristic is also 0 (perfect match).
    with np.errstate(divide='ignore', invalid='ignore'):
        ratios = np.where(f_arr != 0, h_arr / f_arr, np.inf)
        # If both are zero, ratio is technically 1 (stable), but division by zero gave inf.
        # Handle the case where both are zero explicitly
        both_zero = (h_arr == 0) & (f_arr == 0)
        ratios[both_zero] = 1.0
    
    # Check if ratios are within tolerance
    within_tolerance = (ratios >= tolerance_lower) & (ratios <= tolerance_upper)
    
    stable_count = int(np.sum(within_tolerance))
    total_count = len(h_arr)
    stability_ratio = stable_count / total_count if total_count > 0 else 0.0
    is_stable = stability_ratio >= stability_threshold
    
    outlier_indices = np.where(~within_tolerance)[0].tolist()
    
    return {
        "is_stable": bool(is_stable),
        "stability_ratio": float(stability_ratio),
        "stable_count": stable_count,
        "total_count": total_count,
        "outlier_indices": outlier_indices
    }

def run_sensitivity_analysis(
    heuristic_variances_dict: Dict[int, List[float]],
    fullbatch_variances_dict: Dict[int, List[float]],
    stability_tolerance_lower: float = 0.9,
    stability_tolerance_upper: float = 1.1,
    stability_threshold: float = 0.95
) -> Dict[int, Dict]:
    """
    Run sensitivity analysis for window size k (or any other parameter).
    
    Args:
        heuristic_variances_dict: Dictionary mapping parameter value (e.g., k) to list of heuristic variances.
        fullbatch_variances_dict: Dictionary mapping parameter value to list of full-batch variances.
        stability_tolerance_lower: Lower bound for stability ratio.
        stability_tolerance_upper: Upper bound for stability ratio.
        stability_threshold: Minimum fraction of steps required for stability.
        
    Returns:
        Dictionary mapping parameter value to stability check results.
    """
    results = {}
    for key in heuristic_variances_dict.keys():
        if key in fullbatch_variances_dict:
            results[key] = check_stability(
                heuristic_variances_dict[key],
                fullbatch_variances_dict[key],
                tolerance_lower=stability_tolerance_lower,
                tolerance_upper=stability_tolerance_upper,
                stability_threshold=stability_threshold
            )
        else:
            warnings.warn(f"Key {key} missing from fullbatch_variances_dict, skipping.")
    return results

def calculate_correlation_variance_error_pareto(
    variance_errors: Union[List[float], np.ndarray],
    pareto_distances: Union[List[float], np.ndarray]
) -> Dict[str, float]:
    """
    Calculate correlation between variance estimation error and distance to Pareto frontier.
    
    This implements the Plan's revised SC-002 success metric (Correlation) replacing 'coincidence'.
    
    Args:
        variance_errors: List or array of variance estimation errors (e.g., |heuristic - fullbatch|).
        pareto_distances: List or array of distances to the Pareto frontier.
        
    Returns:
        Dictionary containing:
            - 'correlation_coefficient': Pearson correlation coefficient.
            - 'p_value': p-value for the correlation test.
    """
    err_arr = np.array(variance_errors)
    dist_arr = np.array(pareto_distances)
    
    if err_arr.shape != dist_arr.shape:
        raise ValueError(f"Input arrays must have the same shape. Got {err_arr.shape} and {dist_arr.shape}")
    
    if len(err_arr) < 2:
        raise ValueError("Correlation calculation requires at least 2 samples.")
        
    corr_coef, p_val = stats.pearsonr(err_arr, dist_arr)
    
    return {
        "correlation_coefficient": float(corr_coef),
        "p_value": float(p_val)
    }
