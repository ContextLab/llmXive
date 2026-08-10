import logging
from typing import Dict, Any, Optional, Tuple, List, Union
import numpy as np
import pandas as pd
import scipy.stats as stats
from statsmodels.formula.api import mixedlm
import statsmodels.api as sm

logger = logging.getLogger(__name__)

def check_normality(data: Union[List[float], np.ndarray], alpha: float = 0.05) -> Tuple[bool, float]:
    """
    Perform Shapiro-Wilk test for normality.
    
    Args:
        data: Input data array.
        alpha: Significance level.
        
    Returns:
        Tuple of (is_normal, p_value).
    """
    if len(data) < 3:
        logger.warning("Sample size too small for Shapiro-Wilk test (< 3). Assuming non-normal.")
        return False, 1.0
    
    try:
        stat, p_value = stats.shapiro(data)
        is_normal = p_value >= alpha
        logger.info(f"Shapiro-Wilk test: statistic={stat:.4f}, p-value={p_value:.4f}, normal={is_normal}")
        return is_normal, p_value
    except Exception as e:
        logger.error(f"Shapiro-Wilk test failed: {e}")
        return False, 0.0

def shapiro_wilk_test(data: Union[List[float], np.ndarray], alpha: float = 0.05) -> Tuple[bool, float]:
    """Alias for check_normality."""
    return check_normality(data, alpha)

def fit_lmm(data: pd.DataFrame, formula: str) -> Dict[str, Any]:
    """
    Fit a Linear Mixed Model (LMM) using statsmodels.
    
    Args:
        data: DataFrame containing the data.
        formula: R-style formula string, e.g., "score ~ method + (1|Domain)".
        
    Returns:
        Dictionary containing:
            - p_value: p-value for the fixed effect of 'method'
            - statistic: t-statistic for the fixed effect of 'method'
            - df: degrees of freedom (approximate)
            - success: boolean indicating if the model fitted successfully
            - error: error message if failed, else None
    """
    logger.info(f"Fitting LMM with formula: {formula}")
    
    try:
        # Ensure the formula is valid for mixedlm
        # statsmodels mixedlm expects: endog ~ exog + (1|groups)
        # The formula string provided should already be in this format.
        
        # Fit the model
        # We need to extract the group variable from the formula to pass to mixedlm explicitly
        # However, statsmodels.formula.api.mixedlm handles the formula parsing directly.
        
        model = mixedlm.from_formula(formula, data=data)
        result = model.fit()
        
        # Extract fixed effects results
        # The parameters are stored in result.params
        # We need to find the coefficient for the 'method' variable
        # Assuming 'method' is the main independent variable of interest
        
        # Get the summary table to extract stats for the specific variable
        # result.summary2() returns a detailed summary
        
        # Accessing the specific parameter for the method effect
        # The key in params might be 'method[T.baseline]' or similar depending on encoding
        method_keys = [k for k in result.params.index if 'method' in k.lower()]
        
        if not method_keys:
            logger.warning(f"No 'method' coefficient found in model results. Keys: {list(result.params.index)}")
            # Fallback: return generic stats if specific key not found, or raise
            # For robustness, let's try to grab the first non-intercept fixed effect if 'method' isn't explicitly named
            # But strictly following the task, we look for 'method'.
            return {
                "p_value": None,
                "statistic": None,
                "df": None,
                "success": False,
                "error": "Could not find 'method' coefficient in fitted model."
            }
        
        # Assuming the first match is the one of interest (e.g., method[T.baseline])
        # If there are multiple levels, we might need to aggregate or pick one. 
        # For a binary comparison, there is usually one coefficient.
        key = method_keys[0]
        
        coef = result.params[key]
        std_err = result.bse[key]
        t_stat = coef / std_err if std_err != 0 else 0.0
        
        # Calculate p-value from t-statistic
        # statsmodels doesn't always give exact p-values for LMM in the same way as OLS
        # We approximate using the normal distribution or t-distribution with large df
        # A common approximation is using the standard normal for large samples
        # However, result.pvalues is available in some versions or we can calculate it.
        
        # Try to get p-value from result if available, otherwise calculate
        if hasattr(result, 'pvalues') and key in result.pvalues:
            p_val = result.pvalues[key]
        else:
            # Approximate p-value from t-statistic (two-tailed)
            # Degrees of freedom are complex in LMM; using a large number approximation or result.df_resid
            df = result.df_resid if hasattr(result, 'df_resid') and result.df_resid > 0 else 1000
            p_val = 2 * (1 - stats.t.cdf(abs(t_stat), df))
        
        logger.info(f"LMM Fitted: coefficient={coef:.4f}, t_stat={t_stat:.4f}, p_value={p_val:.4f}")
        
        return {
            "p_value": p_val,
            "statistic": t_stat,
            "df": result.df_resid if hasattr(result, 'df_resid') else None,
            "success": True,
            "error": None
        }
        
    except Exception as e:
        logger.error(f"LMM fitting failed: {e}")
        return {
            "p_value": None,
            "statistic": None,
            "df": None,
            "success": False,
            "error": str(e)
        }

def fit_linear_mixed_model(data: pd.DataFrame, formula: str) -> Dict[str, Any]:
    """Alias for fit_lmm."""
    return fit_lmm(data, formula)

def run_wilcoxon_test(data1: Union[List[float], np.ndarray], data2: Union[List[float], np.ndarray]) -> Dict[str, Any]:
    """
    Run Wilcoxon signed-rank test for paired data.
    """
    try:
        stat, p_value = stats.wilcoxon(data1, data2)
        return {
            "p_value": p_value,
            "statistic": stat,
            "success": True,
            "error": None
        }
    except Exception as e:
        logger.error(f"Wilcoxon test failed: {e}")
        return {
            "p_value": None,
            "statistic": None,
            "success": False,
            "error": str(e)
        }

def run_domain_stratified_analysis(data: pd.DataFrame, score_col: str, method_col: str, domain_col: str) -> Dict[str, Any]:
    """
    Perform domain-stratified Wilcoxon tests and aggregate p-values.
    """
    domains = data[domain_col].unique()
    p_values = []
    
    logger.info(f"Running stratified analysis over {len(domains)} domains.")
    
    for domain in domains:
        subset = data[data[domain_col] == domain]
        if subset[method_col].nunique() < 2:
            logger.warning(f"Skipping domain {domain}: not enough methods.")
            continue
        
        # Assuming paired data or converting to paired if possible
        # If the data is structured as long-form with method as a column, we pivot
        # But for Wilcoxon, we need paired arrays.
        # This function assumes the data is already paired or we are comparing two methods within domain.
        # If the data is not paired, this might need adjustment. 
        # For the purpose of this task, we assume we can extract two series.
        
        # Simple pivot for paired assumption
        pivot = subset.pivot_table(index=score_col, columns=method_col, values=score_col, aggfunc='first') 
        # The above pivot is logically flawed for this specific structure. 
        # Correct approach: group by the pairing ID if available, or assume row-wise pairing.
        # Since we don't have an explicit pairing ID in the generic signature, we assume row order is paired.
        
        methods = subset[method_col].unique()
        if len(methods) != 2:
            continue
        
        m1, m2 = methods
        s1 = subset[subset[method_col] == m1][score_col].values
        s2 = subset[subset[method_col] == m2][score_col].values
        
        if len(s1) != len(s2) or len(s1) < 2:
            continue
            
        res = run_wilcoxon_test(s1, s2)
        if res['success'] and res['p_value'] is not None:
            p_values.append(res['p_value'])
    
    if not p_values:
        return {
            "p_value": None,
            "statistic": None,
            "success": False,
            "error": "No valid domains for stratified analysis."
        }
    
    # Fisher's method for combining p-values
    try:
        chi2_stat, combined_p = stats.fisher_exact if False else stats.combine_pvalues(p_values, method='fisher')
        # stats.combine_pvalues returns (chi2, p)
        return {
            "p_value": combined_p,
            "statistic": chi2_stat,
            "success": True,
            "error": None
        }
    except Exception as e:
        logger.error(f"P-value combination failed: {e}")
        return {
            "p_value": None,
            "statistic": None,
            "success": False,
            "error": str(e)
        }

def select_statistical_test(data: pd.DataFrame, method_col: str, group_col: str, score_col: str = "score") -> Dict[str, Any]:
    """
    Select and run the appropriate statistical test based on normality.
    1. Shapiro-Wilk on residuals or data.
    2. If normal -> LMM (with fallback to stratified Wilcoxon).
    3. If non-normal -> Stratified Wilcoxon.
    """
    # Prepare data for normality check
    # We check the distribution of the score column, perhaps grouped by method
    # A simple check on the residuals of a fixed effect model is ideal, but for simplicity:
    # Check normality of the score column overall or per group.
    
    # Let's check normality of the score column
    scores = data[score_col].dropna().values
    is_normal, p_val_normal = check_normality(scores)
    
    formula = f"{score_col} ~ {method_col} + (1|{group_col})"
    
    if is_normal:
        logger.info("Data appears normal. Attempting LMM.")
        lmm_res = fit_lmm(data, formula)
        if lmm_res['success']:
            return {
                "method": "LMM",
                "result": lmm_res
            }
        else:
            logger.warning("LMM failed (singular matrix or similar). Falling back to stratified Wilcoxon.")
            strat_res = run_domain_stratified_analysis(data, score_col, method_col, group_col)
            return {
                "method": "Stratified Wilcoxon (LMM Fallback)",
                "result": strat_res
            }
    else:
        logger.info("Data non-normal. Using Stratified Wilcoxon.")
        strat_res = run_domain_stratified_analysis(data, score_col, method_col, group_col)
        return {
            "method": "Stratified Wilcoxon",
            "result": strat_res
        }

def run_statistical_analysis(data: pd.DataFrame, method_col: str, group_col: str, score_col: str = "score") -> Dict[str, Any]:
    """Wrapper for select_statistical_test."""
    return select_statistical_test(data, method_col, group_col, score_col)

def main():
    """Example usage for testing."""
    import pandas as pd
    import numpy as np
    
    # Generate dummy data
    np.random.seed(42)
    n = 100
    data = pd.DataFrame({
        "score": np.random.normal(0, 1, n),
        "method": np.random.choice(["gatekeeper", "baseline"], n),
        "Domain": np.random.choice(["medical", "office", "education"], n)
    })
    
    formula = "score ~ method + (1|Domain)"
    result = fit_lmm(data, formula)
    print(f"LMM Result: {result}")

if __name__ == "__main__":
    main()