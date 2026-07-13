import logging
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
from scipy import stats
from .models import AnalysisResult

logger = logging.getLogger(__name__)

def run_t_test(group1: List[float], group2: List[float]) -> Tuple[float, float, int]:
    """
    Perform Welch's t-test (default) or Student's t-test based on Levene's test.
    
    Returns:
        Tuple of (t_statistic, p_value, degrees_of_freedom)
    """
    g1 = np.array(group1)
    g2 = np.array(group2)
    
    # Levene's test for equality of variances
    levene_stat, levene_p = stats.levene(g1, g2)
    equal_var = levene_p > 0.05
    
    if equal_var:
        t_stat, p_val = stats.ttest_ind(g1, g2, equal_var=True)
        df = len(g1) + len(g2) - 2
    else:
        t_stat, p_val, df = stats.ttest_ind(g1, g2, equal_var=False)
        
    logger.debug(f"T-test: equal_var={equal_var}, t={t_stat:.4f}, p={p_val:.6f}, df={df}")
    return float(t_stat), float(p_val), int(df)

def calculate_effect_size(group1: List[float], group2: List[float]) -> Tuple[float, float, float]:
    """
    Calculate Cohen's d and 95% confidence interval.
    
    Returns:
        Tuple of (effect_size, ci_lower, ci_upper)
    """
    g1 = np.array(group1)
    g2 = np.array(group2)
    
    n1, n2 = len(g1), len(g2)
    mean1, mean2 = np.mean(g1), np.mean(g2)
    std1, std2 = np.std(g1, ddof=1), np.std(g2, ddof=1)
    
    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0, 0.0, 0.0
        
    d = (mean1 - mean2) / pooled_std
    
    # Approximate SE for Cohen's d
    se_d = np.sqrt((n1 + n2) / (n1 * n2) + (d**2) / (2 * (n1 + n2)))
    
    ci_low = d - 1.96 * se_d
    ci_high = d + 1.96 * se_d
    
    return float(d), float(ci_low), float(ci_high)

def apply_bonferroni_correction(alpha: float, n_tests: int) -> float:
    """
    Apply Bonferroni correction to alpha.
    
    Returns:
        Adjusted alpha value.
    """
    if n_tests <= 0:
        return alpha
    return alpha / n_tests

def frame_inference(p_value: float, effect_size: float, alpha: float) -> str:
    """
    Frame the inference text, explicitly labeling findings as associational.
    
    Returns:
        String describing the inference with caveats.
    """
    sig = p_value < alpha
    direction = "positive" if effect_size > 0 else "negative" if effect_size < 0 else "no"
    
    text = (
        f"Associational analysis indicates a {direction} relationship (d={effect_size:.3f}, "
        f"p={p_value:.4f}). "
        "These results are correlational and do not imply causation. "
        "Methodological caveats apply regarding unobserved confounders."
    )
    
    if not sig:
        text += " The association is not statistically significant at the adjusted alpha level."
        
    return text

def check_collinearity(covariates: Optional[Dict[str, np.ndarray]] = None) -> Dict[str, Any]:
    """
    Detect |r| > 0.8 between predictors.
    
    Returns:
        Dictionary with collinearity diagnostics.
    """
    if not covariates or len(covariates) < 2:
        return {"status": "insufficient_predictors", "max_r": 0.0, "pairs": []}
    
    keys = list(covariates.keys())
    max_r = 0.0
    pairs = []
    
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            k1, k2 = keys[i], keys[j]
            v1, v2 = covariates[k1], covariates[k2]
            
            if len(v1) == len(v2) and len(v1) > 1:
                r, _ = stats.pearsonr(v1, v2)
                r_abs = abs(r)
                if r_abs > max_r:
                    max_r = r_abs
                if r_abs > 0.8:
                    pairs.append({"pair": (k1, k2), "r": r})
    
    return {
        "status": "collinearity_detected" if pairs else "ok",
        "max_r": float(max_r),
        "pairs": pairs
    }

def calculate_power(effect_size: float, n_total: int, alpha: float = 0.05) -> float:
    """
    Compute achieved power for a two-sample t-test.
    
    Returns:
        Power value between 0 and 1.
    """
    # Approximate power calculation for two-sample t-test
    # Using normal approximation for large N
    n_per_group = n_total / 2
    
    # Non-centrality parameter
    ncp = effect_size * np.sqrt(n_per_group / 2)
    
    # Critical t-value (approximate with normal for large N)
    t_crit = stats.norm.ppf(1 - alpha / 2)
    
    # Power is probability of rejecting null given effect
    # Power = P(T > t_crit | H1)
    # Approximation using normal distribution
    power = 1 - stats.norm.cdf(t_crit - ncp) + stats.norm.cdf(-t_crit - ncp)
    
    return float(power)

def aggregate_results(
    t_stat: float,
    p_val: float,
    effect_size: float,
    ci_low: float,
    ci_high: float,
    power: float,
    inference_text: str,
    collinearity_diag: Dict[str, Any],
    robustness_warning: bool
) -> AnalysisResult:
    """
    Aggregate statistical results into an AnalysisResult object.
    
    Returns:
        AnalysisResult object.
    """
    return AnalysisResult(
        t_statistic=t_stat,
        p_value=p_val,
        effect_size=effect_size,
        ci_lower=ci_low,
        ci_upper=ci_high,
        power=power,
        inference_text=inference_text,
        collinearity_diagnostic=collinearity_diag,
        robustness_warning=robustness_warning,
        sensitivity_sweep=[]
    )
