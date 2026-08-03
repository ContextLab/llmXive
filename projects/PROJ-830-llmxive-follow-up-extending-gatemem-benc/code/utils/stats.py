"""
Statistical analysis utilities for the llmXive pipeline.
Implements Shapiro-Wilk, Linear Mixed Models (LMM), and fallback paired tests.
Extends T008a with domain-stratified analysis and automatic fallback logic.
"""
import logging
from typing import Dict, Any, Optional, Tuple, List, Union
import numpy as np
import pandas as pd
import scipy.stats as stats
from statsmodels.formula.api import mixedlm
from statsmodels.regression.mixed_linear_model import MixedLMResults

logger = logging.getLogger(__name__)

def shapiro_wilk_test(data: np.ndarray) -> Tuple[float, float]:
    """
    Perform Shapiro-Wilk test for normality.
    
    Args:
        data: 1D array of values.
        
    Returns:
        Tuple of (statistic, p-value).
    """
    if len(data) < 3:
        logger.warning("Shapiro-Wilk requires at least 3 samples.")
        return 0.0, 1.0
    return stats.shapiro(data)

def fit_linear_mixed_model(
    df: pd.DataFrame, 
    formula: str = "score ~ method + (1|Domain)"
) -> Optional[MixedLMResults]:
    """
    Fit a Linear Mixed Model (LMM) using statsmodels.
    
    Args:
        df: DataFrame containing the data.
        formula: Statsmodels formula string.
        
    Returns:
        Fitted model results or None if fitting fails.
    """
    try:
        # Ensure 'method' is categorical for proper encoding
        if 'method' in df.columns:
            df['method'] = df['method'].astype('category')
        
        model = mixedlm.from_formula(formula, df)
        result = model.fit()
        return result
    except Exception as e:
        logger.warning(f"LMM fitting failed: {e}. Will attempt fallback.")
        return None

def run_paired_ttest(
    group_a: np.ndarray, 
    group_b: np.ndarray
) -> Tuple[float, float]:
    """
    Perform paired t-test.
    
    Args:
        group_a: First group of scores.
        group_b: Second group of scores.
        
    Returns:
        Tuple of (t-statistic, p-value).
    """
    if len(group_a) != len(group_b):
        raise ValueError("Groups must be equal length for paired t-test.")
    if len(group_a) < 2:
        raise ValueError("Need at least 2 samples for t-test.")
    return stats.ttest_rel(group_a, group_b)

def run_wilcoxon_test(
    group_a: np.ndarray, 
    group_b: np.ndarray
) -> Tuple[float, float]:
    """
    Perform Wilcoxon signed-rank test (non-parametric paired test).
    
    Args:
        group_a: First group of scores.
        group_b: Second group of scores.
        
    Returns:
        Tuple of (statistic, p-value).
    """
    if len(group_a) != len(group_b):
        raise ValueError("Groups must be equal length for Wilcoxon test.")
    if len(group_a) < 2:
        raise ValueError("Need at least 2 samples for Wilcoxon test.")
    return stats.wilcoxon(group_a, group_b)

def run_statistical_analysis(
    df: pd.DataFrame,
    score_col: str = "score",
    method_col: str = "method",
    domain_col: str = "Domain"
) -> Dict[str, Any]:
    """
    Main analysis function implementing Constitution Principle VI fallback logic.
    
    1. Try LMM: score ~ method + (1|Domain)
    2. If LMM fails (singular matrix or convergence error), fallback to paired tests.
    
    Args:
        df: DataFrame with scores, methods, and domains.
        score_col: Name of the score column.
        method_col: Name of the method column (Gatekeeper vs Baseline).
        domain_col: Name of the domain column.
        
    Returns:
        Dictionary containing test results, method used, and statistics.
    """
    results = {
        "method_used": "LMM",
        "success": False,
        "test_statistic": None,
        "degrees_of_freedom": None,
        "p_value": None,
        "message": ""
    }

    # 1. Attempt LMM
    lmm_result = fit_linear_mixed_model(df)
    
    if lmm_result is not None:
        try:
            # Extract the coefficient for the 'method' effect
            # The fixed effects are in lmm_result.fe_params
            # We need to identify the coefficient corresponding to the non-baseline method
            params = lmm_result.fe_params
            # Assume the formula is 'score ~ method', so there is an intercept and a method effect
            # We look for a key containing 'method'
            method_param = None
            for key, val in params.items():
                if 'method' in key:
                    method_param = val
                    break
            
            if method_param is None:
                raise ValueError("Could not find method parameter in LMM results.")
                
            # Get p-values
            p_values = lmm_result.pvalues
            method_p = None
            for key, val in p_values.items():
                if 'method' in key:
                    method_p = val
                    break
            
            if method_p is None:
                # Fallback to intercept if no method found (unlikely with correct formula)
                method_p = p_values.iloc[0]

            results["method_used"] = "LMM"
            results["test_statistic"] = float(method_param)
            results["degrees_of_freedom"] = "N/A (Mixed Model)"
            results["p_value"] = float(method_p)
            results["success"] = True
            results["message"] = "LMM fit successful."
            return results
        except Exception as e:
            logger.warning(f"Error parsing LMM results: {e}. Falling back to paired tests.")

    # 2. Fallback: Paired Tests
    logger.info("Falling back to paired tests due to LMM failure.")
    results["method_used"] = "Fallback Paired Test"
    
    # Check for normality of differences
    # We need to pair by some ID, but if we don't have a specific ID, we assume
    # the data is already ordered or we just compare the distributions if paired by index.
    # For a robust fallback, we check normality of differences if possible.
    # Since we might not have a 'pair_id', we assume the rows are paired by index
    # or we group by method and check if we can align them.
    # In many benchmark scenarios, we have the same prompts tested with two methods.
    # If the dataframe is long format (one row per method per prompt), we need to pivot.
    
    # Pivot to wide format for paired test
    try:
        wide_df = df.pivot_table(
            index=df.index, # If no explicit pair ID, use index (risky if not sorted)
            columns=method_col, 
            values=score_col
        )
        
        # If pivot failed due to non-unique index, we might need to group.
        # But assuming standard benchmark output where rows are matched:
        col_a = wide_df.iloc[:, 0].values
        col_b = wide_df.iloc[:, 1].values
        
        if len(col_a) != len(col_b):
            raise ValueError("Cannot align methods for paired test.")
        
        # Shapiro-Wilk on differences
        diffs = col_a - col_b
        _, p_norm = shapiro_wilk_test(diffs)
        
        alpha = 0.05
        if p_norm > alpha:
            # Normal distribution -> Paired T-Test
            t_stat, p_val = run_paired_ttest(col_a, col_b)
            results["test_statistic"] = float(t_stat)
            results["degrees_of_freedom"] = len(diffs) - 1
            results["p_value"] = float(p_val)
            results["method_used"] = "Paired T-Test"
            results["message"] = f"Normality passed (p={p_norm:.4f}). Used Paired T-Test."
        else:
            # Non-normal -> Wilcoxon
            w_stat, p_val = run_wilcoxon_test(col_a, col_b)
            results["test_statistic"] = float(w_stat)
            results["degrees_of_freedom"] = "N/A"
            results["p_value"] = float(p_val)
            results["method_used"] = "Wilcoxon Signed-Rank Test"
            results["message"] = f"Normality failed (p={p_norm:.4f}). Used Wilcoxon."
            
        results["success"] = True
        return results
        
    except Exception as e:
        results["message"] = f"Paired test failed: {e}"
        results["success"] = False
        return results

def run_domain_stratified_analysis(
    df: pd.DataFrame,
    score_col: str = "score",
    method_col: str = "method",
    domain_col: str = "Domain"
) -> Dict[str, Any]:
    """
    Perform domain-stratified analysis as requested in T008b.
    Runs separate statistical tests for each domain and aggregates results.
    
    Args:
        df: DataFrame with scores, methods, and domains.
        score_col: Name of the score column.
        method_col: Name of the method column.
        domain_col: Name of the domain column.
        
    Returns:
        Dictionary containing per-domain results and an aggregated summary.
    """
    logger.info("Running domain-stratified analysis.")
    
    domains = df[domain_col].unique()
    domain_results = {}
    all_p_values = []
    all_test_stats = []
    
    for domain in domains:
        domain_df = df[df[domain_col] == domain]
        
        # Check if we have both methods in this domain
        if domain_df[method_col].nunique() < 2:
            logger.warning(f"Domain '{domain}' missing one of the methods. Skipping.")
            domain_results[domain] = {
                "success": False,
                "message": "Missing methods for comparison."
            }
            continue
        
        # Run analysis for this domain
        result = run_statistical_analysis(
            domain_df, 
            score_col=score_col, 
            method_col=method_col, 
            domain_col=domain_col
        )
        
        domain_results[domain] = result
        
        if result["success"]:
            all_p_values.append(result["p_value"])
            if isinstance(result["test_statistic"], (int, float)):
                all_test_stats.append(result["test_statistic"])
    
    # Aggregate summary
    summary = {
        "total_domains": len(domains),
        "successful_domains": len([r for r in domain_results.values() if r.get("success", False)]),
        "average_p_value": float(np.mean(all_p_values)) if all_p_values else None,
        "average_test_statistic": float(np.mean(all_test_stats)) if all_test_stats else None,
        "methods_used": list(set([r["method_used"] for r in domain_results.values() if r.get("success")]))
    }
    
    return {
        "summary": summary,
        "per_domain_results": domain_results
    }

def main():
    """
    Entry point for CLI usage of stats module.
    Demonstrates the fallback and stratified logic.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Create dummy data for demonstration
    data = {
        "score": [0.8, 0.75, 0.9, 0.85, 0.7, 0.65, 0.88, 0.82],
        "method": ["Gatekeeper", "Gatekeeper", "Gatekeeper", "Gatekeeper", 
                   "Baseline", "Baseline", "Baseline", "Baseline"],
        "Domain": ["medical", "medical", "medical", "medical", 
                   "medical", "medical", "medical", "medical"]
    }
    # Note: In real usage, this data would come from the pipeline output.
    # The pairing here is implicit by index for the demo.
    
    df = pd.DataFrame(data)
    
    # Re-order to ensure pairing works in pivot (Gatekeeper first, then Baseline)
    # In a real scenario, there would be a 'pair_id' column.
    # For this demo, we assume the first 4 are Gatekeeper and next 4 are Baseline,
    # which is not ideal for paired tests without an explicit ID.
    # Let's fix the data to be paired by index explicitly for the demo:
    # We need pairs: (G, B), (G, B)...
    demo_data = {
        "score": [0.8, 0.7, 0.75, 0.65, 0.9, 0.8, 0.85, 0.75],
        "method": ["Gatekeeper", "Baseline", "Gatekeeper", "Baseline", 
                   "Gatekeeper", "Baseline", "Gatekeeper", "Baseline"],
        "Domain": ["medical"] * 8
    }
    df = pd.DataFrame(demo_data)
    
    print("Running Stratified Analysis...")
    results = run_domain_stratified_analysis(df)
    print(f"Results: {results}")

if __name__ == "__main__":
    main()