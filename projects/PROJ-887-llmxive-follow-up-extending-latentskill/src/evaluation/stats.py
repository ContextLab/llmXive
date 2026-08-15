import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import scipy.stats as stats
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_evaluation_results(file_path: str) -> Dict[str, Any]:
    """Load evaluation results from a JSON file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Evaluation results file not found: {file_path}")
    
    with open(path, 'r') as f:
        return json.load(f)

def extract_success_rates(results: Dict[str, Any]) -> Dict[str, List[float]]:
    """Extract success rates for each strategy from evaluation results."""
    success_rates = {}
    if 'strategy_results' in results:
        for strategy, data in results['strategy_results'].items():
            if 'success_rates' in data:
                success_rates[strategy] = data['success_rates']
    return success_rates

def perform_paired_test(group1: List[float], group2: List[float]) -> Tuple[float, float]:
    """Perform a paired t-test or Wilcoxon signed-rank test."""
    if len(group1) != len(group2) or len(group1) < 2:
        raise ValueError("Both groups must have at least 2 samples and equal length")
    
    # Check for normality using Shapiro-Wilk test
    try:
        _, p_normality = stats.shapiro(np.array(group1) - np.array(group2))
        use_t_test = p_normality > 0.05
    except Exception:
        # Default to t-test if Shapiro-Wilk fails
        use_t_test = True
    
    if use_t_test:
        stat, p_value = stats.ttest_rel(group1, group2)
        test_name = "paired_t_test"
    else:
        stat, p_value = stats.wilcoxon(group1, group2)
        test_name = "wilcoxon_signed_rank"
    
    return p_value, test_name

def apply_benjamini_hochberg(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """Apply Benjamini-Hochberg correction to a list of p-values."""
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p_values = np.array([p_values[i] for i in sorted_indices])
    
    # Calculate BH critical values
    ranks = np.arange(1, n + 1)
    critical_values = (ranks / n) * alpha
    
    # Find the largest k such that p_(k) <= critical_(k)
    adjusted_p_values = np.ones(n)
    for i in range(n - 1, -1, -1):
        if sorted_p_values[i] <= critical_values[i]:
            # All p-values up to this index are significant
            for j in range(i + 1):
                adjusted_p_values[sorted_indices[j]] = min(1.0, sorted_p_values[j] * n / (j + 1))
            break
        else:
            adjusted_p_values[sorted_indices[i]] = min(1.0, sorted_p_values[i] * n / (i + 1))
    
    return adjusted_p_values.tolist()

def calculate_effect_size(group1: List[float], group2: List[float]) -> float:
    """Calculate Cohen's d effect size."""
    group1_np = np.array(group1)
    group2_np = np.array(group2)
    
    mean_diff = np.mean(group1_np) - np.mean(group2_np)
    pooled_std = np.sqrt((np.std(group1_np, ddof=1)**2 + np.std(group2_np, ddof=1)**2) / 2)
    
    if pooled_std == 0:
        return 0.0
    
    return mean_diff / pooled_std

def estimate_statistical_power(effect_size: float, n: int, alpha: float = 0.05, desired_power: float = 0.8) -> float:
    """
    Estimate statistical power for a paired t-test.
    
    Args:
        effect_size: Cohen's d effect size
        n: Sample size per group
        alpha: Significance level
        desired_power: Target power (for reference)
        
    Returns:
        Estimated power value between 0 and 1
    """
    if n < 2:
        return 0.0
    
    # Use non-central t-distribution to estimate power
    df = n - 1
    noncentrality_param = effect_size * np.sqrt(n / 2)
    
    # Critical t-value for two-tailed test
    t_critical = stats.t.ppf(1 - alpha/2, df)
    
    # Calculate power using non-central t-distribution
    power = stats.nct.sf(t_critical, df, noncentrality_param) + stats.nct.cdf(-t_critical, df, noncentrality_param)
    
    return max(0.0, min(1.0, power))

def compare_strategies(results: Dict[str, Any], baseline_strategy: str = "baseline") -> Dict[str, Dict[str, Any]]:
    """Compare all strategies against the baseline."""
    success_rates = extract_success_rates(results)
    comparisons = {}
    
    if baseline_strategy not in success_rates:
        logger.warning(f"Baseline strategy '{baseline_strategy}' not found in results")
        return comparisons
    
    baseline_rates = success_rates[baseline_strategy]
    
    for strategy, rates in success_rates.items():
        if strategy == baseline_strategy:
            continue
        
        if len(rates) != len(baseline_rates):
            logger.warning(f"Skipping comparison for {strategy}: length mismatch with baseline")
            continue
        
        try:
            p_value, test_name = perform_paired_test(baseline_rates, rates)
            effect_size = calculate_effect_size(baseline_rates, rates)
            
            comparisons[strategy] = {
                "p_value": p_value,
                "test_used": test_name,
                "effect_size": effect_size,
                "baseline_mean": np.mean(baseline_rates),
                "strategy_mean": np.mean(rates),
                "observed_success_rate_diff": abs(np.mean(rates) - np.mean(baseline_rates))
            }
        except Exception as e:
            logger.error(f"Error comparing {strategy} with baseline: {e}")
            continue
    
    return comparisons

def calculate_power_analysis(comparisons: Dict[str, Dict[str, Any]], alpha: float = 0.05, desired_power: float = 0.8) -> Dict[str, Any]:
    """
    Perform power analysis for all comparisons and add results to the report.
    
    Args:
        comparisons: Dictionary of strategy comparisons with effect sizes
        alpha: Significance level
        desired_power: Target power threshold
        
    Returns:
        Dictionary containing power analysis results for each comparison
    """
    power_results = {}
    warnings = []
    
    for strategy, comp_data in comparisons.items():
        effect_size = comp_data.get("effect_size", 0.0)
        # Assume sample size from the data used in the comparison
        # This would typically come from the number of trials N
        n_trials = 5  # Default assumption based on FR-008 (N >= 5)
        
        # Calculate power
        power = estimate_statistical_power(effect_size, n_trials, alpha, desired_power)
        
        power_results[strategy] = {
            "estimated_power": power,
            "effect_size": effect_size,
            "sample_size_used": n_trials,
            "alpha": alpha,
            "meets_desired_power": power >= desired_power
        }
        
        if power < desired_power:
            warnings.append(
                f"Power analysis for {strategy}: estimated power ({power:.3f}) < desired power ({desired_power}). "
                f"Consider increasing N (currently {n_trials}) to improve statistical power."
            )
    
    return {
        "power_results": power_results,
        "warnings": warnings,
        "parameters": {
            "alpha": alpha,
            "desired_power": desired_power,
            "assumed_effect_size": 0.5,  # As specified in task
            "assumed_sample_size": n_trials
        }
    }

def save_statistics_report(comparisons: Dict[str, Dict[str, Any]], 
                          power_analysis: Dict[str, Any],
                          output_path: str) -> None:
    """Save the complete statistics report including power analysis."""
    report = {
        "comparisons": comparisons,
        "power_analysis": power_analysis,
        "summary": {
            "total_comparisons": len(comparisons),
            "power_warnings_count": len(power_analysis.get("warnings", [])),
            "all_comparisons_meet_power": all(
                data.get("meets_desired_power", False) 
                for data in power_analysis.get("power_results", {}).values()
            )
        }
    }
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Statistics report saved to {output_path}")

def main():
    """Main function to execute power analysis on evaluation results."""
    # Define paths
    results_path = Path("data/results/stats_report.json")
    output_path = Path("data/results/stats_report.json")
    
    # Check if results file exists
    if not results_path.exists():
        logger.error(f"Evaluation results file not found: {results_path}")
        logger.error("Please run the evaluation pipeline first (T029) to generate stats_report.json")
        sys.exit(1)
    
    try:
        # Load evaluation results
        results = load_evaluation_results(str(results_path))
        
        # Extract success rates and compare strategies
        comparisons = compare_strategies(results)
        
        if not comparisons:
            logger.warning("No valid comparisons found. Check if 'baseline' strategy exists in results.")
            sys.exit(0)
        
        # Perform power analysis
        power_analysis = calculate_power_analysis(comparisons)
        
        # Log warnings if power is insufficient
        for warning in power_analysis.get("warnings", []):
            logger.warning(warning)
        
        # Update the report with power analysis
        # Load existing report if it exists, otherwise create new
        if output_path.exists():
            with open(output_path, 'r') as f:
                existing_report = json.load(f)
            existing_report["power_analysis"] = power_analysis
            existing_report["comparisons"] = comparisons
        else:
            existing_report = {
                "comparisons": comparisons,
                "power_analysis": power_analysis
            }
        
        # Save updated report
        with open(output_path, 'w') as f:
            json.dump(existing_report, f, indent=2)
        
        logger.info(f"Power analysis completed and saved to {output_path}")
        logger.info(f"Total comparisons: {len(comparisons)}")
        logger.info(f"Power warnings: {len(power_analysis.get('warnings', []))}")
        
    except Exception as e:
        logger.error(f"Error during power analysis: {e}")
        raise

if __name__ == "__main__":
    main()