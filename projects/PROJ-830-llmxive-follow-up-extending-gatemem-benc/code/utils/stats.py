import logging
from typing import Dict, Any, Optional, Tuple, List, Union
import numpy as np
import pandas as pd
import scipy.stats as stats
from statsmodels.formula.api import mixedlm

from logging_config import setup_logging

logger = setup_logging(__name__)


def shapiro_wilk_test(data: np.ndarray) -> Tuple[float, float]:
    """
    Perform Shapiro-Wilk test for normality.

    Args:
        data: Array of data values.

    Returns:
        Tuple of (statistic, p-value).
    """
    if len(data) < 3:
        logger.warning("Not enough data for Shapiro-Wilk test")
        return 0.0, 1.0
    
    stat, p_value = stats.shapiro(data)
    logger.debug(f"Shapiro-Wilk: stat={stat:.4f}, p={p_value:.4f}")
    return stat, p_value


def fit_linear_mixed_model(
    df: pd.DataFrame,
    formula: str = "score ~ method + (1|Domain)"
) -> Optional[Any]:
    """
    Fit a Linear Mixed Model (LMM).

    Args:
        df: DataFrame containing the data.
        formula: Model formula.

    Returns:
        Fitted model or None if fitting fails.
    """
    try:
        logger.info(f"Fitting LMM with formula: {formula}")
        model = mixedlm.from_formula(formula, df, groups=df["Domain"])
        result = model.fit()
        logger.info("LMM fitted successfully")
        return result
    except Exception as e:
        logger.warning(f"LMM fitting failed: {e}")
        return None


def run_paired_ttest(group1: np.ndarray, group2: np.ndarray) -> Tuple[float, float]:
    """
    Run a paired t-test.

    Args:
        group1: First group of values.
        group2: Second group of values.

    Returns:
        Tuple of (t-statistic, p-value).
    """
    if len(group1) != len(group2):
        raise ValueError("Groups must be of equal length for paired t-test")
    
    stat, p_value = stats.ttest_rel(group1, group2)
    logger.debug(f"Paired t-test: t={stat:.4f}, p={p_value:.4f}")
    return stat, p_value


def run_wilcoxon_test(group1: np.ndarray, group2: np.ndarray) -> Tuple[float, float]:
    """
    Run a Wilcoxon signed-rank test.

    Args:
        group1: First group of values.
        group2: Second group of values.

    Returns:
        Tuple of (statistic, p-value).
    """
    if len(group1) != len(group2):
        raise ValueError("Groups must be of equal length for Wilcoxon test")
    
    stat, p_value = stats.wilcoxon(group1, group2)
    logger.debug(f"Wilcoxon: stat={stat:.4f}, p={p_value:.4f}")
    return stat, p_value


def run_domain_stratified_analysis(
    df: pd.DataFrame,
    score_col: str = "score",
    method_col: str = "method",
    domain_col: str = "Domain"
) -> Dict[str, Any]:
    """
    Run separate tests per domain and aggregate results.

    Args:
        df: DataFrame with results.
        score_col: Name of the score column.
        method_col: Name of the method column.
        domain_col: Name of the domain column.

    Returns:
        Dictionary of results per domain.
    """
    results = {}
    domains = df[domain_col].unique()
    
    for domain in domains:
        domain_df = df[df[domain_col] == domain]
        if len(domain_df) < 2:
            continue
        
        # Simplified logic for demonstration; actual implementation would compare methods
        scores = domain_df[score_col].values
        stat, p_value = shapiro_wilk_test(scores)
        results[domain] = {
            "shapiro_stat": stat,
            "shapiro_p": p_value,
            "n": len(scores)
        }
    
    logger.info(f"Stratified analysis complete for {len(results)} domains")
    return results


def run_statistical_analysis(
    df: pd.DataFrame,
    score_col: str = "score",
    method_col: str = "method",
    domain_col: str = "Domain"
) -> Dict[str, Any]:
    """
    Run full statistical analysis: LMM with fallback to paired tests.

    Args:
        df: DataFrame with results.
        score_col: Name of the score column.
        method_col: Name of the method column.
        domain_col: Name of the domain column.

    Returns:
        Dictionary containing analysis results.
    """
    result = {
        "lmm_result": None,
        "fallback_used": False,
        "fallback_method": None,
        "test_stat": None,
        "p_value": None,
        "df": None
    }

    # Try LMM first
    lmm = fit_linear_mixed_model(df)
    if lmm is not None:
        result["lmm_result"] = lmm.summary().as_text()
        result["test_stat"] = lmm.params.get("method[T.Gatekeeper]", 0)
        result["p_value"] = lmm.pvalues.get("method[T.Gatekeeper]", 1.0)
        result["df"] = len(df) - 2
        return result

    # Fallback: Paired T-Test or Wilcoxon
    logger.info("LMM failed. Attempting fallback tests.")
    methods = df[method_col].unique()
    if len(methods) != 2:
        logger.warning("Cannot perform paired test with more than 2 methods")
        return result

    m1, m2 = methods
    g1 = df[df[method_col] == m1][score_col].values
    g2 = df[df[method_col] == m2][score_col].values

    if len(g1) != len(g2):
        logger.warning("Unequal group sizes for paired test")
        return result

    # Check normality
    _, p_norm = shapiro_wilk_test(g1 - g2)
    
    if p_norm > 0.05:
        stat, p_val = run_paired_ttest(g1, g2)
        result["fallback_method"] = "Paired T-Test"
    else:
        stat, p_val = run_wilcoxon_test(g1, g2)
        result["fallback_method"] = "Wilcoxon Signed-Rank"

    result["fallback_used"] = True
    result["test_stat"] = stat
    result["p_value"] = p_val
    result["df"] = len(g1) - 1

    logger.info(f"Fallback test complete: {result['fallback_method']}")
    return result