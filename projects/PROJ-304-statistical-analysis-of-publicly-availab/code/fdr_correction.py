"""
Benjamini-Hochberg FDR Correction Module.

Implements the Benjamini-Hochberg procedure to control the False Discovery Rate (FDR)
on p-values derived from robust standard errors.
"""
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from logger import get_logger, get_project_root

logger = get_logger(__name__)

def apply_benjamini_hochberg(
    p_values: np.ndarray,
    alpha: float = 0.05,
    method: str = 'indep'
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Apply the Benjamini-Hochberg FDR correction to an array of p-values.

    Parameters
    ----------
    p_values : np.ndarray
        Array of p-values to correct.
    alpha : float
        Significance level (default 0.05).
    method : str
        'indep' for independent tests, 'poscorr' for positive dependency.

    Returns
    -------
    Tuple[np.ndarray, np.ndarray, np.ndarray]
        - Rejected (boolean array): True if the null hypothesis is rejected.
        - Adjusted p-values (np.ndarray): The FDR-corrected p-values.
        - Critical values (np.ndarray): The threshold values used for comparison.
    """
    if len(p_values) == 0:
        return np.array([]), np.array([]), np.array([])

    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p_values = p_values[sorted_indices]
    m = len(sorted_p_values)

    # Calculate the critical values
    # For 'indep' or 'poscorr': (i / m) * alpha
    # i ranges from 1 to m
    ranks = np.arange(1, m + 1)
    critical_values = (ranks / m) * alpha

    # Find the largest k such that p_(k) <= (k/m) * alpha
    # We iterate from the largest p-value downwards
    rejected_sorted = np.zeros(m, dtype=bool)
    found_rejection = False

    for i in range(m - 1, -1, -1):
        if sorted_p_values[i] <= critical_values[i]:
            found_rejection = True
            break

    if found_rejection:
        # All p-values with rank <= i are rejected
        rejected_sorted[:i+1] = True

    # Map back to original order
    rejected = np.zeros(m, dtype=bool)
    rejected[sorted_indices] = rejected_sorted

    # Calculate adjusted p-values
    # adjusted_p[i] = min( (m/k) * p[k] for k >= i )
    # To ensure monotonicity, we take the cumulative minimum from the right
    adjusted_p = np.zeros(m)
    
    # Calculate raw adjusted values: (m / rank) * p
    # rank is 1-based
    raw_adjusted = (m / ranks) * sorted_p_values
    
    # Ensure monotonicity: adjusted_p[i] <= adjusted_p[i+1]
    # We iterate backwards and take the minimum
    for i in range(m - 2, -1, -1):
        if raw_adjusted[i] > raw_adjusted[i+1]:
            raw_adjusted[i] = raw_adjusted[i+1]
    
    # Cap at 1.0
    raw_adjusted = np.minimum(raw_adjusted, 1.0)

    adjusted_p[sorted_indices] = raw_adjusted

    return rejected, adjusted_p, critical_values

def apply_fdr_to_model_results(
    results_df: pd.DataFrame,
    p_value_columns: List[str],
    alpha: float = 0.05
) -> pd.DataFrame:
    """
    Apply FDR correction to specific p-value columns in a DataFrame of model results.

    Parameters
    ----------
    results_df : pd.DataFrame
        DataFrame containing model results, including p-value columns.
    p_value_columns : List[str]
        List of column names containing p-values to correct.
    alpha : float
        Significance level.

    Returns
    -------
    pd.DataFrame
        DataFrame with new columns added:
        - <col>_adj: Adjusted p-values
        - <col>_reject: Boolean indicating rejection of null hypothesis
    """
    df = results_df.copy()
    
    for col in p_value_columns:
        if col not in df.columns:
            logger.warning(f"P-value column '{col}' not found in DataFrame. Skipping.")
            continue

        p_vals = df[col].to_numpy()
        
        # Handle NaNs if present
        has_nan = np.isnan(p_vals).any()
        if has_nan:
            logger.info(f"Handling NaNs in p-value column '{col}'.")
            # Preserve NaNs in the output
            clean_mask = ~np.isnan(p_vals)
            clean_p_vals = p_vals[clean_mask]
            
            rejected, adj_p, _ = apply_benjamini_hochberg(clean_p_vals, alpha)
            
            full_rejected = np.full(len(p_vals), False)
            full_adj_p = np.full(len(p_vals), np.nan)
            
            full_rejected[clean_mask] = rejected
            full_adj_p[clean_mask] = adj_p
        else:
            rejected, adj_p, _ = apply_benjamini_hochberg(p_vals, alpha)
            full_rejected = rejected
            full_adj_p = adj_p

        adj_col_name = f"{col}_adj"
        rej_col_name = f"{col}_reject"
        
        df[adj_col_name] = full_adj_p
        df[rej_col_name] = full_rejected
        
        logger.info(f"Applied FDR correction to '{col}'. "
                    f"Rejections: {full_rejected.sum()} / {len(df)}")

    return df

def main():
    """
    Main entry point for FDR correction task.
    Reads model results from data/processed/model_results.json (or similar),
    applies FDR correction to p-values derived from robust SEs,
    and saves the updated results.
    """
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "model_results.json"
    output_path = project_root / "data" / "processed" / "model_results_fdr.json"

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Ensure T022 (robust SEs) and T026 (save model outputs) have completed.")
        return

    logger.info(f"Loading model results from {input_path}")
    try:
        with open(input_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load model results: {e}")
        return

    # Convert to DataFrame if it's a list of dicts or similar structure
    # Assuming the JSON structure is a list of results or a dict with a 'results' key
    df = pd.DataFrame(data.get('results', data))

    # Identify primary covariates. 
    # Based on T022 description, we look for columns ending in '_pvalue' or similar.
    # We will assume a standard naming convention from T022 output: 
    # e.g., 'traffic_volume_pvalue', 'land_use_pvalue', 'population_pvalue'
    # If the structure is different, this logic adapts.
    
    # Heuristic: Find columns that look like p-values
    p_value_cols = [col for col in df.columns if 'pvalue' in col.lower() or 'p_value' in col.lower()]
    
    if not p_value_cols:
        logger.warning("No p-value columns found in the data. Attempting to infer from schema...")
        # Fallback: If specific columns aren't found, we might need to inspect the data structure
        # For now, we assume the task implies we know the columns or they are standard.
        # If the data format is strictly from T022, it should have specific keys.
        # Let's assume the keys are 'pvalues' (dict) inside each row, or flat columns.
        # If flat columns exist but don't match, we log and exit.
        if 'pvalues' in df.columns:
            # Handle nested dict case if necessary, but usually we flatten first
            logger.error("Nested p-values found. Flattening logic not implemented for this specific case.")
            return
        else:
            logger.error("Could not identify p-value columns to correct. "
                         "Expected columns containing 'pvalue' or 'p_value'.")
            return

    logger.info(f"Applying FDR correction to columns: {p_value_cols}")
    
    corrected_df = apply_fdr_to_model_results(df, p_value_cols, alpha=0.05)

    # Prepare output data
    output_data = corrected_df.to_dict(orient='records')
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving FDR-corrected results to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    logger.info("FDR correction completed successfully.")

if __name__ == "__main__":
    import json
    main()
