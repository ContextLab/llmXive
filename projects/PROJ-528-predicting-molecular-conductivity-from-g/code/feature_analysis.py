import numpy as np
import pandas as pd
from typing import List, Tuple, Optional
import logging
from scipy import stats
from statsmodels.stats.multitest import multipletests

logger = logging.getLogger(__name__)

def calculate_correlation_pvalues(df: pd.DataFrame, target_col: str) -> Dict[str, Tuple[float, float]]:
    """
    Calculate Pearson correlation coefficient and p-value for each feature against target.
    
    Args:
        df: DataFrame with features and target.
        target_col: Name of the target column.
        
    Returns:
        Dictionary mapping feature names to (correlation, p_value).
    """
    results = {}
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if target_col in numeric_cols:
        numeric_cols.remove(target_col)
        
    for col in numeric_cols:
        x = df[col].dropna()
        y = df[target_col].loc[x.index].dropna()
        
        if len(x) < 2:
            continue
            
        try:
            corr, p_val = stats.pearsonr(x, y)
            results[col] = (float(corr), float(p_val))
        except Exception as e:
            logger.warning(f"Failed to calculate correlation for {col}: {e}")
            
    return results

def benjamini_hochberg(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg procedure to adjust p-values.
    
    Args:
        p_values: List of raw p-values.
        
    Returns:
        List of adjusted p-values.
    """
    if not p_values:
        return []
    _, adjusted, _, _ = multipletests(p_values, method='fdr_bh')
    return list(adjusted)

def apply_bh_correction_to_df(corr_results: Dict[str, Tuple[float, float]]) -> Dict[str, float]:
    """
    Apply BH correction to p-values in correlation results.
    
    Args:
        corr_results: Dictionary of (corr, p_val).
        
    Returns:
        Dictionary mapping feature to adjusted p-value.
    """
    p_values = [v[1] for v in corr_results.values()]
    adjusted = benjamini_hochberg(p_values)
    
    # Map back to features (order preserved)
    features = list(corr_results.keys())
    return {features[i]: adjusted[i] for i in range(len(features))}

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Feature analysis and correlation.")
    parser.add_argument("--data", type=str, required=True)
    parser.add_argument("--target", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    args = parser.parse_args()
    
    df = pd.read_csv(args.data)
    corr_results = calculate_correlation_pvalues(df, args.target)
    adjusted = apply_bh_correction_to_df(corr_results)
    
    import json
    with open(args.output, 'w') as f:
        json.dump(adjusted, f, indent=2)
    logger.info(f"Saved adjusted p-values to {args.output}")

if __name__ == "__main__":
    main()
