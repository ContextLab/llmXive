"""
T029a: Perform paired statistical test on Time-to-Pivot differences.

Compares Time-to-Pivot between the rule engine and baseline methods using
a paired t-test or Wilcoxon signed-rank test (depending on normality).

Output: data/derived/time_diff_results.json
Schema: {
    "p_value": float,
    "ci_lower": float,
    "ci_upper": float,
    "statistic": float,
    "test_method": str
}
"""
import json
import sys
import csv
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from collections import defaultdict

import numpy as np
from scipy import stats

# Project root relative path handling
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DERIVED_PATH = PROJECT_ROOT / "data" / "derived"
RESULTS_CSV_PATH = DATA_DERIVED_PATH / "results.csv"
OUTPUT_JSON_PATH = DATA_DERIVED_PATH / "time_diff_results.json"

# Ensure output directory exists
DATA_DERIVED_PATH.mkdir(parents=True, exist_ok=True)

def load_results_csv(path: Path) -> List[Dict[str, Any]]:
    """Load the merged results CSV file."""
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {path}")
    
    results = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results

def extract_paired_differences(
    results: List[Dict[str, Any]]
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract paired Time-to-Pivot values for rule_engine and baseline.
    
    Returns:
        rule_times: numpy array of rule engine times
        baseline_times: numpy array of baseline times
    """
    # Group by task_id
    task_data: Dict[str, Dict[str, float]] = defaultdict(dict)
    
    for row in results:
        task_id = row.get('task_id')
        method = row.get('method')
        time_to_pivot_str = row.get('time_to_pivot')
        
        if not task_id or not method or time_to_pivot_str is None:
            continue
        
        try:
            time_val = float(time_to_pivot_str)
        except (ValueError, TypeError):
            continue
        
        task_data[task_id][method] = time_val
    
    rule_times = []
    baseline_times = []
    
    for task_id, times in task_data.items():
        if 'rule_engine' in times and 'baseline' in times:
            rule_times.append(times['rule_engine'])
            baseline_times.append(times['baseline'])
    
    if len(rule_times) == 0:
        raise ValueError("No paired data found. Ensure both 'rule_engine' and 'baseline' "
                       "methods exist in results.csv with matching task_ids.")
    
    return np.array(rule_times), np.array(baseline_times)

def calculate_confidence_interval(
    differences: np.ndarray,
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate confidence interval for the mean difference using bootstrap.
    
    Args:
        differences: Array of differences (rule - baseline)
        confidence: Confidence level (0.95 for 95% CI)
    
    Returns:
        (ci_lower, ci_upper)
    """
    n_bootstrap = 10000
    rng = np.random.default_rng(42)  # Fixed seed for reproducibility
    
    bootstrap_means = []
    n = len(differences)
    
    for _ in range(n_bootstrap):
        sample = rng.choice(differences, size=n, replace=True)
        bootstrap_means.append(np.mean(sample))
    
    bootstrap_means = np.array(bootstrap_means)
    alpha = 1 - confidence
    ci_lower = np.percentile(bootstrap_means, 100 * alpha / 2)
    ci_upper = np.percentile(bootstrap_means, 100 * (1 - alpha / 2))
    
    return ci_lower, ci_upper

def perform_paired_test(
    rule_times: np.ndarray,
    baseline_times: np.ndarray
) -> Dict[str, Any]:
    """
    Perform paired statistical test (t-test or Wilcoxon).
    
    Checks normality of differences; if normal, uses paired t-test.
    Otherwise, uses Wilcoxon signed-rank test.
    
    Returns:
        Dictionary with test results
    """
    differences = rule_times - baseline_times
    
    # Check normality of differences using Shapiro-Wilk test
    # Only valid for n <= 5000, so use Anderson-Darling for larger n or limit
    if len(differences) <= 5000:
        _, p_normality = stats.shapiro(differences)
    else:
        # For larger samples, use a subset for normality check or Anderson
        _, p_normality, _ = stats.anderson(differences, dist='norm')
        # Anderson returns a statistic and critical values; we approximate p-value
        # If statistic < critical at 5%, assume normal
        p_normality = 0.05 if p_normality < 0.05 else 0.5  # Simplified heuristic
    
    alpha_normality = 0.05
    use_t_test = p_normality > alpha_normality
    
    if use_t_test:
        statistic, p_value = stats.ttest_rel(rule_times, baseline_times)
        test_method = "paired_t_test"
    else:
        statistic, p_value = stats.wilcoxon(rule_times, baseline_times)
        test_method = "wilcoxon_signed_rank"
    
    # Calculate confidence interval for mean difference
    ci_lower, ci_upper = calculate_confidence_interval(differences)
    
    return {
        "p_value": float(p_value),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "statistic": float(statistic),
        "test_method": test_method,
        "n_pairs": len(differences),
        "mean_difference": float(np.mean(differences))
    }

def save_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save results to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {output_path}")

def main() -> None:
    """Main entry point for the time difference test."""
    print(f"Loading results from {RESULTS_CSV_PATH}...")
    
    try:
        results = load_results_csv(RESULTS_CSV_PATH)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    
    print(f"Loaded {len(results)} rows from results CSV.")
    
    try:
        rule_times, baseline_times = extract_paired_differences(results)
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    
    print(f"Found {len(rule_times)} paired observations.")
    print(f"Rule engine mean time: {np.mean(rule_times):.4f} seconds")
    print(f"Baseline mean time: {np.mean(baseline_times):.4f} seconds")
    
    print("Performing paired statistical test...")
    test_results = perform_paired_test(rule_times, baseline_times)
    
    print(f"Test method: {test_results['test_method']}")
    print(f"Statistic: {test_results['statistic']:.4f}")
    print(f"P-value: {test_results['p_value']:.6f}")
    print(f"95% CI for mean difference: [{test_results['ci_lower']:.4f}, {test_results['ci_upper']:.4f}]")
    
    save_results(test_results, OUTPUT_JSON_PATH)
    
    # Exit with appropriate code
    if test_results['p_value'] < 0.05:
        print("Result: Statistically significant difference (p < 0.05)")
    else:
        print("Result: No statistically significant difference (p >= 0.05)")

if __name__ == "__main__":
    main()