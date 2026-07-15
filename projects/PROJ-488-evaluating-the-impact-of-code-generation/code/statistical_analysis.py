"""
Statistical analysis module for comparing code metrics between human-written and LLM-generated code.

This module implements:
- Power analysis (Cohen's d based)
- Mann-Whitney U tests
- Cliff's Delta effect size
- Benjamini-Hochberg correction
"""
import os
import sys
import logging
import math
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from scipy import stats
from scipy.stats import mannwhitneyu

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.logging_config import get_logger
from code.data_model import MetricResult

# Configure logger
logger = get_logger(__name__)

@dataclass
class PowerAnalysisResult:
    """Result of a power analysis calculation."""
    metric_name: str
    effect_size: float
    sample_size: int
    power: float
    alpha: float
    meets_threshold: bool
    
def compute_effect_size_cohen_d(group1: List[float], group2: List[float]) -> float:
    """
    Compute Cohen's d effect size between two groups.
    
    Args:
        group1: First group of values (e.g., human-written)
        group2: Second group of values (e.g., LLM-generated)
        
    Returns:
        Cohen's d value
    """
    n1, n2 = len(group1), len(group2)
    if n1 == 0 or n2 == 0:
        logger.warning("One or both groups are empty. Returning 0 effect size.")
        return 0.0
        
    mean1 = sum(group1) / n1
    mean2 = sum(group2) / n2
    
    var1 = sum((x - mean1) ** 2 for x in group1) / (n1 - 1) if n1 > 1 else 0
    var2 = sum((x - mean2) ** 2 for x in group2) / (n2 - 1) if n2 > 1 else 0
    
    # Pooled standard deviation
    pooled_std = math.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        logger.warning("Pooled standard deviation is zero. Returning 0 effect size.")
        return 0.0
        
    return (mean1 - mean2) / pooled_std

def compute_power_cohen_d(effect_size: float, sample_size: int, alpha: float = 0.05) -> float:
    """
    Compute statistical power given effect size, sample size, and alpha.
    Uses approximation for two-sample t-test power.
    
    Args:
        effect_size: Cohen's d value
        sample_size: Total sample size (n1 + n2, assuming equal groups)
        alpha: Significance level
        
    Returns:
        Statistical power (0 to 1)
    """
    if sample_size <= 2:
        logger.warning("Sample size too small for power calculation.")
        return 0.0
        
    # Approximation for two-sample t-test power
    # Using non-central t-distribution approximation
    n_per_group = sample_size / 2
    if n_per_group < 2:
        return 0.0
        
    # Non-centrality parameter
    ncp = effect_size * math.sqrt(n_per_group / 2)
    
    # Critical t-value (two-tailed)
    df = sample_size - 2
    t_crit = stats.t.ppf(1 - alpha / 2, df)
    
    # Power = P(T > t_crit | non-central t with ncp)
    # Approximation using normal distribution for large samples
    # Power ≈ Φ(ncp - t_crit) + Φ(-ncp - t_crit)
    # For two-sided test, we focus on the primary tail
    power = stats.norm.cdf(ncp - t_crit) + stats.norm.cdf(-ncp - t_crit)
    
    return max(0.0, min(1.0, power))

def compute_cliffs_delta(group1: List[float], group2: List[float]) -> float:
    """
    Compute Cliff's Delta effect size.
    Cliff's Delta measures the probability that a value from group1 is greater
    than a value from group2, minus the reverse probability.
    
    Args:
        group1: First group of values
        group2: Second group of values
        
    Returns:
        Cliff's Delta value (-1 to 1)
    """
    n1, n2 = len(group1), len(group2)
    if n1 == 0 or n2 == 0:
        logger.warning("One or both groups are empty. Returning 0 Cliff's Delta.")
        return 0.0
        
    count_greater = 0
    count_less = 0
    
    for x in group1:
        for y in group2:
            if x > y:
                count_greater += 1
            elif x < y:
                count_less += 1
                
    total_pairs = n1 * n2
    if total_pairs == 0:
        return 0.0
        
    return (count_greater - count_less) / total_pairs

def get_effect_size_magnitude(cliffs_delta: float) -> str:
    """
    Classify Cliff's Delta magnitude.
    
    Args:
        cliffs_delta: Cliff's Delta value
        
    Returns:
        Magnitude label: 'negligible', 'small', 'medium', 'large'
    """
    abs_delta = abs(cliffs_delta)
    if abs_delta < 0.147:
        return 'negligible'
    elif abs_delta < 0.33:
        return 'small'
    elif abs_delta < 0.474:
        return 'medium'
    else:
        return 'large'

def load_metrics_for_comparison(
    metric_type: str, 
    metrics_dir: Path
) -> Tuple[List[float], List[float], int, int]:
    """
    Load metric values for human-written and LLM-generated groups.
    
    Args:
        metric_type: Type of metric (e.g., 'cyclomatic_complexity', 'maintainability')
        metrics_dir: Directory containing metric CSV files
        
    Returns:
        Tuple of (human_values, llm_values, human_count, llm_count)
    """
    # Expected file naming convention based on T023
    # Files are typically named: {metric_type}_metrics.csv
    # with columns: snippet_id, group, score
    
    file_path = metrics_dir / f"{metric_type}_metrics.csv"
    if not file_path.exists():
        # Try alternative naming
        file_path = metrics_dir / f"metrics_{metric_type}.csv"
        
    if not file_path.exists():
        logger.error(f"Metric file not found for {metric_type}")
        return [], [], 0, 0
        
    df = pd.read_csv(file_path)
    
    human_values = df[df['group'] == 'human']['score'].dropna().tolist()
    llm_values = df[df['group'] == 'llm']['score'].dropna().tolist()
    
    return human_values, llm_values, len(human_values), len(llm_values)

def run_mann_whitney_u_test(group1: List[float], group2: List[float]) -> Tuple[float, float]:
    """
    Run Mann-Whitney U test between two groups.
    
    Args:
        group1: First group of values
        group2: Second group of values
        
    Returns:
        Tuple of (U statistic, p-value)
    """
    if len(group1) < 2 or len(group2) < 2:
        logger.warning("Insufficient data for Mann-Whitney U test.")
        return 0.0, 1.0
        
    try:
        stat, p_value = mannwhitneyu(group1, group2, alternative='two-sided')
        return stat, p_value
    except Exception as e:
        logger.error(f"Error in Mann-Whitney U test: {e}")
        return 0.0, 1.0

def run_power_analysis_for_metric(
    metric_name: str,
    human_values: List[float],
    llm_values: List[float],
    alpha: float = 0.05,
    power_threshold: float = 0.8
) -> PowerAnalysisResult:
    """
    Run power analysis for a specific metric comparison.
    Computes achieved power and checks against threshold.
    
    Args:
        metric_name: Name of the metric
        human_values: Values from human-written code
        llm_values: Values from LLM-generated code
        alpha: Significance level
        power_threshold: Minimum acceptable power (default 0.8)
        
    Returns:
        PowerAnalysisResult with computed power and threshold check
    """
    if not human_values or not llm_values:
        logger.warning(f"Empty data for {metric_name}. Cannot compute power.")
        return PowerAnalysisResult(
            metric_name=metric_name,
            effect_size=0.0,
            sample_size=0,
            power=0.0,
            alpha=alpha,
            meets_threshold=False
        )
        
    effect_size = compute_effect_size_cohen_d(human_values, llm_values)
    total_sample = len(human_values) + len(llm_values)
    
    power = compute_power_cohen_d(effect_size, total_sample, alpha)
    meets_threshold = power >= power_threshold
    
    # LOG WARNING IF POWER IS BELOW THRESHOLD
    if not meets_threshold:
        logger.warning(
            f"Power analysis for '{metric_name}' FAILED threshold: "
            f"Power={power:.3f} < {power_threshold:.2f}. "
            f"Effect size (Cohen's d)={effect_size:.3f}, "
            f"Sample size={total_sample}. "
            f"Consider increasing sample size or interpreting results with caution."
        )
    else:
        logger.info(
            f"Power analysis for '{metric_name}' PASSED: "
            f"Power={power:.3f} >= {power_threshold:.2f}."
        )
        
    return PowerAnalysisResult(
        metric_name=metric_name,
        effect_size=effect_size,
        sample_size=total_sample,
        power=power,
        alpha=alpha,
        meets_threshold=meets_threshold
    )

def run_power_analysis_on_metrics(
    metrics_dir: Path,
    output_path: Path,
    alpha: float = 0.05,
    power_threshold: float = 0.8
) -> List[PowerAnalysisResult]:
    """
    Run power analysis for all metrics in the metrics directory.
    
    Args:
        metrics_dir: Directory containing metric CSV files
        output_path: Path to write results CSV
        alpha: Significance level
        power_threshold: Minimum acceptable power
        
    Returns:
        List of PowerAnalysisResult objects
    """
    logger.info(f"Starting power analysis on metrics in {metrics_dir}")
    
    # List of metric types to analyze
    metric_types = [
        'cyclomatic_complexity',
        'maintainability_index',
        'loc',
        'bug_count',
        'style_issues'
    ]
    
    results = []
    
    for metric_type in metric_types:
        human_vals, llm_vals, _, _ = load_metrics_for_comparison(metric_type, metrics_dir)
        
        if not human_vals or not llm_vals:
            logger.warning(f"Skipping {metric_type}: insufficient data.")
            continue
            
        result = run_power_analysis_for_metric(
            metric_type,
            human_vals,
            llm_vals,
            alpha,
            power_threshold
        )
        results.append(result)
        
    # Write results to CSV
    if results:
        df_results = pd.DataFrame([
            {
                'metric_name': r.metric_name,
                'effect_size_cohen_d': r.effect_size,
                'sample_size': r.sample_size,
                'power': r.power,
                'alpha': r.alpha,
                'meets_threshold': r.meets_threshold
            }
            for r in results
        ])
        df_results.to_csv(output_path, index=False)
        logger.info(f"Power analysis results written to {output_path}")
    else:
        logger.warning("No power analysis results to write.")
        
    return results

def run_mann_whitney_u_analysis(
    metrics_dir: Path,
    output_path: Path
) -> Dict[str, Tuple[float, float]]:
    """
    Run Mann-Whitney U tests for all metrics.
    
    Args:
        metrics_dir: Directory containing metric CSV files
        output_path: Path to write results
        
    Returns:
        Dictionary mapping metric name to (U statistic, p-value)
    """
    logger.info(f"Running Mann-Whitney U tests for metrics in {metrics_dir}")
    
    metric_types = [
        'cyclomatic_complexity',
        'maintainability_index',
        'loc',
        'bug_count',
        'style_issues'
    ]
    
    results = {}
    
    for metric_type in metric_types:
        human_vals, llm_vals, _, _ = load_metrics_for_comparison(metric_type, metrics_dir)
        
        if not human_vals or not llm_vals:
            continue
            
        u_stat, p_val = run_mann_whitney_u_test(human_vals, llm_vals)
        results[metric_type] = (u_stat, p_val)
        
    # Write results
    df_results = pd.DataFrame([
        {
            'metric_name': k,
            'u_statistic': v[0],
            'p_value': v[1]
        }
        for k, v in results.items()
    ])
    df_results.to_csv(output_path, index=False)
    
    return results

def run_cliffs_delta_analysis(
    metrics_dir: Path,
    output_path: Path
) -> Dict[str, float]:
    """
    Compute Cliff's Delta for all metrics.
    
    Args:
        metrics_dir: Directory containing metric CSV files
        output_path: Path to write results
        
    Returns:
        Dictionary mapping metric name to Cliff's Delta
    """
    logger.info(f"Computing Cliff's Delta for metrics in {metrics_dir}")
    
    metric_types = [
        'cyclomatic_complexity',
        'maintainability_index',
        'loc',
        'bug_count',
        'style_issues'
    ]
    
    results = {}
    
    for metric_type in metric_types:
        human_vals, llm_vals, _, _ = load_metrics_for_comparison(metric_type, metrics_dir)
        
        if not human_vals or not llm_vals:
            continue
            
        delta = compute_cliffs_delta(human_vals, llm_vals)
        magnitude = get_effect_size_magnitude(delta)
        results[metric_type] = delta
        
        logger.info(f"Cliff's Delta for {metric_type}: {delta:.3f} ({magnitude})")
        
    # Write results
    df_results = pd.DataFrame([
        {
            'metric_name': k,
            'cliffs_delta': v,
            'magnitude': get_effect_size_magnitude(v)
        }
        for k, v in results.items()
    ])
    df_results.to_csv(output_path, index=False)
    
    return results

def apply_benjamini_hochberg_correction(
    p_values: List[float],
    alpha: float = 0.05
) -> List[float]:
    """
    Apply Benjamini-Hochberg correction for multiple comparisons.
    
    Args:
        p_values: List of raw p-values
        alpha: Significance level
        
    Returns:
        List of adjusted p-values
    """
    n = len(p_values)
    if n == 0:
        return []
        
    # Sort p-values with their original indices
    sorted_indices = sorted(range(n), key=lambda i: p_values[i])
    sorted_p_values = [p_values[i] for i in sorted_indices]
    
    adjusted_p_values = [0.0] * n
    prev_adj = 1.0
    
    # BH procedure
    for i in range(n - 1, -1, -1):
        rank = i + 1
        adj_p = min(prev_adj, sorted_p_values[i] * n / rank)
        adjusted_p_values[sorted_indices[i]] = min(adj_p, 1.0)
        prev_adj = adjusted_p_values[sorted_indices[i]]
        
    return adjusted_p_values

def run_benjamini_hochberg_correction_on_metrics(
    metrics_dir: Path,
    output_path: Path
) -> Dict[str, float]:
    """
    Apply BH correction to all metric p-values.
    
    Args:
        metrics_dir: Directory containing metric CSV files
        output_path: Path to write results
        
    Returns:
        Dictionary mapping metric name to adjusted p-value
    """
    logger.info("Applying Benjamini-Hochberg correction")
    
    # First get raw p-values
    raw_results = run_mann_whitney_u_analysis(metrics_dir, Path("/tmp/raw_pvals.csv"))
    
    metric_names = list(raw_results.keys())
    p_values = [raw_results[k][1] for k in metric_names]
    
    adjusted_p_values = apply_benjamini_hochberg_correction(p_values)
    
    adjusted_results = dict(zip(metric_names, adjusted_p_values))
    
    # Write results
    df_results = pd.DataFrame([
        {
            'metric_name': k,
            'raw_p_value': raw_results[k][1],
            'adjusted_p_value': v
        }
        for k, v in adjusted_results.items()
    ])
    df_results.to_csv(output_path, index=False)
    
    return adjusted_results

def write_statistical_results_to_file(
    power_results: List[PowerAnalysisResult],
    mann_whitney_results: Dict[str, Tuple[float, float]],
    cliffs_delta_results: Dict[str, float],
    bh_results: Dict[str, float],
    output_path: Path
):
    """
    Write all statistical results to a single summary file.
    
    Args:
        power_results: Power analysis results
        mann_whitney_results: Mann-Whitney U test results
        cliffs_delta_results: Cliff's Delta results
        bh_results: BH-corrected p-values
        output_path: Path to write the summary
    """
    logger.info(f"Writing statistical results to {output_path}")
    
    rows = []
    for power in power_results:
        metric = power.metric_name
        mw_stat, mw_p = mann_whitney_results.get(metric, (0, 1))
        delta = cliffs_delta_results.get(metric, 0)
        bh_p = bh_results.get(metric, 1)
        
        rows.append({
            'metric_name': metric,
            'effect_size_cohen_d': power.effect_size,
            'sample_size': power.sample_size,
            'power': power.power,
            'meets_power_threshold': power.meets_threshold,
            'mann_whitney_u': mw_stat,
            'raw_p_value': mw_p,
            'cliffs_delta': delta,
            'cliffs_delta_magnitude': get_effect_size_magnitude(delta),
            'adjusted_p_value': bh_p,
            'significant_after_correction': bh_p < 0.05
        })
        
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    logger.info("Statistical results summary written.")

def main():
    """Main entry point for statistical analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run statistical analysis on code metrics")
    parser.add_argument(
        "--metrics-dir",
        type=str,
        default="data/metrics",
        help="Directory containing metric CSV files"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results/statistical_analysis",
        help="Directory to write results"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level"
    )
    parser.add_argument(
        "--power-threshold",
        type=float,
        default=0.8,
        help="Minimum acceptable power"
    )
    
    args = parser.parse_args()
    
    metrics_dir = Path(args.metrics_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run power analysis
    power_results = run_power_analysis_on_metrics(
        metrics_dir,
        output_dir / "power_analysis.csv",
        args.alpha,
        args.power_threshold
    )
    
    # Run Mann-Whitney U tests
    mw_results = run_mann_whitney_u_analysis(
        metrics_dir,
        output_dir / "mann_whitney_u.csv"
    )
    
    # Run Cliff's Delta analysis
    delta_results = run_cliffs_delta_analysis(
        metrics_dir,
        output_dir / "cliffs_delta.csv"
    )
    
    # Apply BH correction
    bh_results = run_benjamini_hochberg_correction_on_metrics(
        metrics_dir,
        output_dir / "bh_corrected_pvalues.csv"
    )
    
    # Write summary
    write_statistical_results_to_file(
        power_results,
        mw_results,
        delta_results,
        bh_results,
        output_dir / "statistical_summary.csv"
    )
    
    logger.info("Statistical analysis complete.")

if __name__ == "__main__":
    main()
