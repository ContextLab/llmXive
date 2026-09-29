import logging
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.formula.api import ols
import json
from pathlib import Path
from .models import AnalysisResult, SensitivitySweep

logger = logging.getLogger(__name__)

def run_t_test(
    group1_scores: List[float],
    group2_scores: List[float],
    equal_var: bool = False
) -> Tuple[float, float]:
    """
    Perform Welch's t-test (or Student's t-test if equal_var=True) on two groups.
    Returns (t_statistic, p_value).
    """
    if not group1_scores or not group2_scores:
        raise ValueError("Cannot run t-test on empty groups")
    
    t_stat, p_val = stats.ttest_ind(group1_scores, group2_scores, equal_var=equal_var)
    return float(t_stat), float(p_val)

def calculate_effect_size(
    group1_scores: List[float],
    group2_scores: List[float],
    pooled_std: Optional[float] = None
) -> float:
    """
    Calculate Cohen's d effect size.
    If pooled_std is provided, use it; otherwise calculate from groups.
    """
    if not group1_scores or not group2_scores:
        return 0.0
    
    mean1 = np.mean(group1_scores)
    mean2 = np.mean(group2_scores)
    
    if pooled_std is None:
        n1, n2 = len(group1_scores), len(group2_scores)
        var1 = np.var(group1_scores, ddof=1)
        var2 = np.var(group2_scores, ddof=1)
        pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
        
    return float((mean1 - mean2) / pooled_std)

def calculate_confidence_interval(
    effect_size: float,
    n1: int,
    n2: int,
    confidence_level: float = 0.95
) -> Tuple[float, float]:
    """
    Approximate confidence interval for Cohen's d.
    Uses non-central t-distribution approximation.
    """
    # Simplified approximation using standard error
    se = np.sqrt((n1 + n2) / (n1 * n2) + (effect_size**2) / (2 * (n1 + n2)))
    z = stats.norm.ppf((1 + confidence_level) / 2)
    lower = effect_size - z * se
    upper = effect_size + z * se
    return float(lower), float(upper)

def apply_bonferroni_correction(
    p_values: List[float],
    alpha: float = 0.05
) -> List[float]:
    """
    Apply Bonferroni correction to a list of p-values.
    Returns adjusted p-values.
    """
    m = len(p_values)
    if m == 0:
        return []
    
    adjusted = [min(p * m, 1.0) for p in p_values]
    return adjusted

def check_collinearity(
    df: pd.DataFrame,
    predictors: List[str],
    threshold: float = 0.8
) -> Dict[str, Any]:
    """
    Check for collinearity between predictors.
    Returns diagnostics including max correlation and pairs exceeding threshold.
    """
    if len(predictors) < 2:
        return {"max_correlation": 0.0, "high_correlation_pairs": [], "flagged": False}
    
    corr_matrix = df[predictors].corr().abs()
    
    # Find upper triangle correlations
    high_pairs = []
    max_corr = 0.0
    
    for i in range(len(predictors)):
        for j in range(i + 1, len(predictors)):
            corr_val = corr_matrix.iloc[i, j]
            if corr_val > max_corr:
                max_corr = corr_val
            if corr_val > threshold:
                high_pairs.append({
                    "pair": [predictors[i], predictors[j]],
                    "correlation": float(corr_val)
                })
    
    return {
        "max_correlation": float(max_corr),
        "high_correlation_pairs": high_pairs,
        "flagged": len(high_pairs) > 0
    }

def calculate_power(
    effect_size: float,
    n1: int,
    n2: int,
    alpha: float = 0.05
) -> float:
    """
    Calculate achieved power for a two-sample t-test.
    Uses non-central t-distribution.
    """
    if n1 <= 0 or n2 <= 0:
        return 0.0
    
    # Approximate power calculation
    df = n1 + n2 - 2
    n = (n1 * n2) / (n1 + n2)
    non_central_param = effect_size * np.sqrt(n)
    
    # Critical t-value
    t_crit = stats.t.ppf(1 - alpha/2, df)
    
    # Power is probability that t > t_crit under alternative
    power = 1 - stats.nct.cdf(t_crit, df, non_central_param) + \
            stats.nct.cdf(-t_crit, df, non_central_param)
    
    return float(power)

def frame_inference(
    p_value: float,
    alpha: float = 0.05,
    effect_size: float = 0.0
) -> str:
    """
    Frame the statistical inference with appropriate caveats.
    Returns a string explaining the associational nature of findings.
    """
    significant = p_value < alpha
    direction = "positive" if effect_size > 0 else ("negative" if effect_size < 0 else "no")
    
    return (
        f"Findings are associational; no causal inference is drawn due to observational nature of data. "
        f"The analysis shows a {direction} association (effect size: {effect_size:.3f}, p-value: {p_value:.4f}). "
        f"{'The association is statistically significant at alpha=0.05.' if significant else 'The association is not statistically significant at alpha=0.05.'}"
    )

def aggregate_stats_results(
    t_statistic: float,
    p_value: float,
    effect_size: float,
    ci_lower: float,
    ci_upper: float,
    inference_text: str,
    power: float,
    collinearity_diag: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Aggregate all statistical results into a single dictionary structure.
    """
    return {
        "t_statistic": t_statistic,
        "p_value": p_value,
        "effect_size_cohen_d": effect_size,
        "confidence_interval": {"lower": ci_lower, "upper": ci_upper},
        "inference_framing": inference_text,
        "power_analysis": {"achieved_power": power, "underpowered": power < 0.80},
        "collinearity_diagnostics": collinearity_diag
    }

def write_partial_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Write the aggregated statistical results to a JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Partial results written to {output_path}")

def finalize_results(
    us2_results_path: str,
    sensitivity_results: List[Dict[str, Any]],
    robustness_warning: bool,
    output_path: str
) -> Dict[str, Any]:
    """
    Merge US2 results (t-test, effect size, etc.) with sensitivity analysis results
    into the final results JSON.
    
    Args:
        us2_results_path: Path to the results_us2.json file containing US2 results
        sensitivity_results: List of sensitivity analysis results from T028/T030
        robustness_warning: Boolean flag from T030
        output_path: Path where the final results.json should be written
        
    Returns:
        The complete merged results dictionary
    """
    # Load US2 results
    try:
        with open(us2_results_path, 'r') as f:
            us2_data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"US2 results file not found at {us2_results_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in US2 results file: {us2_results_path}")
    
    # Ensure required keys exist in US2 data
    required_keys = [
        "t_statistic", "p_value", "effect_size_cohen_d", 
        "confidence_interval", "inference_framing"
    ]
    for key in required_keys:
        if key not in us2_data:
            raise KeyError(f"Missing required key '{key}' in US2 results")
    
    # Format sensitivity analysis results
    formatted_sensitivity = []
    for sweep_result in sensitivity_results:
        formatted_sensitivity.append({
            "threshold_value": sweep_result.get("threshold_value"),
            "n_participants_retained": sweep_result.get("n_participants_retained"),
            "effect_size_cohen_d": sweep_result.get("effect_size_cohen_d"),
            "robustness_flag": sweep_result.get("robustness_flag", False)
        })
    
    # Merge into final structure
    final_results = {
        "t_statistic": us2_data["t_statistic"],
        "p_value": us2_data["p_value"],
        "effect_size_cohen_d": us2_data["effect_size_cohen_d"],
        "confidence_interval": us2_data["confidence_interval"],
        "inference_framing": us2_data["inference_framing"],
        "sensitivity_analysis": formatted_sensitivity,
        "robustness_warning": robustness_warning
    }
    
    # Write final results
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(final_results, f, indent=2)
    
    logger.info(f"Final results written to {output_path}")
    return final_results