import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from scipy import stats

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_evaluation_results(filepath: Path) -> Dict[str, Any]:
    """
    Load evaluation results from a YAML/JSON file.
    Expected structure for sensitivity sweeps:
    {
      "sensitivity_sweep": {
        "k=1": {"strategy": "mean", "success_rates": [0.8, 0.85, ...]},
        "k=3": {"strategy": "mean", "success_rates": [...]},
        ...
      }
    }
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Evaluation results file not found: {filepath}")
    
    # Handle both YAML and JSON based on extension
    suffix = filepath.suffix.lower()
    if suffix == '.yaml' or suffix == '.yml':
        import yaml
        with open(filepath, 'r') as f:
            return yaml.safe_load(f)
    elif suffix == '.json':
        with open(filepath, 'r') as f:
            return json.load(f)
    else:
        # Try JSON first, then YAML
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            import yaml
            with open(filepath, 'r') as f:
                return yaml.safe_load(f)

def extract_sensitivity_success_rates(data: Dict[str, Any], metric: str = 'success_rate') -> Dict[str, List[float]]:
    """
    Extract success rates for each k value from sensitivity sweep data.
    Returns: {k_value: [rate1, rate2, ...]}
    """
    results = {}
    sweep_data = data.get('sensitivity_sweep', {})
    
    for k_key, k_data in sweep_data.items():
        # k_key is like "k=1", "k=3", etc.
        if isinstance(k_data, dict) and 'success_rates' in k_data:
            results[k_key] = k_data['success_rates']
        elif isinstance(k_data, dict) and metric in k_data:
            # If it's a single value, wrap it (though we expect lists from multiple trials)
            val = k_data[metric]
            if isinstance(val, list):
                results[k_key] = val
            else:
                results[k_key] = [val]
    
    return results

def benjamini_hochberg(p_values: List[float], alpha: float = 0.05) -> Tuple[List[bool], List[float]]:
    """
    Apply Benjamini-Hochberg correction for multiple hypothesis testing.
    
    Args:
        p_values: List of raw p-values from hypothesis tests
        alpha: Significance level (default 0.05)
    
    Returns:
        Tuple of (reject_h0_list, adjusted_p_values)
        - reject_h0_list: Boolean list indicating whether to reject H0 for each test
        - adjusted_p_values: List of BH-adjusted p-values
    """
    if not p_values:
        return [], []
    
    n = len(p_values)
    # Sort p-values while keeping track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p_values = np.array([p_values[i] for i in sorted_indices])
    
    # Calculate adjusted p-values
    adjusted_p_values = np.zeros(n)
    for i in range(n - 1, -1, -1):
        # BH adjustment: p_adj = p * n / rank
        rank = i + 1
        adjusted_p_values[i] = sorted_p_values[i] * n / rank
    
    # Ensure adjusted p-values are monotonically increasing (from smallest to largest)
    # We need to enforce that p_adj[i] <= p_adj[i+1] for sorted order
    for i in range(n - 2, -1, -1):
        adjusted_p_values[i] = min(adjusted_p_values[i], adjusted_p_values[i + 1])
    
    # Clip to [0, 1]
    adjusted_p_values = np.clip(adjusted_p_values, 0, 1)
    
    # Determine which hypotheses to reject
    reject_h0 = adjusted_p_values < alpha
    
    # Reorder back to original indices
    final_adjusted_p_values = np.zeros(n)
    final_reject = np.zeros(n, dtype=bool)
    
    for orig_idx, sorted_idx in enumerate(sorted_indices):
        final_adjusted_p_values[sorted_idx] = adjusted_p_values[orig_idx]
        final_reject[sorted_idx] = reject_h0[orig_idx]
    
    return final_reject.tolist(), final_adjusted_p_values.tolist()

def compare_sensitivity_sweeps(data: Dict[str, Any], baseline_k: str = "k=1", alpha: float = 0.05) -> Dict[str, Any]:
    """
    Compare success rates across different k values in a sensitivity sweep.
    Performs paired t-tests between baseline and each other k value,
    then applies Benjamini-Hochberg correction.
    
    Args:
        data: Evaluation results containing sensitivity sweep data
        baseline_k: The k value to use as baseline for comparison
        alpha: Significance level for BH correction
    
    Returns:
        Dictionary with test results, p-values, and BH-adjusted results
    """
    rates = extract_sensitivity_success_rates(data)
    
    if baseline_k not in rates:
        raise ValueError(f"Baseline k value '{baseline_k}' not found in sensitivity sweep data. Available: {list(rates.keys())}")
    
    baseline_rates = rates[baseline_k]
    comparisons = []
    p_values = []
    test_details = []
    
    for k_key, k_rates in rates.items():
        if k_key == baseline_k:
            continue
        
        # Ensure we have paired data (same number of trials)
        min_len = min(len(baseline_rates), len(k_rates))
        if min_len < 2:
            logger.warning(f"Not enough data points for comparison between {baseline_k} and {k_key}. Skipping.")
            continue
        
        paired_baseline = baseline_rates[:min_len]
        paired_k = k_rates[:min_len]
        
        # Perform paired t-test
        t_stat, p_val = stats.ttest_rel(paired_baseline, paired_k)
        
        comparisons.append({
            "baseline": baseline_k,
            "comparison": k_key,
            "t_statistic": float(t_stat),
            "p_value": float(p_val),
            "n_samples": min_len,
            "mean_baseline": float(np.mean(paired_baseline)),
            "mean_comparison": float(np.mean(paired_k))
        })
        
        p_values.append(p_val)
        test_details.append(f"Comparison {baseline_k} vs {k_key}: t={t_stat:.4f}, p={p_val:.4f}")
    
    # Apply Benjamini-Hochberg correction
    if p_values:
        reject_h0, adjusted_p_values = benjamini_hochberg(p_values, alpha)
        
        for i, comp in enumerate(comparisons):
            comp["adjusted_p_value"] = float(adjusted_p_values[i])
            comp["significant_after_bh"] = bool(reject_h0[i])
    else:
        adjusted_p_values = []
        reject_h0 = []
    
    return {
        "baseline_k": baseline_k,
        "comparisons": comparisons,
        "raw_p_values": [float(p) for p in p_values],
        "adjusted_p_values": [float(p) for p in adjusted_p_values],
        "significance_threshold": alpha,
        "tests_performed": len(comparisons),
        "significant_tests": sum(reject_h0) if reject_h0 else 0,
        "details": test_details
    }

def save_sensitivity_report(results: Dict[str, Any], output_path: Path) -> None:
    """
    Save the sensitivity sweep statistical analysis report to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Sensitivity sweep report saved to {output_path}")

def main():
    """
    Main entry point for T029b: Apply Benjamini-Hochberg correction for sensitivity sweeps.
    
    Reads sensitivity sweep results from data/results/sensitivity.yaml,
    performs statistical comparisons between k values, applies BH correction,
    and saves the report to data/results/sensitivity_stats.json.
    """
    # Define paths
    input_path = Path("data/results/sensitivity.yaml")
    output_path = Path("data/results/sensitivity_stats.json")
    
    logger.info(f"Loading sensitivity sweep data from {input_path}")
    
    try:
        data = load_evaluation_results(input_path)
    except Exception as e:
        logger.error(f"Failed to load sensitivity sweep data: {e}")
        sys.exit(1)
    
    logger.info("Extracting success rates for sensitivity sweep analysis")
    
    try:
        results = compare_sensitivity_sweeps(data, baseline_k="k=1", alpha=0.05)
    except Exception as e:
        logger.error(f"Failed to perform sensitivity sweep comparisons: {e}")
        sys.exit(1)
    
    logger.info(f"Performed {results['tests_performed']} comparisons, "
               f"{results['significant_tests']} significant after BH correction")
    
    logger.info(f"Saving report to {output_path}")
    save_sensitivity_report(results, output_path)
    
    # Print summary
    print("\n=== Sensitivity Sweep Statistical Analysis ===")
    print(f"Baseline k: {results['baseline_k']}")
    print(f"Tests performed: {results['tests_performed']}")
    print(f"Significant after BH correction: {results['significant_tests']}")
    print(f"Significance threshold: {results['significance_threshold']}")
    print("\nDetailed comparisons:")
    for comp in results['comparisons']:
        sig_marker = "***" if comp['significant_after_bh'] else ""
        print(f"  {comp['baseline']} vs {comp['comparison']}: "
             f"p={comp['p_value']:.4f} -> adj_p={comp['adjusted_p_value']:.4f} {sig_marker}")
    
    return results

if __name__ == "__main__":
    main()