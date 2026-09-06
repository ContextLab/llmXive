import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from statsmodels.stats.multitest import multipletests

from utils.config import get_processed_path, get_results_path, get_use_synthetic_data, get_random_seed
from utils.logging_config import get_logger

logger = get_logger(__name__)

def load_preprocessed_data() -> pd.DataFrame:
    """
    Load the CLR-transformed dataset from data/processed/cleared_final.csv.
    """
    processed_path = get_processed_path()
    input_file = processed_path / "cleared_final.csv"
    
    if not input_file.exists():
        raise FileNotFoundError(f"Preprocessed data not found at {input_file}. "
                                "Please ensure T020a (CLR transformation) has completed.")
    
    logger.info(f"Loading preprocessed data from {input_file}")
    df = pd.read_csv(input_file)
    logger.info(f"Loaded dataset with shape: {df.shape}")
    return df

def identify_taxa_columns(df: pd.DataFrame) -> List[str]:
    """
    Identify columns representing taxa (CLR transformed) in the dataframe.
    Assumes columns starting with 'taxa_clr_' or containing 'taxon_' are taxa columns.
    Excludes 'subject_id', 'shannon_diversity', 'log_titer', etc.
    """
    exclude_cols = {'subject_id', 'shannon_diversity', 'log_titer', 
                    'titer_baseline', 'titer_post', 'titer_pre_log', 'titer_post_log'}
    
    taxa_cols = []
    for col in df.columns:
        if col in exclude_cols:
            continue
        # Heuristic: CLR columns usually have a specific prefix or pattern based on T020a
        # T020a adds columns like 'taxa_clr_TaxonName' or just 'taxon_X_clr'
        # Based on task T020a description: "Add columns `taxa_clr` (new columns for each taxon)"
        # We assume the CLR columns are numeric and not in the exclude list.
        if col.startswith('taxa_clr_') or col.startswith('taxon_') and '_clr' in col:
            taxa_cols.append(col)
        elif col not in exclude_cols and np.issubdtype(df[col].dtype, np.number):
            # Fallback: if it's a numeric column not explicitly excluded, it might be a taxon
            # But we need to be careful not to include 'shannon_diversity' or 'log_titer' if they slipped in
            if col not in ['shannon_diversity', 'log_titer']:
                taxa_cols.append(col)
    
    # Remove duplicates and ensure we have a clean list
    taxa_cols = list(set(taxa_cols))
    logger.info(f"Identified {len(taxa_cols)} taxa columns: {taxa_cols[:5]}...")
    return taxa_cols

def identify_zero_variance_taxa(df: pd.DataFrame, taxa_cols: List[str], threshold: float = 1e-9) -> List[str]:
    """
    Identify taxa with zero (or near-zero) variance.
    """
    zero_var_taxa = []
    for col in taxa_cols:
        var = df[col].var()
        if var < threshold:
            zero_var_taxa.append(col)
    
    logger.info(f"Identified {len(zero_var_taxa)} zero-variance taxa.")
    return zero_var_taxa

def filter_zero_variance_taxa(df: pd.DataFrame, taxa_cols: List[str], 
                              variance_filtered_taxa_file: Path, threshold: float = 1e-9) -> Tuple[pd.DataFrame, List[str]]:
    """
    Filter out taxa with variance < threshold.
    Loads the variance-filtered list from T032a if available, otherwise calculates it.
    """
    if variance_filtered_taxa_file.exists():
        logger.info(f"Loading variance-filtered taxa from {variance_filtered_taxa_file}")
        with open(variance_filtered_taxa_file, 'r') as f:
            filtered_taxa = json.load(f)
        # Ensure these columns exist in the dataframe
        valid_taxa = [t for t in filtered_taxa if t in df.columns]
        if len(valid_taxa) != len(filtered_taxa):
            missing = set(filtered_taxa) - set(valid_taxa)
            logger.warning(f"Some variance-filtered taxa not found in data: {missing}")
        taxa_cols = valid_taxa
    else:
        logger.warning(f"Variance filtered taxa file {variance_filtered_taxa_file} not found. "
                       "Calculating variance filter now.")
        zero_var = identify_zero_variance_taxa(df, taxa_cols, threshold)
        taxa_cols = [c for c in taxa_cols if c not in zero_var]
        if len(taxa_cols) == 0:
            raise Exception("NoFeaturesError: No taxa with variance > 1e-9 found.")
        
        # Save the calculated list for consistency
        with open(variance_filtered_taxa_file, 'w') as f:
            json.dump(taxa_cols, f)
        logger.info(f"Saved calculated variance-filtered taxa to {variance_filtered_taxa_file}")

    return df[taxa_cols], taxa_cols

def perform_spearman_correlation(df: pd.DataFrame, taxa_cols: List[str], target_col: str = 'log_titer') -> pd.DataFrame:
    """
    Perform Spearman Rank Correlation between each taxon and the target variable.
    Returns a DataFrame with columns: taxon, coefficient, raw_pvalue.
    """
    results = []
    logger.info(f"Performing Spearman correlation for {len(taxa_cols)} taxa against {target_col}")
    
    for taxon in taxa_cols:
        if taxon == target_col or target_col not in df.columns:
            continue
        
        # Handle NaNs
        valid_data = df[[taxon, target_col]].dropna()
        if len(valid_data) < 3:
            logger.warning(f"Not enough data points for {taxon}. Skipping.")
            continue
        
        corr, pval = spearmanr(valid_data[taxon], valid_data[target_col])
        results.append({
            'taxon': taxon,
            'coefficient': corr,
            'raw_pvalue': pval
        })
    
    return pd.DataFrame(results)

def apply_bh_correction(df_results: pd.DataFrame) -> pd.DataFrame:
    """
    Apply Benjamini-Hochberg correction to raw p-values.
    Adds 'adj_pvalue' column.
    """
    if df_results.empty:
        logger.warning("No results to correct.")
        return df_results
    
    pvals = df_results['raw_pvalue'].values
    if len(pvals) == 0:
        return df_results
    
    # multipletests returns (reject, p_corrected, p_corrected_sidak, p_corrected_simes)
    # We want 'p_corrected' which is the BH adjusted p-value
    try:
        _, pvals_adj, _, _ = multipletests(pvals, alpha=0.05, method='fdr_bh')
        df_results['adj_pvalue'] = pvals_adj
    except Exception as e:
        logger.error(f"Error applying BH correction: {e}")
        # Fallback: set adj_pvalue to raw_pvalue if correction fails
        df_results['adj_pvalue'] = pvals
    
    return df_results

def select_significant_taxa(df_results: pd.DataFrame, alpha: float = 0.05) -> List[str]:
    """
    Select taxa with adjusted p-value < alpha.
    """
    significant = df_results[df_results['adj_pvalue'] < alpha]['taxon'].tolist()
    logger.info(f"Selected {len(significant)} significant taxa (adj p < {alpha})")
    return significant

def save_results(df_results: pd.DataFrame, significant_taxa: List[str], output_path: Path):
    """
    Save correlation results to JSON.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    results_list = df_results.to_dict(orient='records')
    output_data = {
        'correlations': results_list,
        'significant_taxa': significant_taxa,
        'total_taxa_tested': len(df_results),
        'method': 'Spearman',
        'correction': 'Benjamini-Hochberg',
        'alpha': 0.05
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Saved correlation results to {output_path}")

def run_correlation_pipeline():
    """
    Main pipeline function for T032.
    1. Load preprocessed data.
    2. Identify taxa columns.
    3. Filter zero-variance taxa (using T032a output if available).
    4. Perform Spearman correlation.
    5. Apply BH correction.
    6. Select significant taxa.
    7. Save results.
    """
    try:
        # Setup paths
        results_path = get_results_path()
        variance_filtered_file = results_path / "variance_filtered_taxa.json"
        output_file = results_path / "correlation_results.json"
        
        # 1. Load Data
        df = load_preprocessed_data()
        
        # 2. Identify Taxa
        taxa_cols = identify_taxa_columns(df)
        
        if not taxa_cols:
            logger.error("No taxa columns found in dataset.")
            # Fallback to variance filter logic to raise error if truly empty
            if not variance_filtered_file.exists():
                raise Exception("NoFeaturesError: No taxa found in dataset.")
            # If variance file exists but no cols found, it's a mismatch
            raise Exception("NoFeaturesError: Variance file exists but no matching columns in data.")

        # 3. Filter Zero Variance (Delegated to T032a output if present)
        # We call the helper which handles loading T032a's output or recalculating
        df_taxa, valid_taxa_list = filter_zero_variance_taxa(df, taxa_cols, variance_filtered_file)
        
        if not valid_taxa_list:
            raise Exception("NoFeaturesError: No taxa with variance > 1e-9 found.")

        # 4. Perform Correlation
        corr_results = perform_spearman_correlation(df_taxa, valid_taxa_list, target_col='log_titer')
        
        if corr_results.empty:
            logger.warning("No correlations could be calculated.")
            # Still save empty result to allow pipeline to continue
            save_results(corr_results, [], output_file)
            return

        # 5. Apply BH Correction
        corr_results = apply_bh_correction(corr_results)
        
        # 6. Select Significant Taxa
        significant_taxa = select_significant_taxa(corr_results)
        
        # 7. Save Results
        save_results(corr_results, significant_taxa, output_file)
        
        logger.info("Correlation pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Correlation pipeline failed: {e}")
        # Re-raise to allow the orchestrator to handle the failure
        raise

def main():
    """
    Entry point for the script.
    """
    logging.basicConfig(level=logging.INFO)
    run_correlation_pipeline()

if __name__ == "__main__":
    main()
