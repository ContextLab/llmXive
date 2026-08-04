"""
Statistical Power Analysis for the 5-run experiment.

Calculates the achieved statistical power for the 5-run experiment given the
observed effect sizes and variance from the Wilcoxon signed-rank tests.

This script:
1. Loads the statistical test results from data/results/statistical_report.md (or JSON if available)
2. Extracts the observed effect sizes (r = Z / sqrt(N)) and variance
3. Calculates the achieved power using the Wilcoxon signed-rank test parameters
4. Generates a comprehensive report in data/results/power_analysis.md

Serves US-3 and FR-005.
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, Any, Optional, Tuple
from scipy.stats import wilcoxon, norm
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from metrics import wilcoxon_signed_rank_test

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
STATISTICAL_REPORT_PATH = "data/results/statistical_report.md"
POWER_ANALYSIS_OUTPUT_PATH = "data/results/power_analysis.md"
EXPERIMENT_RESULTS_PATH = "data/results/experiment_results.json"
DEFAULT_N_RUNS = 5
DEFAULT_ALPHA = 0.05


def calculate_effect_size_r(z_statistic: float, n_pairs: int) -> float:
    """
    Calculate the effect size r for Wilcoxon signed-rank test.
    
    r = Z / sqrt(N)
    where Z is the standardized test statistic and N is the number of pairs.
    
    Args:
        z_statistic: The standardized test statistic (Z)
        n_pairs: Number of paired observations
    
    Returns:
        Effect size r (ranges from -1 to 1)
    """
    if n_pairs <= 0:
        return 0.0
    return z_statistic / np.sqrt(n_pairs)


def calculate_power_wilcoxon(
    effect_size: float,
    n_pairs: int,
    alpha: float = 0.05,
    alternative: str = "two-sided"
) -> float:
    """
    Calculate the statistical power for a Wilcoxon signed-rank test.
    
    This uses a normal approximation to estimate the power based on the
    effect size and sample size.
    
    Args:
        effect_size: The effect size r (Cohen's r)
        n_pairs: Number of paired observations
        alpha: Significance level (default 0.05)
        alternative: Type of test ("two-sided", "greater", "less")
    
    Returns:
        Statistical power (probability of correctly rejecting H0 when false)
    """
    if n_pairs <= 1 or effect_size == 0:
        return 0.0
    
    # For Wilcoxon signed-rank test, we can approximate power using the
    # normal distribution. The non-centrality parameter is approximately:
    # delta = effect_size * sqrt(n_pairs)
    
    delta = effect_size * np.sqrt(n_pairs)
    
    # Critical value for the test
    if alternative == "two-sided":
        z_critical = norm.ppf(1 - alpha / 2)
    elif alternative == "greater":
        z_critical = norm.ppf(1 - alpha)
    else:  # "less"
        z_critical = norm.ppf(alpha)
    
    # Power is the probability that the test statistic exceeds the critical value
    # under the alternative hypothesis
    power = norm.cdf(delta - z_critical) if alternative != "less" else norm.cdf(-delta - z_critical)
    
    return max(0.0, min(1.0, power))


def load_experiment_results() -> Optional[Dict[str, Any]]:
    """
    Load the experiment results from the JSON file.
    
    Returns:
        Dictionary containing experiment results, or None if file doesn't exist.
    """
    if not os.path.exists(EXPERIMENT_RESULTS_PATH):
        logger.warning(f"Experiment results file not found: {EXPERIMENT_RESULTS_PATH}")
        return None
    
    try:
        with open(EXPERIMENT_RESULTS_PATH, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load experiment results: {e}")
        return None


def extract_wilcoxon_results(experiment_results: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Extract Wilcoxon test results from the experiment results.
    
    Args:
        experiment_results: Dictionary containing experiment results
    
    Returns:
        Dictionary mapping metric name to Wilcoxon test results
    """
    results = {}
    
    # Look for Wilcoxon test results in the experiment results
    if "wilcoxon_results" in experiment_results:
        results = experiment_results["wilcoxon_results"]
    elif "statistical_tests" in experiment_results:
        # Try to extract from statistical_tests
        for metric, test_data in experiment_results["statistical_tests"].items():
            if "wilcoxon" in test_data:
                results[metric] = test_data["wilcoxon"]
    
    return results


def perform_power_analysis(
    ndcg_scores_baseline: list,
    ndcg_scores_clustering: list,
    wasted_ratios_baseline: list,
    wasted_ratios_clustering: list,
    alpha: float = DEFAULT_ALPHA
) -> Dict[str, Dict[str, Any]]:
    """
    Perform power analysis for both NDCG and wasted call ratio metrics.
    
    Args:
        ndcg_scores_baseline: NDCG@10 scores from baseline runs
        ndcg_scores_clustering: NDCG@10 scores from clustering-aided runs
        wasted_ratios_baseline: Wasted call ratios from baseline runs
        wasted_ratios_clustering: Wasted call ratios from clustering-aided runs
        alpha: Significance level
    
    Returns:
        Dictionary containing power analysis results for each metric
    """
    power_results = {}
    
    # Analyze NDCG@10
    if len(ndcg_scores_baseline) == len(ndcg_scores_clustering) and len(ndcg_scores_baseline) >= 2:
        try:
            # Perform Wilcoxon test
            stat, p_value, z_statistic = wilcoxon_signed_rank_test(
                ndcg_scores_baseline,
                ndcg_scores_clustering,
                alternative="two-sided"
            )
            
            n_pairs = len(ndcg_scores_baseline)
            effect_size = calculate_effect_size_r(z_statistic, n_pairs)
            power = calculate_power_wilcoxon(effect_size, n_pairs, alpha)
            
            power_results["ndcg_at_10"] = {
                "n_runs": n_pairs,
                "effect_size_r": effect_size,
                "z_statistic": z_statistic,
                "p_value": p_value,
                "statistical_significant": p_value < alpha,
                "achieved_power": power,
                "baseline_mean": float(np.mean(ndcg_scores_baseline)),
                "clustering_mean": float(np.mean(ndcg_scores_clustering)),
                "difference": float(np.mean(ndcg_scores_clustering) - np.mean(ndcg_scores_baseline))
            }
        except Exception as e:
            logger.error(f"Error analyzing NDCG power: {e}")
            power_results["ndcg_at_10"] = {
                "error": str(e),
                "n_runs": len(ndcg_scores_baseline)
            }
    
    # Analyze wasted call ratio
    if len(wasted_ratios_baseline) == len(wasted_ratios_clustering) and len(wasted_ratios_baseline) >= 2:
        try:
            # Perform Wilcoxon test
            stat, p_value, z_statistic = wilcoxon_signed_rank_test(
                wasted_ratios_baseline,
                wasted_ratios_clustering,
                alternative="two-sided"
            )
            
            n_pairs = len(wasted_ratios_baseline)
            effect_size = calculate_effect_size_r(z_statistic, n_pairs)
            power = calculate_power_wilcoxon(effect_size, n_pairs, alpha)
            
            power_results["wasted_call_ratio"] = {
                "n_runs": n_pairs,
                "effect_size_r": effect_size,
                "z_statistic": z_statistic,
                "p_value": p_value,
                "statistical_significant": p_value < alpha,
                "achieved_power": power,
                "baseline_mean": float(np.mean(wasted_ratios_baseline)),
                "clustering_mean": float(np.mean(wasted_ratios_clustering)),
                "difference": float(np.mean(wasted_ratios_clustering) - np.mean(wasted_ratios_baseline))
            }
        except Exception as e:
            logger.error(f"Error analyzing wasted call ratio power: {e}")
            power_results["wasted_call_ratio"] = {
                "error": str(e),
                "n_runs": len(wasted_ratios_baseline)
            }
    
    return power_results


def generate_power_analysis_report(power_results: Dict[str, Dict[str, Any]]) -> str:
    """
    Generate a markdown report for the power analysis.
    
    Args:
        power_results: Dictionary containing power analysis results
    
    Returns:
        Markdown formatted report string
    """
    report_lines = [
        "# Statistical Power Analysis Report",
        "",
        "## Overview",
        "",
        "This report presents the achieved statistical power for the 5-run experiment",
        "comparing the baseline active ranker against the clustering-aided variant.",
        "Power analysis determines the probability of correctly rejecting the null hypothesis",
        "when it is false, given the observed effect sizes and sample size.",
        "",
        "## Methodology",
        "",
        "- **Test**: Wilcoxon signed-rank test (paired, two-sided)",
        "- **Significance Level (α)**: 0.05",
        "- **Sample Size (N)**: 5 independent runs",
        "- **Effect Size Metric**: Cohen's r (r = Z / √N)",
        "- **Power Calculation**: Normal approximation based on effect size and sample size",
        "",
        "## Interpretation Guidelines",
        "",
        "| Power Value | Interpretation |",
        "|-------------|----------------|",
        "| ≥ 0.80      | Adequate power (standard threshold) |",
        "| 0.60 - 0.79 | Moderate power (acceptable but limited) |",
        "| < 0.60      | Low power (results may be unreliable) |",
        "",
        "## Results by Metric",
        ""
    ]
    
    for metric_name, results in power_results.items():
        metric_display = metric_name.replace("_", " ").title()
        report_lines.append(f"### {metric_display}")
        report_lines.append("")
        
        if "error" in results:
            report_lines.append(f"**Analysis Failed**: {results['error']}")
            report_lines.append("")
            continue
        
        report_lines.append("| Metric | Value |")
        report_lines.append("|--------|-------|")
        report_lines.append(f"| Number of Runs | {results['n_runs']} |")
        report_lines.append(f"| Effect Size (r) | {results['effect_size_r']:.4f} |")
        report_lines.append(f"| Z-Statistic | {results['z_statistic']:.4f} |")
        report_lines.append(f"| P-Value | {results['p_value']:.6f} |")
        report_lines.append(f"| Statistically Significant (p < 0.05) | {'Yes' if results['statistical_significant'] else 'No'} |")
        report_lines.append(f"| **Achieved Power** | **{results['achieved_power']:.4f}** |")
        report_lines.append(f"| Baseline Mean | {results['baseline_mean']:.4f} |")
        report_lines.append(f"| Clustering-Aided Mean | {results['clustering_mean']:.4f} |")
        report_lines.append(f"| Mean Difference | {results['difference']:.4f} |")
        report_lines.append("")
        
        # Interpretation
        power = results['achieved_power']
        if power >= 0.80:
            interpretation = "✅ **Adequate power**. The study has sufficient sensitivity to detect the observed effect."
        elif power >= 0.60:
            interpretation = "⚠️ **Moderate power**. The study may detect the effect, but results should be interpreted with caution."
        else:
            interpretation = "❌ **Low power**. The study lacks sufficient sensitivity; non-significant results may be due to inadequate sample size."
        
        report_lines.append(f"**Interpretation**: {interpretation}")
        report_lines.append("")
    
    # Summary section
    report_lines.append("## Summary and Recommendations", "")
    
    adequate_metrics = sum(1 for r in power_results.values() if "achieved_power" in r and r["achieved_power"] >= 0.80)
    total_metrics = len(power_results)
    
    report_lines.append(f"Out of {total_metrics} metrics analyzed, {adequate_metrics} achieved adequate statistical power (≥0.80).")
    report_lines.append("")
    
    if adequate_metrics == total_metrics:
        report_lines.append("✅ **Conclusion**: The 5-run experimental design provides sufficient statistical power to support the research conclusions.")
    elif adequate_metrics > 0:
        report_lines.append("⚠️ **Conclusion**: Some metrics have adequate power, but others may require additional runs for more reliable conclusions.")
    else:
        report_lines.append("❌ **Conclusion**: The current sample size (N=5) may be insufficient to reliably detect the observed effects. Consider increasing the number of runs.")
    
    report_lines.append("")
    report_lines.append("## Limitations", "")
    report_lines.append("- Power analysis is based on observed effect sizes from only 5 runs.")
    report_lines.append("- The normal approximation may be less accurate for very small sample sizes.")
    report_lines.append("- Power estimates assume the observed effect sizes are representative of the true population effects.")
    report_lines.append("")
    report_lines.append("---", "")
    report_lines.append(f"*Report generated on: {__import__('datetime').datetime.now().isoformat()}*")
    
    return "\n".join(report_lines)


def main():
    """Main entry point for power analysis."""
    parser = argparse.ArgumentParser(description="Perform statistical power analysis for the experiment.")
    parser.add_argument(
        "--alpha",
        type=float,
        default=DEFAULT_ALPHA,
        help=f"Significance level (default: {DEFAULT_ALPHA})"
    )
    parser.add_argument(
        "--input-results",
        type=str,
        default=EXPERIMENT_RESULTS_PATH,
        help=f"Path to experiment results JSON file (default: {EXPERIMENT_RESULTS_PATH})"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=POWER_ANALYSIS_OUTPUT_PATH,
        help=f"Path for output power analysis report (default: {POWER_ANALYSIS_OUTPUT_PATH})"
    )
    
    args = parser.parse_args()
    
    logger.info("Starting statistical power analysis...")
    
    # Load experiment results
    if not os.path.exists(args.input_results):
        logger.error(f"Experiment results file not found: {args.input_results}")
        logger.error("Please ensure the experiment has been run and results are available.")
        sys.exit(1)
    
    try:
        with open(args.input_results, 'r') as f:
            experiment_results = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load experiment results: {e}")
        sys.exit(1)
    
    # Extract data for analysis
    ndcg_baseline = []
    ndcg_clustering = []
    wasted_baseline = []
    wasted_clustering = []
    
    # Try to extract from the experiment results
    if "results" in experiment_results:
        for run_data in experiment_results["results"]:
            if "ndcg_baseline" in run_data:
                ndcg_baseline.append(run_data["ndcg_baseline"])
            if "ndcg_clustering" in run_data:
                ndcg_clustering.append(run_data["ndcg_clustering"])
            if "wasted_ratio_baseline" in run_data:
                wasted_baseline.append(run_data["wasted_ratio_baseline"])
            if "wasted_ratio_clustering" in run_data:
                wasted_clustering.append(run_data["wasted_ratio_clustering"])
    
    # If not found in the expected structure, try alternative locations
    if not ndcg_baseline and "ndcg_baseline_scores" in experiment_results:
        ndcg_baseline = experiment_results["ndcg_baseline_scores"]
    if not ndcg_clustering and "ndcg_clustering_scores" in experiment_results:
        ndcg_clustering = experiment_results["ndcg_clustering_scores"]
    if not wasted_baseline and "wasted_ratio_baseline_scores" in experiment_results:
        wasted_baseline = experiment_results["wasted_ratio_baseline_scores"]
    if not wasted_clustering and "wasted_ratio_clustering_scores" in experiment_results:
        wasted_clustering = experiment_results["wasted_ratio_clustering_scores"]
    
    # Validate we have enough data
    if len(ndcg_baseline) < 2 or len(ndcg_clustering) < 2:
        logger.error("Insufficient NDCG data for power analysis (need at least 2 runs).")
        logger.error(f"Found: {len(ndcg_baseline)} baseline, {len(ndcg_clustering)} clustering runs.")
        sys.exit(1)
    
    if len(wasted_baseline) < 2 or len(wasted_clustering) < 2:
        logger.error("Insufficient wasted call ratio data for power analysis (need at least 2 runs).")
        logger.error(f"Found: {len(wasted_baseline)} baseline, {len(wasted_clustering)} clustering runs.")
        sys.exit(1)
    
    logger.info(f"Analyzing power for {len(ndcg_baseline)} runs (NDCG) and {len(wasted_baseline)} runs (wasted ratio).")
    
    # Perform power analysis
    power_results = perform_power_analysis(
        ndcg_baseline,
        ndcg_clustering,
        wasted_baseline,
        wasted_clustering,
        alpha=args.alpha
    )
    
    # Generate report
    report = generate_power_analysis_report(power_results)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Write report to file
    with open(args.output, 'w') as f:
        f.write(report)
    
    logger.info(f"Power analysis report written to: {args.output}")
    
    # Print summary to console
    print("\n" + "="*60)
    print("POWER ANALYSIS SUMMARY")
    print("="*60)
    for metric, results in power_results.items():
        if "achieved_power" in results:
            print(f"{metric.replace('_', ' ').title()}: Power = {results['achieved_power']:.4f} "
                  f"(Effect Size r = {results['effect_size_r']:.4f})")
    print("="*60 + "\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
