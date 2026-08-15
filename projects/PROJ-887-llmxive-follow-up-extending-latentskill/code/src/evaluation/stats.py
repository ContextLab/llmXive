import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
from scipy import stats

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_evaluation_results(filepath: str) -> Dict[str, Any]:
    """Load evaluation results from a JSON file."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Evaluation results file not found: {filepath}")
    
    with open(path, 'r') as f:
        return json.load(f)

def extract_success_rates(results: Dict[str, Any], strategy: str) -> List[float]:
    """Extract success rates for a specific strategy from results."""
    if strategy not in results:
        raise ValueError(f"Strategy '{strategy}' not found in results")
    
    # Assuming results are structured as {'strategy_name': [run1, run2, ...]}
    # where each run is 1 (success) or 0 (failure)
    runs = results[strategy]
    if not runs:
        raise ValueError(f"No runs found for strategy '{strategy}'")
    
    return [float(r) for r in runs]

def perform_paired_test(group_a: List[float], group_b: List[float], test_type: str = 't') -> Tuple[float, float]:
    """
    Perform a paired statistical test between two groups.
    
    Args:
        group_a: List of success rates for group A
        group_b: List of success rates for group B
        test_type: 't' for t-test, 'wilcoxon' for Wilcoxon signed-rank test
    
    Returns:
        Tuple of (statistic, p-value)
    
    Raises:
        ValueError: If groups have different lengths or are empty
    """
    if len(group_a) != len(group_b):
        raise ValueError(f"Groups must have equal length. Got {len(group_a)} and {len(group_b)}")
    
    if len(group_a) == 0:
        raise ValueError("Groups cannot be empty")
    
    # Check for zero variance (non-convergence)
    var_a = np.var(group_a, ddof=1)
    var_b = np.var(group_b, ddof=1)
    
    if var_a == 0 or var_b == 0:
        logger.warning("Zero variance in group, statistical test skipped. Returning NaN for p-value.")
        return (np.nan, np.nan)
    
    if test_type == 't':
        # Paired t-test
        stat, p_value = stats.ttest_rel(group_a, group_b)
    elif test_type == 'wilcoxon':
        # Wilcoxon signed-rank test
        stat, p_value = stats.wilcoxon(group_a, group_b)
    else:
        raise ValueError(f"Unknown test type: {test_type}. Use 't' or 'wilcoxon'")
    
    return (float(stat), float(p_value))

def apply_benjamini_hochberg(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values
    
    Returns:
        List of corrected p-values
    """
    if not p_values:
        return []
    
    # Filter out NaN values for the correction process
    valid_indices = [i for i, p in enumerate(p_values) if not np.isnan(p)]
    if not valid_indices:
        return p_values  # All are NaN, return as is
    
    valid_p_values = [p_values[i] for i in valid_indices]
    n = len(valid_p_values)
    
    # Sort p-values and keep track of original indices
    sorted_p_values = sorted(valid_p_values)
    ranks = range(1, n + 1)
    
    # Calculate BH critical values
    bh_corrected = []
    for i, p in enumerate(sorted_p_values):
        rank = i + 1
        corrected_p = min(1.0, (n / rank) * p)
        bh_corrected.append(corrected_p)
    
    # Ensure monotonicity (corrected p-values should not decrease as rank increases)
    for i in range(n - 2, -1, -1):
        bh_corrected[i] = min(bh_corrected[i], bh_corrected[i + 1])
    
    # Map back to original order
    result = p_values.copy()
    for idx, corrected_p in zip(valid_indices, bh_corrected):
        result[idx] = corrected_p
    
    return result

def calculate_statistical_power(effect_size: float, n: int, alpha: float = 0.05) -> float:
    """
    Estimate statistical power for a paired t-test.
    
    Args:
        effect_size: Cohen's d effect size
        n: Number of pairs
        alpha: Significance level
    
    Returns:
        Estimated power (0.0 to 1.0)
    """
    if n <= 1:
        return 0.0
    
    # Use scipy's power analysis approximation
    # For paired t-test, degrees of freedom = n - 1
    df = n - 1
    
    # Calculate non-centrality parameter
    ncp = effect_size * np.sqrt(n)
    
    # Calculate power using survival function of non-central t-distribution
    # This is an approximation; for exact power, use statsmodels
    from scipy.stats import nct
    
    # Two-tailed test
    t_crit = stats.t.ppf(1 - alpha/2, df)
    power = 1 - nct.cdf(t_crit, df, ncp) + nct.cdf(-t_crit, df, ncp)
    
    return float(power)

def compare_strategies(results: Dict[str, Any], strategies: List[str], test_type: str = 't') -> Dict[str, Any]:
    """
    Compare multiple strategies pairwise and return statistics.
    
    Args:
        results: Evaluation results dictionary
        strategies: List of strategy names to compare
        test_type: Type of statistical test ('t' or 'wilcoxon')
    
    Returns:
        Dictionary with comparison results
    """
    if len(strategies) < 2:
        raise ValueError("At least two strategies are required for comparison")
    
    comparisons = []
    raw_p_values = []
    
    for i in range(len(strategies)):
        for j in range(i + 1, len(strategies)):
            str_a = strategies[i]
            str_b = strategies[j]
            
            try:
                group_a = extract_success_rates(results, str_a)
                group_b = extract_success_rates(results, str_b)
                
                stat, p_value = perform_paired_test(group_a, group_b, test_type)
                
                comparisons.append({
                    'strategy_a': str_a,
                    'strategy_b': str_b,
                    'statistic': stat,
                    'p_value': p_value,
                    'n': len(group_a)
                })
                
                raw_p_values.append(p_value)
                
            except ValueError as e:
                logger.warning(f"Skipping comparison {str_a} vs {str_b}: {e}")
                comparisons.append({
                    'strategy_a': str_a,
                    'strategy_b': str_b,
                    'statistic': np.nan,
                    'p_value': np.nan,
                    'n': 0,
                    'error': str(e)
                })
                raw_p_values.append(np.nan)
    
    # Apply Benjamini-Hochberg correction
    corrected_p_values = apply_benjamini_hochberg(raw_p_values)
    
    # Update comparisons with corrected p-values
    for i, comp in enumerate(comparisons):
        if not np.isnan(corrected_p_values[i]):
            comp['bh_corrected_p_value'] = corrected_p_values[i]
    
    return {
        'comparisons': comparisons,
        'raw_p_values': raw_p_values,
        'bh_corrected_p_values': corrected_p_values
    }

def save_statistics_report(report: Dict[str, Any], filepath: str) -> None:
    """Save the statistics report to a JSON file."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Statistics report saved to {filepath}")

def main():
    """Main function to run statistical analysis on evaluation results."""
    # Default paths
    results_path = Path("data/results/evaluation_results.json")
    output_path = Path("data/results/stats_report.json")
    
    # Allow override via command line arguments
    if len(sys.argv) > 1:
        results_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])
    
    logger.info(f"Loading evaluation results from {results_path}")
    
    try:
        results = load_evaluation_results(results_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Define strategies to compare (adjust based on actual data)
    strategies = ['synthesized', 'baseline', 'single_neighbor', 'unweighted_mean', 'cosine_weighted']
    strategies = [s for s in strategies if s in results]
    
    if len(strategies) < 2:
        logger.error("Not enough strategies found in results for comparison")
        sys.exit(1)
    
    logger.info(f"Comparing strategies: {strategies}")
    
    # Perform pairwise comparisons
    comparison_results = compare_strategies(results, strategies, test_type='t')
    
    # Calculate mean success rates
    mean_success_rates = {}
    for strategy in strategies:
        try:
            rates = extract_success_rates(results, strategy)
            mean_success_rates[strategy] = float(np.mean(rates))
        except Exception as e:
            logger.warning(f"Could not calculate mean for {strategy}: {e}")
            mean_success_rates[strategy] = np.nan
    
    # Estimate statistical power (example: compare first two strategies)
    power_estimate = None
    if len(strategies) >= 2:
        try:
            group_a = extract_success_rates(results, strategies[0])
            group_b = extract_success_rates(results, strategies[1])
            
            # Calculate effect size (Cohen's d for paired samples)
            diff = np.array(group_a) - np.array(group_b)
            mean_diff = np.mean(diff)
            std_diff = np.std(diff, ddof=1)
            
            if std_diff > 0:
                effect_size = mean_diff / std_diff
                power = calculate_statistical_power(effect_size, len(group_a))
                power_estimate = {
                    'effect_size': float(effect_size),
                    'n': len(group_a),
                    'power': float(power)
                }
                logger.info(f"Estimated power for {strategies[0]} vs {strategies[1]}: {power:.3f}")
            else:
                logger.warning("Standard deviation of differences is zero, cannot calculate effect size")
        except Exception as e:
            logger.warning(f"Could not calculate power estimate: {e}")
    
    # Compile the final report
    report = {
        'mean_success_rate': mean_success_rates,
        'bh_corrected_p_values': comparison_results['bh_corrected_p_values'],
        'comparisons': comparison_results['comparisons'],
        'power_estimate': power_estimate,
        'analysis_timestamp': str(Path.cwd().joinpath(output_path).parent),
        'strategies_analyzed': strategies
    }
    
    # Save the report
    save_statistics_report(report, output_path)
    
    logger.info("Statistical analysis completed successfully")
    return report

if __name__ == "__main__":
    main()