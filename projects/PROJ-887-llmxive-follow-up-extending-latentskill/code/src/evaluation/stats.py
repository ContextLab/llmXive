import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from scipy import stats

from src.utils.config import get_project_root, get_results_path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_evaluation_results(results_path: Path) -> Dict[str, Any]:
    """Load evaluation results from a JSON file."""
    if not results_path.exists():
        raise FileNotFoundError(f"Evaluation results file not found: {results_path}")
    with open(results_path, 'r') as f:
        return json.load(f)

def extract_success_rates(evaluation_results: Dict[str, Any]) -> Dict[str, float]:
    """Extract success rates from evaluation results."""
    success_rates = {}
    for strategy, data in evaluation_results.items():
        if isinstance(data, dict) and 'success_rate' in data:
            success_rates[strategy] = data['success_rate']
        elif isinstance(data, list):
            # Calculate success rate from binary outcomes
            successes = sum(1 for x in data if x)
            total = len(data)
            success_rates[strategy] = successes / total if total > 0 else 0.0
    return success_rates

def perform_paired_test(group1: List[float], group2: List[float]) -> Tuple[float, float]:
    """Perform paired t-test or Wilcoxon signed-rank test."""
    if len(group1) != len(group2):
        raise ValueError("Groups must have the same length for paired test")
    if len(group1) < 2:
        raise ValueError("Need at least 2 samples for statistical test")

    # Check for normality (Shapiro-Wilk test)
    if len(group1) <= 30:
        _, p_normality = stats.shapiro(group1)
        _, p_normality2 = stats.shapiro(group2)
        use_t_test = p_normality > 0.05 and p_normality2 > 0.05
    else:
        use_t_test = True  # Assume normality for large samples

    if use_t_test:
        stat, p_value = stats.ttest_rel(group1, group2)
        test_type = "paired_t_test"
    else:
        stat, p_value = stats.wilcoxon(group1, group2)
        test_type = "wilcoxon_signed_rank"

    return p_value, test_type

def apply_benjamini_hochberg(p_values: List[float], alpha: float = 0.05) -> List[Tuple[int, float, bool]]:
    """Apply Benjamini-Hochberg correction to a list of p-values."""
    n = len(p_values)
    if n == 0:
        return []

    # Sort p-values and keep original indices
    sorted_indices = sorted(range(n), key=lambda i: p_values[i])
    sorted_p_values = [p_values[i] for i in sorted_indices]

    # Calculate BH critical values
    bh_thresholds = [(i + 1) / n * alpha for i in range(n)]

    # Find the largest k such that p_(k) <= threshold_(k)
    rejected = [False] * n
    for i in range(n - 1, -1, -1):
        if sorted_p_values[i] <= bh_thresholds[i]:
            for j in range(i + 1):
                rejected[sorted_indices[j]] = True
            break

    # Adjusted p-values (step-up procedure)
    adjusted_p_values = [0.0] * n
    min_adj = 1.0
    for i in range(n - 1, -1, -1):
        adj = min((n / (i + 1)) * sorted_p_values[i], min_adj)
        min_adj = min(min_adj, adj)
        adjusted_p_values[sorted_indices[i]] = min(adj, 1.0)

    return [(sorted_indices[i], adjusted_p_values[i], rejected[i]) for i in range(n)]

def calculate_statistical_power(n: int, effect_size: float, alpha: float = 0.05, two_tailed: bool = True) -> float:
    """
    Calculate statistical power for a t-test.
    Uses the non-central t-distribution approximation.
    """
    if n < 2:
        return 0.0

    # Degrees of freedom
    df = n - 1

    # Critical t-value
    if two_tailed:
        t_crit = stats.t.ppf(1 - alpha / 2, df)
    else:
        t_crit = stats.t.ppf(1 - alpha, df)

    # Non-centrality parameter
    ncp = effect_size * np.sqrt(n)

    # Calculate power using non-central t-distribution
    # Power = P(T > t_crit | H1) + P(T < -t_crit | H1) for two-tailed
    if two_tailed:
        power = 1 - stats.nct.cdf(t_crit, df, ncp) + stats.nct.cdf(-t_crit, df, ncp)
    else:
        power = 1 - stats.nct.cdf(t_crit, df, ncp)

    return float(power)

def compare_strategies(results: Dict[str, List[float]], baseline_strategy: str = "baseline") -> Dict[str, Dict[str, Any]]:
    """Compare all strategies against the baseline."""
    if baseline_strategy not in results:
        raise ValueError(f"Baseline strategy '{baseline_strategy}' not found in results")

    baseline_data = results[baseline_strategy]
    comparisons = {}

    for strategy, data in results.items():
        if strategy == baseline_strategy:
            continue

        if len(data) != len(baseline_data):
            logger.warning(f"Skipping {strategy}: length mismatch with baseline")
            continue

        p_value, test_type = perform_paired_test(baseline_data, data)
        effect_size = (np.mean(data) - np.mean(baseline_data)) / (np.std(baseline_data, ddof=1) or 1e-8)

        comparisons[strategy] = {
            "p_value": p_value,
            "test_type": test_type,
            "effect_size": effect_size,
            "mean_baseline": float(np.mean(baseline_data)),
            "mean_strategy": float(np.mean(data)),
            "std_baseline": float(np.std(baseline_data, ddof=1)),
            "std_strategy": float(np.std(data, ddof=1)),
            "n_samples": len(data)
        }

    return comparisons

def save_statistics_report(report: Dict[str, Any], output_path: Path) -> None:
    """Save the statistics report to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Statistics report saved to {output_path}")

def main():
    """Main function to run statistical analysis with power analysis check."""
    project_root = get_project_root()
    results_path = project_root / "data" / "results" / "evaluations.json"
    output_path = project_root / "data" / "results" / "stats_report.json"

    # Load evaluation results
    try:
        evaluation_results = load_evaluation_results(results_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        # Create a minimal report indicating failure
        report = {
            "status": "failed",
            "error": str(e),
            "power_analysis": None
        }
        save_statistics_report(report, output_path)
        return 1

    # Extract success rates for each strategy
    success_rates = extract_success_rates(evaluation_results)

    # Prepare raw data for comparisons (using the lists from eval results)
    comparison_data = {}
    for strategy, data in evaluation_results.items():
        if isinstance(data, list):
            comparison_data[strategy] = data
        elif isinstance(data, dict) and 'outcomes' in data:
            comparison_data[strategy] = data['outcomes']

    if not comparison_data:
        logger.error("No valid comparison data found in evaluation results")
        report = {
            "status": "failed",
            "error": "No valid comparison data found",
            "power_analysis": None
        }
        save_statistics_report(report, output_path)
        return 1

    # Perform comparisons against baseline
    baseline_strategy = "baseline" if "baseline" in comparison_data else next(iter(comparison_data.keys()))
    comparisons = compare_strategies(comparison_data, baseline_strategy)

    # Collect all p-values for BH correction
    all_p_values = [comp["p_value"] for comp in comparisons.values()]

    # Apply Benjamini-Hochberg correction
    if all_p_values:
        bh_results = apply_benjamini_hochberg(all_p_values)
        bh_corrected = {}
        for idx, adj_p, rejected in bh_results:
            strategy = list(comparisons.keys())[idx]
            bh_corrected[strategy] = {
                "adjusted_p_value": float(adj_p),
                "rejected_null": bool(rejected)
            }
            comparisons[strategy]["bh_adjusted_p_value"] = float(adj_p)
            comparisons[strategy]["rejected_null"] = bool(rejected)
    else:
        bh_corrected = {}

    # Calculate observed effect sizes and power
    observed_diffs = {}
    power_analysis_results = {}
    n_samples = None

    for strategy, comp in comparisons.items():
        mean_diff = comp["mean_strategy"] - comp["mean_baseline"]
        observed_diffs[strategy] = mean_diff
        n_samples = comp.get("n_samples", 0)

        # Calculate effect size (Cohen's d)
        pooled_std = np.sqrt((comp["std_baseline"]**2 + comp["std_strategy"]**2) / 2)
        if pooled_std > 0:
            effect_size = mean_diff / pooled_std
        else:
            effect_size = 0.0

        # Calculate statistical power
        if n_samples and n_samples > 1:
            power = calculate_statistical_power(n_samples, abs(effect_size))
        else:
            power = 0.0

        power_analysis_results[strategy] = {
            "observed_effect_size": float(effect_size),
            "observed_success_rate_diff": float(mean_diff),
            "n_samples": n_samples,
            "statistical_power": float(power),
            "power_threshold": 0.8,
            "power_adequate": bool(power >= 0.8),
            "recommendation": "Power adequate" if power >= 0.8 else f"Power low ({power:.2f}). Consider increasing N to {max(30, int(16 / (effect_size**2) if effect_size != 0 else 100))} for 80% power."
        }

    # Determine if overall power is adequate
    all_adequate = all(p["power_adequate"] for p in power_analysis_results.values()) if power_analysis_results else False

    # Compile final report
    report = {
        "status": "completed",
        "baseline_strategy": baseline_strategy,
        "comparisons": comparisons,
        "bh_corrected_p_values": bh_corrected,
        "power_analysis": {
            "all_adequate": all_adequate,
            "per_strategy": power_analysis_results,
            "default_effect_size_assumed": 0.5,
            "alpha": 0.05,
            "desired_power": 0.8
        },
        "summary": {
            "total_comparisons": len(comparisons),
            "significant_after_bh": sum(1 for c in comparisons.values() if c.get("rejected_null", False)),
            "power_adequate_count": sum(1 for p in power_analysis_results.values() if p["power_adequate"])
        }
    }

    # Save report
    save_statistics_report(report, output_path)

    # Log warnings for low power
    for strategy, p_analysis in power_analysis_results.items():
        if not p_analysis["power_adequate"]:
            logger.warning(f"Low power for {strategy}: {p_analysis['statistical_power']:.2f}. {p_analysis['recommendation']}")

    return 0

if __name__ == "__main__":
    sys.exit(main())