import os
import sys
import logging
import math
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union
from dataclasses import dataclass
from scipy import stats
from scipy.special import erf

# Import existing project utilities
from logging_config import get_logger
from data_model import MetricResult

@dataclass
class PowerAnalysisResult:
    metric_name: str
    group1_label: str
    group2_label: str
    effect_size: float
    sample_size: float
    power: float
    alpha: float
    threshold_met: bool
    warning_message: Optional[str]

def compute_effect_size_cohen_d(group1: List[float], group2: List[float]) -> float:
    """
    Compute Cohen's d effect size between two groups.
    d = (mean1 - mean2) / pooled_std
    """
    if not group1 or not group2:
        return 0.0
    
    mean1 = sum(group1) / len(group1)
    mean2 = sum(group2) / len(group2)
    
    n1 = len(group1)
    n2 = len(group2)
    
    var1 = sum((x - mean1) ** 2 for x in group1) / (n1 - 1) if n1 > 1 else 0.0
    var2 = sum((x - mean2) ** 2 for x in group2) / (n2 - 1) if n2 > 1 else 0.0
    
    # Pooled standard deviation
    pooled_std = math.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
    
    return (mean1 - mean2) / pooled_std

def compute_power_cohen_d(effect_size: float, sample_size: float, alpha: float = 0.05) -> float:
    """
    Compute achieved statistical power given effect size, sample size, and alpha.
    Uses the non-central t-distribution approximation for two-sample t-test.
    
    Power = P(|T| > t_crit | non-centrality parameter = delta)
    """
    if sample_size <= 0 or effect_size == 0:
        return 0.0
    
    # For two independent samples of equal size n
    # Non-centrality parameter (delta)
    delta = effect_size * math.sqrt(sample_size / 2)
    
    # Degrees of freedom
    df = 2 * sample_size - 2
    
    # Critical t-value for two-tailed test
    t_crit = stats.t.ppf(1 - alpha / 2, df)
    
    # Approximate power using normal approximation for large df
    # Power = P(Z > t_crit - delta) + P(Z < -t_crit - delta)
    # Simplified: Power ≈ 1 - Φ(t_crit - delta) + Φ(-t_crit - delta)
    # Since delta is usually positive for effect, we focus on the main tail
    
    # More accurate approximation using normal distribution
    z_crit = stats.norm.ppf(1 - alpha / 2)
    
    # Power calculation using normal approximation
    power = stats.norm.cdf(-z_crit + abs(delta)) + stats.norm.cdf(-z_crit - abs(delta))
    
    return max(0.0, min(1.0, power))

def compute_cliffs_delta(group1: List[float], group2: List[float]) -> float:
    """
    Compute Cliff's delta effect size.
    """
    if not group1 or not group2:
        return 0.0
    
    n1 = len(group1)
    n2 = len(group2)
    
    count_greater = 0
    count_less = 0
    count_equal = 0
    
    for x in group1:
        for y in group2:
            if x > y:
                count_greater += 1
            elif x < y:
                count_less += 1
            else:
                count_equal += 1
    
    total = n1 * n2
    if total == 0:
        return 0.0
    
    return (count_greater - count_less) / total

def get_effect_size_magnitude(effect_size: float) -> str:
    """
    Classify effect size magnitude based on Cohen's conventions.
    |d| < 0.2: negligible
    0.2 <= |d| < 0.5: small
    0.5 <= |d| < 0.8: medium
    |d| >= 0.8: large
    """
    abs_d = abs(effect_size)
    if abs_d < 0.2:
        return "negligible"
    elif abs_d < 0.5:
        return "small"
    elif abs_d < 0.8:
        return "medium"
    else:
        return "large"

def load_metrics_for_comparison(
    metric_name: str,
    data_dir: Path
) -> Tuple[List[float], List[float], str, str]:
    """
    Load metric values for human-written and LLM-generated code from processed CSV files.
    Returns (human_values, llm_values, human_label, llm_label)
    """
    # Expected file naming convention based on project structure
    # data/metrics/metric_<metric_name>_human.csv
    # data/metrics/metric_<metric_name>_llm.csv
    
    human_file = data_dir / f"metric_{metric_name}_human.csv"
    llm_file = data_dir / f"metric_{metric_name}_llm.csv"
    
    if not human_file.exists():
        raise FileNotFoundError(f"Human metrics file not found: {human_file}")
    if not llm_file.exists():
        raise FileNotFoundError(f"LLM metrics file not found: {llm_file}")
    
    df_human = pd.read_csv(human_file)
    df_llm = pd.read_csv(llm_file)
    
    # Find the score column (could be 'score', 'value', or metric-specific)
    score_col = None
    for col in ['score', 'value', metric_name, 'cyclomatic_complexity', 'maintainability_index', 'bug_count']:
        if col in df_human.columns:
            score_col = col
            break
    
    if score_col is None:
        # Fallback: use first numeric column
        numeric_cols = df_human.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            score_col = numeric_cols[0]
        else:
            raise ValueError(f"No numeric score column found in {human_file}")
    
    # Get labels from metadata if available, otherwise use defaults
    human_label = df_human.get('group_label', ['human'])[0] if 'group_label' in df_human.columns else "human"
    llm_label = df_llm.get('group_label', ['llm'])[0] if 'group_label' in df_llm.columns else "llm"
    
    # Filter out NaN values
    human_values = df_human[score_col].dropna().tolist()
    llm_values = df_llm[score_col].dropna().tolist()
    
    return human_values, llm_values, human_label, llm_label

def run_mann_whitney_u_test(group1: List[float], group2: List[float]) -> Dict[str, float]:
    """
    Run Mann-Whitney U test and return U statistic and p-value.
    """
    if not group1 or not group2:
        return {'u_statistic': 0.0, 'p_value': 1.0}
    
    u_stat, p_value = stats.mannwhitneyu(group1, group2, alternative='two-sided')
    
    return {
        'u_statistic': float(u_stat),
        'p_value': float(p_value)
    }

def run_power_analysis_for_metric(
    metric_name: str,
    data_dir: Path,
    alpha: float = 0.05,
    power_threshold: float = 0.8
) -> Optional[PowerAnalysisResult]:
    """
    Perform power analysis for a single metric comparing human vs LLM code.
    Computes effect size, sample size, and achieved power.
    Enforces power >= threshold and logs warnings if not met.
    """
    logger = get_logger("statistical_analysis")
    
    try:
        human_values, llm_values, human_label, llm_label = load_metrics_for_comparison(metric_name, data_dir)
        
        if not human_values or not llm_values:
            logger.warning(f"No valid data for metric {metric_name}")
            return None
        
        # Compute effect size (Cohen's d)
        effect_size = compute_effect_size_cohen_d(human_values, llm_values)
        
        # Use the smaller sample size for conservative power estimate
        sample_size = min(len(human_values), len(llm_values))
        
        # Compute achieved power
        power = compute_power_cohen_d(effect_size, sample_size, alpha)
        
        # Check if power threshold is met
        threshold_met = power >= power_threshold
        warning_msg = None
        
        if not threshold_met:
            warning_msg = (
                f"Power analysis for '{metric_name}': achieved power ({power:.4f}) "
                f"is below threshold ({power_threshold}). Effect size: {effect_size:.4f}, "
                f"sample size: {sample_size}. Consider increasing sample size or "
                f"re-evaluating the metric's discriminative ability."
            )
            logger.warning(warning_msg)
        else:
            logger.info(f"Power analysis for '{metric_name}': power = {power:.4f} (threshold met)")
        
        return PowerAnalysisResult(
            metric_name=metric_name,
            group1_label=human_label,
            group2_label=llm_label,
            effect_size=effect_size,
            sample_size=sample_size,
            power=power,
            alpha=alpha,
            threshold_met=threshold_met,
            warning_message=warning_msg
        )
        
    except Exception as e:
        logger.error(f"Error in power analysis for {metric_name}: {str(e)}")
        return None

def run_power_analysis_on_metrics(
    metrics: List[str],
    data_dir: Path,
    alpha: float = 0.05,
    power_threshold: float = 0.8
) -> List[PowerAnalysisResult]:
    """
    Run power analysis for multiple metrics.
    """
    logger = get_logger("statistical_analysis")
    results = []
    
    for metric in metrics:
        result = run_power_analysis_for_metric(metric, data_dir, alpha, power_threshold)
        if result:
            results.append(result)
    
    return results

def run_mann_whitney_u_analysis(
    metrics: List[str],
    data_dir: Path
) -> List[Dict]:
    """
    Run Mann-Whitney U test for multiple metrics.
    """
    results = []
    
    for metric in metrics:
        try:
            human_values, llm_values, _, _ = load_metrics_for_comparison(metric, data_dir)
            if human_values and llm_values:
                test_result = run_mann_whitney_u_test(human_values, llm_values)
                results.append({
                    'metric': metric,
                    **test_result
                })
        except Exception as e:
            logging.getLogger("statistical_analysis").error(f"Error in U-test for {metric}: {e}")
    
    return results

def run_cliffs_delta_analysis(
    metrics: List[str],
    data_dir: Path
) -> List[Dict]:
    """
    Compute Cliff's delta for multiple metrics.
    """
    results = []
    
    for metric in metrics:
        try:
            human_values, llm_values, _, _ = load_metrics_for_comparison(metric, data_dir)
            if human_values and llm_values:
                delta = compute_cliffs_delta(human_values, llm_values)
                magnitude = get_effect_size_magnitude(delta)
                results.append({
                    'metric': metric,
                    'cliffs_delta': delta,
                    'magnitude': magnitude
                })
        except Exception as e:
            logging.getLogger("statistical_analysis").error(f"Error in Cliff's delta for {metric}: {e}")
    
    return results

def apply_benjamini_hochberg_correction(
    p_values: List[float],
    alpha: float = 0.05
) -> List[float]:
    """
    Apply Benjamini-Hochberg correction for multiple comparisons.
    Returns adjusted p-values.
    """
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values and keep original indices
    indexed_pvals = sorted(enumerate(p_values), key=lambda x: x[1])
    sorted_pvals = [x[1] for x in indexed_pvals]
    
    # Compute adjusted p-values
    adjusted = [0.0] * n
    prev_adj = 1.0
    
    for i in range(n - 1, -1, -1):
        rank = i + 1
        adj_val = min(prev_adj, sorted_pvals[i] * n / rank)
        adjusted[indexed_pvals[i][0]] = min(adj_val, 1.0)
        prev_adj = adjusted[indexed_pvals[i][0]]
    
    return adjusted

def run_benjamini_hochberg_correction_on_metrics(
    p_values: List[float],
    alpha: float = 0.05
) -> List[float]:
    """
    Wrapper for BH correction.
    """
    return apply_benjamini_hochberg_correction(p_values, alpha)

def write_statistical_results_to_file(
    results: List[Dict],
    output_path: Path
):
    """
    Write statistical analysis results to a JSON file.
    """
    import json
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def main():
    """
    Main entry point for running power analysis on all metrics.
    """
    logger = get_logger("statistical_analysis")
    logger.info("Starting power analysis pipeline...")
    
    # Define metrics to analyze (based on radon and pylint outputs)
    metrics = [
        'cyclomatic_complexity',
        'maintainability_index',
        'loc',
        'bug_count'
    ]
    
    data_dir = Path("data/metrics")
    output_dir = Path("data/metrics")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run power analysis
    power_results = run_power_analysis_on_metrics(metrics, data_dir, alpha=0.05, power_threshold=0.8)
    
    # Run Mann-Whitney U tests
    u_results = run_mann_whitney_u_analysis(metrics, data_dir)
    
    # Run Cliff's delta analysis
    delta_results = run_cliffs_delta_analysis(metrics, data_dir)
    
    # Combine results
    all_results = []
    for metric in metrics:
        power_entry = next((r for r in power_results if r.metric_name == metric), None)
        u_entry = next((r for r in u_results if r['metric'] == metric), None)
        delta_entry = next((r for r in delta_results if r['metric'] == metric), None)
        
        combined = {
            'metric': metric,
            'power_analysis': {
                'power': power_entry.power if power_entry else None,
                'effect_size': power_entry.effect_size if power_entry else None,
                'sample_size': power_entry.sample_size if power_entry else None,
                'threshold_met': power_entry.threshold_met if power_entry else None,
                'warning': power_entry.warning_message if power_entry else None
            },
            'mann_whitney': u_entry if u_entry else None,
            'cliffs_delta': delta_entry if delta_entry else None
        }
        all_results.append(combined)
    
    # Write results
    output_file = output_dir / "statistical_analysis_results.json"
    write_statistical_results_to_file(all_results, output_file)
    
    logger.info(f"Statistical analysis results written to {output_file}")
    
    # Summary of power analysis
    warnings_count = sum(1 for r in power_results if not r.threshold_met)
    if warnings_count > 0:
        logger.warning(f"Power threshold not met for {warnings_count} metric(s). Review warnings above.")
    
    return all_results

if __name__ == "__main__":
    main()