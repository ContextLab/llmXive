"""
Statistical analysis utilities for GateMem benchmarking.

Implements:
- Shapiro-Wilk normality test
- Linear Mixed Models (LMM) with statsmodels
- Paired t-test and Wilcoxon signed-rank fallbacks
- Domain-stratified analysis
"""

import logging
from typing import Dict, Any, Optional, Tuple, List, Union
import numpy as np
import pandas as pd
import scipy.stats as stats
from statsmodels.formula.api import mixedlm
from statsmodels.regression.mixed_linear_model import MixedLMResults

logger = logging.getLogger(__name__)

def shapiro_wilk_test(data: Union[np.ndarray, pd.Series, List[float]]) -> Dict[str, Any]:
    """
    Perform Shapiro-Wilk normality test.
    
    Args:
        data: Input data array or series
        
    Returns:
        Dictionary with 'statistic' and 'pvalue' keys
    """
    data_array = np.asarray(data).flatten()
    # Remove NaN values
    data_array = data_array[~np.isnan(data_array)]
    
    if len(data_array) < 3:
        logger.warning("Shapiro-Wilk test requires at least 3 data points. Returning NaN.")
        return {"statistic": np.nan, "pvalue": np.nan}
    
    try:
        statistic, pvalue = stats.shapiro(data_array)
        return {"statistic": float(statistic), "pvalue": float(pvalue)}
    except Exception as e:
        logger.error(f"Shapiro-Wilk test failed: {e}")
        return {"statistic": np.nan, "pvalue": np.nan}

def fit_linear_mixed_model(
    df: pd.DataFrame,
    formula: str = "score ~ method + (1|Domain)",
    random_state: Optional[int] = None
) -> Dict[str, Any]:
    """
    Fit a Linear Mixed Model (LMM) using statsmodels.
    
    Args:
        df: DataFrame containing the data
        formula: Model formula (default: score ~ method + (1|Domain))
        random_state: Random seed for reproducibility
        
    Returns:
        Dictionary with model results or error information
    """
    if random_state is not None:
        np.random.seed(random_state)
    
    try:
        # Fit the model
        model = mixedlm.from_formula(formula, data=df, groups="Domain")
        result = model.fit()
        
        return {
            "success": True,
            "method": "LMM",
            "formula": formula,
            "fixed_effects": result.params.to_dict(),
            "random_effects_variance": result.random_effects,
            "log_likelihood": result.llf,
            "aic": result.aic,
            "bic": result.bic,
            "p_values": result.pvalues.to_dict(),
            "degrees_of_freedom": None,  # LMM uses approximate DF
            "test_statistic": None,  # We'll extract specific coefficients if needed
            "message": "LMM fitted successfully"
        }
    except Exception as e:
        logger.warning(f"LMM fitting failed (likely singular matrix): {e}")
        return {
            "success": False,
            "method": "LMM",
            "error": str(e),
            "message": "LMM failed - singular matrix or convergence issue"
        }

def run_paired_ttest(
    group1: Union[np.ndarray, pd.Series, List[float]],
    group2: Union[np.ndarray, pd.Series, List[float]]
) -> Dict[str, Any]:
    """
    Perform paired t-test.
    
    Args:
        group1: First group of paired data
        group2: Second group of paired data
        
    Returns:
        Dictionary with test results
    """
    g1 = np.asarray(group1).flatten()
    g2 = np.asarray(group2).flatten()
    
    # Remove NaN pairs
    mask = ~(np.isnan(g1) | np.isnan(g2))
    g1 = g1[mask]
    g2 = g2[mask]
    
    if len(g1) < 2:
        logger.warning("Paired t-test requires at least 2 pairs. Returning NaN.")
        return {
            "success": True,
            "method": "paired_ttest",
            "statistic": np.nan,
            "pvalue": np.nan,
            "degrees_of_freedom": len(g1) - 1 if len(g1) > 1 else np.nan,
            "message": "Insufficient data for paired t-test"
        }
    
    try:
        statistic, pvalue = stats.ttest_rel(g1, g2)
        return {
            "success": True,
            "method": "paired_ttest",
            "statistic": float(statistic),
            "pvalue": float(pvalue),
            "degrees_of_freedom": len(g1) - 1,
            "message": "Paired t-test completed successfully"
        }
    except Exception as e:
        logger.error(f"Paired t-test failed: {e}")
        return {
            "success": False,
            "method": "paired_ttest",
            "error": str(e),
            "message": "Paired t-test failed"
        }

def run_wilcoxon_test(
    group1: Union[np.ndarray, pd.Series, List[float]],
    group2: Union[np.ndarray, pd.Series, List[float]]
) -> Dict[str, Any]:
    """
    Perform Wilcoxon signed-rank test (non-parametric paired test).
    
    Args:
        group1: First group of paired data
        group2: Second group of paired data
        
    Returns:
        Dictionary with test results
    """
    g1 = np.asarray(group1).flatten()
    g2 = np.asarray(group2).flatten()
    
    # Remove NaN pairs
    mask = ~(np.isnan(g1) | np.isnan(g2))
    g1 = g1[mask]
    g2 = g2[mask]
    
    if len(g1) < 2:
        logger.warning("Wilcoxon test requires at least 2 pairs. Returning NaN.")
        return {
            "success": True,
            "method": "wilcoxon",
            "statistic": np.nan,
            "pvalue": np.nan,
            "degrees_of_freedom": None,
            "message": "Insufficient data for Wilcoxon test"
        }
    
    try:
        statistic, pvalue = stats.wilcoxon(g1, g2)
        return {
            "success": True,
            "method": "wilcoxon",
            "statistic": float(statistic),
            "pvalue": float(pvalue),
            "degrees_of_freedom": None,
            "message": "Wilcoxon test completed successfully"
        }
    except Exception as e:
        logger.error(f"Wilcoxon test failed: {e}")
        return {
            "success": False,
            "method": "wilcoxon",
            "error": str(e),
            "message": "Wilcoxon test failed"
        }

def run_statistical_analysis(
    df: pd.DataFrame,
    score_col: str = "score",
    method_col: str = "method",
    domain_col: str = "Domain",
    method1: str = "Gatekeeper",
    method2: str = "Baseline"
) -> Dict[str, Any]:
    """
    Run full statistical analysis with automatic fallback.
    
    Tries LMM first, then falls back to paired tests if LMM fails
    (singular matrix) or if data is flat (constant values).
    
    Args:
        df: DataFrame with scores, methods, and domains
        score_col: Name of the score column
        method_col: Name of the method column
        domain_col: Name of the domain column
        method1: First method to compare
        method2: Second method to compare
        
    Returns:
        Dictionary with analysis results and method used
    """
    # Filter for the two methods
    df_filtered = df[df[method_col].isin([method1, method2])]
    
    if len(df_filtered) == 0:
        return {
            "success": False,
            "error": f"No data found for methods {method1} and {method2}",
            "method_used": None
        }
    
    # Check for flat data (constant values)
    unique_scores = df_filtered[score_col].nunique()
    if unique_scores == 1:
        logger.warning("Data is flat (constant values). Cannot perform statistical tests.")
        return {
            "success": False,
            "error": "Data is flat (constant values)",
            "method_used": None,
            "message": "No variance in data - statistical tests not applicable"
        }
    
    # Try LMM first
    formula = f"{score_col} ~ {method_col} + (1|{domain_col})"
    lmm_result = fit_linear_mixed_model(df_filtered, formula=formula)
    
    if lmm_result["success"]:
        logger.info("LMM succeeded. Using LMM results.")
        return {
            "success": True,
            "method_used": "LMM",
            "results": lmm_result,
            "message": "Analysis completed using Linear Mixed Model"
        }
    
    # LMM failed - try paired tests
    logger.info("LMM failed. Attempting paired tests as fallback.")
    
    # Reshape data for paired test
    pivot = df_filtered.pivot_table(
        index=df_filtered.groupby(method_col).cumcount(),
        columns=method_col,
        values=score_col
    )
    
    if method1 not in pivot.columns or method2 not in pivot.columns:
        return {
            "success": False,
            "error": f"Could not reshape data for paired test. Missing columns: {method1} or {method2}",
            "method_used": None
        }
    
    g1 = pivot[method1].dropna()
    g2 = pivot[method2].dropna()
    
    # Ensure same length by taking intersection
    min_len = min(len(g1), len(g2))
    if min_len < 2:
        logger.warning("Insufficient paired data for t-test/Wilcoxon.")
        return {
            "success": False,
            "error": "Insufficient paired data",
            "method_used": None
        }
    
    g1 = g1.iloc[:min_len]
    g2 = g2.iloc[:min_len]
    
    # Try paired t-test first (more powerful if assumptions met)
    ttest_result = run_paired_ttest(g1, g2)
    
    if ttest_result["success"] and not np.isnan(ttest_result["pvalue"]):
        logger.info("Paired t-test succeeded. Using paired t-test results.")
        return {
            "success": True,
            "method_used": "paired_ttest",
            "results": ttest_result,
            "message": "Analysis completed using paired t-test (LMM fallback)"
        }
    
    # Fall back to Wilcoxon
    logger.info("Paired t-test failed or inconclusive. Using Wilcoxon test.")
    wilcoxon_result = run_wilcoxon_test(g1, g2)
    
    if wilcoxon_result["success"]:
        return {
            "success": True,
            "method_used": "wilcoxon",
            "results": wilcoxon_result,
            "message": "Analysis completed using Wilcoxon signed-rank test (LMM fallback)"
        }
    
    return {
        "success": False,
        "error": "All statistical methods failed",
        "method_used": None,
        "lmm_error": lmm_result.get("error"),
        "ttest_result": ttest_result,
        "wilcoxon_result": wilcoxon_result
    }

def run_domain_stratified_analysis(
    df: pd.DataFrame,
    score_col: str = "score",
    method_col: str = "method",
    domain_col: str = "Domain",
    method1: str = "Gatekeeper",
    method2: str = "Baseline"
) -> Dict[str, Any]:
    """
    Run domain-stratified analysis (separate tests per domain).
    
    Per Constitution Principle VI, if LMM is not feasible, we run
    separate paired tests for each domain and aggregate results.
    
    Args:
        df: DataFrame with scores, methods, domains
        score_col: Name of the score column
        method_col: Name of the method column
        domain_col: Name of the domain column
        method1: First method to compare
        method2: Second method to compare
        
    Returns:
        Dictionary with per-domain results and aggregated summary
    """
    domains = df[domain_col].unique()
    domain_results = {}
    all_pvalues = []
    all_statistics = []
    methods_used = []
    
    logger.info(f"Running domain-stratified analysis for {len(domains)} domains: {domains}")
    
    for domain in domains:
        domain_df = df[df[domain_col] == domain]
        
        # Check if we have both methods in this domain
        if method1 not in domain_df[method_col].values or method2 not in domain_df[method_col].values:
            logger.warning(f"Skipping domain '{domain}': missing one or both methods.")
            domain_results[domain] = {
                "success": False,
                "error": f"Missing method in domain '{domain}'",
                "method_used": None
            }
            continue
        
        # Run statistical analysis for this domain
        result = run_statistical_analysis(
            domain_df,
            score_col=score_col,
            method_col=method_col,
            domain_col=domain_col,
            method1=method1,
            method2=method2
        )
        
        domain_results[domain] = result
        
        if result["success"]:
            methods_used.append(result["method_used"])
            if "results" in result:
                res = result["results"]
                if "pvalue" in res and not np.isnan(res["pvalue"]):
                    all_pvalues.append(res["pvalue"])
                if "statistic" in res and not np.isnan(res["statistic"]):
                    all_statistics.append(res["statistic"])
    
    # Aggregate results
    if len(all_pvalues) > 0:
        mean_pvalue = np.mean(all_pvalues)
        median_pvalue = np.median(all_pvalues)
        min_pvalue = np.min(all_pvalues)
        
        # Determine dominant method used
        from collections import Counter
        method_counts = Counter(methods_used)
        dominant_method = method_counts.most_common(1)[0][0] if method_counts else None
        
        aggregation = {
            "num_domains_tested": len([d for d in domain_results if domain_results[d]["success"]]),
            "num_domains_failed": len([d for d in domain_results if not domain_results[d]["success"]]),
            "mean_pvalue": float(mean_pvalue),
            "median_pvalue": float(median_pvalue),
            "min_pvalue": float(min_pvalue),
            "dominant_method": dominant_method,
            "all_pvalues": [float(p) for p in all_pvalues],
            "all_statistics": [float(s) for s in all_statistics]
        }
    else:
        aggregation = {
            "num_domains_tested": 0,
            "num_domains_failed": len(domains),
            "mean_pvalue": np.nan,
            "median_pvalue": np.nan,
            "min_pvalue": np.nan,
            "dominant_method": None,
            "all_pvalues": [],
            "all_statistics": []
        }
    
    return {
        "success": len(all_pvalues) > 0,
        "method_used": "domain_stratified",
        "per_domain_results": domain_results,
        "aggregation": aggregation,
        "message": f"Domain-stratified analysis completed for {len(domains)} domains"
    }

def main():
    """
    Main function for testing statistical analysis functions.
    """
    # Create sample data for testing
    np.random.seed(42)
    n_samples = 100
    
    data = {
        "score": np.random.normal(0.75, 0.1, n_samples),
        "method": np.random.choice(["Gatekeeper", "Baseline"], n_samples),
        "Domain": np.random.choice(["medical", "office", "education", "household"], n_samples)
    }
    
    df = pd.DataFrame(data)
    
    # Test LMM
    print("Testing LMM...")
    lmm_res = fit_linear_mixed_model(df)
    print(f"LMM Success: {lmm_res['success']}")
    
    # Test full analysis
    print("\nTesting full statistical analysis...")
    full_res = run_statistical_analysis(df)
    print(f"Success: {full_res['success']}, Method: {full_res.get('method_used')}")
    
    # Test domain-stratified analysis
    print("\nTesting domain-stratified analysis...")
    strat_res = run_domain_stratified_analysis(df)
    print(f"Success: {strat_res['success']}, Domains tested: {strat_res['aggregation']['num_domains_tested']}")

if __name__ == "__main__":
    main()