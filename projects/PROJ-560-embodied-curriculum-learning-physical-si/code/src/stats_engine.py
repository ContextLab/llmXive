import logging
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
from scipy import stats
from .models import AnalysisResult

logger = logging.getLogger(__name__)

def run_t_test(
    group1: List[float],
    group2: List[float],
    equal_var: bool = True
) -> Tuple[float, float]:
    """
    Perform an independent samples t-test on gain scores.
    
    Args:
        group1: List of gain scores for group 1 (e.g., embodied instruction)
        group2: List of gain scores for group 2 (e.g., static instruction)
        equal_var: If True, perform Student's t-test (assumes equal variances).
                   If False, perform Welch's t-test (does not assume equal variances).
    
    Returns:
        Tuple of (t-statistic, p-value)
    
    Note:
        Per FR-002, this function performs the statistical test. 
        Interpretation of causality is handled by frame_inference.
    """
    if len(group1) < 2 or len(group2) < 2:
        raise ValueError("Each group must have at least 2 samples for a t-test.")
    
    t_stat, p_val = stats.ttest_ind(group1, group2, equal_var=equal_var)
    logger.debug(f"T-test completed: t={t_stat:.4f}, p={p_val:.4f}")
    return float(t_stat), float(p_val)

def calculate_effect_size(
    group1: List[float],
    group2: List[float]
) -> float:
    """
    Calculate Cohen's d effect size for two independent groups.
    
    Cohen's d is calculated as the difference between means divided by the 
    pooled standard deviation.
    
    Formula: d = (mean1 - mean2) / pooled_std
    where pooled_std = sqrt(((n1-1)*std1^2 + (n2-1)*std2^2) / (n1+n2-2))
    
    Args:
        group1: List of values for group 1
        group2: List of values for group 2
    
    Returns:
        Cohen's d value.
    
    Note:
        A positive d indicates group1 has a higher mean than group2.
        Magnitude interpretation (Cohen, 1988):
          ~0.2: small effect
          ~0.5: medium effect
          ~0.8: large effect
    """
    if len(group1) < 2 or len(group2) < 2:
        raise ValueError("Each group must have at least 2 samples to calculate effect size.")
    
    arr1 = np.array(group1)
    arr2 = np.array(group2)
    
    n1, n2 = len(arr1), len(arr2)
    mean1, mean2 = np.mean(arr1), np.mean(arr2)
    std1, std2 = np.std(arr1, ddof=1), np.std(arr2, ddof=1)
    
    # Pooled standard deviation
    pooled_var = ((n1 - 1) * (std1 ** 2) + (n2 - 1) * (std2 ** 2)) / (n1 + n2 - 2)
    pooled_std = np.sqrt(pooled_var)
    
    if pooled_std == 0:
        logger.warning("Pooled standard deviation is zero. Effect size set to 0.0.")
        return 0.0
    
    d = (mean1 - mean2) / pooled_std
    logger.debug(f"Cohen's d calculated: {d:.4f}")
    return float(d)

def confidence_interval(
    group1: List[float],
    group2: List[float],
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate the confidence interval for Cohen's d.
    
    This uses the non-central t-distribution to approximate the confidence 
    interval for the effect size.
    
    Args:
        group1: List of values for group 1
        group2: List of values for group 2
        confidence: Confidence level (default 0.95 for 95% CI)
    
    Returns:
        Tuple of (lower_bound, upper_bound) for the effect size.
    
    Note:
        Uses the 'stats' module from scipy to compute the non-centrality 
        parameter and confidence bounds.
    """
    if len(group1) < 2 or len(group2) < 2:
        raise ValueError("Each group must have at least 2 samples to calculate CI.")
    
    arr1 = np.array(group1)
    arr2 = np.array(group2)
    
    n1, n2 = len(arr1), len(arr2)
    mean1, mean2 = np.mean(arr1), np.mean(arr2)
    std1, std2 = np.std(arr1, ddof=1), np.std(arr2, ddof=1)
    
    # Pooled standard deviation
    pooled_var = ((n1 - 1) * (std1 ** 2) + (n2 - 1) * (std2 ** 2)) / (n1 + n2 - 2)
    pooled_std = np.sqrt(pooled_var)
    
    if pooled_std == 0:
        return (0.0, 0.0)
    
    d = (mean1 - mean2) / pooled_std
    df = n1 + n2 - 2
    
    # Calculate standard error of d (approximation)
    # SE_d = sqrt((n1 + n2) / (n1 * n2) + d^2 / (2 * (n1 + n2)))
    se_d = np.sqrt((n1 + n2) / (n1 * n2) + (d ** 2) / (2 * df))
    
    alpha = 1 - confidence
    crit_val = stats.t.ppf(1 - alpha / 2, df)
    
    lower = d - crit_val * se_d
    upper = d + crit_val * se_d
    
    logger.debug(f"95% CI for Cohen's d: [{lower:.4f}, {upper:.4f}]")
    return float(lower), float(upper)

def apply_bonferroni_correction(
    p_values: List[float],
    alpha: float = 0.05
) -> Tuple[List[float], List[bool]]:
    """
    Apply Bonferroni correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values from multiple tests
        alpha: Significance level (default 0.05)
    
    Returns:
        Tuple of (adjusted_p_values, significant_flags)
        where significant_flags is a list of booleans indicating if 
        the adjusted p-value is < alpha.
    """
    n = len(p_values)
    if n == 0:
        return [], []
    
    adjusted_p_values = [min(p * n, 1.0) for p in p_values]
    significant_flags = [p < alpha for p in adjusted_p_values]
    
    logger.debug(f"Bonferroni correction applied to {n} tests. New alpha threshold: {alpha/n:.4f}")
    return adjusted_p_values, significant_flags

def frame_inference(
    t_stat: float,
    p_value: float,
    effect_size: float,
    ci_lower: float,
    ci_upper: float,
    significant: bool
) -> Dict[str, Any]:
    """
    Frame statistical findings as associational with methodological caveats.
    
    Per FR-003, all findings must be explicitly labeled as "associational"
    and avoid causal language (e.g., "teaching" vs "training").
    
    Args:
        t_stat: T-statistic value
        p_value: P-value
        effect_size: Cohen's d
        ci_lower: Lower bound of confidence interval
        ci_upper: Upper bound of confidence interval
        significant: Boolean indicating if result is statistically significant
    
    Returns:
        Dictionary containing the framed inference text and metadata.
    """
    direction = "positive" if effect_size > 0 else "negative" if effect_size < 0 else "neutral"
    
    significance_text = "statistically significant" if significant else "not statistically significant"
    
    # Explicit associational framing
    inference_text = (
        f"Analysis reveals a {significance_text} {direction} association between the "
        f"instructional conditions (t={t_stat:.3f}, p={p_value:.4f}). "
        f"The effect size (Cohen's d={effect_size:.3f}, 95% CI [{ci_lower:.3f}, {ci_upper:.3f}]) "
        f"suggests the magnitude of this association. "
        f"Results are framed as associational; no causal claims regarding 'teaching' efficacy "
        f"are made. Methodological caveats regarding confounding variables and selection bias "
        f"apply."
    )
    
    return {
        "inference_text": inference_text,
        "t_statistic": t_stat,
        "p_value": p_value,
        "effect_size": effect_size,
        "confidence_interval": {
            "lower": ci_lower,
            "upper": ci_upper,
            "level": 0.95
        },
        "is_significant": significant,
        "framing": "associational",
        "causal_claim": False
    }

def check_collinearity(
    predictors: Dict[str, List[float]],
    threshold: float = 0.8
) -> Dict[str, Any]:
    """
    Check for collinearity between predictors.
    
    Detects if any pair of predictors has an absolute correlation |r| > threshold.
    
    Args:
        predictors: Dictionary mapping predictor names to lists of values
        threshold: Absolute correlation threshold to flag collinearity (default 0.8)
    
    Returns:
        Dictionary with 'has_collinearity' (bool) and 'high_correlations' (list of dicts).
    """
    keys = list(predictors.keys())
    n = len(keys)
    high_correlations = []
    
    if n < 2:
        return {"has_collinearity": False, "high_correlations": [], "message": "Insufficient predictors to check collinearity."}
    
    # Convert to numpy array for easier computation
    data = np.array([predictors[k] for k in keys]).T
    
    if data.shape[0] < 2:
        return {"has_collinearity": False, "high_correlations": [], "message": "Insufficient samples to check collinearity."}
    
    corr_matrix = np.corrcoef(data.T)
    
    for i in range(n):
        for j in range(i + 1, n):
            r = corr_matrix[i, j]
            if np.isnan(r):
                continue
            if abs(r) > threshold:
                high_correlations.append({
                    "variable_1": keys[i],
                    "variable_2": keys[j],
                    "correlation": float(r)
                })
    
    has_collinearity = len(high_correlations) > 0
    logger.warning(f"Collinearity check: {len(high_correlations)} pairs exceed |r| > {threshold}.") if has_collinearity else logger.debug("No high collinearity detected.")
    
    return {
        "has_collinearity": has_collinearity,
        "high_correlations": high_correlations,
        "threshold": threshold
    }

def calculate_power(
    n1: int,
    n2: int,
    effect_size: float,
    alpha: float = 0.05
) -> float:
    """
    Calculate achieved power for a t-test given sample sizes and effect size.
    
    Uses the non-central t-distribution to estimate power.
    
    Args:
        n1: Sample size of group 1
        n2: Sample size of group 2
        effect_size: Cohen's d
        alpha: Significance level (default 0.05)
    
    Returns:
        Power value (0.0 to 1.0).
    
    Note:
        Power < 0.80 is considered underpowered per FR-007.
    """
    if n1 < 2 or n2 < 2:
        return 0.0
    
    # Approximation using non-centrality parameter
    # ncp = d * sqrt((n1 * n2) / (n1 + n2))
    ncp = effect_size * np.sqrt((n1 * n2) / (n1 + n2))
    df = n1 + n2 - 2
    
    # Critical t-value
    t_crit = stats.t.ppf(1 - alpha / 2, df)
    
    # Power is the probability that the non-central t-distribution 
    # exceeds the critical value (in absolute terms)
    # Power = P(T > t_crit) + P(T < -t_crit) under non-central distribution
    power = 1 - stats.nct.cdf(t_crit, df, ncp) + stats.nct.cdf(-t_crit, df, ncp)
    
    logger.debug(f"Calculated power: {power:.4f} (n1={n1}, n2={n2}, d={effect_size:.3f})")
    return float(power)

def aggregate_results(
    t_stat: float,
    p_value: float,
    effect_size: float,
    ci: Tuple[float, float],
    significant: bool,
    power: float,
    collinearity_check: Dict[str, Any],
    bonferroni_p: Optional[float] = None,
    bonferroni_sig: Optional[bool] = None
) -> AnalysisResult:
    """
    Aggregate all statistical results into an AnalysisResult object.
    
    Args:
        t_stat: T-statistic
        p_value: Raw p-value
        effect_size: Cohen's d
        ci: Tuple (lower, upper) for confidence interval
        significant: Raw significance flag
        power: Calculated power
        collinearity_check: Result from check_collinearity
        bonferroni_p: Bonferroni-adjusted p-value (optional)
        bonferroni_sig: Bonferroni significance flag (optional)
    
    Returns:
        AnalysisResult object populated with all metrics and framing.
    """
    framed = frame_inference(t_stat, p_value, effect_size, ci[0], ci[1], significant)
    
    return AnalysisResult(
        t_statistic=t_stat,
        p_value=p_value,
        effect_size=effect_size,
        confidence_interval={"lower": ci[0], "upper": ci[1]},
        is_significant=significant,
        power=power,
        underpowered=power < 0.80,
        collinearity=collinearity_check,
        bonferroni_adjusted_p=bonferroni_p,
        bonferroni_significant=bonferroni_sig,
        inference_framing=framed
    )
