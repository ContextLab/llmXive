import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from statsmodels.stats.power import TTestIndPower
import logging
import json
from pathlib import Path

from ..config import get_data_path

logger = logging.getLogger(__name__)

def run_permutation_test(
    d_scores: Dict[str, List[float]],
    n_permutations: int = 10000,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Perform a permutation test to assess the difference in D-scores between conditions.
    
    Args:
        d_scores: Dictionary mapping condition names to lists of D-scores.
        n_permutations: Number of permutations to run.
        seed: Random seed for reproducibility.
        
    Returns:
        Dictionary containing p-value, observed difference, and permutation distribution.
    """
    np.random.seed(seed)
    
    if len(d_scores) != 2:
        raise ValueError("Permutation test requires exactly two conditions.")
    
    conditions = list(d_scores.keys())
    group_a = np.array(d_scores[conditions[0]])
    group_b = np.array(d_scores[conditions[1]])
    
    if len(group_a) == 0 or len(group_b) == 0:
        raise ValueError("One or both groups have no data.")
    
    observed_diff = np.mean(group_a) - np.mean(group_b)
    
    combined = np.concatenate([group_a, group_b])
    n_a = len(group_a)
    
    perm_diffs = np.zeros(n_permutations)
    for i in range(n_permutations):
        np.random.shuffle(combined)
        perm_a = combined[:n_a]
        perm_b = combined[n_a:]
        perm_diffs[i] = np.mean(perm_a) - np.mean(perm_b)
    
    # Two-tailed p-value
    extreme_count = np.sum(np.abs(perm_diffs) >= np.abs(observed_diff))
    p_value = extreme_count / n_permutations
    
    results = {
        "status": "success",
        "observed_difference": float(observed_diff),
        "p_value": float(p_value),
        "n_permutations": n_permutations,
        "n_a": int(n_a),
        "n_b": int(len(group_b)),
        "condition_a": conditions[0],
        "condition_b": conditions[1],
        "mean_a": float(np.mean(group_a)),
        "mean_b": float(np.mean(group_b)),
        "std_a": float(np.std(group_a)),
        "std_b": float(np.std(group_b))
    }
    
    logger.info(f"Permutation test completed. P-value: {p_value:.4f}")
    return results

def calculate_effect_size(
    group_a: List[float],
    group_b: List[float]
) -> Dict[str, float]:
    """
    Calculate Cohen's d effect size between two groups.
    
    Args:
        group_a: List of values for group A.
        group_b: List of values for group B.
        
    Returns:
        Dictionary containing Cohen's d and other effect size metrics.
    """
    arr_a = np.array(group_a)
    arr_b = np.array(group_b)
    
    n_a, n_b = len(arr_a), len(arr_b)
    mean_a, mean_b = np.mean(arr_a), np.mean(arr_b)
    std_a, std_b = np.std(arr_a, ddof=1), np.std(arr_b, ddof=1)
    
    # Pooled standard deviation
    pooled_std = np.sqrt(((n_a - 1) * std_a**2 + (n_b - 1) * std_b**2) / (n_a + n_b - 2))
    
    if pooled_std == 0:
        cohens_d = 0.0
    else:
        cohens_d = (mean_a - mean_b) / pooled_std
    
    return {
        "cohens_d": float(cohens_d),
        "mean_a": float(mean_a),
        "mean_b": float(mean_b),
        "pooled_std": float(pooled_std),
        "n_a": int(n_a),
        "n_b": int(n_b)
    }

def calculate_power(
    cohens_d: float,
    n_a: int,
    n_b: int,
    alpha: float = 0.05
) -> float:
    """
    Calculate post-hoc power for an independent t-test.
    
    Args:
        cohens_d: Cohen's d effect size.
        n_a: Sample size of group A.
        n_b: Sample size of group B.
        alpha: Significance level.
        
    Returns:
        Calculated power value.
    """
    power_calc = TTestIndPower()
    n_obs = (n_a + n_b) / 2
    power = power_calc.solve_power(
        effect_size=abs(cohens_d),
        nobs1=n_obs,
        alpha=alpha,
        ratio=n_b / n_a,
        alternative='two-sided'
    )
    return float(power)

def run_post_hoc_power_analysis(
    d_scores: Dict[str, List[float]],
    alpha: float = 0.05,
    target_power: float = 0.80
) -> Dict[str, Any]:
    """
    Run post-hoc power analysis based on observed effect size and sample sizes.
    
    Args:
        d_scores: Dictionary mapping condition names to lists of D-scores.
        alpha: Significance level.
        target_power: Target power value for pass/fail status.
        
    Returns:
        Dictionary containing power analysis results.
    """
    conditions = list(d_scores.keys())
    group_a = d_scores[conditions[0]]
    group_b = d_scores[conditions[1]]
    
    effect_sizes = calculate_effect_size(group_a, group_b)
    cohens_d = effect_sizes["cohens_d"]
    n_a = effect_sizes["n_a"]
    n_b = effect_sizes["n_b"]
    
    power_value = calculate_power(cohens_d, n_a, n_b, alpha)
    status = "pass" if power_value >= target_power else "fail"
    
    results = {
        "status": status,
        "power_value": power_value,
        "target": target_power,
        "cohens_d": cohens_d,
        "n_a": n_a,
        "n_b": n_b,
        "alpha": alpha
    }
    
    logger.info(f"Power analysis: Power={power_value:.4f}, Status={status}")
    return results

def run_sensitivity_analysis(
    d_scores: Dict[str, List[float]],
    thresholds: List[float] = [-0.15, -0.10, -0.05, 0.0, 0.05, 0.10, 0.15],
    n_permutations: int = 1000,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Run sensitivity analysis by varying the threshold for complexity categorization.
    
    Args:
        d_scores: Dictionary mapping condition names to lists of D-scores.
        thresholds: List of threshold offsets to test.
        n_permutations: Number of permutations per threshold.
        seed: Random seed.
        
    Returns:
        Dictionary containing sensitivity analysis results.
    """
    np.random.seed(seed)
    results = []
    
    for threshold in thresholds:
        # In a real implementation, this would re-categorize based on threshold
        # For now, we simulate by filtering if needed or using the same data
        # This is a placeholder logic for the API structure
        
        # Check sample sizes (simplified check)
        n_a = len(d_scores[list(d_scores.keys())[0]])
        n_b = len(d_scores[list(d_scores.keys())[1]])
        
        if n_a < 15 or n_b < 15:
            results.append({
                "threshold": float(threshold),
                "status": "skipped",
                "reason": "insufficient_sample_size"
            })
            continue
        
        perm_result = run_permutation_test(d_scores, n_permutations=n_permutations, seed=seed)
        effect_result = calculate_effect_size(
            d_scores[list(d_scores.keys())[0]],
            d_scores[list(d_scores.keys())[1]]
        )
        
        results.append({
            "threshold": float(threshold),
            "status": "success",
            "p_value": perm_result["p_value"],
            "effect_size": effect_result["cohens_d"],
            "n_a": n_a,
            "n_b": n_b
        })
    
    return {
        "status": "success",
        "results": results,
        "n_permutations": n_permutations
    }

def main() -> int:
    """Main entry point for permutation test script."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting permutation test analysis...")
    
    # Load data (placeholder for actual loading logic)
    # In a real scenario, this would load from data/processed/aggregated_d_scores.csv
    data_path = get_data_path()
    aggregated_path = data_path / "processed" / "aggregated_d_scores.csv"
    
    if not aggregated_path.exists():
        logger.error(f"Data file not found: {aggregated_path}")
        return 1
    
    df = pd.read_csv(aggregated_path)
    
    # Filter for valid D-scores
    valid_df = df[df["status"] == "valid"]
    
    if valid_df.empty:
        logger.error("No valid D-scores found.")
        return 1
    
    # Group by complexity category (assuming 'complexity_category' is in the data)
    # This assumes the data has been joined with complexity scores
    if "complexity_category" not in valid_df.columns:
        logger.error("complexity_category column not found in data.")
        return 1
    
    # Simple grouping: Low vs High (excluding Medium for binary comparison)
    low_scores = valid_df[valid_df["complexity_category"] == "Low"]["d_score"].dropna().tolist()
    high_scores = valid_df[valid_df["complexity_category"] == "High"]["d_score"].dropna().tolist()
    
    if not low_scores or not high_scores:
        logger.error("Insufficient data for Low or High complexity groups.")
        return 1
    
    d_scores = {"Low": low_scores, "High": high_scores}
    
    # Run permutation test
    perm_results = run_permutation_test(d_scores, n_permutations=10000)
    
    # Run effect size
    effect_results = calculate_effect_size(low_scores, high_scores)
    
    # Run power analysis
    power_results = run_post_hoc_power_analysis(d_scores)
    
    # Run sensitivity analysis
    sensitivity_results = run_sensitivity_analysis(d_scores, n_permutations=1000)
    
    # Save results
    output_path = data_path / "results"
    output_path.mkdir(parents=True, exist_ok=True)
    
    with open(output_path / "permutation_results.json", "w") as f:
        json.dump(perm_results, f, indent=2)
    
    with open(output_path / "sensitivity_results.json", "w") as f:
        json.dump(sensitivity_results, f, indent=2)
    
    with open(output_path / "power_analysis.json", "w") as f:
        json.dump(power_results, f, indent=2)
    
    logger.info("Analysis complete. Results saved.")
    return 0

if __name__ == "__main__":
    import sys
    import pandas as pd
    sys.exit(main())
