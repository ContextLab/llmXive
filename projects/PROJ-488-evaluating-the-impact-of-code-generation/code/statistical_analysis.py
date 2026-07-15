import os
import sys
import logging
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from scipy import stats

# Import local utilities
from seeds import set_seed, get_seed_value
from logging_config import setup_logger, get_logger
from state_tracker import update_state_with_artifact, load_state_file, save_state_file

# Configure logger
logger = setup_logger("statistical_analysis")

class PowerAnalysisResult:
    def __init__(self, metric_name: str, sample_size: int, effect_size: float, power: float, passed: bool):
        self.metric_name = metric_name
        self.sample_size = sample_size
        self.effect_size = effect_size
        self.power = power
        self.passed = passed

def compute_effect_size_cohen_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """Compute Cohen's d effect size."""
    mean1, mean2 = np.mean(group1), np.mean(group2)
    std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)
    n1, n2 = len(group1), len(group2)
    
    # Pooled standard deviation
    pooled_std = math.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
    return (mean1 - mean2) / pooled_std

def compute_power_cohen_d(effect_size: float, n1: int, n2: int, alpha: float = 0.05) -> float:
    """Approximate power for a two-sample t-test given effect size and sample sizes."""
    # Using non-central t-distribution approximation
    # d = effect size
    # n1, n2 = sample sizes
    # alpha = significance level
    
    df = n1 + n2 - 2
    ncp = effect_size * math.sqrt((n1 * n2) / (n1 + n2))
    
    # Critical t-value
    t_crit = stats.t.ppf(1 - alpha/2, df)
    
    # Power is probability of rejecting null when alternative is true
    # P(|T| > t_crit | non-central t with ncp)
    power = 1 - (stats.nct.cdf(t_crit, df, ncp) - stats.nct.cdf(-t_crit, df, ncp))
    return power

def compute_cliffs_delta(group1: np.ndarray, group2: np.ndarray) -> float:
    """Compute Cliff's Delta effect size."""
    n1, n2 = len(group1), len(group2)
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
    abs_delta = abs(cliffs_delta)
    if abs_delta < 0.147:
        return "negligible"
    elif abs_delta < 0.33:
        return "small"
    elif abs_delta < 0.474:
        return "medium"
    else:
        return "large"

def load_metrics_data(metrics_dir: Path) -> Dict[str, Dict[str, List[float]]]:
    """Load metric data from CSV files into a structured dictionary."""
    data = {}
    if not metrics_dir.exists():
        raise FileNotFoundError(f"Metrics directory not found: {metrics_dir}")
    
    for csv_file in metrics_dir.glob("*.csv"):
        metric_name = csv_file.stem
        df = pd.read_csv(csv_file)
        
        # Expect columns: snippet_id, group (human/llm), score
        if 'group' not in df.columns or 'score' not in df.columns:
            logger.warning(f"Skipping {csv_file}: missing required columns")
            continue
        
        groups = df['group'].unique()
        if len(groups) < 2:
            logger.warning(f"Skipping {csv_file}: not enough groups")
            continue
        
        data[metric_name] = {
            'human': df[df['group'] == 'human']['score'].dropna().tolist(),
            'llm': df[df['group'] == 'llm']['score'].dropna().tolist()
        }
    
    return data

def run_mann_whitney_u_test(group1: List[float], group2: List[float]) -> Tuple[float, float]:
    """
    Run Mann-Whitney U test.
    Returns (U_statistic, p_value).
    """
    if len(group1) == 0 or len(group2) == 0:
        logger.error("One of the groups is empty")
        return 0.0, 1.0
    
    u_stat, p_val = stats.mannwhitneyu(group1, group2, alternative='two-sided')
    return float(u_stat), float(p_val)

def run_power_analysis_for_metric(metric_name: str, group1: List[float], group2: List[float], alpha: float = 0.05) -> PowerAnalysisResult:
    """Run power analysis for a specific metric."""
    n1, n2 = len(group1), len(group2)
    if n1 == 0 or n2 == 0:
        return PowerAnalysisResult(metric_name, 0, 0.0, 0.0, False)
    
    effect_size = compute_effect_size_cohen_d(np.array(group1), np.array(group2))
    power = compute_power_cohen_d(effect_size, n1, n2, alpha)
    passed = power >= 0.8
    
    return PowerAnalysisResult(metric_name, n1, effect_size, power, passed)

def run_power_analysis_on_metrics(metrics_data: Dict[str, Dict[str, List[float]]], alpha: float = 0.05) -> Dict[str, PowerAnalysisResult]:
    """Run power analysis for all metrics."""
    results = {}
    for metric_name, groups in metrics_data.items():
        results[metric_name] = run_power_analysis_for_metric(metric_name, groups['human'], groups['llm'], alpha)
        res = results[metric_name]
        if not res.passed:
            logger.warning(f"Power analysis failed for {metric_name}: power={res.power:.3f} < 0.8")
        else:
            logger.info(f"Power analysis passed for {metric_name}: power={res.power:.3f}")
    return results

def run_mann_whitney_u_analysis(metrics_data: Dict[str, Dict[str, List[float]]]) -> Dict[str, Dict[str, Any]]:
    """
    Run Mann-Whitney U test for each metric comparison.
    Returns dictionary of results.
    """
    results = {}
    for metric_name, groups in metrics_data.items():
        u_stat, p_val = run_mann_whitney_u_test(groups['human'], groups['llm'])
        results[metric_name] = {
            'metric_name': metric_name,
            'u_statistic': u_stat,
            'p_value': p_val,
            'n_human': len(groups['human']),
            'n_llm': len(groups['llm'])
        }
        logger.info(f"Mann-Whitney U test for {metric_name}: U={u_stat:.2f}, p={p_val:.6f}")
    return results

def save_mann_whitney_results(results: Dict[str, Dict[str, Any]], output_path: Path):
    """Save Mann-Whitney U test results to a CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([
        {
            'metric_name': r['metric_name'],
            'u_statistic': r['u_statistic'],
            'p_value': r['p_value'],
            'n_human': r['n_human'],
            'n_llm': r['n_llm']
        }
        for r in results.values()
    ])
    df.to_csv(output_path, index=False)
    logger.info(f"Saved Mann-Whitney U results to {output_path}")

def save_power_analysis_results(results: Dict[str, PowerAnalysisResult], output_path: Path):
    """Save power analysis results to a CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([
        {
            'metric_name': r.metric_name,
            'sample_size': r.sample_size,
            'effect_size': r.effect_size,
            'power': r.power,
            'passed': r.passed
        }
        for r in results.values()
    ])
    df.to_csv(output_path, index=False)
    logger.info(f"Saved power analysis results to {output_path}")

def apply_benjamini_hochberg_correction(p_values: List[float]) -> List[float]:
    """Apply Benjamini-Hochberg correction to a list of p-values."""
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values and keep original indices
    sorted_indices = sorted(range(n), key=lambda i: p_values[i])
    sorted_p = [p_values[i] for i in sorted_indices]
    
    corrected_p = [0.0] * n
    prev_corrected = 1.0
    
    # Calculate corrected p-values from largest to smallest
    for i in range(n - 1, -1, -1):
        rank = i + 1
        # BH critical value
        critical_value = (rank / n) * 0.05
        # The corrected p-value is min(critical_value, previous_corrected)
        # But we also ensure monotonicity
        corrected_val = min(critical_value, prev_corrected)
        # Actually, standard BH: p_adj[i] = p[i] * n / rank
        # Then enforce monotonicity from the end
        corrected_val = sorted_p[i] * n / rank
        corrected_p[sorted_indices[i]] = corrected_val
        prev_corrected = corrected_val
    
    # Enforce monotonicity (cumulative min from the end)
    for i in range(n - 2, -1, -1):
        corrected_p[sorted_indices[i]] = min(corrected_p[sorted_indices[i]], corrected_p[sorted_indices[i+1]])
    
    # Cap at 1.0
    corrected_p = [min(p, 1.0) for p in corrected_p]
    
    return corrected_p

def run_benjamini_hochberg_correction_on_metrics(mw_results: Dict[str, Dict[str, Any]], output_path: Path):
    """Apply BH correction to all metric p-values and save results."""
    metric_names = list(mw_results.keys())
    p_values = [mw_results[m]['p_value'] for m in metric_names]
    
    adjusted_p = apply_benjamini_hochberg_correction(p_values)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([
        {
            'metric_name': metric_names[i],
            'raw_p_value': p_values[i],
            'adjusted_p_value': adjusted_p[i]
        }
        for i in range(len(metric_names))
    ])
    df.to_csv(output_path, index=False)
    logger.info(f"Saved BH corrected p-values to {output_path}")
    return df

def run_cliffs_delta_analysis(metrics_data: Dict[str, Dict[str, List[float]]]) -> Dict[str, Dict[str, Any]]:
    """Compute Cliff's delta for each metric."""
    results = {}
    for metric_name, groups in metrics_data.items():
        delta = compute_cliffs_delta(np.array(groups['human']), np.array(groups['llm']))
        magnitude = get_effect_size_magnitude(delta)
        results[metric_name] = {
            'metric_name': metric_name,
            'cliffs_delta': delta,
            'magnitude': magnitude,
            'n_human': len(groups['human']),
            'n_llm': len(groups['llm'])
        }
        logger.info(f"Cliff's delta for {metric_name}: {delta:.4f} ({magnitude})")
    return results

def save_cliffs_delta_results(results: Dict[str, Dict[str, Any]], output_path: Path):
    """Save Cliff's delta results to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([
        {
            'metric_name': r['metric_name'],
            'cliffs_delta': r['cliffs_delta'],
            'magnitude': r['magnitude'],
            'n_human': r['n_human'],
            'n_llm': r['n_llm']
        }
        for r in results.values()
    ])
    df.to_csv(output_path, index=False)
    logger.info(f"Saved Cliff's delta results to {output_path}")

def main():
    """Main entry point for statistical analysis."""
    set_seed(get_seed_value())
    
    project_root = Path(__file__).parent.parent
    metrics_dir = project_root / "data" / "metrics"
    results_dir = project_root / "results"
    
    logger.info("Starting statistical analysis pipeline")
    
    # Load metrics
    try:
        metrics_data = load_metrics_data(metrics_dir)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    if not metrics_data:
        logger.error("No metric data found. Ensure metrics have been extracted.")
        sys.exit(1)
    
    logger.info(f"Loaded {len(metrics_data)} metrics for analysis")
    
    # 1. Mann-Whitney U Test
    mw_results = run_mann_whitney_u_analysis(metrics_data)
    mw_output_path = results_dir / "mann_whitney_u_results.csv"
    save_mann_whitney_results(mw_results, mw_output_path)
    
    # 2. Power Analysis
    power_results = run_power_analysis_on_metrics(metrics_data)
    power_output_path = results_dir / "power_analysis_results.csv"
    save_power_analysis_results(power_results, power_output_path)
    
    # 3. Cliff's Delta
    cd_results = run_cliffs_delta_analysis(metrics_data)
    cd_output_path = results_dir / "cliffs_delta_results.csv"
    save_cliffs_delta_results(cd_results, cd_output_path)
    
    # 4. Benjamini-Hochberg Correction
    bh_output_path = results_dir / "bh_corrected_pvalues.csv"
    run_benjamini_hochberg_correction_on_metrics(mw_results, bh_output_path)
    
    # Update state file
    state_file = project_root / "state" / "projects" / "PROJ-488-evaluating-the-impact-of-code-generation.yaml"
    if state_file.exists():
        update_state_with_artifact(state_file, "statistical_analysis", mw_output_path)
        update_state_with_artifact(state_file, "statistical_analysis", power_output_path)
        update_state_with_artifact(state_file, "statistical_analysis", cd_output_path)
        update_state_with_artifact(state_file, "statistical_analysis", bh_output_path)
    
    logger.info("Statistical analysis pipeline completed successfully")

if __name__ == "__main__":
    main()
