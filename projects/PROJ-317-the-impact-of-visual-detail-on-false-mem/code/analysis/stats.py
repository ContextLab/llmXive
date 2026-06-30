import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
from scipy import stats
from statsmodels.stats.power import FTestAnovaPower

from config import get_project_root, get_processed_dir, get_data_dir

logger = logging.getLogger(__name__)

def calculate_anova_power(effect_size: float = 0.25, alpha: float = 0.05, power: float = 0.80) -> int:
    """
    Calculate the required sample size for a one-way repeated measures ANOVA.
    
    Args:
        effect_size: Cohen's f effect size (default: 0.25 for medium)
        alpha: Significance level (default: 0.05)
        power: Desired statistical power (default: 0.80)
        
    Returns:
        Required sample size (n)
    """
    # For repeated measures ANOVA, we use FTestAnovaPower
    # Note: This assumes a simple one-way design; for repeated measures,
    # we approximate using the standard F-test power calculation
    analysis = FTestAnovaPower()
    # n_groups is typically 3 for our design: baseline, enhanced, reduced
    n_groups = 3
    n = analysis.solve_power(
        effect_size=effect_size,
        n_groups=n_groups,
        alpha=alpha,
        power=power,
        alternative='larger'
    )
    return int(np.ceil(n))

def save_power_analysis(output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Calculate and save power analysis results to a JSON file.
    
    Args:
        output_path: Optional path to save the JSON file. If None, uses default path.
        
    Returns:
        Dictionary containing the power analysis results
    """
    project_root = get_project_root()
    if output_path is None:
        output_path = str(project_root / "data" / "processed" / "power_analysis.json")
    
    n = calculate_anova_power()
    result = {
        "alpha": 0.05,
        "power": 0.80,
        "effect_size": 0.25,
        "n_groups": 3,
        "required_sample_size": n,
        "description": "One-way repeated measures ANOVA power calculation"
    }
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Power analysis saved to {output_path}")
    return result

def run_repeated_measures_anova(data: Dict[str, List[float]], factor_name: str = "condition") -> Dict[str, Any]:
    """
    Perform a repeated measures ANOVA on the provided data.
    
    Args:
        data: Dictionary mapping condition names to lists of response values
        factor_name: Name of the within-subjects factor
        
    Returns:
        Dictionary containing ANOVA results
    """
    conditions = list(data.keys())
    n_conditions = len(conditions)
    
    if n_conditions < 2:
        raise ValueError("At least two conditions are required for ANOVA")
    
    # Convert data to arrays
    arrays = [np.array(data[cond]) for cond in conditions]
    lengths = [len(arr) for arr in arrays]
    
    if len(set(lengths)) > 1:
        # Handle unbalanced data by padding with NaN or truncating
        # For simplicity, we'll truncate to the minimum length
        min_len = min(lengths)
        arrays = [arr[:min_len] for arr in arrays]
    
    # Perform one-way ANOVA (approximation for repeated measures)
    # Note: For true repeated measures, we would need a more specialized test
    # like stats.f_oneway with correction, or use pingouin's rm_anova
    f_stat, p_val = stats.f_oneway(*arrays)
    
    # Calculate effect size (eta-squared)
    # eta^2 = SS_between / SS_total
    grand_mean = np.mean(np.concatenate(arrays))
    ss_between = sum(len(arr) * (np.mean(arr) - grand_mean)**2 for arr in arrays)
    ss_within = sum(np.sum((arr - np.mean(arr))**2) for arr in arrays)
    ss_total = ss_between + ss_within
    eta_squared = ss_between / ss_total if ss_total > 0 else 0.0
    
    result = {
        "factor_name": factor_name,
        "n_conditions": n_conditions,
        "n_per_condition": lengths[0] if lengths else 0,
        "f_statistic": float(f_stat),
        "p_value": float(p_val),
        "eta_squared": float(eta_squared),
        "significant": p_val < 0.05,
        "degrees_of_freedom": (n_conditions - 1, (lengths[0] - 1) * (n_conditions - 1)) if lengths else (0, 0)
    }
    
    return result

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Bonferroni correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values
        alpha: Significance level
        
    Returns:
        Dictionary containing corrected results
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return {"corrected_p_values": [], "significant_count": 0}
    
    adjusted_alpha = alpha / n_tests
    corrected_p_values = [min(p * n_tests, 1.0) for p in p_values]
    significant = [p < adjusted_alpha for p in corrected_p_values]
    
    result = {
        "n_tests": n_tests,
        "original_alpha": alpha,
        "adjusted_alpha": adjusted_alpha,
        "corrected_p_values": corrected_p_values,
        "significant_flags": significant,
        "significant_count": sum(significant)
    }
    
    return result

def save_bonferroni_results(result: Dict[str, Any], output_path: Optional[str] = None) -> None:
    """
    Save Bonferroni correction results to a JSON file.
    
    Args:
        result: Dictionary containing Bonferroni results
        output_path: Optional path to save the JSON file
    """
    project_root = get_project_root()
    if output_path is None:
        output_path = str(project_root / "data" / "processed" / "bonferroni_results.json")
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Bonferroni results saved to {output_path}")

def check_dataset_fit(mock_data: Dict[str, List[float]], target_distribution: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check if the mock data distribution matches the target distribution.
    
    This function compares the statistical properties of the generated mock data
    against a target distribution to ensure the dataset is suitable for analysis.
    
    Args:
        mock_data: Dictionary mapping condition names to lists of values
        target_distribution: Dictionary containing target parameters:
            - 'mean': target mean
            - 'std': target standard deviation
            - 'min_range': minimum acceptable range (Q3 - Q1)
            - 'sample_size': expected sample size per condition
        
    Returns:
        Dictionary containing fit assessment results
    """
    results = {
        "conditions": {},
        "overall_fit": True,
        "warnings": []
    }
    
    target_mean = target_distribution.get('mean', 0.5)
    target_std = target_distribution.get('std', 0.15)
    min_range = target_distribution.get('min_range', 0.3)
    expected_n = target_distribution.get('sample_size', 30)
    
    all_values = []
    for condition, values in mock_data.items():
        arr = np.array(values)
        all_values.extend(values)
        
        mean = float(np.mean(arr))
        std = float(np.std(arr))
        q1 = float(np.percentile(arr, 25))
        q3 = float(np.percentile(arr, 75))
        iqr = q3 - q1
        min_val = float(np.min(arr))
        max_val = float(np.max(arr))
        
        # Check against targets
        mean_diff = abs(mean - target_mean)
        std_diff = abs(std - target_std)
        
        condition_result = {
            "n": len(values),
            "mean": mean,
            "std": std,
            "q1": q1,
            "q3": q3,
            "iqr": iqr,
            "min": min_val,
            "max": max_val,
            "mean_diff_from_target": mean_diff,
            "std_diff_from_target": std_diff,
            "fit_mean": mean_diff < (target_std * 0.5),  # Within half a std
            "fit_std": std_diff < (target_std * 0.5),
            "fit_range": iqr >= min_range
        }
        
        results["conditions"][condition] = condition_result
        
        if not condition_result["fit_mean"]:
            results["warnings"].append(f"Condition '{condition}': Mean {mean:.3f} deviates significantly from target {target_mean:.3f}")
        if not condition_result["fit_std"]:
            results["warnings"].append(f"Condition '{condition}': Std {std:.3f} deviates significantly from target {target_std:.3f}")
        if not condition_result["fit_range"]:
            results["warnings"].append(f"Condition '{condition}': IQR {iqr:.3f} is below minimum threshold {min_range}")
    
    # Overall assessment
    if all_values:
        overall_mean = float(np.mean(all_values))
        overall_std = float(np.std(all_values))
        overall_q1 = float(np.percentile(all_values, 25))
        overall_q3 = float(np.percentile(all_values, 75))
        
        results["overall_statistics"] = {
            "total_n": len(all_values),
            "mean": overall_mean,
            "std": overall_std,
            "q1": overall_q1,
            "q3": overall_q3,
            "iqr": overall_q3 - overall_q1
        }
        
        # Check sample size
        for condition, data_list in mock_data.items():
            if len(data_list) < expected_n * 0.8:  # Allow 20% tolerance
                results["warnings"].append(f"Condition '{condition}': Sample size {len(data_list)} is below expected {expected_n}")
    
    results["overall_fit"] = len(results["warnings"]) == 0
    
    return results

def main():
    """
    Main entry point for running power analysis and dataset fit checks.
    """
    # Run power analysis
    logger.info("Running power analysis...")
    power_result = save_power_analysis()
    logger.info(f"Required sample size: {power_result['required_sample_size']}")
    
    # Example dataset fit check (placeholder for actual data)
    # In a real scenario, this would be called with actual mock data
    logger.info("Dataset fit check function available via check_dataset_fit()")
    
    return power_result

if __name__ == "__main__":
    main()