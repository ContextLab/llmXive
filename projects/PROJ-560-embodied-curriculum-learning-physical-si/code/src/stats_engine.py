import logging
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.formula.api import ols
import json
import os
from pathlib import Path

# Ensure output directory exists
os.makedirs("data/processed", exist_ok=True)

logger = logging.getLogger(__name__)

def run_t_test(gain_scores_embodied: np.ndarray, gain_scores_static: np.ndarray, 
               equal_var: bool = True) -> Tuple[float, float]:
    """
    Perform Student's or Welch's t-test on gain scores.
    Returns (t_statistic, p_value).
    """
    if equal_var:
        t_stat, p_val = stats.ttest_ind(gain_scores_embodied, gain_scores_static, equal_var=True)
    else:
        t_stat, p_val = stats.ttest_ind(gain_scores_embodied, gain_scores_static, equal_var=False)
    return float(t_stat), float(p_val)

def calculate_effect_size(group1: np.ndarray, group2: np.ndarray) -> float:
    """Calculate Cohen's d."""
    mean1, mean2 = np.mean(group1), np.mean(group2)
    std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)
    n1, n2 = len(group1), len(group2)
    
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
    return float((mean1 - mean2) / pooled_std)

def calculate_confidence_interval(effect_size: float, group1: np.ndarray, group2: np.ndarray, 
                                  confidence: float = 0.95) -> Tuple[float, float]:
    """Calculate confidence interval for effect size."""
    n1, n2 = len(group1), len(group2)
    n = n1 + n2
    # Approximate standard error for Cohen's d
    se = np.sqrt((n1 + n2) / (n1 * n2) + effect_size**2 / (2 * (n1 + n2)))
    z = stats.norm.ppf((1 + confidence) / 2)
    return float(effect_size - z * se), float(effect_size + z * se)

def apply_bonferroni_correction(p_value: float, n_concepts: int) -> float:
    """Apply Bonferroni correction."""
    return min(p_value * n_concepts, 1.0)

def check_collinearity(df: pd.DataFrame, predictors: List[str]) -> Dict[str, Any]:
    """Detect |r| > 0.8 between predictors."""
    corr_matrix = df[predictors].corr()
    high_corr = {}
    for i, col1 in enumerate(predictors):
        for j, col2 in enumerate(predictors):
            if i < j:
                r = corr_matrix.loc[col1, col2]
                if abs(r) > 0.8:
                    high_corr[f"{col1}_{col2}"] = float(r)
    return {
        "detected": len(high_corr) > 0,
        "high_correlations": high_corr,
        "max_correlation": float(corr_matrix.abs().max().max()) if not corr_matrix.empty else 0.0
    }

def calculate_power(effect_size: float, n1: int, n2: int, alpha: float = 0.05) -> Dict[str, Any]:
    """Compute achieved power."""
    n_total = n1 + n2
    # Approximate power calculation for t-test
    # Using non-central t-distribution approximation
    df = n_total - 2
    # Effect size in terms of standard error
    se = np.sqrt(1/n1 + 1/n2)
    non_central_param = effect_size / se
    
    # Critical t value
    t_crit = stats.t.inv(1 - alpha/2, df)
    
    # Power is probability that non-central t > t_crit
    # Using scipy's nct (non-central t)
    try:
        power = 1 - stats.nct.cdf(t_crit, df, non_central_param) + stats.nct.cdf(-t_crit, df, non_central_param)
    except Exception:
        power = 0.0
      
    return {
        "achieved_power": float(power),
        "is_underpowered": float(power) < 0.80,
        "effect_size": float(effect_size),
        "sample_sizes": {"n1": n1, "n2": n2}
    }

def frame_inference() -> str:
    """Return the mandatory associational framing statement."""
    return "Findings are associational; no causal inference is drawn due to observational nature of data."

def aggregate_stats_results(ancova_results: Dict[str, Any], 
                            t_statistic: float, 
                            p_value: float, 
                            corrected_p_value: float, 
                            effect_size_cohen_d: float, 
                            confidence_interval: Tuple[float, float], 
                            power_analysis: Dict[str, Any], 
                            collinearity_diagnostics: Dict[str, Any]) -> Dict[str, Any]:
    """Combine all statistical results into a single dictionary."""
    return {
        "ancova_results": ancova_results,
        "t_statistic": t_statistic,
        "p_value": p_value,
        "corrected_p_value": corrected_p_value,
        "effect_size_cohen_d": effect_size_cohen_d,
        "confidence_interval": list(confidence_interval),
        "inference_framing": frame_inference(),
        "power_analysis": power_analysis,
        "collinearity_diagnostics": collinearity_diagnostics
    }

def write_partial_results(
    ancova_results: Dict[str, Any],
    t_statistic: float,
    p_value: float,
    corrected_p_value: float,
    effect_size_cohen_d: float,
    confidence_interval: Tuple[float, float],
    power_analysis: Dict[str, Any],
    collinearity_diagnostics: Dict[str, Any],
    output_path: str = "data/processed/results_us2.json"
) -> str:
    """
    Write the aggregated dictionary to a JSON file.
    Returns the path to the written file.
    
    Schema Keys required:
    - ancova_results (PRIMARY: F-statistic, p-value, adjusted_means)
    - t_statistic (SECONDARY)
    - p_value (SECONDARY)
    - corrected_p_value (Bonferroni-adjusted, required when N_concepts > 1)
    - effect_size_cohen_d
    - confidence_interval
    - inference_framing (Must contain the full explanatory statement from FR-003)
    - power_analysis
    - collinearity_diagnostics
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Aggregate results
    results = aggregate_stats_results(
        ancova_results=ancova_results,
        t_statistic=t_statistic,
        p_value=p_value,
        corrected_p_value=corrected_p_value,
        effect_size_cohen_d=effect_size_cohen_d,
        confidence_interval=confidence_interval,
        power_analysis=power_analysis,
        collinearity_diagnostics=collinearity_diagnostics
    )
    
    # Write to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Partial results written to {output_path}")
    return output_path

def finalize_results(
    partial_results_path: str,
    sensitivity_analysis: List[Dict[str, Any]],
    robustness_warning: bool,
    output_path: str = "data/processed/results.json"
) -> str:
    """
    Merge US2 results with sensitivity analysis into the final report.
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Load partial results
    with open(partial_results_path, 'r', encoding='utf-8') as f:
        base_results = json.load(f)
    
    # Construct final report
    final_report = {
        **base_results,
        "sensitivity_analysis": sensitivity_analysis,
        "robustness_warning": robustness_warning
    }
    
    # Write final report
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_report, f, indent=2)
    
    logger.info(f"Final results written to {output_path}")
    return output_path
