import os
import sys
import logging
import json
import warnings
from pathlib import Path
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from statsmodels.stats.multitest import multipletests

# Import shared utilities from utils
from utils import (
    get_project_root_path,
    get_data_processed_path,
    get_data_qc_path,
    ensure_directory,
    setup_logger,
    get_logger
)
from config import get_project_root

# Configure logging
logger = setup_logger("correlation_analysis")

def load_merged_data() -> pd.DataFrame:
    """
    Load the merged dataset from the processed directory.
    Checks for existence and handles the Data Gap scenario.
    """
    root = get_project_root_path()
    data_dir = get_data_processed_path(root)
    merged_path = data_dir / "merged_dataset.parquet"

    if not merged_path.exists():
        logger.warning("Merged dataset not found at %s. Data Gap detected.", merged_path)
        return None
    
    try:
        df = pd.read_parquet(merged_path)
        logger.info("Loaded merged dataset with %d samples and %d features.", len(df), df.shape[1])
        return df
    except Exception as e:
        logger.error("Failed to load merged dataset: %s", str(e))
        return None

def compute_spearman_correlations(df: pd.DataFrame, chunk_size: int = 1000) -> pd.DataFrame:
    """
    Compute Spearman correlations between microbiome taxa and cognitive scores.
    Implements memory chunking to handle large datasets (N=10,000+) efficiently.
    
    Args:
        df: The merged dataset containing taxa and cognitive scores.
        chunk_size: Number of cognitive variables to process in parallel per chunk.
    
    Returns:
        DataFrame with columns: ['taxa', 'cognitive_var', 'correlation', 'pvalue']
    """
    if df is None or df.empty:
        logger.warning("Cannot compute correlations on empty or None DataFrame.")
        return pd.DataFrame(columns=['taxa', 'cognitive_var', 'correlation', 'pvalue'])

    # Identify columns
    # Assumption: Cognitive scores are numeric columns not in the taxa list, 
    # or we explicitly define them. For this implementation, we assume 
    # columns starting with 'cog_' or specific names are cognitive, 
    # and others are taxa. 
    # A more robust approach: check schema or config. 
    # Here we infer: if 'cognitive_score_z' exists, use it. Otherwise, assume all numeric 
    # columns except taxa columns are targets.
    
    # Heuristic: Columns containing 'cog' or 'score' are targets.
    # For robustness, let's assume the merged data has a specific structure defined in spec.
    # If not, we take the last numeric column as the target if only one exists, 
    # or iterate all non-taxon numeric columns.
    
    # Let's assume the cognitive score column is named 'cognitive_score_z' based on T013.
    # If not present, we fall back to the first numeric column that isn't an ID.
    cognitive_cols = [c for c in df.columns if 'cog' in c.lower() or 'score' in c.lower()]
    if not cognitive_cols:
        # Fallback: all numeric columns that are not obvious IDs
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        cognitive_cols = [c for c in numeric_cols if not c.endswith('_id') and c != 'sample_id']
    
    if not cognitive_cols:
        logger.error("No cognitive score columns found in dataset.")
        return pd.DataFrame(columns=['taxa', 'cognitive_var', 'correlation', 'pvalue'])
    
    # Assume all other numeric columns are taxa
    taxa_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c not in cognitive_cols]
    
    if not taxa_cols:
        logger.warning("No taxa columns found in dataset.")
        return pd.DataFrame(columns=['taxa', 'cognitive_var', 'correlation', 'pvalue'])

    logger.info("Computing correlations for %d taxa vs %d cognitive variables.", len(taxa_cols), len(cognitive_cols))

    results = []
    n_taxa = len(taxa_cols)
    
    # Process cognitive variables in chunks to manage memory if needed,
    # though the main constraint is usually the pairwise calculation.
    # We will iterate through cognitive variables and compute correlations with all taxa.
    
    total_pairs = len(taxa_cols) * len(cognitive_cols)
    logger.info("Total correlation pairs to compute: %d", total_pairs)

    for i, cog_col in enumerate(cognitive_cols):
        if i % 10 == 0:
            logger.debug("Processing cognitive variable %d/%d: %s", i+1, len(cognitive_cols), cog_col)
        
        cog_data = df[cog_col].dropna()
        taxa_indices = cog_data.index
        
        # Filter taxa data to match the non-NaN indices of the cognitive variable
        # This is more efficient than passing NaNs to spearmanr which might raise warnings
        taxa_subset = df.loc[taxa_indices, taxa_cols]
        
        # Chunking the taxa calculation to avoid massive intermediate arrays if N is huge
        # Although spearmanr is vectorized, we can chunk the loop over taxa_cols
        for j in range(0, n_taxa, chunk_size):
            chunk_taxa = taxa_cols[j:j+chunk_size]
            chunk_data = taxa_subset[chunk_taxa]
            
            # Vectorized Spearman correlation
            # scipy.stats.spearmanr returns a SpearmanResult object
            # When x is 1D and y is 2D, it computes correlation between x and each column of y
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    corr_res = spearmanr(cog_data, chunk_data, axis=0)
                
                # corr_res.correlation is a 1D array if x is 1D and y is 2D
                # corr_res.pvalue is a 1D array
                correlations = corr_res.correlation
                pvalues = corr_res.pvalue
                
                if isinstance(correlations, (int, float)):
                    correlations = [correlations]
                    pvalues = [pvalues]
                
                for k, taxon in enumerate(chunk_taxa):
                    results.append({
                        'taxa': taxon,
                        'cognitive_var': cog_col,
                        'correlation': float(correlations[k]),
                        'pvalue': float(pvalues[k])
                    })
            except Exception as e:
                logger.warning("Error computing correlation for %s vs %s: %s", cog_col, chunk_taxa, str(e))

    return pd.DataFrame(results)

def apply_fdr_correction(df_results: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """
    Apply Benjamini-Hochberg FDR correction to p-values.
    
    Args:
        df_results: DataFrame with 'pvalue' column.
        alpha: Significance threshold.
    
    Returns:
        DataFrame with added 'qvalue' and 'significant' columns.
    """
    if df_results is None or df_results.empty:
        return df_results

    logger.info("Applying FDR correction to %d results.", len(df_results))
    
    # Group by cognitive variable to correct within each test set, or global?
    # Typically, we correct across all tests.
    pvals = df_results['pvalue'].values
    
    try:
        reject, pvals_corrected, _, _ = multipletests(pvals, alpha=alpha, method='fdr_bh')
        df_results = df_results.copy()
        df_results['qvalue'] = pvals_corrected
        df_results['significant'] = reject
    except Exception as e:
        logger.error("FDR correction failed: %s", str(e))
        df_results['qvalue'] = np.nan
        df_results['significant'] = False

    return df_results

def save_correlation_results(df_results: pd.DataFrame, df_fdr: pd.DataFrame):
    """
    Save correlation results and FDR-corrected results to disk.
    """
    root = get_project_root_path()
    processed_dir = get_data_processed_path(root)
    ensure_directory(processed_dir)

    corr_path = processed_dir / "correlation_results_raw.parquet"
    fdr_path = processed_dir / "correlation_results_fdr.parquet"
    json_path = processed_dir / "correlation_summary.json"

    if df_results is not None and not df_results.empty:
        df_results.to_parquet(corr_path, index=False)
        logger.info("Saved raw correlation results to %s", corr_path)
    
    if df_fdr is not None and not df_fdr.empty:
        df_fdr.to_parquet(fdr_path, index=False)
        logger.info("Saved FDR-corrected results to %s", fdr_path)
        
        # Generate summary JSON
        summary = {
            "total_pairs": len(df_fdr),
            "significant_pairs": int(df_fdr['significant'].sum()),
            "mean_correlation": float(df_fdr['correlation'].mean()) if not df_fdr.empty else 0.0,
            "min_correlation": float(df_fdr['correlation'].min()) if not df_fdr.empty else 0.0,
            "max_correlation": float(df_fdr['correlation'].max()) if not df_fdr.empty else 0.0,
            "q_threshold": 0.05
        }
        
        with open(json_path, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info("Saved summary to %s", json_path)
    else:
        logger.warning("No results to save for FDR.")

def main():
    """
    Main entry point for the correlation analysis pipeline.
    Handles the Data Gap scenario gracefully.
    """
    logger.info("Starting correlation analysis (T036 optimized).")
    
    # Load data
    df = load_merged_data()
    
    if df is None:
        logger.info("Data Gap detected. Skipping correlation analysis.")
        # Create a dummy file or log to indicate N/A
        root = get_project_root_path()
        processed_dir = get_data_processed_path(root)
        ensure_directory(processed_dir)
        gap_log = processed_dir / "correlation_gap_status.json"
        with open(gap_log, 'w') as f:
            json.dump({"status": "N/A", "reason": "Merged dataset missing (Data Gap)"}, f)
        return

    # Compute correlations with chunking
    df_corr = compute_spearman_correlations(df, chunk_size=500)
    
    if df_corr.empty:
        logger.warning("No correlations computed.")
        return

    # Apply FDR
    df_fdr = apply_fdr_correction(df_corr)
    
    # Save results
    save_correlation_results(df_corr, df_fdr)
    
    logger.info("Correlation analysis completed successfully.")

if __name__ == "__main__":
    main()