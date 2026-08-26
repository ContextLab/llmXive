"""
Power Analysis Module for llmXive Follow-up Study

This module calculates post-hoc statistical power for the observed effects
in the comparison of traversal strategies (Baseline vs. Lazy, Baseline vs. Greedy).
It uses the actual sample size and effect sizes derived from the execution results.
"""

import os
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from scipy import stats
from scipy.stats import ttest_ind, ttest_rel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_ALPHA = 0.05
DEFAULT_POWER = 0.80


def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file."""
    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    with open(file_path, 'r') as f:
        return json.load(f)


def load_csv_accuracies(file_path: Path, strategy_name: str) -> List[float]:
    """
    Load accuracy values from a CSV file for a specific strategy.
    Expects a CSV with columns: task_id, accuracy, nodes_visited, latency_ms, status
    """
    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    accuracies = []
    with open(file_path, 'r') as f:
        import csv
        reader = csv.DictReader(f)
        for row in reader:
            # Only include completed tasks for power analysis
            if row.get('status', '').upper() == 'COMPLETED':
                try:
                    acc = float(row['accuracy'])
                    accuracies.append(acc)
                except (ValueError, KeyError):
                    continue

    if not accuracies:
        logger.warning(f"No valid completed tasks found in {file_path} for {strategy_name}")
    return accuracies


def calculate_effect_size(group1: List[float], group2: List[float], paired: bool = True) -> float:
    """
    Calculate Cohen's d (effect size) for two groups.
    For paired data, uses Cohen's d for paired samples.
    For independent data, uses standard Cohen's d.
    """
    if not group1 or not group2:
        return 0.0

    arr1 = np.array(group1)
    arr2 = np.array(group2)

    if paired and len(arr1) == len(arr2):
        # Paired effect size: mean of differences / std of differences
        diffs = arr1 - arr2
        mean_diff = np.mean(diffs)
        std_diff = np.std(diffs, ddof=1)
        if std_diff == 0:
            return 0.0
        return mean_diff / std_diff
    else:
        # Independent effect size (Cohen's d)
        mean1, mean2 = np.mean(arr1), np.mean(arr2)
        std1, std2 = np.std(arr1, ddof=1), np.std(arr2, ddof=1)
        
        # Pooled standard deviation
        n1, n2 = len(arr1), len(arr2)
        if n1 + n2 <= 2:
            return 0.0
        
        pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
        
        if pooled_std == 0:
            return 0.0
        
        return (mean1 - mean2) / pooled_std


def calculate_power_from_tstat(t_stat: float, df: int, alpha: float = DEFAULT_ALPHA, n1: int = 0, n2: int = 0) -> float:
    """
    Estimate statistical power from t-statistic and degrees of freedom.
    Uses the non-central t-distribution approximation.
    """
    if df <= 0:
        return 0.0

    # Critical t-value for two-tailed test
    t_crit = stats.t.ppf(1 - alpha / 2, df)
    
    # Non-centrality parameter (NCP)
    # For a two-sample t-test: NCP = t_stat * sqrt(1/n1 + 1/n2) * sqrt(n1*n2/(n1+n2))
    # Simplified approximation using t_stat and df
    # NCP ≈ t_stat * sqrt(df / (df + t_stat^2)) * sqrt(2) ? 
    # More robust: NCP = t_stat * sqrt(n_eff) where n_eff is effective sample size
    
    # If we have sample sizes, calculate NCP properly
    if n1 > 0 and n2 > 0:
        n_eff = (n1 * n2) / (n1 + n2)
        ncp = t_stat * np.sqrt(n_eff / (n1 + n2)) * np.sqrt(2) # Approximation
        # Better approach: NCP = delta * sqrt(n_eff) where delta is effect size
        # We'll use the t-statistic directly with the non-central t CDF
        pass
    
    # Approximation: Power = P(|T| > t_crit | H1)
    # Using the non-central t-distribution with NCP derived from t_stat
    # NCP ≈ t_stat * sqrt(df / (df + t_stat^2)) is not quite right.
    # Let's use the relationship: t = delta * sqrt(n/2) for equal n
    # So delta = t * sqrt(2/n)
    # NCP = delta * sqrt(n/2) = t
    # Actually, for large samples, Power ≈ Φ(|t| - t_crit) + Φ(-|t| - t_crit)
    # But we should use the non-central t-distribution.
    
    # Robust approximation using normal distribution for large df
    if df > 30:
        # Power ≈ 1 - Φ(t_crit - |t_stat|) + Φ(-t_crit - |t_stat|)
        # Simplified: Power ≈ Φ(|t_stat| - t_crit)
        power = stats.norm.cdf(abs(t_stat) - t_crit)
        return max(0.0, min(1.0, power))
    else:
        # For small samples, use non-central t-distribution
        # Estimate NCP from t_stat and df
        # NCP = t_stat * sqrt( (n1+n2)/(n1*n2) ) * sqrt( (n1+n2-2)/2 ) ?
        # Let's use a standard approximation: NCP ≈ t_stat * sqrt(df / (df + t_stat^2)) * sqrt(2) is wrong.
        # Correct: t = NCP / sqrt(1 + NCP^2/df) ? No.
        # t = (mean_diff / std_err) = (delta * sqrt(n/2)) / (sigma / sqrt(n/2)) = delta * sqrt(n/2)
        # So NCP = delta * sqrt(n/2) = t_stat * sqrt(n/2) / sqrt(n/2) * sqrt(n/2) = t_stat * sqrt(n/2) ?
        # Actually, for equal n, NCP = t_stat * sqrt(n/2) is not correct.
        # NCP = delta * sqrt(n/2). And t = delta * sqrt(n/2) / sqrt(1 + ...).
        # Let's just use the t-statistic as the NCP for a rough estimate in scipy
        # scipy.stats.nct.cdf(t_crit, df, ncp)
        
        # Simple heuristic: NCP ≈ t_stat * sqrt(2) for equal sample sizes
        ncp = t_stat * np.sqrt(2) 
        # Power = 1 - CDF(t_crit, df, ncp) + CDF(-t_crit, df, ncp)
        cdf_pos = stats.nct.cdf(t_crit, df, ncp)
        cdf_neg = stats.nct.cdf(-t_crit, df, ncp)
        power = 1 - (cdf_pos - cdf_neg)
        return max(0.0, min(1.0, power))


def calculate_power_from_effect_size(effect_size: float, n1: int, n2: int, alpha: float = DEFAULT_ALPHA, paired: bool = True) -> float:
    """
    Calculate statistical power given effect size and sample sizes.
    """
    if n1 <= 0 or n2 <= 0:
        return 0.0

    if paired:
        n = min(n1, n2)
        df = n - 1
        # NCP for paired t-test: delta * sqrt(n)
        ncp = effect_size * np.sqrt(n)
    else:
        # NCP for independent t-test: delta * sqrt(n_eff)
        n_eff = (n1 * n2) / (n1 + n2)
        df = n1 + n2 - 2
        ncp = effect_size * np.sqrt(n_eff)

    t_crit = stats.t.ppf(1 - alpha / 2, df)
    
    # Power = 1 - (CDF(t_crit, df, ncp) - CDF(-t_crit, df, ncp))
    cdf_pos = stats.nct.cdf(t_crit, df, ncp)
    cdf_neg = stats.nct.cdf(-t_crit, df, ncp)
    power = 1 - (cdf_pos - cdf_neg)
    
    return max(0.0, min(1.0, power))


def analyze_comparison(
    baseline_acc: List[float],
    strategy_acc: List[float],
    strategy_name: str,
    alpha: float = DEFAULT_ALPHA
) -> Dict[str, Any]:
    """
    Perform power analysis for a single comparison (Baseline vs. Strategy).
    """
    result = {
        "strategy": strategy_name,
        "n_baseline": len(baseline_acc),
        "n_strategy": len(strategy_acc),
        "effect_size": None,
        "t_statistic": None,
        "p_value": None,
        "power": None,
        "min_power": False
    }

    if not baseline_acc or not strategy_acc:
        logger.warning(f"Insufficient data for {strategy_name} comparison")
        return result

    # Determine if paired (same tasks) or independent
    # In our case, same tasks are run with different strategies, so paired
    paired = len(baseline_acc) == len(strategy_acc)

    # Calculate effect size
    effect_size = calculate_effect_size(baseline_acc, strategy_acc, paired=paired)
    result["effect_size"] = round(effect_size, 4)

    # Perform t-test
    if paired:
        t_stat, p_val = ttest_rel(baseline_acc, strategy_acc)
    else:
        t_stat, p_val = ttest_ind(baseline_acc, strategy_acc)
    
    result["t_statistic"] = round(float(t_stat), 4)
    result["p_value"] = round(float(p_val), 6)

    # Calculate power
    n1, n2 = len(baseline_acc), len(strategy_acc)
    df = n1 + n2 - 2 if not paired else n1 - 1

    # Use effect size based power calculation
    power = calculate_power_from_effect_size(effect_size, n1, n2, alpha, paired)
    result["power"] = round(power, 4)

    # Check if power is sufficient
    if power < DEFAULT_POWER:
        result["min_power"] = True

    return result


def run_power_analysis(
    baseline_csv: Path,
    lazy_csv: Path,
    greedy_csv: Path,
    output_path: Path,
    alpha: float = DEFAULT_ALPHA
) -> Dict[str, Any]:
    """
    Run power analysis for all comparisons and save results.
    """
    logger.info(f"Loading baseline data from {baseline_csv}")
    baseline_acc = load_csv_accuracies(baseline_csv, "Baseline")

    logger.info(f"Loading Lazy data from {lazy_csv}")
    lazy_acc = load_csv_accuracies(lazy_csv, "Lazy")

    logger.info(f"Loading Greedy data from {greedy_csv}")
    greedy_acc = load_csv_accuracies(greedy_csv, "Greedy")

    comparisons = [
        analyze_comparison(baseline_acc, lazy_acc, "Lazy", alpha),
        analyze_comparison(baseline_acc, greedy_acc, "Greedy", alpha)
    ]

    # Aggregate results
    summary = {
        "alpha": alpha,
        "threshold_power": DEFAULT_POWER,
        "comparisons": comparisons,
        "total_tasks_baseline": len(baseline_acc),
        "total_tasks_lazy": len(lazy_acc),
        "total_tasks_greedy": len(greedy_acc)
    }

    # Check overall power sufficiency
    insufficient = [c for c in comparisons if c["min_power"]]
    summary["insufficient_power_count"] = len(insufficient)
    summary["is_sufficient"] = len(insufficient) == 0
    summary["recommendation"] = (
        "Sample size is sufficient for all comparisons." 
        if summary["is_sufficient"] 
        else "Consider increasing sample size for comparisons with insufficient power."
    )

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save results
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Power analysis results saved to {output_path}")
    return summary


def main():
    """Main entry point for power analysis."""
    parser = argparse.ArgumentParser(description="Run post-hoc power analysis for traversal strategies.")
    parser.add_argument(
        "--baseline",
        type=str,
        default="data/processed/baseline_results.csv",
        help="Path to baseline results CSV"
    )
    parser.add_argument(
        "--lazy",
        type=str,
        default="data/processed/lazy_results.csv",
        help="Path to lazy strategy results CSV"
    )
    parser.add_argument(
        "--greedy",
        type=str,
        default="data/processed/greedy_results.csv",
        help="Path to greedy strategy results CSV"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/power_analysis.json",
        help="Output path for power analysis JSON"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=DEFAULT_ALPHA,
        help="Significance level (default: 0.05)"
    )

    args = parser.parse_args()

    baseline_path = Path(args.baseline)
    lazy_path = Path(args.lazy)
    greedy_path = Path(args.greedy)
    output_path = Path(args.output)

    try:
        results = run_power_analysis(
            baseline_path,
            lazy_path,
            greedy_path,
            output_path,
            args.alpha
        )
        print(json.dumps(results, indent=2))
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during power analysis: {e}")
        raise


if __name__ == "__main__":
    main()