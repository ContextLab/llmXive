"""
Statistical analysis engine.

Implements t-tests, effect size calculations, power analysis, and
associational framing of results.
"""
import logging
from typing import List, Tuple, Dict, Any, Optional

import numpy as np
from scipy import stats

from .models import AnalysisResult

logger = logging.getLogger(__name__)


def run_t_test(group1: List[float], group2: List[float]) -> Tuple[float, float]:
    """
    Perform a t-test comparing two groups.

    Uses Welch's t-test if variances are unequal (determined by Levene's test).

    Args:
        group1 (List[float]): First group of values.
        group2 (List[float]): Second group of values.

    Returns:
        Tuple[float, float]: (t_statistic, p_value)
    """
    if len(group1) < 2 or len(group2) < 2:
        raise ValueError("Each group must have at least 2 samples for t-test.")

    # Levene's test for equality of variances
    _, p_levene = stats.levene(group1, group2)
    equal_var = p_levene > 0.05

    if equal_var:
        t_stat, p_val = stats.ttest_ind(group1, group2, equal_var=True)
        logger.debug("Student's t-test used (equal variances).")
    else:
        t_stat, p_val = stats.ttest_ind(group1, group2, equal_var=False)
        logger.debug("Welch's t-test used (unequal variances).")

    return float(t_stat), float(p_val)


def calculate_effect_size(group1: List[float], group2: List[float]) -> float:
    """
    Calculate Cohen's d effect size.

    Args:
        group1 (List[float]): First group of values.
        group2 (List[float]): Second group of values.

    Returns:
        float: Cohen's d.
    """
    mean1, mean2 = np.mean(group1), np.mean(group2)
    std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)
    n1, n2 = len(group1), len(group2)

    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0

    return float((mean1 - mean2) / pooled_std)


def calculate_confidence_interval(group1: List[float], group2: List[float], confidence: float = 0.95) -> Optional[Tuple[float, float]]:
    """
    Calculate the confidence interval for the difference in means.

    Args:
        group1 (List[float]): First group of values.
        group2 (List[float]): Second group of values.
        confidence (float): Confidence level (e.g., 0.95).

    Returns:
        Optional[Tuple[float, float]]: (lower, upper) bounds or None if calculation fails.
    """
    try:
        mean1, mean2 = np.mean(group1), np.mean(group2)
        std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)
        n1, n2 = len(group1), len(group2)

        se = np.sqrt((std1**2 / n1) + (std2**2 / n2))
        df = n1 + n2 - 2
        t_crit = stats.t.ppf((1 + confidence) / 2, df)

        diff = mean1 - mean2
        lower = diff - t_crit * se
        upper = diff + t_crit * se
        return (float(lower), float(upper))
    except Exception as e:
        logger.error(f"Failed to calculate confidence interval: {e}")
        return None


def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """
    Apply Bonferroni correction to a list of p-values.

    Args:
        p_values (List[float]): List of p-values.
        alpha (float): Significance level.

    Returns:
        List[float]: Adjusted p-values.
    """
    n = len(p_values)
    if n == 0:
        return []
    adjusted = [min(p * n, 1.0) for p in p_values]
    logger.debug(f"Bonferroni correction applied to {n} tests. Alpha: {alpha}")
    return adjusted


def frame_inference(effect_size: float, p_value: float, caveats: List[str]) -> List[str]:
    """
    Frame the statistical inference as associational with required caveats.

    Args:
        effect_size (float): Calculated effect size.
        p_value (float): Calculated p-value.
        caveats (List[str]): Existing list of caveats.

    Returns:
        List[str]: Updated list of caveats including associational framing.
    """
    framing = [
        "Results are presented as associational only.",
        "No causal claims regarding 'teaching' vs 'training' are made.",
        f"Effect size (Cohen's d): {effect_size:.3f}, p-value: {p_value:.4f}."
    ]
    return caveats + framing


def check_collinearity(data: Dict[str, List[float]]) -> Optional[Dict[str, Any]]:
    """
    Check for collinearity between predictors.

    Args:
        data (Dict[str, List[float]]): Dictionary of predictor names and values.

    Returns:
        Optional[Dict[str, Any]]: Collinearity report or None if no issues.
    """
    keys = list(data.keys())
    report = {"highly_correlated_pairs": []}
    threshold = 0.8

    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            corr_matrix = np.corrcoef(data[keys[i]], data[keys[j]])
            if corr_matrix.shape == (2, 2):
                corr = corr_matrix[0, 1]
                if abs(corr) > threshold:
                    report["highly_correlated_pairs"].append({
                        "pair": [keys[i], keys[j]],
                        "correlation": float(corr)
                    })
                    logger.warning(f"High collinearity detected between {keys[i]} and {keys[j]}: r={corr:.3f}")

    if report["highly_correlated_pairs"]:
        return report
    return None


def calculate_power(group1: List[float], group2: List[float], alpha: float = 0.05) -> float:
    """
    Calculate achieved statistical power.

    Args:
        group1 (List[float]): First group of values.
        group2 (List[float]): Second group of values.
        alpha (float): Significance level.

    Returns:
        float: Estimated power.
    """
    effect = calculate_effect_size(group1, group2)
    n1, n2 = len(group1), len(group2)
    # Approximate power calculation using scipy
    # statsmodels is not imported to keep dependencies minimal, using approximation
    from scipy.stats import t
    df = n1 + n2 - 2
    # Non-centrality parameter
    ncp = effect * np.sqrt((n1 * n2) / (n1 + n2))
    t_crit = t.ppf(1 - alpha/2, df)
    # Power is 1 - beta
    # This is a simplified approximation
    power = 1 - t.cdf(t_crit, df, ncp) + t.cdf(-t_crit, df, ncp)
    return float(power)


def aggregate_results(
    t_stat: float,
    p_val: float,
    effect: float,
    ci: Optional[Tuple[float, float]],
    caveats: List[str],
    power: float,
    collinearity: Optional[Dict[str, Any]],
    robustness: Optional[bool]
) -> AnalysisResult:
    """
    Aggregate all statistical results into an AnalysisResult object.

    Args:
        t_stat (float): t-statistic.
        p_val (float): p-value.
        effect (float): Effect size.
        ci (Optional[Tuple[float, float]]): Confidence interval.
        caveats (List[str]): List of caveats.
        power (float): Achieved power.
        collinearity (Optional[Dict[str, Any]]): Collinearity report.
        robustness (Optional[bool]): Robustness warning flag.

    Returns:
        AnalysisResult: Aggregated result object.
    """
    return AnalysisResult(
        t_statistic=t_stat,
        p_value=p_val,
        effect_size=effect,
        confidence_interval=ci,
        methodological_caveats=caveats,
        power=power,
        collinearity_report=collinearity,
        robustness_warning=robustness
    )
