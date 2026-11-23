"""
Power Analysis Module for llmXive Research Pipeline.

This module implements post-hoc power analysis on accuracy distributions
derived from the baseline and heuristic strategy experiments.

It calculates:
1. Effect Size (Cohen's d) between paired samples.
2. Statistical Power based on the calculated t-statistic and effect size.
3. Aggregate power analysis across multiple comparisons.
"""

import os
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from scipy import stats
from scipy.stats import ttest_rel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Load a JSON file containing statistical test results.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Dictionary containing the JSON data, or None if file not found.
    """
    path = Path(file_path)
    if not path.exists():
        logger.error(f"File not found: {file_path}")
        return None
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {file_path}: {e}")
        return None


def load_csv_accuracies(file_path: str, column: str = 'accuracy') -> Optional[List[float]]:
    """
    Load accuracy values from a CSV file.

    Args:
        file_path: Path to the CSV file.
        column: Name of the column containing accuracy values.

    Returns:
        List of accuracy values, or None if file not found or error.
    """
    import csv
    path = Path(file_path)
    if not path.exists():
        logger.error(f"File not found: {file_path}")
        return None
    
    accuracies = []
    try:
        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if column in row:
                    try:
                        val = float(row[column])
                        if not np.isnan(val):
                            accuracies.append(val)
                    except ValueError:
                        continue
    except Exception as e:
        logger.error(f"Error reading CSV {file_path}: {e}")
        return None
    
    if not accuracies:
        logger.warning(f"No valid accuracy values found in {file_path}")
        return None
    
    return accuracies


def calculate_effect_size(sample1: List[float], sample2: List[float], paired: bool = True) -> float:
    """
    Calculate Cohen's d effect size for two samples.

    For paired samples, it calculates the effect size based on the
    differences between pairs.

    Args:
        sample1: First sample (e.g., Baseline accuracies).
        sample2: Second sample (e.g., Heuristic accuracies).
        paired: Whether the samples are paired (default True).

    Returns:
        Cohen's d effect size.
    """
    if len(sample1) != len(sample2):
        logger.warning("Sample lengths differ. Paired assumption may be invalid.")
        # If not paired, we can't easily align them without an ID, 
        # but for this analysis we assume alignment by index or task order.
    
    if paired:
        diffs = np.array(sample1) - np.array(sample2)
        mean_diff = np.mean(diffs)
        std_diff = np.std(diffs, ddof=1)
        if std_diff == 0:
            return 0.0
        return mean_diff / std_diff
    else:
        # Unpaired Cohen's d (pooled standard deviation)
        n1, n2 = len(sample1), len(sample2)
        mean1, mean2 = np.mean(sample1), np.mean(sample2)
        var1, var2 = np.var(sample1, ddof=1), np.var(sample2, ddof=1)
        
        pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
        if pooled_std == 0:
            return 0.0
        return (mean1 - mean2) / pooled_std


def calculate_power_from_tstat(t_stat: float, df: int, alpha: float = 0.05) -> float:
    """
    Calculate statistical power given a t-statistic and degrees of freedom.
    Uses the non-central t-distribution approximation.

    Args:
        t_stat: The calculated t-statistic.
        df: Degrees of freedom.
        alpha: Significance level (default 0.05).

    Returns:
        Estimated statistical power (0.0 to 1.0).
    """
    # Critical t-value for two-tailed test
    t_crit = stats.t.ppf(1 - alpha / 2, df)
    
    # Calculate non-centrality parameter (approx)
    # For a paired t-test, non-centrality parameter delta = t_stat
    # Power is P(|T| > t_crit | delta)
    # We approximate using the cumulative distribution of the non-central t
    
    # Using the survival function for the upper tail and CDF for lower
    # Power = P(T > t_crit) + P(T < -t_crit) under the alternative hypothesis
    # The alternative hypothesis distribution is non-central t with ncp = t_stat (approx)
    
    # More precise calculation using non-central t CDF
    # Power = 1 - (CDF(t_crit) - CDF(-t_crit)) under non-central t
    # Note: scipy.stats.nct.cdf(x, df, nc)
    
    cdf_upper = stats.nct.cdf(t_crit, df, t_stat)
    cdf_lower = stats.nct.cdf(-t_crit, df, t_stat)
    
    power = 1.0 - (cdf_upper - cdf_lower)
    return float(power)


def calculate_power_from_effect_size(effect_size: float, n: int, alpha: float = 0.05, two_tailed: bool = True) -> float:
    """
    Calculate power given effect size and sample size.
    Uses the standard approximation for t-tests.

    Args:
        effect_size: Cohen's d.
        n: Sample size (number of pairs).
        alpha: Significance level.
        two_tailed: Whether the test is two-tailed.

    Returns:
        Estimated statistical power.
    """
    if n <= 1:
        return 0.0
    
    df = n - 1
    # Non-centrality parameter
    ncp = effect_size * np.sqrt(n)
    
    t_crit = stats.t.ppf(1 - alpha / 2, df)
    
    cdf_upper = stats.nct.cdf(t_crit, df, ncp)
    cdf_lower = stats.nct.cdf(-t_crit, df, ncp)
    
    power = 1.0 - (cdf_upper - cdf_lower)
    return float(power)


def analyze_comparison(
    baseline_acc: List[float],
    heuristic_acc: List[float],
    heuristic_name: str,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform a complete power analysis for a single comparison.

    Args:
        baseline_acc: List of baseline accuracies.
        heuristic_acc: List of heuristic accuracies.
        heuristic_name: Name of the heuristic strategy.
        alpha: Significance level.

    Returns:
        Dictionary containing analysis results.
    """
    if len(baseline_acc) != len(heuristic_acc):
        logger.error(f"Length mismatch for {heuristic_name}: Baseline={len(baseline_acc)}, Heuristic={len(heuristic_acc)}")
        return {
            "heuristic": heuristic_name,
            "status": "error",
            "error": "Length mismatch between baseline and heuristic samples"
        }
    
    n = len(baseline_acc)
    if n < 2:
        return {
            "heuristic": heuristic_name,
            "status": "error",
            "error": "Insufficient sample size (n < 2)"
        }
    
    # 1. Perform Paired T-Test (or Wilcoxon if normality fails, but for power analysis we often assume t-test context)
    # We use ttest_rel as the primary metric for power calculation here.
    t_stat, p_val = ttest_rel(baseline_acc, heuristic_acc)
    
    # 2. Calculate Effect Size (Cohen's d for paired)
    effect_size = calculate_effect_size(baseline_acc, heuristic_acc, paired=True)
    
    # 3. Calculate Power from T-Statistic
    df = n - 1
    power_from_t = calculate_power_from_tstat(t_stat, df, alpha)
    
    # 4. Calculate Power from Effect Size (Cross-check)
    power_from_d = calculate_power_from_effect_size(effect_size, n, alpha)
    
    # Determine significance
    is_significant = p_val < alpha
    
    result = {
        "heuristic": heuristic_name,
        "n": n,
        "mean_baseline": float(np.mean(baseline_acc)),
        "mean_heuristic": float(np.mean(heuristic_acc)),
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "is_significant": is_significant,
        "effect_size_cohens_d": float(effect_size),
        "power_from_t_stat": float(power_from_t),
        "power_from_effect_size": float(power_from_d),
        "alpha": alpha,
        "df": df,
        "status": "success"
    }
    
    logger.info(f"Power analysis for {heuristic_name}: Power={power_from_t:.3f}, Effect={effect_size:.3f}, p={p_val:.4f}")
    return result


def run_power_analysis(
    stats_clean_path: str,
    stats_noisy_path: str,
    baseline_clean_path: str,
    lazy_clean_path: str,
    greedy_clean_path: str,
    baseline_noisy_path: str,
    lazy_noisy_path: str,
    greedy_noisy_path: str,
    output_path: str
) -> None:
    """
    Orchestrates the power analysis for both clean and noisy datasets.

    Args:
        stats_clean_path: Path to stats_clean.json (optional, for reference).
        stats_noisy_path: Path to stats_noisy.json (optional, for reference).
        baseline_clean_path: Path to baseline_results.csv.
        lazy_clean_path: Path to lazy_results.csv.
        greedy_clean_path: Path to greedy_results.csv.
        baseline_noisy_path: Path to noisy_baseline_results.csv.
        lazy_noisy_path: Path to lazy_noisy_results.csv (or equivalent).
        greedy_noisy_path: Path to greedy_noisy_results.csv (or equivalent).
        output_path: Path to save the final power analysis JSON report.
    """
    results = {
        "clean_data": {},
        "noisy_data": {},
        "summary": {}
    }
    
    # --- Clean Data Analysis ---
    logger.info("Starting power analysis for CLEAN data...")
    baseline_clean = load_csv_accuracies(baseline_clean_path)
    lazy_clean = load_csv_accuracies(lazy_clean_path)
    greedy_clean = load_csv_accuracies(greedy_clean_path)
    
    if baseline_clean and lazy_clean:
        results["clean_data"]["lazy_vs_baseline"] = analyze_comparison(
            baseline_clean, lazy_clean, "Lazy", alpha=0.05
        )
    
    if baseline_clean and greedy_clean:
        results["clean_data"]["greedy_vs_baseline"] = analyze_comparison(
            baseline_clean, greedy_clean, "Greedy", alpha=0.05
        )
    
    # --- Noisy Data Analysis ---
    logger.info("Starting power analysis for NOISY data...")
    baseline_noisy = load_csv_accuracies(baseline_noisy_path)
    lazy_noisy = load_csv_accuracies(lazy_noisy_path)
    greedy_noisy = load_csv_accuracies(greedy_noisy_path)
    
    if baseline_noisy and lazy_noisy:
        results["noisy_data"]["lazy_vs_baseline"] = analyze_comparison(
            baseline_noisy, lazy_noisy, "Lazy", alpha=0.05
        )
    
    if baseline_noisy and greedy_noisy:
        results["noisy_data"]["greedy_vs_baseline"] = analyze_comparison(
            baseline_noisy, greedy_noisy, "Greedy", alpha=0.05
        )
    
    # --- Summary ---
    # Calculate average power across comparisons
    all_powers = []
    for dataset in ["clean_data", "noisy_data"]:
        for key, val in results[dataset].items():
            if val.get("status") == "success":
                all_powers.append(val["power_from_t_stat"])
    
    if all_powers:
        results["summary"]["mean_power"] = float(np.mean(all_powers))
        results["summary"]["min_power"] = float(np.min(all_powers))
        results["summary"]["max_power"] = float(np.max(all_powers))
        results["summary"]["comparisons_analyzed"] = len(all_powers)
    else:
        results["summary"]["mean_power"] = 0.0
        results["summary"]["comparisons_analyzed"] = 0
        results["summary"]["error"] = "No valid comparisons found for power calculation."
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Power analysis results saved to {output_path}")


def main():
    """
    Main entry point for the power analysis script.
    Parses arguments and runs the analysis.
    """
    parser = argparse.ArgumentParser(description="Perform post-hoc power analysis on llmXive results.")
    
    # Input paths - defaulting to standard project paths
    parser.add_argument("--stats-clean", type=str, default="data/processed/stats_clean.json",
                        help="Path to clean statistical test results JSON.")
    parser.add_argument("--stats-noisy", type=str, default="data/processed/stats_noisy.json",
                        help="Path to noisy statistical test results JSON.")
    parser.add_argument("--baseline-clean", type=str, default="data/processed/baseline_results.csv",
                        help="Path to baseline results CSV (clean).")
    parser.add_argument("--lazy-clean", type=str, default="data/processed/lazy_results.csv",
                        help="Path to lazy results CSV (clean).")
    parser.add_argument("--greedy-clean", type=str, default="data/processed/greedy_results.csv",
                        help="Path to greedy results CSV (clean).")
    parser.add_argument("--baseline-noisy", type=str, default="data/processed/noisy_baseline_results.csv",
                        help="Path to baseline results CSV (noisy).")
    parser.add_argument("--lazy-noisy", type=str, default="data/processed/lazy_noisy_results.csv",
                        help="Path to lazy results CSV (noisy).")
    parser.add_argument("--greedy-noisy", type=str, default="data/processed/greedy_noisy_results.csv",
                        help="Path to greedy results CSV (noisy).")
    parser.add_argument("--output", type=str, default="data/processed/power_analysis_results.json",
                        help="Path to output JSON report.")
    
    args = parser.parse_args()
    
    run_power_analysis(
        stats_clean_path=args.stats_clean,
        stats_noisy_path=args.stats_noisy,
        baseline_clean_path=args.baseline_clean,
        lazy_clean_path=args.lazy_clean,
        greedy_clean_path=args.greedy_clean,
        baseline_noisy_path=args.baseline_noisy,
        lazy_noisy_path=args.lazy_noisy,
        greedy_noisy_path=args.greedy_noisy,
        output_path=args.output
    )


if __name__ == "__main__":
    main()