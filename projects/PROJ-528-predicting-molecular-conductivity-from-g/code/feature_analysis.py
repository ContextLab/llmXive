"""
Feature analysis module including Benjamini-Hochberg correction.
"""
import numpy as np
import pandas as pd
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

def calculate_correlation_pvalues(df: pd.DataFrame, target_col: str, feature_cols: Optional[List[str]] = None) -> Dict[str, Tuple[float, float]]:
    """
    Calculate Pearson correlation coefficient and p-value for each feature vs target.
    """
    from scipy.stats import pearsonr
    
    if feature_cols is None:
        feature_cols = [col for col in df.columns if col not in ['smiles', 'status', target_col]]
    
    results = {}
    for feature in feature_cols:
        if feature not in df.columns:
            continue
        
        x = df[feature].dropna()
        y = df[target_col].loc[x.index].dropna()
        
        if len(x) < 3:
            results[feature] = (0.0, 1.0)
            continue
        
        corr, p_val = pearsonr(x, y)
        results[feature] = (corr, p_val)
    
    return results

def benjamini_hochberg(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.
    """
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values and keep original indices
    sorted_indices = np.argsort(p_values)
    sorted_p_values = np.array(p_values)[sorted_indices]
    
    # Calculate adjusted p-values
    adjusted = np.zeros(n)
    for i in range(n):
        adjusted[sorted_indices[i]] = sorted_p_values[i] * n / (i + 1)
    
    # Ensure monotonicity (cumulative min from the end)
    for i in range(n - 2, -1, -1):
        adjusted[sorted_indices[i]] = min(adjusted[sorted_indices[i]], adjusted[sorted_indices[i+1]])
    
    # Clip to [0, 1]
    adjusted = np.clip(adjusted, 0, 1)
    
    return adjusted.tolist()

def apply_bh_correction_to_df(df: pd.DataFrame, p_value_col: str = 'p_value', result_col: str = 'adj_p_value') -> pd.DataFrame:
    """
    Apply Benjamini-Hochberg correction to a DataFrame column of p-values.
    """
    p_values = df[p_value_col].tolist()
    adj_p_values = benjamini_hochberg(p_values)
    df[result_col] = adj_p_values
    return df

def main():
    """
    Main entry point for feature analysis.
    """
    import argparse
    from config import DATA_PATH, TARGET_VAR
    import json

    parser = argparse.ArgumentParser(description="Feature Analysis")
    parser.add_argument('--data', type=str, default=DATA_PATH, help='Path to processed data CSV')
    parser.add_argument('--output', type=str, default='data/processed/correlation_results.json', help='Output path for correlation results')
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    df = pd.read_csv(args.data)
    if df.empty:
        logger.error("Loaded dataframe is empty")
        sys.exit(1)
    
    target_col = TARGET_VAR if TARGET_VAR in df.columns else 'HOMO_LUMO_gap'
    results = calculate_correlation_pvalues(df, target_col)
    
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump({k: list(v) for k, v in results.items()}, f, indent=2)
    
    logger.info(f"Saved correlation results to {args.output}")

if __name__ == "__main__":
    main()