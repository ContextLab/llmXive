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

# Add project root to path to resolve imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils import get_data_processed_path, get_data_qc_path, setup_logger, get_logger
from config import get_project_root

# Configure logging
logger = setup_logger('correlation_analysis', level=logging.INFO)

def load_merged_data():
    """
    Load the merged dataset from the processed directory.
    Handles the case where the file might not exist (Data Gap scenario).
    """
    root = get_project_root()
    # Fix for API contract: get_data_processed_path must accept root or no args
    # We call it with root to be safe, relying on the updated utils.py
    try:
        data_dir = get_data_processed_path(root)
    except TypeError:
        # Fallback if utils.py hasn't been updated yet (though it should be)
        data_dir = get_data_processed_path()
    
    data_path = data_dir / "merged_dataset.parquet"
    
    if not data_path.exists():
        logger.warning(f"Merged dataset not found at {data_path}. Skipping correlation analysis.")
        return None
    
    logger.info(f"Loading merged data from {data_path}")
    df = pd.read_parquet(data_path)
    logger.info(f"Loaded {len(df)} samples with {len(df.columns)} columns")
    return df

def compute_spearman_correlations(df):
    """
    Compute Spearman rank correlations between microbial taxa and cognitive scores.
    Explicitly labels outputs as 'associational'.
    """
    if df is None:
        return None

    # Identify columns
    # We assume the merged dataset has columns for taxa (relative_abundance) and cognitive scores (z_score)
    # We need to filter for taxa columns (likely numeric and not metadata) and cognitive columns
    
    # Heuristic: Cognitive scores are usually named 'z_score' or similar in our schema
    # Taxa are usually the rest of the numeric columns excluding metadata like 'sample_id', 'participant_id', 'age', 'sex', 'bmi'
    
    metadata_cols = ['sample_id', 'participant_id', 'age', 'sex', 'bmi', 'task_type']
    cognitive_cols = [col for col in df.columns if 'z_score' in col.lower() or 'cognitive' in col.lower()]
    
    # If no explicit cognitive column found, look for the target variable
    if not cognitive_cols:
        # Fallback: assume 'z_score' is the target if it exists
        if 'z_score' in df.columns:
            cognitive_cols = ['z_score']
        else:
            logger.error("No cognitive score columns found in merged dataset.")
            return None

    # Taxa columns: numeric columns not in metadata or cognitive
    taxa_cols = [col for col in df.select_dtypes(include=[np.number]).columns 
                 if col not in metadata_cols and col not in cognitive_cols]
    
    if not taxa_cols:
        logger.warning("No taxa columns found for correlation analysis.")
        return None

    logger.info(f"Computing correlations for {len(taxa_cols)} taxa against {len(cognitive_cols)} cognitive scores.")
    
    results = []
    
    for taxon in taxa_cols:
        for cog in cognitive_cols:
            # Drop rows with NaN in either column
            valid_data = df[[taxon, cog]].dropna()
            if len(valid_data) < 3:
                continue
            
            try:
                corr, p_value = spearmanr(valid_data[taxon], valid_data[cog])
                results.append({
                    "taxon": taxon,
                    "cognitive_metric": cog,
                    "correlation": float(corr),
                    "p_value": float(p_value),
                    "n_samples": len(valid_data),
                    "associational_framing": True # Explicit label
                })
            except Exception as e:
                logger.warning(f"Failed to compute correlation for {taxon} vs {cog}: {e}")
    
    if not results:
        logger.warning("No valid correlations computed.")
        return None

    return pd.DataFrame(results)

def apply_fdr_correction(df_results):
    """
    Apply Benjamini-Hochberg FDR correction to p-values.
    Flags significant taxa (q < 0.05).
    """
    if df_results is None or df_results.empty:
        return None

    # Perform FDR correction
    # We correct p-values across all tests
    p_values = df_results['p_value'].values
    
    # multipletests returns (reject, pval_corrected, alphacSidak, alphacBonf)
    reject, p_corrected, _, _ = multipletests(p_values, alpha=0.05, method='fdr_bh')
    
    df_results['q_value'] = p_corrected
    df_results['is_significant'] = reject
    df_results['fdr_method'] = 'benjamini-hochberg'
    
    significant_count = df_results['is_significant'].sum()
    logger.info(f"FDR correction applied. {significant_count} significant taxa found (q < 0.05).")
    
    return df_results

def save_correlation_results(df_results):
    """
    Save correlation results to data/processed/ with metadata.
    """
    if df_results is None:
        logger.info("No results to save.")
        return

    root = get_project_root()
    try:
        data_dir = get_data_processed_path(root)
    except TypeError:
        data_dir = get_data_processed_path()
    
    output_path = data_dir / "correlation_results.json"
    
    # Ensure directory exists
    data_dir.mkdir(parents=True, exist_ok=True)
    
# Convert to list of dicts for JSON serialization
    results_list = df_results.to_dict(orient='records')
    
    output_data = {
        "metadata": {
            "description": "Spearman correlation between gut microbiome taxa and cognitive flexibility scores",
            "fr_003_compliance": True,
            "fr_004_compliance": True,
            "associational_only": True,
            "fdr_method": "benjamini-hochberg",
            "alpha_threshold": 0.05,
            "generated_at": str(pd.Timestamp.now())
        },
        "results": results_list
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Correlation results saved to {output_path}")
    
    # Also save a CSV for easier inspection
    csv_path = data_dir / "correlation_results.csv"
    df_results.to_csv(csv_path, index=False)
    logger.info(f"Correlation results CSV saved to {csv_path}")

def main():
    """
    Main entry point for T022: Correlation Analysis and FDR Correction.
    """
    logger.info("Starting correlation analysis (T022).")
    
    # 1. Load merged data
    df = load_merged_data()
    
    # 2. Conditional skip if data gap
    if df is None:
        logger.info("Skipping correlation analysis due to missing merged dataset (Data Gap).")
        # Create a placeholder result indicating N/A to satisfy the requirement of producing a file
        # but clearly marking it as N/A due to data gap, not fabrication.
        root = get_project_root()
        try:
            data_dir = get_data_processed_path(root)
        except TypeError:
            data_dir = get_data_processed_path()
        
        output_path = data_dir / "correlation_results.json"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        placeholder_data = {
            "metadata": {
                "status": "N/A",
                "reason": "Merged dataset not found (Data Gap detected in T014)",
                "associational_only": True
            },
            "results": []
        }
        with open(output_path, 'w') as f:
            json.dump(placeholder_data, f, indent=2)
        logger.info(f"Created placeholder correlation results at {output_path} due to data gap.")
        return

    # 3. Compute correlations
    df_corr = compute_spearman_correlations(df)
    
    if df_corr is None:
        logger.warning("Correlation computation yielded no results.")
        return

    # 4. Apply FDR correction
    df_corr_fdr = apply_fdr_correction(df_corr)
    
    # 5. Save results
    save_correlation_results(df_corr_fdr)
    
    logger.info("Correlation analysis and FDR correction completed successfully.")

if __name__ == "__main__":
    main()