import logging
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
from scipy import stats
from .models import AnalysisResult


def run_t_test(
    group1: List[float], 
    group2: List[float], 
    use_welch: bool = True
) -> Tuple[float, float]:
    """
    Perform a t-test comparing two independent groups.
    
    Args:
        group1: List of values for the first group.
        group2: List of values for the second group.
        use_welch: If True, use Welch's t-test; otherwise, use Student's t-test.
        
    Returns:
        A tuple containing the t-statistic and p-value.
    """
    if len(group1) < 2 or len(group2) < 2:
        raise ValueError("Both groups must have at least 2 samples for a t-test.")
    
    if use_welch:
        t_stat, p_val = stats.ttest_ind(group1, group2, equal_var=False)
    else:
        t_stat, p_val = stats.ttest_ind(group1, group2, equal_var=True)
        
    return float(t_stat), float(p_val)


def calculate_effect_size(group1: List[float], group2: List[float]) -> float:
    """
    Calculate Cohen's d effect size.
    
    Args:
        group1: List of values for the first group.
        group2: List of values for the second group.
        
    Returns:
        The calculated Cohen's d.
    """
    mean1 = np.mean(group1)
    mean2 = np.mean(group2)
    std1 = np.std(group1, ddof=1)
    std2 = np.std(group2, ddof=1)
    
    pooled_std = np.sqrt((std1**2 + std2**2) / 2)
    
    if pooled_std == 0:
        return 0.0
        
    return float((mean1 - mean2) / pooled_std)


def calculate_confidence_interval(
    group1: List[float], 
    group2: List[float], 
    confidence: float = 0.95
) -> List[float]:
    """
    Calculate the confidence interval for the difference in means.
    
    Args:
        group1: List of values for the first group.
        group2: List of values for the second group.
        confidence: The confidence level (e.g., 0.95).
        
    Returns:
        A list containing the lower and upper bounds of the CI.
    """
    mean_diff = np.mean(group1) - np.mean(group2)
    n1, n2 = len(group1), len(group2)
    var1 = np.var(group1, ddof=1)
    var2 = np.var(group2, ddof=1)
    
    se = np.sqrt(var1/n1 + var2/n2)
    df = (var1/n1 + var2/n2)**2 / ((var1/n1)**2/(n1-1) + (var2/n2)**2/(n2-1))
    
    t_crit = stats.t.ppf((1 + confidence) / 2, df)
    margin = t_crit * se
    
    return [float(mean_diff - margin), float(mean_diff + margin)]


def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """
    Apply Bonferroni correction to a list of p-values.
    
    Args:
        p_values: List of p-values to correct.
        alpha: The significance level.
        
    Returns:
        A list of adjusted p-values.
    """
    n = len(p_values)
    if n == 0:
        return []
        
    adjusted = [min(p * n, 1.0) for p in p_values]
    return adjusted


def frame_inference(result: AnalysisResult) -> Dict[str, Any]:
    """
    Frame the statistical inference as associational.
    
    Args:
        result: The analysis result to frame.
        
    Returns:
        A dictionary containing the framed inference.
    """
    return {
        "finding": "associational",
        "t_statistic": result.t_statistic,
        "p_value": result.p_value,
        "effect_size": result.effect_size,
        "caveat": "Results are associational and do not imply causation."
    }


def check_collinearity(covariates: List[Dict[str, float]]) -> Dict[str, Any]:
    """
    Check for collinearity between predictors.
    
    Args:
        covariates: List of dictionaries, each representing a sample's covariates.
        
    Returns:
        A dictionary containing collinearity diagnostics.
    """
    if len(covariates) < 2:
        return {"collinearity_detected": False, "details": "Insufficient data"}
        
    # Extract columns
    keys = list(covariates[0].keys())
    data = np.array([[sample[k] for k in keys] for sample in covariates])
    
    if data.shape[1] < 2:
        return {"collinearity_detected": False, "details": "Only one predictor"}
        
    corr_matrix = np.corrcoef(data.T)
    max_corr = 0.0
    max_pair = None
    
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            corr = abs(corr_matrix[i, j])
            if corr > max_corr:
                max_corr = corr
                max_pair = (keys[i], keys[j])
                
    detected = max_corr > 0.8
    
    return {
        "collinearity_detected": detected,
        "max_correlation": float(max_corr),
        "pair": list(max_pair) if max_pair else None,
        "details": f"Max |r| = {max_corr:.2f} between {max_pair}" if max_pair else "No pairs found"
    }


def calculate_power(
    effect_size: float, 
    n1: int, 
    n2: int, 
    alpha: float = 0.05
) -> float:
    """
    Calculate the achieved statistical power.
    
    Args:
        effect_size: The effect size (Cohen's d).
        n1: Sample size of group 1.
        n2: Sample size of group 2.
        alpha: Significance level.
        
    Returns:
        The calculated power.
    """
    # Approximate power calculation for t-test
    # Using non-centrality parameter approximation
    n = (n1 * n2) / (n1 + n2)
    ncp = effect_size * np.sqrt(n)
    
    # Critical t-value
    df = n1 + n2 - 2
    t_crit = stats.t.ppf(1 - alpha/2, df)
    
    # Power is probability of rejecting null when alternative is true
    # Approximated by CDF of non-central t
    power = 1 - stats.nct.cdf(t_crit, df, ncp) + stats.nct.cdf(-t_crit, df, ncp)
    
    return float(power)


def aggregate_results(
    t_stat: float, 
    p_val: float, 
    effect: float, 
    ci: List[float], 
    method: str,
    power: Optional[float] = None,
    collinearity: Optional[Dict[str, Any]] = None
) -> AnalysisResult:
    """
    Aggregate statistical results into an AnalysisResult object.
    
    Args:
        t_stat: T-statistic.
        p_val: P-value.
        effect: Effect size.
        ci: Confidence interval.
        method: Method used.
        power: Calculated power.
        collinearity: Collinearity diagnostics.
        
    Returns:
        An AnalysisResult object.
    """
    return AnalysisResult(
        t_statistic=t_stat,
        p_value=p_val,
        effect_size=effect,
        confidence_interval=ci,
        method=method,
        power=power,
        collinearity_diagnostic=collinearity
    )
