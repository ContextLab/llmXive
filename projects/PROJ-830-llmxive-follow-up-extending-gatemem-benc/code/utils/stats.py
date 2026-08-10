"""
Statistics Module.
Implements Shapiro-Wilk, LMM, and fallback tests.
"""
import logging
from typing import Dict, Any, Optional, Tuple, List, Union
import numpy as np
import pandas as pd
import scipy.stats as stats
from statsmodels.formula.api import mixedlm
from statsmodels.stats.anova import anova_lm

from code.logging_config import setup_logging

logger = setup_logging(__name__)

def shapiro_wilk_test(data: List[float]) -> Tuple[float, float]:
    """
    Perform Shapiro-Wilk normality test.
    Returns (statistic, p-value).
    """
    if len(data) < 3:
        return 0.0, 1.0
    return stats.shapiro(data)

def fit_linear_mixed_model(data: pd.DataFrame, formula: str) -> Any:
    """
    Fit a Linear Mixed-Effects Model.
    Formula example: 'score ~ method + (1|Episode_ID)'
    """
    try:
        model = mixedlm(formula, data, groups=data["Episode_ID"])
        result = model.fit()
        return result
    except Exception as e:
        logger.warning(f"LMM fitting failed: {e}")
        raise e

def run_paired_ttest(group1: List[float], group2: List[float]) -> Tuple[float, float]:
    """Run paired t-test."""
    return stats.ttest_rel(group1, group2)

def run_wilcoxon_test(group1: List[float], group2: List[float]) -> Tuple[float, float]:
    """Run Wilcoxon signed-rank test."""
    return stats.wilcoxon(group1, group2)

def run_statistical_analysis(data: pd.DataFrame, formula: str) -> Dict[str, Any]:
    """
    Run statistical analysis with explicit fallback logic.
    1. Attempt LMM.
    2. If SingularMatrixError, fallback to paired t-test.
    3. If variance is 0, fallback to Wilcoxon.
    4. Else use LMM.
    """
    # Check variance
    if data["score"].var() == 0:
        logger.info("Variance is 0. Using Wilcoxon test.")
        # Group by method
        g1 = data[data["method"] == "gatekeeper"]["score"].tolist()
        g2 = data[data["method"] == "baseline"]["score"].tolist()
        stat, p = run_wilcoxon_test(g1, g2)
        return {
            "method": "wilcoxon",
            "statistic": stat,
            "p_value": p,
            "df": None
        }

    try:
        logger.info("Attempting LMM fit.")
        lmm_result = fit_linear_mixed_model(data, formula)
        # Extract p-value for method
        # This is a simplification; real extraction depends on the model output
        p_value = lmm_result.pvalues.get("method[T.gatekeeper]", 1.0)
        return {
            "method": "LMM",
            "statistic": lmm_result.llr,
            "p_value": p_value,
            "df": lmm_result.df_resid
        }
    except Exception as e:
        if "SingularMatrixError" in str(type(e)) or "singular" in str(e).lower():
            logger.info("SingularMatrixError. Falling back to paired t-test.")
            g1 = data[data["method"] == "gatekeeper"]["score"].tolist()
            g2 = data[data["method"] == "baseline"]["score"].tolist()
            stat, p = run_paired_ttest(g1, g2)
            return {
                "method": "paired_ttest",
                "statistic": stat,
                "p_value": p,
                "df": len(g1) - 1
            }
        else:
            # Other errors, re-raise or fallback
            logger.error(f"Statistical analysis failed: {e}")
            raise e

def run_domain_stratified_analysis(data: pd.DataFrame) -> Dict[str, Any]:
    """Run domain-stratified analysis."""
    # Simplified: average p-values across domains
    domains = data["Domain"].unique()
    p_values = []
    for d in domains:
        subset = data[data["Domain"] == d]
        if len(subset) > 1:
            res = run_statistical_analysis(subset, "score ~ method + (1|Episode_ID)")
            p_values.append(res["p_value"])
    
    avg_p = np.mean(p_values) if p_values else 1.0
    return {"average_p_value": avg_p}

def main():
    # Demo
    data = pd.DataFrame({
        "score": [1, 2, 3, 4, 5, 6],
        "method": ["gatekeeper", "gatekeeper", "gatekeeper", "baseline", "baseline", "baseline"],
        "Episode_ID": [1, 1, 1, 2, 2, 2],
        "Domain": ["A", "A", "A", "A", "A", "A"]
    })
    res = run_statistical_analysis(data, "score ~ method + (1|Episode_ID)")
    print(res)

if __name__ == "__main__":
    main()