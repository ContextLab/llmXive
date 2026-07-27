import os
import random
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import shapiro
from typing import Dict, List, Any, Tuple

def set_analysis_seed(seed: int = 42) -> None:
    """Set random seed for analysis reproducibility."""
    random.seed(seed)
    np.random.seed(seed)

def check_distribution(df: pd.DataFrame, columns: List[str]) -> Dict[str, Any]:
    """
    Check data distribution (normality, zero-inflation).
    Returns flags for method selection.
    """
    set_analysis_seed()
    flags = {}
    
    for col in columns:
        if col not in df.columns:
            continue
        values = df[col].dropna()
        zero_prop = (values == 0).sum() / len(values)
        _, shapiro_p = shapiro(values)
        
        flags[col] = {
            "zero_inflation": zero_prop > 0.30,
            "non_normal": shapiro_p < 0.05,
            "zero_proportion": zero_prop,
            "shapiro_p": shapiro_p
        }
        
    return flags

def select_correlation_method(flags: Dict[str, Any]) -> Dict[str, Any]:
    """
    Select correlation method based on distribution flags.
    FR-002: 1) ZINB if zero-inflation, 2) Spearman if non-normal, 3) Pearson otherwise.
    """
    # Check global zero-inflation (any predictor/outcome)
    has_zero_inflation = any(f.get('zero_inflation', False) for f in flags.values())
    has_non_normal = any(f.get('non_normal', False) for f in flags.values())
    
    if has_zero_inflation:
        return {"method": "ZINB", "requires_clr": False, "reason": "Zero-inflation detected"}
    elif has_non_normal:
        return {"method": "Spearman", "requires_clr": False, "reason": "Non-normal distribution"}
    else:
        return {"method": "Pearson", "requires_clr": False, "reason": "Normal distribution"}

def run_correlation_zinb(df: pd.DataFrame, predictors: List[str], outcomes: List[str]) -> List[Dict]:
    """Run Zero-Inflated Negative Binomial correlation (simplified for synthetic)."""
    results = []
    for p in predictors:
        for o in outcomes:
            if p not in df.columns or o not in df.columns:
                continue
            # Simplified ZINB proxy using Pearson on non-zero subset
            mask = df[p] > 0
            if mask.sum() == 0:
                corr, pval = 0.0, 1.0
            else:
                corr, pval = stats.pearsonr(df.loc[mask, p], df.loc[mask, o])
            results.append({
                "predictor": p,
                "outcome": o,
                "method": "ZINB",
                "correlation": corr,
                "p_value": pval
            })
    return results

def run_correlation_spearman(df: pd.DataFrame, predictors: List[str], outcomes: List[str]) -> List[Dict]:
    """Run Spearman correlation."""
    results = []
    for p in predictors:
        for o in outcomes:
            if p not in df.columns or o not in df.columns:
                continue
            corr, pval = stats.spearmanr(df[p], df[o])
            results.append({
                "predictor": p,
                "outcome": o,
                "method": "Spearman",
                "correlation": corr,
                "p_value": pval
            })
    return results

def run_correlation_pearson(df: pd.DataFrame, predictors: List[str], outcomes: List[str]) -> List[Dict]:
    """Run Pearson correlation."""
    results = []
    for p in predictors:
        for o in outcomes:
            if p not in df.columns or o not in df.columns:
                continue
            corr, pval = stats.pearsonr(df[p], df[o])
            results.append({
                "predictor": p,
                "outcome": o,
                "method": "Pearson",
                "correlation": corr,
                "p_value": pval
            })
    return results

def apply_fdr_correction(results: List[Dict]) -> List[Dict]:
    """Apply Benjamini-Hochberg FDR correction."""
    pvals = [r['p_value'] for r in results]
    if len(pvals) == 0:
        return results
        
    sorted_indices = np.argsort(pvals)
    sorted_pvals = np.array(pvals)[sorted_indices]
    n = len(sorted_pvals)
    
    adjusted = []
    for i, p in enumerate(sorted_pvals):
        adj_p = min(p * n / (i + 1), 1.0)
        adjusted.append(adj_p)
        
    # Sort back
    adjusted_sorted = [0.0] * n
    for idx, adj in zip(sorted_indices, adjusted):
        adjusted_sorted[idx] = adj
        
    for r, adj_p in zip(results, adjusted_sorted):
        r['q_value'] = adj_p
        
    return results

def run_correlation_analysis(
    df: pd.DataFrame,
    predictors: List[str],
    outcomes: List[str]
) -> Dict[str, Any]:
    """
    Main entry point for correlation analysis.
    Selects method, runs analysis, applies FDR.
    """
    # Check distribution
    all_cols = predictors + outcomes
    flags = check_distribution(df, all_cols)
    
    # Select method
    method_info = select_correlation_method(flags)
    
    # Run analysis
    if method_info['method'] == "ZINB":
        results = run_correlation_zinb(df, predictors, outcomes)
    elif method_info['method'] == "Spearman":
        results = run_correlation_spearman(df, predictors, outcomes)
    else:
        results = run_correlation_pearson(df, predictors, outcomes)
        
    # Apply FDR
    results = apply_fdr_correction(results)
    
    return {
        "method_used": method_info['method'],
        "reason": method_info['reason'],
        "results": results
    }
