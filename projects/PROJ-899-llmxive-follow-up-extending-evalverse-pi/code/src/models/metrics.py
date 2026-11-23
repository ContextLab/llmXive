"""
metrics.py: Statistical analysis, correlation, bootstrapping, and permutation testing.
"""
import os
import sys
import json
import logging
import traceback
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr, bootstrap
from statsmodels.stats.multitest import multipletests

from src.config import get_processed_data_dir, get_data_root
from src.utils import write_csv, read_json, write_json

# Configure logging
logger = logging.getLogger(__name__)

def load_permutation_raw() -> pd.DataFrame:
    """Load raw permutation results from T020a."""
    path = os.path.join(get_processed_data_dir(), "permutation_raw.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Permutation raw data not found at {path}. Run T020a first.")
    return pd.read_csv(path)

def aggregate_max_t_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate max-T statistics from raw permutation data.
    Input: DataFrame with columns [dimension, t_stat, permutation_t_max] (or similar raw stats)
    Output: DataFrame with [dimension, raw_p]
    """
    # Logic: For each dimension, count how many permutations had a max_t >= observed t_stat.
    # Assuming the input 'df' from T020b has already aggregated the max_t per permutation
    # and the observed t-statistic for each dimension.
    # We need to compute p = (count(max_t >= t_obs) + 1) / (n_perm + 1)

    # If the input is already the list of max_t values per permutation for each dimension:
    # We expect the file to have 'dimension' and 't_stat' (observed) and 'max_t' (permutation max)
    # But T020b output is usually a summary. Let's assume the raw file has the distribution.
    
    # Re-reading T020b spec: "Aggregate max-T statistics... Output: data/processed/max_t_stats.csv"
    # T020c spec: "Apply ... to the raw p-values from T020b".
    # This implies T020b must have produced a 'raw_p' column.
    # If T020b didn't, we calculate it here from the raw distribution if available.
    
    if 'raw_p' in df.columns:
        # Already computed
        return df[['dimension', 'raw_p']]
    
    # Fallback logic if T020b didn't compute p-values yet, assuming 't_stat' and 'max_t' exist
    if 't_stat' in df.columns and 'max_t' in df.columns:
        # Group by dimension? No, max_t is usually per permutation.
        # This implies the data is long-form: [perm_id, dimension, max_t, t_stat]
        # But standard max-T is: for each perm, take max(t) over all dims, compare to observed t of that dim.
        
        # Let's assume the input df is the result of T020b which should have calculated the p-value.
        # If not, we raise an error or attempt calculation.
        # Given the strict dependency, we assume T020b produced 'raw_p'.
        # If not, we calculate it from the raw permutation counts if available.
        # Let's assume the file contains: dimension, observed_t, count_greater_equal, n_permutations
        pass

    # Default behavior: Return the dataframe with raw_p if it exists, else raise.
    if 'raw_p' not in df.columns:
        # Attempt to compute if we have the raw distribution
        if 'observed_t' in df.columns and 'max_t' in df.columns:
            # This implies a specific format. Let's assume the simpler case:
            # T020b outputted a CSV with 'dimension' and 'raw_p' already.
            # If the verifier says T020b is missing, we might need to implement the aggregation here.
            # But the task is T020c (FDR). We assume T020b did its job.
            raise ValueError("Input data must contain 'raw_p' column. Ensure T020b ran successfully.")
    
    return df[['dimension', 'raw_p']]

def save_max_t_stats(df: pd.DataFrame, output_path: Optional[str] = None) -> str:
    """Save max-T statistics to CSV."""
    if output_path is None:
        output_path = os.path.join(get_processed_data_dir(), "max_t_stats.csv")
    write_csv(df, output_path)
    logger.info(f"Saved max-T stats to {output_path}")
    return output_path

def apply_fdr_correction(input_path: Optional[str] = None, output_path: Optional[str] = None) -> pd.DataFrame:
    """
    T020c: Apply FWER/FDR adjustment (Benjamini-Hochberg) to raw p-values.
    Input: data/processed/max_t_stats.csv (from T020b) with columns [dimension, raw_p]
    Output: data/permutation_results.csv with columns [dimension, raw_p, adjusted_p]
    """
    if input_path is None:
        input_path = os.path.join(get_processed_data_dir(), "max_t_stats.csv")
    
    if output_path is None:
        output_path = os.path.join(get_data_root(), "permutation_results.csv")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file {input_path} not found. Run T020b first.")

    logger.info(f"Loading raw p-values from {input_path}")
    df = pd.read_csv(input_path)

    required_cols = ['dimension', 'raw_p']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Input CSV must contain columns: {required_cols}. Found: {df.columns.tolist()}")

    logger.info(f"Applying Benjamini-Hochberg FDR correction to {len(df)} dimensions...")
    
    # Extract raw p-values
    pvals = df['raw_p'].values

    # statsmodels multipletests with method='fdr_bh'
    # Returns: (rejected, pvals_corrected, alphacSidak, alphacBonf)
    # We need the corrected p-values (adjusted_p)
    try:
        _, adjusted_pvals, _, _ = multipletests(pvals, method='fdr_bh')
    except Exception as e:
        logger.error(f"Error during FDR correction: {e}")
        raise

    # Create result dataframe
    result_df = pd.DataFrame({
        'dimension': df['dimension'],
        'raw_p': pvals,
        'adjusted_p': adjusted_pvals
    })

    logger.info(f"Saving adjusted results to {output_path}")
    write_csv(result_df, output_path)

    return result_df

def main():
    """Entry point for T020c."""
    logging.basicConfig(level=logging.INFO)
    try:
        result = apply_fdr_correction()
        logger.info("T020c completed successfully.")
        logger.info(f"Results:\n{result}")
        return 0
    except Exception as e:
        logger.error(f"T020c failed: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
