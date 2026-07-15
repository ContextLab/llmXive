"""
Statistics Utility Module.

Provides statistical functions for VIF, Jaccard index, etc.
"""
import logging
import sys
from pathlib import Path
from typing import List, Set, Dict, Any, Union, Optional, Tuple
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

def calculate_vif(df: pd.DataFrame, feature: str, features: List[str]) -> float:
    """
    Calculate Variance Inflation Factor for a specific feature.

    Args:
        df: DataFrame containing the data.
        feature: The feature column to calculate VIF for.
        features: List of all feature columns including the target feature.

    Returns:
        VIF value.
    """
    # Remove NaNs for regression
    valid_cols = [feature] + [f for f in features if f in df.columns]
    clean_df = df[valid_cols].dropna()
    
    if len(clean_df) < 2 or len(valid_cols) < 2:
        return np.nan

    try:
        # Regress feature against all other features
        X = clean_df[[f for f in features if f != feature and f in clean_df.columns]]
        y = clean_df[feature]
        
        if X.empty:
            return 1.0
        
        # Add intercept
        X_with_intercept = pd.concat([pd.Series(1, index=X.index, name='intercept'), X], axis=1)
        
        # OLS calculation
        # beta = (X'X)^-1 X'y
        # R^2 = 1 - SSE/SST
        # VIF = 1 / (1 - R^2)
        
        # Using numpy for linear algebra
        X_mat = X_with_intercept.values
        y_vec = y.values
        
        # Check for singular matrix
        XtX = X_mat.T @ X_mat
        if np.linalg.cond(XtX) > 1e10:
            logger.warning(f"Singular matrix detected for VIF calculation of {feature}")
            return np.inf
        
        # Solve for coefficients
        try:
            coeffs = np.linalg.solve(XtX, X_mat.T @ y_vec)
            y_pred = X_mat @ coeffs
            residuals = y_vec - y_pred
            
            ss_res = np.sum(residuals**2)
            ss_tot = np.sum((y_vec - np.mean(y_vec))**2)
            
            if ss_tot == 0:
                return 1.0
                
            r_squared = 1 - (ss_res / ss_tot)
            if r_squared >= 1.0:
                return np.inf
            
            vif = 1 / (1 - r_squared)
            return float(vif)
        except np.linalg.LinAlgError:
            return np.inf
    except Exception as e:
        logger.error(f"Error calculating VIF for {feature}: {e}")
        return np.nan

def run_vif_analysis(df: pd.DataFrame, features: List[str]) -> pd.DataFrame:
    """
    Run VIF analysis on a list of features.

    Args:
        df: DataFrame.
        features: List of feature names.

    Returns:
        DataFrame with VIF values.
    """
    vif_results = []
    for feat in features:
        vif = calculate_vif(df, feat, features)
        vif_results.append({'feature': feat, 'vif': vif})
    return pd.DataFrame(vif_results)

def benjamini_hochberg_correction(p_values: List[float], alpha: float = 0.05) -> List[bool]:
    """
    Apply Benjamini-Hochberg correction to a list of p-values.

    Args:
        p_values: List of p-values.
        alpha: Significance level.

    Returns:
        List of booleans indicating significance after correction.
    """
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values and keep original indices
    sorted_indices = np.argsort(p_values)
    sorted_p_values = np.array(p_values)[sorted_indices]
    
    # Calculate adjusted p-values (BH procedure)
    # p_adj[i] = p[i] * n / (i + 1)
    # But we need to ensure monotonicity
    
    adjusted_p_values = np.zeros(n)
    for i in range(n):
        adjusted_p_values[i] = sorted_p_values[i] * n / (i + 1)
    
    # Ensure monotonicity (cumulative min from the end)
    for i in range(n - 2, -1, -1):
        adjusted_p_values[i] = min(adjusted_p_values[i], adjusted_p_values[i+1])
    
    # Determine significance
    significant = adjusted_p_values <= alpha
    
    # Map back to original order
    result = [False] * n
    for idx, is_sig in zip(sorted_indices, significant):
        result[idx] = is_sig
        
    return result

def calculate_jaccard_index(set_a: Set[Any], set_b: Set[Any]) -> float:
    """
    Calculate Jaccard index between two sets.

    Args:
        set_a: First set.
        set_b: Second set.

    Returns:
        Jaccard index (0 to 1).
    """
    if not set_a and not set_b:
        return 1.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    if union == 0:
        return 0.0
    return intersection / union

def calculate_jaccard_stability_matrix(feature_sets: List[Set[Any]]) -> pd.DataFrame:
    """
    Calculate Jaccard stability matrix for a list of feature sets.

    Args:
        feature_sets: List of sets of features.

    Returns:
        DataFrame representing the stability matrix.
    """
    n = len(feature_sets)
    if n == 0:
        return pd.DataFrame()
    
    matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            matrix[i, j] = calculate_jaccard_index(feature_sets[i], feature_sets[j])
    
    return pd.DataFrame(matrix)

def calculate_mean_jaccard_stability(feature_sets: List[Set[Any]]) -> float:
    """
    Calculate mean Jaccard stability across all pairs.

    Args:
        feature_sets: List of sets of features.

    Returns:
        Mean Jaccard index.
    """
    if len(feature_sets) < 2:
        return 1.0
    
    matrix = calculate_jaccard_stability_matrix(feature_sets)
    # Exclude diagonal
    n = matrix.shape[0]
    off_diag_sum = matrix.sum().sum() - np.trace(matrix)
    count = n * n - n
    if count == 0:
        return 1.0
    return off_diag_sum / count

def save_jaccard_stability_report(matrix: pd.DataFrame, path: Path) -> None:
    """
    Save Jaccard stability matrix to a CSV file.

    Args:
        matrix: The stability matrix DataFrame.
        path: Output path.
    """
    matrix.to_csv(path, index=False)
    logger.info(f"Jaccard stability report saved to {path}")

def main() -> int:
    """
    Entry point for stats module (for testing).
    """
    logger.info("Stats module loaded.")
    return 0

if __name__ == "__main__":
    sys.exit(main())