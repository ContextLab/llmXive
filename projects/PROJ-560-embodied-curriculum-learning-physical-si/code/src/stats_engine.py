"""
Statistical engine for embodied curriculum learning analysis.
Implements t-tests, effect sizes, corrections, and diagnostic checks.
"""
import logging
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
from scipy import stats
from .models import AnalysisResult

logger = logging.getLogger(__name__)

def run_t_test(group_a: List[float], group_b: List[float], equal_var: bool = False) -> Dict[str, Any]:
    """
    Perform an independent samples t-test on gain scores.
    
    Logic:
    1. Check for empty groups.
    2. Perform Levene's test for equality of variances if `equal_var` is not explicitly forced.
       However, per FR-002, we decide Student vs Welch based on Levene's result.
       If Levene's p-value < 0.05, variances are unequal -> Welch's t-test.
       Otherwise -> Student's t-test.
    3. Compute t-statistic and p-value.
    
    Args:
        group_a: List of gain scores for the first group (e.g., Embodied).
        group_b: List of gain scores for the second group (e.g., Static).
        equal_var: If True, force Student's t-test (equal variances assumed).
                   If False, determine test type via Levene's test.
    
    Returns:
        Dictionary with keys: 'test_type', 't_statistic', 'p_value', 'df'.
    
    Raises:
        ValueError: If groups are empty or contain non-numeric data.
    """
    if not group_a or not group_b:
        raise ValueError("Both groups must contain at least one observation.")
    
    arr_a = np.array(group_a)
    arr_b = np.array(group_b)
    
    # Validate data types
    if not np.issubdtype(arr_a.dtype, np.number) or not np.issubdtype(arr_b.dtype, np.number):
        raise ValueError("Input groups must contain numeric values.")
    
    # Determine test type based on Levene's test if not forced
    if not equal_var:
        levene_stat, levene_p = stats.levene(arr_a, arr_b)
        logger.debug(f"Levene's Test: stat={levene_stat:.4f}, p={levene_p:.4f}")
        if levene_p < 0.05:
            test_type = "Welch's t-test"
            equal_var_assumed = False
            logger.info("Variances unequal (Levene p < 0.05). Using Welch's t-test.")
        else:
            test_type = "Student's t-test"
            equal_var_assumed = True
            logger.info("Variances equal (Levene p >= 0.05). Using Student's t-test.")
    else:
        test_type = "Student's t-test (forced)"
        equal_var_assumed = True
    
    # Run t-test
    t_stat, p_val = stats.ttest_ind(arr_a, arr_b, equal_var=equal_var_assumed)
    
    # Calculate degrees of freedom
    n1, n2 = len(arr_a), len(arr_b)
    if equal_var_assumed:
        df = n1 + n2 - 2
    else:
        # Welch-Satterthwaite equation
        v1 = np.var(arr_a, ddof=1)
        v2 = np.var(arr_b, ddof=1)
        num = (v1/n1 + v2/n2)**2
        den = (v1/n1)**2 / (n1-1) + (v2/n2)**2 / (n2-1)
        df = num / den
    
    result = {
        "test_type": test_type,
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "df": float(df),
        "n_a": n1,
        "n_b": n2
    }
    
    logger.info(f"T-Test Result: {test_type}, t={t_stat:.4f}, p={p_val:.4f}, df={df:.2f}")
    return result

def calculate_effect_size(group_a: List[float], group_b: List[float]) -> Dict[str, float]:
    """
    Calculate Cohen's d effect size.
    
    Args:
        group_a: List of gain scores for group A.
        group_b: List of gain scores for group B.
    
    Returns:
        Dictionary with 'cohens_d' and 'pooled_std'.
    """
    if not group_a or not group_b:
        raise ValueError("Both groups must contain observations.")
    
    arr_a = np.array(group_a)
    arr_b = np.array(group_b)
    
    mean_a = np.mean(arr_a)
    mean_b = np.mean(arr_b)
    
    n1, n2 = len(arr_a), len(arr_b)
    var1 = np.var(arr_a, ddof=1)
    var2 = np.var(arr_b, ddof=1)
    
    # Pooled standard deviation
    pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
    pooled_std = np.sqrt(pooled_var)
    
    if pooled_std == 0:
        cohens_d = 0.0
    else:
        cohens_d = (mean_a - mean_b) / pooled_std
    
    logger.debug(f"Cohen's d: {cohens_d:.4f}, Pooled Std: {pooled_std:.4f}")
    return {
        "cohens_d": float(cohens_d),
        "pooled_std": float(pooled_std),
        "mean_a": float(mean_a),
        "mean_b": float(mean_b)
    }

def calculate_confidence_interval(group_a: List[float], group_b: List[float], confidence: float = 0.95) -> Dict[str, float]:
    """
    Calculate confidence interval for the difference in means.
    
    Args:
        group_a: List of gain scores for group A.
        group_b: List of gain scores for group B.
        confidence: Confidence level (e.g., 0.95).
    
    Returns:
        Dictionary with 'ci_lower', 'ci_upper', 'mean_diff'.
    """
    if not group_a or not group_b:
        raise ValueError("Both groups must contain observations.")
    
    arr_a = np.array(group_a)
    arr_b = np.array(group_b)
    
    mean_diff = np.mean(arr_a) - np.mean(arr_b)
    
    # Standard error of the difference
    n1, n2 = len(arr_a), len(arr_b)
    var1 = np.var(arr_a, ddof=1)
    var2 = np.var(arr_b, ddof=1)
    
    se_diff = np.sqrt(var1/n1 + var2/n2)
    
    # Critical value from t-distribution
    # Approximate df using Welch-Satterthwaite for CI
    num = (var1/n1 + var2/n2)**2
    den = (var1/n1)**2 / (n1-1) + (var2/n2)**2 / (n2-1)
    df = num / den if den > 0 else n1 + n2 - 2
    
    alpha = 1 - confidence
    t_crit = stats.t.ppf(1 - alpha/2, df)
    
    margin = t_crit * se_diff
    
    ci_lower = mean_diff - margin
    ci_upper = mean_diff + margin
    
    logger.debug(f"95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")
    return {
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "mean_diff": float(mean_diff),
        "confidence_level": confidence
    }

def apply_bonferroni_correction(p_values: List[float], num_tests: int) -> List[Dict[str, Any]]:
    """
    Apply Bonferroni correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values.
        num_tests: Total number of tests performed (for correction factor).
    
    Returns:
        List of dictionaries with 'raw_p', 'adjusted_p', 'is_significant'.
    """
    if not p_values:
        return []
    
    adjusted_results = []
    alpha = 0.05
    adjusted_alpha = alpha / num_tests if num_tests > 0 else alpha
    
    for p in p_values:
        adj_p = min(p * num_tests, 1.0)
        is_sig = adj_p < alpha
        adjusted_results.append({
            "raw_p": float(p),
            "adjusted_p": float(adj_p),
            "is_significant": is_sig,
            "threshold": adjusted_alpha
        })
    
    logger.info(f"Bonferroni correction applied: {num_tests} tests, adjusted alpha={adjusted_alpha:.4f}")
    return adjusted_results

def frame_inference(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Explicitly label findings as 'associational' and add methodological caveats.
    
    Args:
        results: Dictionary containing statistical test results.
    
    Returns:
        Updated dictionary with framing metadata.
    """
    framed = results.copy()
    framed["interpretation_framing"] = "associational"
    framed["methodological_caveats"] = [
        "Results indicate an association between instruction type and gain scores.",
        "Causal claims cannot be made without randomization or controlled experimental design.",
        "Confounding variables may influence the observed relationship."
    ]
    logger.debug("Inference framed as associational.")
    return framed

def check_collinearity(data: Dict[str, List[float]], threshold: float = 0.8) -> Dict[str, Any]:
    """
    Detect collinearity between predictors (covariates) if present.
    
    Args:
        data: Dictionary where keys are feature names and values are lists of values.
        threshold: Absolute correlation threshold to flag collinearity.
    
    Returns:
        Dictionary with 'collinearity_detected', 'pairs', 'diagnostics'.
    """
    keys = list(data.keys())
    n_features = len(keys)
    pairs = []
    collinearity_detected = False
    
    if n_features < 2:
        return {
            "collinearity_detected": False,
            "pairs": [],
            "diagnostics": "Insufficient features for collinearity check."
        }
    
    # Convert to numpy array for matrix operations
    try:
        matrix = np.column_stack([np.array(data[k]) for k in keys])
    except ValueError:
        return {
            "collinearity_detected": False,
            "pairs": [],
            "diagnostics": "Feature arrays have mismatched lengths."
        }
    
    # Calculate correlation matrix
    corr_matrix = np.corrcoef(matrix.T)
    
    for i in range(n_features):
        for j in range(i + 1, n_features):
            corr_val = corr_matrix[i, j]
            if abs(corr_val) > threshold:
                collinearity_detected = True
                pairs.append({
                    "feature_1": keys[i],
                    "feature_2": keys[j],
                    "correlation": float(corr_val),
                    "flag": "HIGH_COLLINEARITY"
                })
    
    return {
        "collinearity_detected": collinearity_detected,
        "pairs": pairs,
        "diagnostics": f"Checked {n_features} features. Threshold: {threshold}."
    }

def calculate_power(group_a: List[float], group_b: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Calculate achieved statistical power for the observed effect size.
    
    Args:
        group_a: List of gain scores for group A.
        group_b: List of gain scores for group B.
        alpha: Significance level.
    
    Returns:
        Dictionary with 'power', 'is_underpowered'.
    """
    if not group_a or not group_b:
        return {"power": 0.0, "is_underpowered": True, "reason": "Empty groups"}
    
    arr_a = np.array(group_a)
    arr_b = np.array(group_b)
    
    n1, n2 = len(arr_a), len(arr_b)
    mean_diff = np.mean(arr_a) - np.mean(arr_b)
    
    var1 = np.var(arr_a, ddof=1)
    var2 = np.var(arr_b, ddof=1)
    pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
    pooled_std = np.sqrt(pooled_var)
    
    if pooled_std == 0:
        return {"power": 0.0, "is_underpowered": True, "reason": "Zero variance"}
    
    cohens_d = mean_diff / pooled_std
    
    # Power calculation using t-test parameters
    # Approximation using non-centrality parameter
    # ncp = d * sqrt(n1*n2 / (n1+n2))
    ncp = cohens_d * np.sqrt((n1 * n2) / (n1 + n2))
    df = n1 + n2 - 2
    
    # Critical t-value
    t_crit = stats.t.ppf(1 - alpha/2, df)
    
    # Power is probability that t > t_crit under H1
    # Using non-central t-distribution
    power = stats.nct.sf(t_crit, df, ncp) + stats.nct.cdf(-t_crit, df, ncp)
    
    is_underpowered = power < 0.80
    
    logger.info(f"Calculated Power: {power:.4f}. Underpowered: {is_underpowered}")
    
    return {
        "power": float(power),
        "is_underpowered": is_underpowered,
        "effect_size": float(cohens_d),
        "sample_size_total": n1 + n2
    }

def aggregate_results(t_test_result: Dict[str, Any], effect_size: Dict[str, float], 
                      ci_result: Dict[str, float], power_result: Dict[str, Any],
                      collinearity: Dict[str, Any], bonferroni: Optional[List[Dict[str, Any]]] = None) -> AnalysisResult:
    """
    Aggregate all statistical results into an AnalysisResult object.
    
    Args:
        t_test_result: Output from run_t_test.
        effect_size: Output from calculate_effect_size.
        ci_result: Output from calculate_confidence_interval.
        power_result: Output from calculate_power.
        collinearity: Output from check_collinearity.
        bonferroni: Optional list of adjusted p-values.
    
    Returns:
        AnalysisResult dataclass instance.
    """
    return AnalysisResult(
        test_type=t_test_result["test_type"],
        t_statistic=t_test_result["t_statistic"],
        p_value=t_test_result["p_value"],
        df=t_test_result["df"],
        effect_size_cohens_d=effect_size["cohens_d"],
        mean_diff=ci_result["mean_diff"],
        ci_lower=ci_result["ci_lower"],
        ci_upper=ci_result["ci_upper"],
        power=power_result["power"],
        is_underpowered=power_result["is_underpowered"],
        collinearity_detected=collinearity["collinearity_detected"],
        collinearity_pairs=collinearity["pairs"],
        bonferroni_results=bonferroni or [],
        interpretation_framing="associational"
    )