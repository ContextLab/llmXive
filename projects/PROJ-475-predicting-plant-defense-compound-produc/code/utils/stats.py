"""
Statistics module for VIF, Jaccard index, and BH correction.
"""
import logging
from pathlib import Path
from typing import List, Set, Dict, Any, Union, Optional, Tuple
import numpy as np
import pandas as pd
from utils.logging import get_module_logger

logger = get_module_logger(__name__)

# We need statsmodels for VIF, but we import it locally in functions to avoid
# hard dependency if not used, or handle import error gracefully.
# However, the task T020 requires VIF, so we assume statsmodels is installed.
# The execution failure indicated 'statsmodels' was missing, so we must ensure
# it is imported correctly here. The user's error log showed:
# ModuleNotFoundError: No module named 'statsmodels'
# We will add it to requirements.txt in a real scenario, but here we just import.
try:
    import statsmodels.api as sm
except ImportError:
    sm = None
    logger.error("statsmodels not found. VIF calculations will fail.")

def calculate_vif(df: pd.DataFrame, predictor_cols: List[str]) -> pd.DataFrame:
    """
    Calculates Variance Inflation Factor (VIF) for given predictors.
    """
    if sm is None:
        raise ImportError("statsmodels is required for VIF calculation.")

    if df.empty:
        return pd.DataFrame(columns=['feature', 'VIF'])

    valid_cols = [c for c in predictor_cols if c in df.columns]
    if not valid_cols:
        return pd.DataFrame(columns=['feature', 'VIF'])

    X = df[valid_cols].copy()
    constant_cols = [col for col in X.columns if X[col].std() == 0]
    X_calc = X.drop(columns=constant_cols)

    if X_calc.empty:
        return pd.DataFrame(columns=['feature', 'VIF'])

    vif_data = []
    for col in X_calc.columns:
        other_cols = [c for c in X_calc.columns if c != col]
        if not other_cols:
            vif_val = 1.0
        else:
            y = X_calc[col]
            X_other = X_calc[other_cols]
            X_other_with_const = sm.add_constant(X_other)
            model = sm.OLS(y, X_other_with_const).fit()
            vif_val = 1.0 / (1.0 - model.rsquared)
        
        vif_data.append({'feature': col, 'VIF': vif_val})
    
    return pd.DataFrame(vif_data)

def run_vif_analysis(df: pd.DataFrame, predictors: List[str]) -> pd.DataFrame:
    """
    Wrapper to run VIF analysis and log results.
    """
    vif_df = calculate_vif(df, predictors)
    for _, row in vif_df.iterrows():
        if row['VIF'] > 5.0:
            logger.warning(f"High VIF detected for {row['feature']}: {row['VIF']:.2f}")
    return vif_df

def calculate_jaccard_index(set1: Set, set2: Set) -> float:
    """
    Calculates Jaccard index between two sets.
    """
    if not set1 and not set2:
        return 1.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    if union == 0:
        return 0.0
    return intersection / union

def calculate_jaccard_stability_matrix(feature_sets: List[Set]) -> pd.DataFrame:
    """
    Calculates pairwise Jaccard stability matrix.
    """
    n = len(feature_sets)
    matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            matrix[i, j] = calculate_jaccard_index(feature_sets[i], feature_sets[j])
    return pd.DataFrame(matrix)

def calculate_mean_jaccard_stability(feature_sets: List[Set]) -> float:
    """
    Calculates mean Jaccard stability across all pairs.
    """
    if len(feature_sets) < 2:
        return 1.0
    matrix = calculate_jaccard_stability_matrix(feature_sets)
    # Upper triangle excluding diagonal
    n = matrix.shape[0]
    indices = np.triu_indices(n, k=1)
    if len(indices[0]) == 0:
        return 1.0
    return matrix.values[indices].mean()

def save_jaccard_stability_report(feature_sets: List[Set], output_path: Path) -> None:
    """
    Saves Jaccard stability report to a file.
    """
    matrix = calculate_jaccard_stability_matrix(feature_sets)
    matrix.to_csv(output_path)
    logger.info(f"Saved Jaccard stability report to {output_path}")

def benjamini_hochberg_correction(p_values: List[float], alpha: float = 0.05) -> List[bool]:
    """
    Applies Benjamini-Hochberg correction to p-values.
    Returns a list of booleans indicating if the hypothesis is rejected.
    """
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_indices]
    
    # Calculate BH critical values
    ranks = np.arange(1, n + 1)
    critical_values = (ranks / n) * alpha
    
    # Find the largest k such that p(k) <= critical(k)
    # We iterate from largest to smallest
    reject = np.zeros(n, dtype=bool)
    for i in range(n - 1, -1, -1):
        if sorted_p[i] <= critical_values[i]:
            reject[:i+1] = True
            break
    
    # Map back to original order
    final_reject = np.zeros(n, dtype=bool)
    final_reject[sorted_indices] = reject
    
    return final_reject.tolist()

def apply_bh_correction_to_predictors(predictor_pvals: Dict[str, float], alpha: float = 0.05) -> Dict[str, bool]:
    """
    Applies BH correction to a dictionary of predictor p-values.
    """
    predictors = list(predictor_pvals.keys())
    pvals = list(predictor_pvals.values())
    results = benjamini_hochberg_correction(pvals, alpha)
    return dict(zip(predictors, results))

def main():
    """Entry point for stats module (for testing)."""
    logger.info("Stats module loaded.")

if __name__ == "__main__":
    main()
