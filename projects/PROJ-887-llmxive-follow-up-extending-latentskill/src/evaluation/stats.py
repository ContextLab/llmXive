import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
from scipy import stats

# Import project configuration
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.utils.config import get_project_root, get_results_path

logger = logging.getLogger(__name__)

# Constants for power analysis
DEFAULT_EFFECT_SIZE = 0.5
DEFAULT_ALPHA = 0.05
DEFAULT_DESIRED_POWER = 0.8

def load_evaluation_results(results_path: Path) -> Dict[str, Any]:
    """Load the statistics report from disk."""
    if not results_path.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}")
    
    with open(results_path, 'r') as f:
        return json.load(f)

def extract_success_rates(report: Dict[str, Any]) -> Dict[str, float]:
    """Extract success rates from the report."""
    if 'strategy_results' not in report:
        raise ValueError("Report missing 'strategy_results' key")
    
    rates = {}
    for strategy, data in report['strategy_results'].items():
        if 'mean_success_rate' in data:
            rates[strategy] = data['mean_success_rate']
    return rates

def perform_paired_test(group1: List[float], group2: List[float]) -> Tuple[float, float]:
    """
    Perform a paired t-test or Wilcoxon signed-rank test.
    Returns (statistic, p_value).
    """
    if len(group1) != len(group2) or len(group1) < 2:
        raise ValueError("Groups must have equal length >= 2 for paired test")
    
    # Check for normality of differences (Shapiro-Wilk)
    diffs = np.array(group1) - np.array(group2)
    try:
        _, p_normality = stats.shapiro(diffs)
        use_ttest = p_normality > 0.05
    except Exception:
        # Fallback to t-test if Shapiro fails
        use_ttest = True

    if use_ttest:
        stat, p_val = stats.ttest_rel(group1, group2)
    else:
        stat, p_val = stats.wilcoxon(group1, group2)
    
    return float(stat), float(p_val)

def apply_benjamini_hochberg(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg correction to a list of p-values.
    Returns corrected p-values.
    """
    if not p_values:
        return []
    
    m = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_indices]
    
    # Calculate BH critical values
    ranks = np.arange(1, m + 1)
    critical_values = (ranks / m) * DEFAULT_ALPHA
    
    # Find the largest k such that p_(k) <= critical_(k)
    # We need to adjust p-values to be monotonic
    adjusted_p = np.zeros(m)
    min_val = 1.0
    for i in reversed(range(m)):
        val = min(1.0, sorted_p[i] * (m / (i + 1)))
        min_val = min(min_val, val)
        adjusted_p[i] = min_val
    
    # Reorder back to original
    final_adjusted = np.zeros(m)
    final_adjusted[sorted_indices] = adjusted_p
    
    return final_adjusted.tolist()

def calculate_statistical_power(
    n: int, 
    effect_size: float, 
    alpha: float = DEFAULT_ALPHA, 
    desired_power: float = DEFAULT_DESIRED_POWER
) -> float:
    """
    Calculate statistical power for a paired t-test.
    
    Args:
        n: Number of pairs (trials)
        effect_size: Cohen's d (standardized difference)
        alpha: Significance level
        desired_power: Target power (not used in calculation, used for comparison)
    
    Returns:
        Estimated power (0.0 to 1.0)
    """
    if n < 2:
        return 0.0
    
    # Degrees of freedom
    df = n - 1
    
    # Non-centrality parameter for paired t-test
    ncp = effect_size * np.sqrt(n)
    
    # Critical t-value for two-tailed test
    t_crit = stats.t.ppf(1 - alpha / 2, df)
    
    # Power is the probability that the non-central t-distribution
    # exceeds the critical value
    # We approximate using the non-central t CDF
    power = 1 - stats.nct.cdf(t_crit, df, ncp) + stats.nct.cdf(-t_crit, df, ncp)
    
    return float(power)

def compare_strategies(
    results: Dict[str, Dict[str, Any]], 
    baseline_strategy: str = "baseline"
) -> List[Tuple[str, float, float]]:
    """
    Compare all strategies against the baseline.
    Returns list of (strategy_name, statistic, p_value).
    """
    comparisons = []
    
    if baseline_strategy not in results:
        raise ValueError(f"Baseline strategy '{baseline_strategy}' not found in results")
    
    baseline_data = results[baseline_strategy]
    if 'success_rates' not in baseline_data:
        raise ValueError(f"Baseline strategy missing 'success_rates' data")
    
    baseline_rates = baseline_data['success_rates']
    
    for strategy_name, data in results.items():
        if strategy_name == baseline_strategy:
            continue
        
        if 'success_rates' not in data:
            logger.warning(f"Skipping {strategy_name}: missing success_rates")
            continue
        
        strategy_rates = data['success_rates']
        
        if len(baseline_rates) != len(strategy_rates):
            logger.warning(f"Skipping {strategy_name}: length mismatch with baseline")
            continue
        
        stat, p_val = perform_paired_test(baseline_rates, strategy_rates)
        comparisons.append((strategy_name, stat, p_val))
    
    return comparisons

def save_statistics_report(
    report: Dict[str, Any], 
    output_path: Path
) -> None:
    """Save the statistics report to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Statistics report saved to {output_path}")

def main() -> None:
    """
    Main entry point for T043: Power Analysis Check.
    
    Reads data/results/stats_report.json, performs power analysis,
    updates the report with estimated power, and saves it back.
    """
    project_root = get_project_root()
    results_path = get_results_path()
    report_path = results_path / "stats_report.json"
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    logger.info(f"Loading report from {report_path}")
    
    try:
        report = load_evaluation_results(report_path)
    except FileNotFoundError as e:
        logger.error(f"Failed to load report: {e}")
        sys.exit(1)
    
    # Extract observed effect size from the report
    # We assume the report contains 'strategy_results' with 'mean_success_rate'
    # and we need to calculate the observed difference for power analysis
    
    strategy_results = report.get('strategy_results', {})
    
    if not strategy_results:
        logger.warning("No strategy results found in report. Skipping power analysis.")
        # Still save the report as is
        save_statistics_report(report, report_path)
        return
    
    # Find baseline and a comparison strategy to estimate effect size
    # We'll use the first available strategy vs baseline
    baseline_key = None
    comparison_key = None
    
    for key in strategy_results:
        if 'baseline' in key.lower():
            baseline_key = key
            break
    
    if not baseline_key:
        # Use the first key as baseline if 'baseline' not found
        baseline_key = list(strategy_results.keys())[0]
    
    for key in strategy_results:
        if key != baseline_key:
            comparison_key = key
            break
    
    if not comparison_key:
        logger.warning("Only one strategy found. Cannot compute effect size for power analysis.")
        # Set a default low power or skip
        report['power_analysis'] = {
            'estimated_power': 0.0,
            'note': 'Insufficient strategies for power analysis'
        }
        save_statistics_report(report, report_path)
        return
    
    # Extract success rates
    baseline_rates = strategy_results[baseline_key].get('success_rates', [])
    comparison_rates = strategy_results[comparison_key].get('success_rates', [])
    
    if not baseline_rates or not comparison_rates:
        logger.warning("Missing success rate data for power analysis.")
        report['power_analysis'] = {
            'estimated_power': 0.0,
            'note': 'Missing success rate data'
        }
        save_statistics_report(report, report_path)
        return
    
    # Calculate observed effect size (Cohen's d for paired samples)
    diffs = np.array(baseline_rates) - np.array(comparison_rates)
    mean_diff = np.mean(diffs)
    std_diff = np.std(diffs, ddof=1)
    
    if std_diff == 0:
        effect_size = 0.0
    else:
        effect_size = mean_diff / std_diff
    
    n = len(baseline_rates)
    
    # Calculate power
    estimated_power = calculate_statistical_power(
        n=n,
        effect_size=abs(effect_size), # Use absolute value for power calculation
        alpha=DEFAULT_ALPHA,
        desired_power=DEFAULT_DESIRED_POWER
    )
    
    # Prepare power analysis result
    power_analysis = {
        'observed_effect_size': float(effect_size),
        'sample_size': n,
        'alpha': DEFAULT_ALPHA,
        'estimated_power': float(estimated_power),
        'desired_power': DEFAULT_DESIRED_POWER,
        'sufficient_power': estimated_power >= DEFAULT_DESIRED_POWER,
        'recommendation': 'Proceed with test' if estimated_power >= DEFAULT_DESIRED_POWER else f'Consider increasing N (current power {estimated_power:.2f} < {DEFAULT_DESIRED_POWER})'
    }
    
    # Update report
    report['power_analysis'] = power_analysis
    
    # Log warning if power is low
    if estimated_power < DEFAULT_DESIRED_POWER:
        logger.warning(f"Statistical power is low ({estimated_power:.2f}). {power_analysis['recommendation']}")
    else:
        logger.info(f"Statistical power is sufficient ({estimated_power:.2f}).")
    
    # Save updated report
    save_statistics_report(report, report_path)
    
    logger.info("Power analysis complete and report updated.")

if __name__ == "__main__":
    main()
