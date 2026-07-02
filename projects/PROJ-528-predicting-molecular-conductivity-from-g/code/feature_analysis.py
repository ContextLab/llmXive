import numpy as np
import pandas as pd
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

def calculate_correlation_pvalues(
    df: pd.DataFrame, 
    target_col: str, 
    feature_cols: List[str]
) -> pd.DataFrame:
    """
    Calculate Pearson correlation coefficients and p-values between features and target.
    
    Args:
        df: DataFrame containing features and target
        target_col: Name of the target column
        feature_cols: List of feature column names
        
    Returns:
        DataFrame with columns: feature, correlation, p_value
    """
    results = []
    target = df[target_col].dropna()
    
    for col in feature_cols:
        if col not in df.columns:
            logger.warning(f"Feature {col} not found in DataFrame, skipping.")
            continue
        
        feature = df[col].dropna()
        min_len = min(len(target), len(feature))
        
        if min_len < 3:
            logger.warning(f"Insufficient data for {col}, skipping.")
            continue
        
        # Align indices
        common_idx = target.index.intersection(feature.index)
        if len(common_idx) < 3:
            logger.warning(f"Insufficient common data for {col}, skipping.")
            continue
        
        x = feature.loc[common_idx]
        y = target.loc[common_idx]
        
        # Calculate correlation and p-value
        corr, p_val = x.corr(y), 0.0
        try:
            # Use scipy.stats if available, otherwise approximate
            from scipy import stats
            corr, p_val = stats.pearsonr(x, y)
        except ImportError:
            logger.warning("scipy not available, using numpy approximation for p-value")
            # Fallback: simple t-statistic approximation for p-value
            if abs(corr) < 1.0:
                t_stat = corr * np.sqrt((len(x) - 2) / (1 - corr**2))
                # Approximate p-value using t-distribution CDF (simple approximation)
                # This is a rough approximation; scipy is preferred
                p_val = 2 * (1 - 0.5 * (1 + np.sign(t_stat) * (1 - np.exp(-0.5 * t_stat**2 / (len(x) - 1)))))
            else:
                p_val = 0.0
        
        results.append({
            'feature': col,
            'correlation': corr,
            'p_value': p_val
        })
    
    return pd.DataFrame(results)

def benjamini_hochberg(
    p_values: List[float], 
    alpha: float = 0.05
) -> Tuple[List[float], List[bool]]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values
        alpha: Significance level (default 0.05)
        
    Returns:
        Tuple of (adjusted_p_values, boolean_significance_list)
    """
    if not p_values:
        return [], []
    
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_pvals = np.array(p_values)[sorted_indices]
    
    # Calculate adjusted p-values
    adjusted_pvals = np.zeros(n)
    for i in range(n):
        rank = i + 1
        # BH formula: p_adj = p * n / rank
        adj = sorted_pvals[i] * n / rank
        # Ensure monotonicity: adjusted p-values should be non-decreasing
        if i > 0:
            adj = max(adj, adjusted_pvals[i-1])
        adjusted_pvals[i] = min(adj, 1.0)  # Cap at 1.0
    
    # Reorder to original sequence
    final_adjusted = np.zeros(n)
    final_significance = np.zeros(n, dtype=bool)
    for i, idx in enumerate(sorted_indices):
        final_adjusted[idx] = adjusted_pvals[i]
        final_significance[idx] = final_adjusted[idx] <= alpha
    
    return final_adjusted.tolist(), final_significance.tolist()

def apply_bh_correction_to_df(
    df: pd.DataFrame, 
    p_col: str = 'p_value', 
    alpha: float = 0.05
) -> pd.DataFrame:
    """
    Apply Benjamini-Hochberg correction to a DataFrame of p-values.
    
    Args:
        df: DataFrame containing p-values (must have a column named p_col)
        p_col: Name of the p-value column
        alpha: Significance level
        
    Returns:
        DataFrame with added columns: 'adj_p_value' and 'is_significant'
    """
    if p_col not in df.columns:
        raise ValueError(f"Column {p_col} not found in DataFrame")
    
    p_vals = df[p_col].tolist()
    adj_p_vals, is_sig = benjamini_hochberg(p_vals, alpha)
    
    result = df.copy()
    result['adj_p_value'] = adj_p_vals
    result['is_significant'] = is_sig
    
    return result

def main():
    """
    Main function to demonstrate BH correction on correlation data.
    Expects data/processed/correlation_results.csv to exist.
    """
    import os
    import json
    from logging_config import setup_logging

    setup_logging()
    
    input_path = 'data/processed/correlation_results.csv'
    output_path = 'data/processed/correlation_results_fdr.csv'
    
    if not os.path.exists(input_path):
        logger.error(f"Input file {input_path} not found. Run T041 first.")
        return
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} correlations from {input_path}")
    
    if 'p_value' not in df.columns:
        logger.error("Column 'p_value' not found in input DataFrame")
        return
    
    corrected_df = apply_bh_correction_to_df(df, p_col='p_value', alpha=0.05)
    
    # Save results
    corrected_df.to_csv(output_path, index=False)
    logger.info(f"Saved FDR-corrected results to {output_path}")
    
    # Log summary
    significant_count = corrected_df['is_significant'].sum()
    logger.info(f"Significant features after FDR correction (α=0.05): {significant_count}/{len(df)}")
    
    # Print top features
    top_features = corrected_df.sort_values('adj_p_value').head(10)
    logger.info("Top 10 features by adjusted p-value:\n" + top_features.to_string())

if __name__ == "__main__":
    main()
