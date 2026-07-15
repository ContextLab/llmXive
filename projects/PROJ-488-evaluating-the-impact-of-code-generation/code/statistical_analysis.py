import os
import sys
import logging
import math
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from scipy.stats import mannwhitneyu
from statsmodels.stats.multitest import multipletests

from data_model import MetricResult
from logging_config import setup_logger, get_logger
from state_tracker import update_state_with_artifact, load_state_file, save_state_file

# Ensure logger is configured
logger = get_logger("statistical_analysis")

class PowerAnalysisResult:
    def __init__(self, metric_name: str, achieved_power: float, effect_size: float, sample_size: int):
        self.metric_name = metric_name
        self.achieved_power = achieved_power
        self.effect_size = effect_size
        self.sample_size = sample_size

def compute_effect_size_cohen_d(group1: List[float], group2: List[float]) -> float:
    """Compute Cohen's d effect size."""
    mean1, mean2 = sum(group1) / len(group1), sum(group2) / len(group2)
    var1 = sum((x - mean1) ** 2 for x in group1) / len(group1)
    var2 = sum((x - mean2) ** 2 for x in group2) / len(group2)
    pooled_std = math.sqrt((var1 + var2) / 2)
    if pooled_std == 0:
        return 0.0
    return (mean1 - mean2) / pooled_std

def compute_power_cohen_d(effect_size: float, n1: int, n2: int, alpha: float = 0.05) -> float:
    """Approximate power calculation for t-test (using normal approximation)."""
    # Simplified approximation: Z = d * sqrt(n1*n2 / (2*(n1+n2)))
    # Power = Phi(Z - Z_alpha)
    from scipy.stats import norm
    n_eff = (n1 * n2) / (n1 + n2)
    z_stat = abs(effect_size) * math.sqrt(n_eff / 2)
    z_crit = norm.ppf(1 - alpha / 2)
    power = norm.cdf(z_stat - z_crit)
    return power

def compute_cliffs_delta(group1: List[float], group2: List[float]) -> float:
    """Compute Cliff's delta effect size."""
    n1, n2 = len(group1), len(group2)
    if n1 == 0 or n2 == 0:
        return 0.0
    count_greater = 0
    count_less = 0
    for x in group1:
        for y in group2:
            if x > y:
                count_greater += 1
            elif x < y:
                count_less += 1
    return (count_greater - count_less) / (n1 * n2)

def get_effect_size_magnitude(cliffs_delta: float) -> str:
    """Map Cliff's delta to magnitude labels."""
    abs_val = abs(cliffs_delta)
    if abs_val < 0.147:
        return "negligible"
    elif abs_val < 0.33:
        return "small"
    elif abs_val < 0.474:
        return "medium"
    else:
        return "large"

def load_metrics_for_comparison(metric_type: str) -> Tuple[List[float], List[float]]:
    """
    Load metric values for human and LLM groups from processed CSVs.
    Expects files like: data/metrics/{metric_type}_human.csv and data/metrics/{metric_type}_llm.csv
    """
    metrics_dir = Path("data/metrics")
    if not metrics_dir.exists():
        raise FileNotFoundError(f"Metrics directory not found: {metrics_dir}")

    human_file = metrics_dir / f"{metric_type}_human.csv"
    llm_file = metrics_dir / f"{metric_type}_llm.csv"

    if not human_file.exists() or not llm_file.exists():
        raise FileNotFoundError(f"Missing metric files for {metric_type}")

    df_human = pd.read_csv(human_file)
    df_llm = pd.read_csv(llm_file)

    # Identify the score column (usually 'score' or 'value')
    score_col = None
    for col in ['score', 'value', 'result']:
        if col in df_human.columns:
            score_col = col
            break
    
    if score_col is None:
        score_col = df_human.columns[1] # Fallback to second column

    group1 = df_human[score_col].dropna().tolist()
    group2 = df_llm[score_col].dropna().tolist()

    return group1, group2

def run_mann_whitney_u_test(group1: List[float], group2: List[float], alternative: str = 'two-sided') -> Tuple[float, float]:
    """
    Run Mann-Whitney U test.
    Returns: (statistic, p_value)
    """
    if len(group1) < 2 or len(group2) < 2:
        logger.warning("Insufficient data for Mann-Whitney U test")
        return 0.0, 1.0
    
    try:
        stat, p_val = mannwhitneyu(group1, group2, alternative=alternative)
        return float(stat), float(p_val)
    except Exception as e:
        logger.error(f"Error running Mann-Whitney U test: {e}")
        return 0.0, 1.0

def run_power_analysis_for_metric(metric_name: str, group1: List[float], group2: List[float]) -> PowerAnalysisResult:
    """Run power analysis for a single metric."""
    d = compute_effect_size_cohen_d(group1, group2)
    power = compute_power_cohen_d(d, len(group1), len(group2))
    return PowerAnalysisResult(metric_name, power, d, len(group1))

def run_power_analysis_on_metrics(metrics: List[str]) -> List[PowerAnalysisResult]:
    """Run power analysis for all specified metrics."""
    results = []
    for metric in metrics:
        try:
            g1, g2 = load_metrics_for_comparison(metric)
            res = run_power_analysis_for_metric(metric, g1, g2)
            results.append(res)
            if res.achieved_power < 0.8:
                logger.warning(f"Low power ({res.achieved_power:.2f}) for metric {metric}")
        except Exception as e:
            logger.error(f"Failed power analysis for {metric}: {e}")
    return results

def run_mann_whitney_u_analysis(metrics: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Run Mann-Whitney U test for each metric and return results.
    """
    results = {}
    for metric in metrics:
        try:
            g1, g2 = load_metrics_for_comparison(metric)
            stat, p_val = run_mann_whitney_u_test(g1, g2)
            results[metric] = {
                "statistic": stat,
                "p_value": p_val,
                "n_human": len(g1),
                "n_llm": len(g2)
            }
            logger.info(f"Mann-Whitney U for {metric}: p={p_val:.4f}")
        except Exception as e:
            logger.error(f"Failed Mann-Whitney U for {metric}: {e}")
            results[metric] = {"error": str(e)}
    return results

def run_cliffs_delta_analysis(metrics: List[str]) -> Dict[str, Dict[str, Any]]:
    """Compute Cliff's delta for each metric."""
    results = {}
    for metric in metrics:
        try:
            g1, g2 = load_metrics_for_comparison(metric)
            delta = compute_cliffs_delta(g1, g2)
            magnitude = get_effect_size_magnitude(delta)
            results[metric] = {
                "cliffs_delta": delta,
                "magnitude": magnitude
            }
        except Exception as e:
            logger.error(f"Failed Cliff's delta for {metric}: {e}")
            results[metric] = {"error": str(e)}
    return results

def apply_benjamini_hochberg_correction(results: Dict[str, Dict[str, Any]], alpha: float = 0.05) -> Dict[str, Dict[str, Any]]:
    """
    Apply Benjamini-Hochberg correction to p-values.
    Input: results dict with 'p_value' keys.
    Output: dict with added 'p_adjusted' and 'significant' keys.
    """
    metrics = list(results.keys())
    p_values = []
    valid_metrics = []
    
    for m in metrics:
        if 'p_value' in results[m]:
            p_values.append(results[m]['p_value'])
            valid_metrics.append(m)
    
    if not p_values:
        return results

    # Use statsmodels for BH correction
    try:
        reject, p_adjusted, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')
    except Exception as e:
        logger.error(f"BH correction failed: {e}")
        return results

    for i, m in enumerate(valid_metrics):
        results[m]['p_adjusted'] = float(p_adjusted[i])
        results[m]['significant'] = bool(reject[i])
    
    return results

def run_benjamini_hochberg_correction_on_metrics(metrics: List[str]) -> Dict[str, Dict[str, Any]]:
    """Run Mann-Whitney, then apply BH correction."""
    raw_results = run_mann_whitney_u_analysis(metrics)
    corrected_results = apply_benjamini_hochberg_correction(raw_results)
    return corrected_results

def write_statistical_results_to_file(results: Dict[str, Dict[str, Any]], output_path: str):
    """Write statistical results to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Wrote statistical results to {output_path}")

def main():
    """Main entry point for T028: Mann-Whitney U test execution."""
    logger.info("Starting Mann-Whitney U test analysis (T028)")
    
    # Define metrics to analyze based on project scope
    metrics = ['cyclomatic_complexity', 'maintainability_index', 'potential_bugs']
    
    try:
        # Run analysis
        results = run_benjamini_hochberg_correction_on_metrics(metrics)
        
        # Write raw p-values and adjusted p-values
        output_file = "data/metrics/statistical_results.json"
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        write_statistical_results_to_file(results, output_file)
        
        # Update state
        state_file = Path("state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml")
        if state_file.exists():
            update_state_with_artifact(str(state_file), output_file)
        
        logger.info("T028 completed successfully")
        return results
    except Exception as e:
        logger.error(f"Task T028 failed: {e}")
        raise

if __name__ == "__main__":
    main()