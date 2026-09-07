"""
Statistical analysis module for the llmXive follow-up project.
Implements statistical tests, binning, threshold analysis, and power analysis.
"""

import json
import csv
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from scipy import stats
from scipy.stats import shapiro, ttest_rel, wilcoxon, pointbiserialr

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_results_from_csv(file_path: str) -> List[Dict[str, Any]]:
    """
    Load results from a CSV file into a list of dictionaries.

    Args:
        file_path (str): Path to the CSV file.

    Returns:
        List[Dict[str, Any]]: List of result dictionaries.
    """
    results = []
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric fields
                for key in row:
                    if row[key] is not None:
                        try:
                            if '.' in row[key]:
                                row[key] = float(row[key])
                            else:
                                row[key] = int(row[key])
                        except (ValueError, TypeError):
                            pass  # Keep as string
                results.append(row)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        raise
    return results


def count_timeout_tasks(results: List[Dict[str, Any]]) -> int:
    """
    Count the number of tasks that timed out.

    Args:
        results (List[Dict[str, Any]]): List of result dictionaries.

    Returns:
        int: Number of timeout tasks.
    """
    return sum(1 for r in results if r.get('status') == 'TIMEOUT' or r.get('timeout', False))


def count_completed_tasks(results: List[Dict[str, Any]]) -> int:
    """
    Count the number of tasks that completed successfully.

    Args:
        results (List[Dict[str, Any]]): List of result dictionaries.

    Returns:
        int: Number of completed tasks.
    """
    return sum(1 for r in results if r.get('status') == 'SUCCESS' or (r.get('status') not in ['TIMEOUT', 'ERROR'] and r.get('accuracy') is not None))


def aggregate_timeout_stats(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate statistics related to timeouts.

    Args:
        results (List[Dict[str, Any]]): List of result dictionaries.

    Returns:
        Dict[str, Any]: Dictionary containing timeout statistics.
    """
    timeout_count = count_timeout_tasks(results)
    completed_count = count_completed_tasks(results)
    total_count = len(results)

    return {
        'total_tasks': total_count,
        'timeout_count': timeout_count,
        'completed_count': completed_count,
        'timeout_rate': timeout_count / total_count if total_count > 0 else 0.0,
        'completion_rate': completed_count / total_count if total_count > 0 else 0.0
    }


def save_stats_report(stats: Dict[str, Any], output_path: str) -> None:
    """
    Save statistics report to a JSON file.

    Args:
        stats (Dict[str, Any]): Statistics dictionary.
        output_path (str): Path to the output JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Stats report saved to {output_path}")


def run_ttest_clean(baseline_results_path: str, heuristic_results_path: str) -> Dict[str, Any]:
    """
    Perform statistical comparison between baseline and heuristic on clean data.
    Automatically selects between paired t-test and Wilcoxon signed-rank test
    based on normality check (Shapiro-Wilk).

    Args:
        baseline_results_path (str): Path to baseline results CSV.
        heuristic_results_path (str): Path to heuristic results CSV.

    Returns:
        Dict[str, Any]: Dictionary containing test results.
    """
    logger.info(f"Loading baseline results from {baseline_results_path}")
    baseline_data = load_results_from_csv(baseline_results_path)
    logger.info(f"Loading heuristic results from {heuristic_results_path}")
    heuristic_data = load_results_from_csv(heuristic_results_path)

    if not baseline_data or not heuristic_data:
        logger.warning("One or both datasets are empty. Cannot perform statistical test.")
        return {
            'test_type': 'none',
            'reason': 'Empty dataset',
            'p_value': None,
            'statistic': None,
            'significant': None,
            'normality_check': None
        }

    # Extract accuracies
    baseline_acc = [r['accuracy'] for r in baseline_data if 'accuracy' in r and r['accuracy'] is not None]
    heuristic_acc = [r['accuracy'] for r in heuristic_data if 'accuracy' in r and r['accuracy'] is not None]

    if len(baseline_acc) != len(heuristic_acc):
        logger.warning("Baseline and heuristic datasets have different lengths. Cannot perform paired test.")
        return {
            'test_type': 'none',
            'reason': 'Mismatched dataset lengths',
            'p_value': None,
            'statistic': None,
            'significant': None,
            'normality_check': None
        }

    if len(baseline_acc) < 3:
        logger.warning("Insufficient data points for normality test.")
        return {
            'test_type': 'none',
            'reason': 'Insufficient data points',
            'p_value': None,
            'statistic': None,
            'significant': None,
            'normality_check': None
        }

    # Normality check using Shapiro-Wilk
    try:
        stat_b, p_b = shapiro(baseline_acc)
        stat_h, p_h = shapiro(heuristic_acc)
        normality_check = {
            'baseline': {'statistic': stat_b, 'p_value': p_b, 'is_normal': p_b > 0.05},
            'heuristic': {'statistic': stat_h, 'p_value': p_h, 'is_normal': p_h > 0.05}
        }
        logger.info(f"Normality check (Shapiro-Wilk): Baseline p={p_b:.4f}, Heuristic p={p_h:.4f}")
    except Exception as e:
        logger.warning(f"Shapiro-Wilk test failed: {e}. Defaulting to Wilcoxon.")
        normality_check = {'error': str(e)}
        # Default to non-parametric if normality check fails
        stat, p_val = wilcoxon(baseline_acc, heuristic_acc)
        return {
            'test_type': 'wilcoxon',
            'reason': 'Normality check failed',
            'p_value': p_val,
            'statistic': stat,
            'significant': p_val < 0.05,
            'normality_check': normality_check
        }

    # Decide test based on normality
    # If both are normal, use t-test; otherwise, use Wilcoxon
    use_ttest = normality_check['baseline']['is_normal'] and normality_check['heuristic']['is_normal']

    if use_ttest:
        logger.info("Performing paired t-test (data is normal).")
        stat, p_val = ttest_rel(baseline_acc, heuristic_acc)
        test_type = 'paired_ttest'
    else:
        logger.info("Performing Wilcoxon signed-rank test (data is non-normal).")
        stat, p_val = wilcoxon(baseline_acc, heuristic_acc)
        test_type = 'wilcoxon'

    return {
        'test_type': test_type,
        'p_value': p_val,
        'statistic': stat,
        'significant': p_val < 0.05,
        'normality_check': normality_check,
        'sample_size': len(baseline_acc)
    }


def run_ttest_noisy(baseline_results_path: str, heuristic_results_path: str) -> Dict[str, Any]:
    """
    Perform statistical comparison between baseline and heuristic on noisy data.
    Automatically selects between paired t-test and Wilcoxon signed-rank test
    based on normality check (Shapiro-Wilk).

    Args:
        baseline_results_path (str): Path to noisy baseline results CSV.
        heuristic_results_path (str): Path to noisy heuristic results CSV.

    Returns:
        Dict[str, Any]: Dictionary containing test results.
    """
    logger.info(f"Loading noisy baseline results from {baseline_results_path}")
    baseline_data = load_results_from_csv(baseline_results_path)
    logger.info(f"Loading noisy heuristic results from {heuristic_results_path}")
    heuristic_data = load_results_from_csv(heuristic_results_path)

    if not baseline_data or not heuristic_data:
        logger.warning("One or both datasets are empty. Cannot perform statistical test.")
        return {
            'test_type': 'none',
            'reason': 'Empty dataset',
            'p_value': None,
            'statistic': None,
            'significant': None,
            'normality_check': None
        }

    # Extract accuracies
    baseline_acc = [r['accuracy'] for r in baseline_data if 'accuracy' in r and r['accuracy'] is not None]
    heuristic_acc = [r['accuracy'] for r in heuristic_data if 'accuracy' in r and r['accuracy'] is not None]

    if len(baseline_acc) != len(heuristic_acc):
        logger.warning("Baseline and heuristic datasets have different lengths. Cannot perform paired test.")
        return {
            'test_type': 'none',
            'reason': 'Mismatched dataset lengths',
            'p_value': None,
            'statistic': None,
            'significant': None,
            'normality_check': None
        }

    if len(baseline_acc) < 3:
        logger.warning("Insufficient data points for normality test.")
        return {
            'test_type': 'none',
            'reason': 'Insufficient data points',
            'p_value': None,
            'statistic': None,
            'significant': None,
            'normality_check': None
        }

    # Normality check using Shapiro-Wilk
    try:
        stat_b, p_b = shapiro(baseline_acc)
        stat_h, p_h = shapiro(heuristic_acc)
        normality_check = {
            'baseline': {'statistic': stat_b, 'p_value': p_b, 'is_normal': p_b > 0.05},
            'heuristic': {'statistic': stat_h, 'p_value': p_h, 'is_normal': p_h > 0.05}
        }
        logger.info(f"Normality check (Shapiro-Wilk) for noisy data: Baseline p={p_b:.4f}, Heuristic p={p_h:.4f}")
    except Exception as e:
        logger.warning(f"Shapiro-Wilk test failed: {e}. Defaulting to Wilcoxon.")
        normality_check = {'error': str(e)}
        # Default to non-parametric if normality check fails
        stat, p_val = wilcoxon(baseline_acc, heuristic_acc)
        return {
            'test_type': 'wilcoxon',
            'reason': 'Normality check failed',
            'p_value': p_val,
            'statistic': stat,
            'significant': p_val < 0.05,
            'normality_check': normality_check
        }

    # Decide test based on normality
    use_ttest = normality_check['baseline']['is_normal'] and normality_check['heuristic']['is_normal']

    if use_ttest:
        logger.info("Performing paired t-test on noisy data (data is normal).")
        stat, p_val = ttest_rel(baseline_acc, heuristic_acc)
        test_type = 'paired_ttest'
    else:
        logger.info("Performing Wilcoxon signed-rank test on noisy data (data is non-normal).")
        stat, p_val = wilcoxon(baseline_acc, heuristic_acc)
        test_type = 'wilcoxon'

    return {
        'test_type': test_type,
        'p_value': p_val,
        'statistic': stat,
        'significant': p_val < 0.05,
        'normality_check': normality_check,
        'sample_size': len(baseline_acc)
    }


def calc_point_biserial(tasks_df: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate the Point-Biserial correlation coefficient between nodes_visited and reasoning success rate.

    Args:
        tasks_df (List[Dict[str, Any]]): List of task dictionaries.

    Returns:
        Dict[str, Any]: Dictionary containing correlation results.
    """
    if not tasks_df:
        logger.warning("Empty task list. Cannot calculate correlation.")
        return {'correlation': None, 'p_value': None, 'n': 0}

    nodes_visited = [r['nodes_visited'] for r in tasks_df if 'nodes_visited' in r and r['nodes_visited'] is not None]
    # Define success as accuracy > 0.5 (or any threshold indicating correct reasoning)
    # Assuming 'accuracy' is a float between 0 and 1
    success = [1 if r.get('accuracy', 0) > 0.5 else 0 for r in tasks_df if 'accuracy' in r and r['accuracy'] is not None]

    if len(nodes_visited) != len(success):
        logger.warning("Mismatched lengths for nodes_visited and success.")
        return {'correlation': None, 'p_value': None, 'n': 0}

    if len(nodes_visited) < 3:
        logger.warning("Insufficient data points for correlation.")
        return {'correlation': None, 'p_value': None, 'n': 0}

    try:
        corr, p_val = pointbiserialr(success, nodes_visited)
        return {
            'correlation': corr,
            'p_value': p_val,
            'n': len(nodes_visited),
            'significant': p_val < 0.05
        }
    except Exception as e:
        logger.error(f"Error calculating point-biserial correlation: {e}")
        return {'correlation': None, 'p_value': None, 'n': len(nodes_visited), 'error': str(e)}


def bin_tasks_by_nodes(tasks_df: List[Dict[str, Any]], min_bin_size: int = 3) -> List[List[Dict[str, Any]]]:
    """
    Bin tasks by nodes_visited, ensuring each bin has at least min_bin_size tasks.

    Args:
        tasks_df (List[Dict[str, Any]]): List of task dictionaries.
        min_bin_size (int): Minimum number of tasks per bin.

    Returns:
        List[List[Dict[str, Any]]]: List of bins, each bin is a list of task dictionaries.
    """
    if not tasks_df:
        return []

    # Sort by nodes_visited
    sorted_tasks = sorted(tasks_df, key=lambda x: x.get('nodes_visited', 0))

    bins = []
    current_bin = []

    for task in sorted_tasks:
        current_bin.append(task)
        if len(current_bin) >= min_bin_size:
            bins.append(current_bin)
            current_bin = []

    # Add remaining tasks to the last bin if any
    if current_bin:
        if bins:
            bins[-1].extend(current_bin)
        else:
            bins.append(current_bin)

    return bins


def find_inflection_point(baseline_results_path: str, heuristic_results_path: str) -> Dict[str, Any]:
    """
    Find the inflection point where the heuristic's accuracy drops below 95% of baseline.
    Uses binning by nodes_visited and checks statistical significance.

    Args:
        baseline_results_path (str): Path to baseline results CSV.
        heuristic_results_path (str): Path to heuristic results CSV.

    Returns:
        Dict[str, Any]: Dictionary containing inflection point analysis.
    """
    baseline_data = load_results_from_csv(baseline_results_path)
    heuristic_data = load_results_from_csv(heuristic_results_path)

    if not baseline_data or not heuristic_data:
        return {'inflection_point': None, 'reason': 'Empty dataset'}

    # Combine data and bin by nodes_visited
    # Assuming task_id is unique and present in both
    # For simplicity, we'll bin heuristic data by nodes_visited
    heuristic_tasks = [r for r in heuristic_data if 'nodes_visited' in r and r['nodes_visited'] is not None]
    bins = bin_tasks_by_nodes(heuristic_tasks, min_bin_size=3)

    if not bins:
        return {'inflection_point': None, 'reason': 'No valid bins found'}

    # Calculate baseline mean accuracy
    baseline_acc = [r['accuracy'] for r in baseline_data if 'accuracy' in r and r['accuracy'] is not None]
    if not baseline_acc:
        return {'inflection_point': None, 'reason': 'No baseline accuracy data'}
    baseline_mean = np.mean(baseline_acc)
    threshold = 0.95 * baseline_mean

    # Perform statistical test to check significance first
    test_result = run_ttest_clean(baseline_results_path, heuristic_results_path)
    if test_result['test_type'] == 'none' or not test_result.get('significant', False):
        return {
            'inflection_point': None,
            'reason': 'No statistically significant difference detected',
            'p_value': test_result.get('p_value'),
            'test_type': test_result.get('test_type')
        }

    # Find first bin where mean accuracy < 95% of baseline
    inflection_bin_index = None
    for i, bin_tasks in enumerate(bins):
        bin_acc = [t['accuracy'] for t in bin_tasks if 'accuracy' in t and t['accuracy'] is not None]
        if not bin_acc:
            continue
        bin_mean = np.mean(bin_acc)
        if bin_mean < threshold:
            inflection_bin_index = i
            break

    if inflection_bin_index is None:
        return {
            'inflection_point': None,
            'reason': 'No inflection point detected (accuracy never dropped below threshold)'
        }

    # Return details of the inflection bin
    inflection_bin = bins[inflection_bin_index]
    inflection_nodes = [t['nodes_visited'] for t in inflection_bin if 'nodes_visited' in t]
    inflection_acc = [t['accuracy'] for t in inflection_bin if 'accuracy' in t]

    return {
        'inflection_point': {
            'bin_index': inflection_bin_index,
            'nodes_visited_range': (min(inflection_nodes), max(inflection_nodes)) if inflection_nodes else None,
            'mean_accuracy': np.mean(inflection_acc) if inflection_acc else None,
            'bin_size': len(inflection_bin),
            'threshold_value': threshold
        },
        'total_bins': len(bins),
        'baseline_mean_accuracy': baseline_mean,
        'test_significance': test_result.get('significant')
    }


def calculate_effect_size(group1: List[float], group2: List[float]) -> Dict[str, float]:
    """
    Calculate Cohen's d effect size between two groups.

    Args:
        group1 (List[float]): First group of values.
        group2 (List[float]): Second group of values.

    Returns:
        Dict[str, float]: Dictionary containing effect size and interpretation.
    """
    if not group1 or not group2:
        return {'cohens_d': None, 'interpretation': 'Insufficient data'}

    mean1, mean2 = np.mean(group1), np.mean(group2)
    std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)
    n1, n2 = len(group1), len(group2)

    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))

    if pooled_std == 0:
        return {'cohens_d': 0.0, 'interpretation': 'Zero variance'}

    cohens_d = (mean1 - mean2) / pooled_std

    # Interpretation
    abs_d = abs(cohens_d)
    if abs_d < 0.2:
        interpretation = 'negligible'
    elif abs_d < 0.5:
        interpretation = 'small'
    elif abs_d < 0.8:
        interpretation = 'medium'
    else:
        interpretation = 'large'

    return {
        'cohens_d': cohens_d,
        'interpretation': interpretation
    }


def calculate_power_from_effect_size(effect_size: float, n: int, alpha: float = 0.05) -> float:
    """
    Estimate statistical power based on effect size and sample size.
    This is a simplified approximation.

    Args:
        effect_size (float): Cohen's d effect size.
        n (int): Sample size per group (assumed equal).
        alpha (float): Significance level.

    Returns:
        float: Estimated power.
    """
    # Using a simplified formula for power in t-test
    # This is an approximation; for precise power, use statsmodels or G*Power
    from scipy.stats import nct

    df = 2 * n - 2
    noncentrality = effect_size * np.sqrt(n / 2)

    # Critical t-value for two-tailed test
    t_crit = stats.t.ppf(1 - alpha / 2, df)

    # Power is the probability that the non-central t-distribution exceeds the critical value
    power = 1 - nct.cdf(t_crit, df, noncentrality) + nct.cdf(-t_crit, df, noncentrality)

    return power


def run_power_analysis(baseline_results_path: str, heuristic_results_path: str) -> Dict[str, Any]:
    """
    Perform post-hoc power analysis on the accuracy distributions.

    Args:
        baseline_results_path (str): Path to baseline results CSV.
        heuristic_results_path (str): Path to heuristic results CSV.

    Returns:
        Dict[str, Any]: Dictionary containing power analysis results.
    """
    baseline_data = load_results_from_csv(baseline_results_path)
    heuristic_data = load_results_from_csv(heuristic_results_path)

    if not baseline_data or not heuristic_data:
        return {'error': 'Empty dataset'}

    baseline_acc = [r['accuracy'] for r in baseline_data if 'accuracy' in r and r['accuracy'] is not None]
    heuristic_acc = [r['accuracy'] for r in heuristic_data if 'accuracy' in r and r['accuracy'] is not None]

    if len(baseline_acc) != len(heuristic_acc) or len(baseline_acc) < 2:
        return {'error': 'Insufficient or mismatched data'}

    effect_size_result = calculate_effect_size(baseline_acc, heuristic_acc)
    effect_size = effect_size_result['cohens_d']
    n = len(baseline_acc)

    if effect_size is None:
        return {'error': 'Could not calculate effect size'}

    power = calculate_power_from_effect_size(effect_size, n)

    return {
        'effect_size': effect_size,
        'effect_size_interpretation': effect_size_result['interpretation'],
        'sample_size': n,
        'estimated_power': power,
        'power_interpretation': 'adequate' if power >= 0.8 else 'low'
    }


def main():
    """
    Main function to run statistical analyses.
    This is a placeholder for command-line interface.
    """
    parser = argparse.ArgumentParser(description='Statistical Analysis for llmXive')
    parser.add_argument('--baseline', type=str, required=True, help='Path to baseline results CSV')
    parser.add_argument('--heuristic', type=str, required=True, help='Path to heuristic results CSV')
    parser.add_argument('--output', type=str, required=True, help='Path to output JSON file')
    parser.add_argument('--analysis', type=str, choices=['ttest', 'power', 'all'], default='all', help='Type of analysis to run')

    args = parser.parse_args()

    results = {}

    if args.analysis in ['ttest', 'all']:
        logger.info("Running statistical test...")
        results['ttest'] = run_ttest_clean(args.baseline, args.heuristic)

    if args.analysis in ['power', 'all']:
        logger.info("Running power analysis...")
        results['power'] = run_power_analysis(args.baseline, args.heuristic)

    # Save results
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Analysis complete. Results saved to {args.output}")


if __name__ == '__main__':
    main()