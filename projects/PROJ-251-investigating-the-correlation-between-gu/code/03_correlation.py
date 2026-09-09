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

from utils.config import get_processed_path, get_results_path, get_use_synthetic_data
from utils.logging_config import get_logger

logger = get_logger(__name__)

def load_preprocessed_data(filepath: Path) -> pd.DataFrame:
    """Load the CLR-transformed dataset."""
    if not filepath.exists():
        raise FileNotFoundError(f"Preprocessed data file not found: {filepath}")
    logger.info(f"Loading preprocessed data from {filepath}")
    return pd.read_csv(filepath)

def identify_taxa_columns(df: pd.DataFrame) -> List[str]:
    """Identify columns that represent CLR-transformed taxa."""
    # Based on the pipeline, CLR columns are prefixed with 'taxa_clr_' or similar
    # We assume the variance filter output (T032a) defines the valid taxa list
    # If not passed explicitly, we infer from column names that are numeric/float
    # and not standard metadata columns.
    exclude_cols = {'subject_id', 'titer_baseline', 'titer_post', 'shannon_diversity',
                    'titer_pre_log', 'titer_post_log', 'log_titer'}
    taxa_cols = [col for col in df.columns if col not in exclude_cols]
    logger.info(f"Identified {len(taxa_cols)} potential taxa columns")
    return taxa_cols

def identify_zero_variance_taxa(df: pd.DataFrame, taxa_cols: List[str], threshold: float = 1e-9) -> List[str]:
    """Identify taxa with variance below the threshold."""
    zero_var = []
    for col in taxa_cols:
        if col in df.columns:
            if df[col].var() < threshold:
                zero_var.append(col)
    logger.info(f"Identified {len(zero_var)} zero-variance taxa")
    return zero_var

def filter_zero_variance_taxa(df: pd.DataFrame, taxa_cols: List[str], threshold: float = 1e-9) -> Tuple[pd.DataFrame, List[str]]:
    """Filter out zero-variance taxa and return the cleaned dataframe and remaining taxa list."""
    zero_var = identify_zero_variance_taxa(df, taxa_cols, threshold)
    remaining_cols = [c for c in taxa_cols if c not in zero_var]
    if len(remaining_cols) == 0:
        logger.error("No features with variance > threshold found.")
        raise ValueError("NoFeaturesError: No taxa with variance > 1e-9 found.")
    
    # Filter dataframe to keep only remaining taxa columns
    # We keep metadata columns as well
    meta_cols = [c for c in df.columns if c not in taxa_cols]
    final_cols = meta_cols + remaining_cols
    return df[final_cols], remaining_cols

def perform_spearman_correlation(df: pd.DataFrame, taxa_cols: List[str], target_col: str = 'log_titer') -> List[Dict[str, Any]]:
    """Perform Spearman correlation between each taxon and the target variable."""
    results = []
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataframe")
    
    for taxon in taxa_cols:
        if taxon not in df.columns:
            continue
        
        # Drop rows where either taxon or target is NaN
        valid_data = df[[taxon, target_col]].dropna()
        if len(valid_data) < 3:
            logger.warning(f"Not enough data for {taxon}, skipping")
            continue
        
        rho, p_val = spearmanr(valid_data[taxon], valid_data[target_col])
        results.append({
            'taxon': taxon,
            'coefficient': float(rho),
            'raw_pvalue': float(p_val)
        })
    
    logger.info(f"Performed Spearman correlation for {len(results)} taxa")
    return results

def apply_bh_correction(correlation_results: List[Dict[str, Any]], alpha: float = 0.05) -> List[Dict[str, Any]]:
    """Apply Benjamini-Hochberg correction to p-values."""
    if not correlation_results:
        return []
    
    pvals = [r['raw_pvalue'] for r in correlation_results]
    # multipletests returns (reject, pval_corrected, pval_corrected_lower, pval_corrected_upper)
    # We use method='fdr_bh' for Benjamini-Hochberg
    reject, pvals_corrected, _, _ = multipletests(pvals, alpha=alpha, method='fdr_bh')
    
    for i, result in enumerate(correlation_results):
        result['adj_pvalue'] = float(pvals_corrected[i])
        result['significant'] = bool(reject[i])
    
    logger.info(f"Applied BH correction to {len(correlation_results)} p-values")
    return correlation_results

def select_significant_taxa(correlation_results: List[Dict[str, Any]], alpha: float = 0.05) -> List[str]:
    """Select taxa with adjusted p-value < alpha."""
    significant = [r['taxon'] for r in correlation_results if r.get('significant', False)]
    logger.info(f"Selected {len(significant)} significant taxa")
    return significant

def save_results(correlation_results: List[Dict[str, Any]], output_path: Path):
    """Save correlation results to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(correlation_results, f, indent=2)
    logger.info(f"Saved correlation results to {output_path}")

def run_correlation_pipeline(
    input_path: Path,
    variance_filtered_taxa_path: Path,
    output_path: Path,
    target_col: str = 'log_titer',
    variance_threshold: float = 1e-9,
    alpha: float = 0.05
) -> List[str]:
    """
    Run the full correlation analysis pipeline:
    1. Load preprocessed data
    2. Load variance-filtered taxa list
    3. Perform Spearman correlation
    4. Apply BH correction
    5. Select significant taxa
    6. Save results
    """
    logger.info("Starting correlation pipeline")
    
    # Load data
    df = load_preprocessed_data(input_path)
    
    # Load variance-filtered taxa
    if not variance_filtered_taxa_path.exists():
        raise FileNotFoundError(f"Variance filtered taxa file not found: {variance_filtered_taxa_path}")
    
    with open(variance_filtered_taxa_path, 'r') as f:
        variance_filtered_taxa = json.load(f)
    
    logger.info(f"Loaded {len(variance_filtered_taxa)} variance-filtered taxa")
    
    # Filter dataframe to only include variance-filtered taxa
    # Ensure all taxa exist in dataframe
    available_taxa = [t for t in variance_filtered_taxa if t in df.columns]
    if len(available_taxa) == 0:
        raise ValueError("No variance-filtered taxa found in the preprocessed data")
    
    # Perform correlation
    correlation_results = perform_spearman_correlation(df, available_taxa, target_col)
    
    # Apply BH correction
    correlation_results = apply_bh_correction(correlation_results, alpha)
    
    # Select significant taxa
    significant_taxa = select_significant_taxa(correlation_results, alpha)
    
    # If no significant taxa, use all variance-filtered taxa as fallback (per spec)
    if len(significant_taxa) == 0:
        logger.warning("No significant taxa found. Using all variance-filtered taxa as fallback.")
        significant_taxa = available_taxa
    
    # Save results
    save_results(correlation_results, output_path)
    
    logger.info(f"Correlation pipeline completed. Significant taxa: {len(significant_taxa)}")
    return significant_taxa

def main():
    """Main entry point for the correlation analysis."""
    try:
        # Get paths from config
        input_path = get_processed_path() / 'cleared_final.csv'
        variance_filtered_path = get_results_path() / 'variance_filtered_taxa.json'
        output_path = get_results_path() / 'correlation_results.json'
        
        # Run pipeline
        significant_taxa = run_correlation_pipeline(
            input_path=input_path,
            variance_filtered_taxa_path=variance_filtered_path,
            output_path=output_path
        )
        
        logger.info(f"Pipeline completed successfully. Significant taxa: {significant_taxa}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
