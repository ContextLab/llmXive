"""
Statistics utility module.
Includes VIF calculation (if not in preprocessing), Jaccard index, BH correction.
Note: VIF is also implemented in preprocessing.py for pipeline integration.
This module provides a standalone function for VIF if needed elsewhere.
"""
import logging
import sys
from pathlib import Path
from typing import List, Set, Dict, Any, Union, Optional, Tuple
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

try:
    from utils.logging import get_module_logger
except ImportError:
    logging.basicConfig(level=logging.INFO)
    def get_module_logger(name):
        return logging.getLogger(name)

logger = get_module_logger(__name__)

def calculate_vif(df: pd.DataFrame, predictor_cols: List[str]) -> Dict[str, float]:
    """
    Calculate VIF for a list of predictors in a DataFrame.
    
    Args:
        df: DataFrame containing the data.
        predictor_cols: List of column names to calculate VIF for.
        
    Returns:
        Dictionary mapping predictor name to VIF value.
    """
    vif_results = {}
    if len(predictor_cols) < 2:
        return vif_results
    
    for col in predictor_cols:
        X = df[predictor_cols].drop(columns=[col])
        y = df[col]
        
        if X.shape[1] == 0:
            vif_results[col] = 1.0
            continue
        
        try:
            X_with_const = sm.add_constant(X)
            model = sm.OLS(y, X_with_const).fit()
            r_squared = model.rsquared
            vif = 1.0 / (1.0 - r_squared) if r_squared < 1.0 else np.inf
            vif_results[col] = vif
        except Exception as e:
            logger.error(f"Error calculating VIF for {col}: {e}")
            vif_results[col] = np.nan
    
    return vif_results

def run_vif_analysis(df: pd.DataFrame, threshold: float = 5.0) -> pd.DataFrame:
    """
    Run VIF analysis on all numeric predictors in a DataFrame.
    
    Args:
        df: Input DataFrame.
        threshold: VIF threshold for flagging.
        
    Returns:
        DataFrame with predictor and VIF values.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # Exclude ID columns
    exclude_cols = ['population_id', 'env_id', 'compound_id']
    predictor_cols = [c for c in numeric_cols if c not in exclude_cols]
    
    vif_dict = calculate_vif(df, predictor_cols)
    vif_df = pd.DataFrame(list(vif_dict.items()), columns=['predictor', 'vif'])
    vif_df = vif_df.sort_values(by='vif', ascending=False)
    
    high_vif = vif_df[vif_df['vif'] > threshold]
    if not high_vif.empty:
        logger.warning(f"Found {len(high_vif)} predictors with VIF > {threshold}: {high_vif['predictor'].tolist()}")
    
    return vif_df

def calculate_jaccard_index(set1: Set[Any], set2: Set[Any]) -> float:
    """
    Calculate Jaccard index between two sets.
    
    Args:
        set1: First set.
        set2: Second set.
        
    Returns:
        Jaccard index (0.0 to 1.0).
    """
    if not set1 and not set2:
        return 1.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union > 0 else 0.0

def calculate_jaccard_stability_matrix(feature_sets: List[Set[Any]]) -> pd.DataFrame:
    """
    Calculate Jaccard stability matrix for a list of feature sets.
    
    Args:
        feature_sets: List of sets of features.
        
    Returns:
        DataFrame representing the Jaccard similarity matrix.
    """
    n = len(feature_sets)
    if n == 0:
        return pd.DataFrame()
    
    matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            matrix[i, j] = calculate_jaccard_index(feature_sets[i], feature_sets[j])
    
    return pd.DataFrame(matrix, index=range(n), columns=range(n))

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
    total_pairs = n * (n - 1) / 2
    if total_pairs == 0:
        return 1.0
    
    # Sum upper triangle
    upper_sum = matrix.values[np.triu_indices(n, k=1)].sum()
    return upper_sum / total_pairs

def save_jaccard_stability_report(feature_sets: List[Set[Any]], output_path: str):
    """
    Save Jaccard stability matrix and mean to a report file.
    
    Args:
        feature_sets: List of sets of features.
        output_path: Path to save the report.
    """
    matrix = calculate_jaccard_stability_matrix(feature_sets)
    mean_stability = calculate_mean_jaccard_stability(feature_sets)
    
    report_path = Path(output_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w') as f:
        f.write(f"Mean Jaccard Stability: {mean_stability:.4f}\n")
        f.write("\nJaccard Similarity Matrix:\n")
        f.write(matrix.to_string())

def benjamini_hochberg_correction(p_values: List[float], alpha: float = 0.05) -> Tuple[List[bool], List[float]]:
    """
    Apply Benjamini-Hochberg correction to a list of p-values.
    
    Args:
        p_values: List of p-values.
        alpha: Significance level.
        
    Returns:
        Tuple of (rejections, adjusted p-values).
    """
    n = len(p_values)
    if n == 0:
        return [], []
    
    # Sort p-values with original indices
    sorted_indices = np.argsort(p_values)
    sorted_p_values = np.array(p_values)[sorted_indices]
    
    # Calculate adjusted p-values
    adjusted_p_values = np.zeros(n)
    for i in range(n):
        adjusted_p_values[sorted_indices[i]] = sorted_p_values[i] * n / (i + 1)
    
    # Ensure monotonicity (cumulative min from the end)
    for i in range(n - 2, -1, -1):
        adjusted_p_values[sorted_indices[i]] = min(adjusted_p_values[sorted_indices[i]], adjusted_p_values[sorted_indices[i+1]])
    
    # Determine rejections
    rejections = adjusted_p_values <= alpha
    
    return rejections.tolist(), adjusted_p_values.tolist()

def apply_bh_correction_to_predictors(df: pd.DataFrame, p_value_col: str, alpha: float = 0.05) -> pd.DataFrame:
    """
    Apply BH correction to a column of p-values in a DataFrame.
    
    Args:
        df: DataFrame with p-values.
        p_value_col: Name of the p-value column.
        alpha: Significance level.
        
    Returns:
        DataFrame with added 'adjusted_p_value' and 'significant' columns.
    """
    p_values = df[p_value_col].tolist()
    rejections, adjusted_p_values = benjamini_hochberg_correction(p_values, alpha)
    
    df_out = df.copy()
    df_out['adjusted_p_value'] = adjusted_p_values
    df_out['significant'] = rejections
    
    return df_out

def main():
    """
    Main entry point for stats module (for testing).
    """
    # Example usage
    logger.info("Stats module loaded.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
