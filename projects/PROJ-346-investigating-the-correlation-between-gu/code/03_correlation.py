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

# Import from utils for path handling and constants
# Note: Using relative import logic compatible with the project structure
try:
    from utils import get_data_processed_path, get_data_qc_path, setup_logger, sanitize_file_path
except ImportError:
    # Fallback for direct execution if path manipulation is needed
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from utils import get_data_processed_path, get_data_qc_path, setup_logger, sanitize_file_path

logger = setup_logger("correlation")

def load_merged_data():
    """Load the merged dataset from the processed directory."""
    processed_dir = get_data_processed_path()
    merged_path = processed_dir / "merged_dataset.parquet"
    
    if not merged_path.exists():
        logger.warning(f"Merged dataset not found at {merged_path}. Skipping correlation analysis.")
        return None
    
    logger.info(f"Loading merged data from {merged_path}")
    try:
        df = pd.read_parquet(merged_path)
        return df
    except Exception as e:
        logger.error(f"Failed to load merged data: {e}")
        return None

def compute_spearman_correlations(df):
    """
    Compute Spearman rank correlations between taxa and cognitive scores.
    Explicitly labels outputs as 'associational'.
    """
    if df is None or df.empty:
        logger.warning("Empty or None dataframe provided for correlation.")
        return None

    # Identify columns: assume 'taxon_name' is not a predictor, 'z_score' is target
    # We need columns that are numeric and represent taxa abundances
    # Based on schema: taxon_name (str), relative_abundance (float), z_score (float)
    
    # Pivot or select relevant columns
    # Assuming the dataframe is wide: rows = samples, columns = taxa + z_score
    # Filter for numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if 'z_score' not in numeric_cols:
        logger.error("z_score column not found in numeric data.")
        return None
    
    taxa_cols = [c for c in numeric_cols if c != 'z_score']
    
    if not taxa_cols:
        logger.warning("No taxa columns found for correlation.")
        return None

    logger.info(f"Computing Spearman correlations for {len(taxa_cols)} taxa against z_score.")
    
    results = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for taxa in taxa_cols:
            # Handle missing values by dropping rows for this pair
            valid_data = df[[taxa, 'z_score']].dropna()
            if len(valid_data) < 3:
                continue
            
            corr, p_val = spearmanr(valid_data[taxa], valid_data['z_score'])
            
            results.append({
                'taxon': taxa,
                'correlation_coefficient': corr,
                'p_value': p_val,
                'n_samples': len(valid_data),
                'framing': 'associational',  # Explicit FR-005 labeling
                'method': 'Spearman Rank Correlation'
            })
    
    if not results:
        return pd.DataFrame()
        
    return pd.DataFrame(results)

def apply_fdr_correction(df_results):
    """Apply Benjamini-Hochberg FDR correction to p-values."""
    if df_results is None or df_results.empty:
        return df_results
    
    p_values = df_results['p_value'].values
    if len(p_values) == 0:
        return df_results

    # multipletests returns (reject, pval_corrected, pval_corrected, alphacSidak)
    # We use method='fdr_bh' for Benjamini-Hochberg
    try:
        reject, pvals_corrected, _, _ = multipletests(p_values, method='fdr_bh')
        df_results['q_value'] = pvals_corrected
        df_results['is_significant'] = reject & (pvals_corrected < 0.05)
    except Exception as e:
        logger.error(f"FDR correction failed: {e}")
        df_results['q_value'] = np.nan
        df_results['is_significant'] = False
    
    return df_results

def save_correlation_results(df_results):
    """Save correlation results to data/processed/ with metadata."""
    if df_results is None or df_results.empty:
        logger.warning("No results to save.")
        return

    processed_dir = get_data_processed_path()
    output_path = processed_dir / "correlation_results.json"
    
    # Ensure output is in a committed location if data/processed is gitignored
    # The prompt noted "every produced artifact is gitignored". 
    # We will save to the declared path but also ensure it's written.
    # If the runner expects it in a specific non-ignored spot, we rely on the quickstart logic.
    # However, the task says "Save ... to data/processed/".
    
    # Convert to dict for JSON serialization
    results_dict = df_results.to_dict(orient='records')
    
    # Add top-level metadata
    output_data = {
        'metadata': {
            'analysis_type': 'correlation',
            'method': 'Spearman Rank Correlation',
            'correction': 'Benjamini-Hochberg FDR',
            'framing': 'associational only',  # FR-005 requirement
            'timestamp': pd.Timestamp.now().isoformat(),
            'description': 'Associational analysis of gut microbiome and cognitive flexibility.'
        },
        'results': results_dict
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Saved correlation results to {output_path}")

def main():
    """Main entry point for correlation analysis."""
    logger.info("Starting correlation analysis (FR-003, FR-004).")
    
    # Load data
    df = load_merged_data()
    
    if df is None:
        logger.info("No merged data available. Exiting gracefully.")
        # Create a minimal result file indicating N/A to satisfy the run-book if needed
        # But per instructions, we must NOT fake results. We just exit.
        return

    # Compute correlations
    df_corr = compute_spearman_correlations(df)
    
    if df_corr is None or df_corr.empty:
        logger.warning("No correlations computed.")
        return

    # Apply FDR
    df_corr = apply_fdr_correction(df_corr)
    
    # Save results
    save_correlation_results(df_corr)
    
    # Log summary
    n_sig = df_corr['is_significant'].sum() if 'is_significant' in df_corr.columns else 0
    logger.info(f"Analysis complete. {len(df_corr)} taxa tested, {n_sig} significant (q < 0.05).")

if __name__ == "__main__":
    main()
