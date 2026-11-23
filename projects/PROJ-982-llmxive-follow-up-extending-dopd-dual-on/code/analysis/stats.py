"""
Statistical analysis module for DOPD vs Uniform supervision comparison.

Implements Mann-Whitney U tests, effect size calculations (Cliff's delta),
and Coefficient of Variation (CV) for reproducibility metrics.
"""
import numpy as np
import json
import os
from typing import Dict, Any, Optional, Tuple, List
from scipy.stats import mannwhitneyu
from utils.logging import TrainingLogger

def load_accuracy_logs(log_dir: str) -> Dict[str, List[float]]:
    """
    Load accuracy logs from JSON files in the specified directory.
    
    Args:
        log_dir: Path to directory containing log files.
        
    Returns:
        Dictionary mapping regime names to lists of accuracy values.
    """
    results = {"DOPD": [], "Uniform": []}
    
    if not os.path.exists(log_dir):
        raise FileNotFoundError(f"Log directory not found: {log_dir}")
        
    for filename in os.listdir(log_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(log_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    
                    # Determine regime from filename or content
                    regime = None
                    if "dopd" in filename.lower():
                        regime = "DOPD"
                    elif "uniform" in filename.lower():
                        regime = "Uniform"
                    elif "regime" in data:
                        regime = data["regime"]
                        
                    if regime and regime in results:
                        # Extract accuracy values
                        if "final_accuracy" in data:
                            results[regime].append(data["final_accuracy"])
                        elif "accuracies" in data:
                            results[regime].extend(data["accuracies"])
                        elif "metrics" in data and "accuracy" in data["metrics"]:
                            results[regime].append(data["metrics"]["accuracy"])
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Could not parse {filename}: {e}")
                
    return results

def calculate_effect_size(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Calculate Cliff's delta effect size between two independent groups.
    
    Cliff's delta measures the probability that a random value from group1
    is greater than a random value from group2, minus the reverse probability.
    
    Formula: delta = (P(x > y) + 0.5 * P(x == y)) - P(y > x)
    Range: [-1, 1] where 0 indicates no effect.
    
    Args:
        group1: First group of values (e.g., DOPD accuracies).
        group2: Second group of values (e.g., Uniform accuracies).
        
    Returns:
        Cliff's delta effect size value.
    """
    if len(group1) == 0 or len(group2) == 0:
        raise ValueError("Both groups must have at least one value")
        
    n1, n2 = len(group1), len(group2)
    count_greater = 0
    count_less = 0
    count_equal = 0
    
    for x in group1:
        for y in group2:
            if x > y:
                count_greater += 1
            elif x < y:
                count_less += 1
            else:
                count_equal += 1
                
    total = n1 * n2
    delta = (count_greater + 0.5 * count_equal - count_less) / total
    
    return delta

def calculate_coefficient_of_variation(group: np.ndarray) -> float:
    """
    Calculate the Coefficient of Variation (CV) for a group.
    
    CV = (Standard Deviation / Mean) * 100
    Measures relative variability independent of the unit of measurement.
    
    Args:
        group: Array of values.
        
    Returns:
        Coefficient of Variation as a percentage.
    """
    if len(group) == 0:
        raise ValueError("Group must have at least one value")
        
    mean = np.mean(group)
    if mean == 0:
        raise ValueError("Cannot calculate CV when mean is zero")
        
    std = np.std(group, ddof=1)  # Sample standard deviation
    cv = (std / abs(mean)) * 100
    
    return cv

def run_mann_whitney_test(group1: np.ndarray, group2: np.ndarray) -> Tuple[float, float, str]:
    """
    Run a one-tailed Mann-Whitney U test comparing two independent groups.
    
    H0: mean(group1) <= mean(group2)
    H1: mean(group1) > mean(group2)
    
    Args:
        group1: First group (e.g., DOPD accuracies).
        group2: Second group (e.g., Uniform accuracies).
        
    Returns:
        Tuple of (statistic, p_value, interpretation).
    """
    if len(group1) < 2 or len(group2) < 2:
        raise ValueError("Both groups must have at least 2 values for Mann-Whitney U test")
        
    # Use 'greater' alternative for one-tailed test
    statistic, p_value = mannwhitneyu(group1, group2, alternative='greater')
    
    # Interpretation
    if p_value < 0.05:
        interpretation = "Reject H0: DOPD significantly outperforms Uniform"
    else:
        interpretation = "Fail to reject H0: No significant difference"
        
    return statistic, p_value, interpretation

def analyze_generalization_results(
    dopd_accuracies: List[float],
    uniform_accuracies: List[float],
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Perform comprehensive statistical analysis of generalization results.
    
    This function:
    1. Runs Mann-Whitney U test
    2. Calculates Cliff's delta effect size
    3. Computes Coefficient of Variation for reproducibility
    4. Logs exploratory status if effect size is small (< 0.5)
    
    Args:
        dopd_accuracies: List of DOPD regime accuracies.
        uniform_accuracies: List of Uniform regime accuracies.
        output_path: Optional path to save results as JSON.
        
    Returns:
        Dictionary containing all analysis results.
    """
    dopd_arr = np.array(dopd_accuracies)
    uniform_arr = np.array(uniform_accuracies)
    
    if len(dopd_arr) == 0 or len(uniform_arr) == 0:
        raise ValueError("Both accuracy lists must be non-empty")
        
    # Mann-Whitney U test
    u_stat, p_value, interpretation = run_mann_whitney_test(dopd_arr, uniform_arr)
    
    # Effect size (Cliff's delta)
    effect_size = calculate_effect_size(dopd_arr, uniform_arr)
    
    # Coefficient of Variation for reproducibility
    cv_dopd = calculate_coefficient_of_variation(dopd_arr)
    cv_uniform = calculate_coefficient_of_variation(uniform_arr)
    
    # Exploratory status check per FR-005
    is_exploratory = abs(effect_size) < 0.5
    status = "EXPLORATORY" if is_exploratory else "CONFIRMED"
    
    # Summary statistics
    results = {
        "sample_sizes": {
            "dopd": len(dopd_arr),
            "uniform": len(uniform_arr)
        },
        "descriptive_statistics": {
            "dopd": {
                "mean": float(np.mean(dopd_arr)),
                "std": float(np.std(dopd_arr, ddof=1)),
                "min": float(np.min(dopd_arr)),
                "max": float(np.max(dopd_arr)),
                "cv_percent": float(cv_dopd)
            },
            "uniform": {
                "mean": float(np.mean(uniform_arr)),
                "std": float(np.std(uniform_arr, ddof=1)),
                "min": float(np.min(uniform_arr)),
                "max": float(np.max(uniform_arr)),
                "cv_percent": float(cv_uniform)
            }
        },
        "mann_whitney_test": {
            "statistic": float(u_stat),
            "p_value": float(p_value),
            "interpretation": interpretation,
            "significant_at_0.05": p_value < 0.05
        },
        "effect_size": {
            "cliffs_delta": float(effect_size),
            "magnitude": "small" if abs(effect_size) < 0.3 else "medium" if abs(effect_size) < 0.5 else "large",
            "is_exploratory": is_exploratory,
            "status": status
        },
        "reproducibility": {
            "dopd_cv_percent": float(cv_dopd),
            "uniform_cv_percent": float(cv_uniform),
            "cv_difference": float(abs(cv_dopd - cv_uniform))
        },
        "analysis_summary": {
            "hypothesis": "DOPD generalization accuracy > Uniform generalization accuracy",
            "conclusion": interpretation,
            "effect_magnitude": f"{status} (|δ| = {abs(effect_size):.3f})",
            "recommendation": "Proceed with confidence" if not is_exploratory and p_value < 0.05 else "Requires further investigation"
        }
    }
    
    # Save results if output path provided
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
    return results

def analyze_generalization_results_from_logs(
    log_dir: str,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to load logs and run analysis in one step.
    
    Args:
        log_dir: Directory containing experiment log files.
        output_path: Optional path to save results.
        
    Returns:
        Analysis results dictionary.
    """
    logs = load_accuracy_logs(log_dir)
    
    if not logs["DOPD"] or not logs["Uniform"]:
        raise ValueError("Could not find sufficient data for both regimes in logs")
        
    return analyze_generalization_results(
        logs["DOPD"],
        logs["Uniform"],
        output_path
    )