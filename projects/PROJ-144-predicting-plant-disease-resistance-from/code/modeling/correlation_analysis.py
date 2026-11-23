"""
T021a: Compute Correlations & FDR.

Loads batch-corrected metabolite matrix and labels.
Computes pairwise Pearson correlations between each metabolite and the resistance label.
Applies Benjamini-Hochberg FDR correction to p-values.
Filters results for |r| > 0.4 and adjusted p < 0.01.
Outputs results to results/correlation_analysis_raw.json.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats

# Add project root to path to resolve imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from utils.constants import RESULTS_DIR, DATA_PROCESSED_DIR
from utils.io import ensure_dirs, log_pipeline_status

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_processed_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Loads the batch-corrected matrix and labels.
    Raises FileNotFoundError if inputs are missing.
    """
    matrix_path = DATA_PROCESSED_DIR / "batch_corrected_matrix.csv"
    labels_path = DATA_PROCESSED_DIR / "labels.csv"

    if not matrix_path.exists():
        raise FileNotFoundError(f"Input file missing: {matrix_path}. Run T017a/b first.")
    if not labels_path.exists():
        raise FileNotFoundError(f"Input file missing: {labels_path}. Run T017a/b first.")

    logger.info(f"Loading matrix from {matrix_path}")
    df_matrix = pd.read_csv(matrix_path, index_col=0)

    logger.info(f"Loading labels from {labels_path}")
    df_labels = pd.read_csv(labels_path, index_col=0)

    # Ensure alignment
    common_samples = df_matrix.index.intersection(df_labels.index)
    if len(common_samples) == 0:
        raise ValueError("No common samples between matrix and labels.")
    
    df_matrix = df_matrix.loc[common_samples]
    df_labels = df_labels.loc[common_samples]

    # Identify the binary label column (usually 'binary_label' or 'resistance')
    label_col = None
    potential_cols = ['binary_label', 'resistance', 'phenotype', 'resistance_score']
    for col in potential_cols:
        if col in df_labels.columns:
            label_col = col
            break
    
    if label_col is None:
        raise ValueError(f"Could not find resistance label column. Available: {df_labels.columns.tolist()}")

    # Extract series
    y = df_labels[label_col].astype(float)
    X = df_matrix.astype(float)

    return X, y

def compute_correlations(X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
    """
    Computes Pearson correlation and p-value for each metabolite against the label.
    Returns a DataFrame with columns: 'metabolite', 'r', 'p_value'.
    """
    logger.info("Computing pairwise correlations...")
    
    results = []
    for metabolite in X.columns:
        x = X[metabolite]
        
        # Handle constant features or missing data
        if x.std() == 0 or x.isna().all():
            r, p = 0.0, 1.0
        else:
            r, p = stats.pearsonr(x, y)
        
        results.append({
            "metabolite": metabolite,
            "r": float(r),
            "p_value": float(p)
        })

    df_results = pd.DataFrame(results)
    return df_results

def apply_fdr_correction(df: pd.DataFrame, alpha: float = 0.01) -> pd.DataFrame:
    """
    Applies Benjamini-Hochberg FDR correction to p-values.
    Filters for |r| > 0.4 and adjusted p < alpha.
    """
    logger.info(f"Applying Benjamini-Hochberg FDR correction (alpha={alpha})...")
    
    # Sort by p-value for BH procedure
    df_sorted = df.sort_values('p_value').reset_index(drop=True)
    n = len(df_sorted)
    
    # Calculate adjusted p-values (FDR)
    # p_adj = p * n / rank
    df_sorted['rank'] = np.arange(1, n + 1)
    df_sorted['p_adj'] = df_sorted['p_value'] * n / df_sorted['rank']
    
    # Ensure monotonicity (optional but good practice for BH)
    # Iterate backwards to ensure p_adj[i] <= p_adj[i+1]
    min_p = 1.0
    for i in reversed(range(n)):
        if df_sorted.loc[i, 'p_adj'] < min_p:
            min_p = df_sorted.loc[i, 'p_adj']
        else:
            df_sorted.loc[i, 'p_adj'] = min_p
    
    # Restore original order
    df_sorted = df_sorted.sort_index().drop(columns=['rank'])
    df_sorted.rename(columns={'p_adj': 'p_adj'}, inplace=True)

    # Filter based on criteria: |r| > 0.4 and p_adj < 0.01
    mask = (df_sorted['r'].abs() > 0.4) & (df_sorted['p_adj'] < alpha)
    df_filtered = df_sorted[mask].copy()
    
    logger.info(f"Found {len(df_filtered)} significant metabolites after FDR correction.")
    
    return df_filtered

def main():
    """
    Main entry point for T021a.
    """
    try:
        # Load data
        X, y = load_processed_data()
        
        # Compute correlations
        df_corr = compute_correlations(X, y)
        
        # Apply FDR and filter
        df_sig = apply_fdr_correction(df_corr, alpha=0.01)
        
        # Prepare output
        output_data = {
            "parameters": {
                "threshold_r": 0.4,
                "threshold_p_adj": 0.01,
                "method": "pearson",
                "fdr_method": "benjamini_hochberg"
            },
            "summary": {
                "total_metabolites": len(df_corr),
                "significant_metabolites": len(df_sig)
            },
            "results": df_sig.to_dict(orient='records')
        }
        
        # Ensure output directory exists
        ensure_dirs(RESULTS_DIR)
        
        output_path = RESULTS_DIR / "correlation_analysis_raw.json"
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Successfully wrote results to {output_path}")
        log_pipeline_status("T021a", "completed", str(output_path))
        
    except FileNotFoundError as e:
        logger.error(str(e))
        log_pipeline_status("T021a", "failed", str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        log_pipeline_status("T021a", "failed", str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()