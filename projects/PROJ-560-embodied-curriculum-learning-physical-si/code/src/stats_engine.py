import logging
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.formula.api import ols

logger = logging.getLogger(__name__)

def run_t_test(
    group1_scores: List[float],
    group2_scores: List[float]
) -> Tuple[float, float]:
    """
    Perform a t-test between two groups.
    
    Args:
        group1_scores: Scores for group 1.
        group2_scores: Scores for group 2.
        
    Returns:
        Tuple of (t_statistic, p_value).
    """
    if len(group1_scores) < 2 or len(group2_scores) < 2:
        raise ValueError("Each group must have at least 2 scores for t-test")
    
    # Levene's test for equality of variances
    levene_stat, levene_p = stats.levene(group1_scores, group2_scores)
    equal_var = levene_p > 0.05
    
    t_stat, p_val = stats.ttest_ind(
        group1_scores,
        group2_scores,
        equal_var=equal_var
    )
    
    logger.info(f"T-test (equal_var={equal_var}): t={t_stat:.4f}, p={p_val:.4f}")
    return float(t_stat), float(p_val)

def run_ancova(
    df: pd.DataFrame,
    dependent_var: str,
    factor_var: str,
    covariate_var: str
) -> Dict[str, float]:
    """
    Perform ANCOVA analysis.
    
    Args:
        df: DataFrame containing the data.
        dependent_var: Name of the dependent variable.
        factor_var: Name of the factor variable.
        covariate_var: Name of the covariate variable.
        
    Returns:
        Dictionary with F-statistic and p-value.
    """
    formula = f"{dependent_var} ~ {covariate_var} + C({factor_var})"
    model = ols(formula, data=df).fit()
    
    anova_table = stats.anova_lm(model, typ=2)
    
    f_stat = anova_table["F"]["C({})".format(factor_var)]
    p_val = anova_table["PR(>F)"]["C({})".format(factor_var)]
    
    logger.info(f"ANCOVA: F={f_stat:.4f}, p={p_val:.4f}")
    return {"f_statistic": float(f_stat), "p_value": float(p_val)}

def calculate_effect_size(
    group1_scores: List[float],
    group2_scores: List[float]
) -> float:
    """
    Calculate Cohen's d effect size.
    
    Args:
        group1_scores: Scores for group 1.
        group2_scores: Scores for group 2.
        
    Returns:
        Cohen's d value.
    """
    mean1 = np.mean(group1_scores)
    mean2 = np.mean(group2_scores)
    std1 = np.std(group1_scores, ddof=1)
    std2 = np.std(group2_scores, ddof=1)
    
    pooled_std = np.sqrt((std1**2 + std2**2) / 2)
    
    if pooled_std == 0:
        return 0.0
    
    return float((mean1 - mean2) / pooled_std)

def calculate_confidence_interval(
    effect_size: float,
    n1: int,
    n2: int,
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate confidence interval for effect size.
    
    Args:
        effect_size: Cohen's d value.
        n1: Sample size of group 1.
        n2: Sample size of group 2.
        confidence: Confidence level.
        
    Returns:
        Tuple of (lower_bound, upper_bound).
    """
    # Approximate standard error for Cohen's d
    n = n1 + n2
    se = np.sqrt((n / (n1 * n2)) + (effect_size**2 / (2 * n)))
    
    z = stats.norm.ppf((1 + confidence) / 2)
    lower = effect_size - z * se
    upper = effect_size + z * se
    
    return float(lower), float(upper)

def apply_bonferroni_correction(
    p_values: List[float],
    alpha: float = 0.05
) -> List[float]:
    """
    Apply Bonferroni correction to a list of p-values.
    
    Args:
        p_values: List of p-values.
        alpha: Significance level.
        
    Returns:
        List of adjusted p-values.
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return []
    
    adjusted = [min(p * n_tests, 1.0) for p in p_values]
    logger.info(f"Bonferroni correction applied: {n_tests} tests, alpha={alpha}")
    return adjusted

def check_collinearity(
    df: pd.DataFrame,
    predictors: List[str]
) -> Dict[str, float]:
    """
    Check for collinearity between predictors.
    
    Args:
        df: DataFrame containing the data.
        predictors: List of predictor column names.
        
    Returns:
        Dictionary with correlation coefficients.
    """
    corr_matrix = df[predictors].corr()
    max_corr = 0.0
    for i in range(len(predictors)):
        for j in range(i + 1, len(predictors)):
            corr = abs(corr_matrix.iloc[i, j])
            if corr > max_corr:
                max_corr = corr
    
    logger.info(f"Max collinearity: {max_corr:.4f}")
    return {"max_correlation": float(max_corr)}

def calculate_power(
    effect_size: float,
    n1: int,
    n2: int,
    alpha: float = 0.05
) -> float:
    """
    Calculate achieved power for a t-test.
    
    Args:
        effect_size: Cohen's d value.
        n1: Sample size of group 1.
        n2: Sample size of group 2.
        alpha: Significance level.
        
    Returns:
        Power value.
    """
    from statsmodels.stats.power import TTestIndPower
    
    power_analysis = TTestIndPower()
    n = n1 + n2
    power = power_analysis.power(effect_size=effect_size, nobs1=n/2, ratio=1.0, alpha=alpha)
    
    logger.info(f"Calculated power: {power:.4f}")
    return float(power)

def frame_inference(
    findings: Dict[str, Any]
) -> str:
    """
    Frame the inference as associational.
    
    Args:
        findings: Dictionary of findings.
        
    Returns:
        Framed inference string.
    """
    return "associational"

def aggregate_stats_results(
    ancova_result: Dict[str, float],
    t_test_result: Tuple[float, float],
    effect_size: float,
    confidence_interval: Tuple[float, float],
    power: float,
    collinearity: Dict[str, float],
    inference_framing: str
) -> Dict[str, Any]:
    """
    Aggregate all statistical results into a single dictionary.
    
    Args:
        ancova_result: ANCOVA results.
        t_test_result: T-test results.
        effect_size: Cohen's d.
        confidence_interval: CI tuple.
        power: Power value.
        collinearity: Collinearity diagnostics.
        inference_framing: Framing string.
        
    Returns:
        Aggregated results dictionary.
    """
    return {
        "ancova_f_statistic": ancova_result.get("f_statistic", 0.0),
        "ancova_p_value": ancova_result.get("p_value", 0.0),
        "secondary_descriptive_stats": {
            "t_statistic": t_test_result[0],
            "p_value": t_test_result[1]
        },
        "effect_size_cohen_d": effect_size,
        "confidence_interval": list(confidence_interval),
        "inference_framing": inference_framing,
        "power": power,
        "collinearity_diagnostics": collinearity
    }

def write_analysis_results(
    results: Dict[str, Any],
    output_path: str
) -> None:
    """
    Write analysis results to a JSON file.
    
    Args:
        results: Dictionary of results.
        output_path: Path to the output JSON file.
    """
    from pathlib import Path
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Analysis results written to {output_path}")