"""
Module: 03_correlation.py
Purpose: Implement Spearman rank correlation with Permutation Testing and BH correction.
Dependency: T020c (cleared_with_diversity.csv with CLR taxa and log_titer)
Output: data/results/correlation_results.json
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from statsmodels.stats.multitest import multipletests

# Local imports matching API surface
from utils.config import get_random_seed, get_output_path, get_processed_path
from utils.logging_config import get_logger, log_sample_size
from utils.validators import validate_correlation_results_schema

logger = get_logger(__name__)

def load_preprocessed_data() -> pd.DataFrame:
    """Load the preprocessed dataset containing CLR taxa and log_titer."""
    input_path = get_processed_path("cleared_with_diversity.csv")
    if not input_path.exists():
        raise FileNotFoundError(f"Preprocessed data not found at {input_path}. "
                                "Ensure T020c has completed successfully.")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} subjects from {input_path}")
    return df

def identify_zero_variance_taxa(df: pd.DataFrame) -> List[str]:
    """Identify taxa with zero variance across all subjects."""
    # Identify columns that are likely taxa (exclude metadata columns)
    metadata_cols = ['subject_id', 'titer_baseline', 'titer_post', 'log_titer', 'shannon_diversity']
    taxa_cols = [col for col in df.columns if col not in metadata_cols]
    
    zero_var_taxa = []
    for col in taxa_cols:
        if df[col].var() == 0:
            zero_var_taxa.append(col)
    
    if zero_var_taxa:
        logger.warning(f"Found {len(zero_var_taxa)} zero-variance taxa: {zero_var_taxa}")
    
    return zero_var_taxa

def filter_zero_variance_taxa(df: pd.DataFrame, zero_var_taxa: List[str]) -> pd.DataFrame:
    """Remove zero-variance taxa from the dataframe."""
    if not zero_var_taxa:
        return df
    
    df_filtered = df.drop(columns=zero_var_taxa)
    logger.info(f"Filtered out {len(zero_var_taxa)} zero-variance taxa. "
                f"Remaining taxa: {len(df_filtered.columns) - 5}")  # -5 for metadata
    return df_filtered

def perform_permutation_test(
    df: pd.DataFrame, 
    taxa_cols: List[str], 
    target_col: str, 
    n_permutations: int = 1000, 
    random_seed: int = 42
) -> Dict[str, Dict[str, float]]:
    """
    Perform Spearman correlation with permutation testing for each taxon.
    
    Args:
        df: DataFrame with CLR-transformed taxa and target variable
        taxa_cols: List of taxon column names
        target_col: Name of the target variable (log_titer)
        n_permutations: Number of permutations for empirical p-value calculation
        random_seed: Random seed for reproducibility
    
    Returns:
        Dictionary mapping taxon names to correlation stats (observed_corr, empirical_pvalue)
    """
    np.random.seed(random_seed)
    target_values = df[target_col].values
    results = {}
    
    logger.info(f"Starting permutation test with {n_permutations} permutations for {len(taxa_cols)} taxa")
    
    for i, taxon in enumerate(taxa_cols):
        if i % 50 == 0:
            logger.info(f"Processing taxon {i+1}/{len(taxa_cols)}: {taxon}")
        
        taxon_values = df[taxon].values
        
        # Calculate observed Spearman correlation
        corr, _ = spearmanr(taxon_values, target_values)
        
        # Permutation test: shuffle target labels and recalculate correlation
        permuted_corrs = []
        for _ in range(n_permutations):
            shuffled_target = np.random.permutation(target_values)
            perm_corr, _ = spearmanr(taxon_values, shuffled_target)
            permuted_corrs.append(perm_corr)
        
        # Calculate empirical p-value (two-tailed)
        # Count how many permuted correlations are as extreme or more extreme than observed
        extreme_count = sum(1 for pc in permuted_corrs if abs(pc) >= abs(corr))
        empirical_pvalue = (extreme_count + 1) / (n_permutations + 1)  # Add 1 to avoid zero p-value
        
        results[taxon] = {
            'observed_correlation': float(corr),
            'empirical_pvalue': float(empirical_pvalue),
            'n_permutations': n_permutations
        }
    
    return results

def apply_bh_correction(correlation_results: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
    """
    Apply Benjamini-Hochberg correction to empirical p-values.
    
    Args:
        correlation_results: Dictionary of correlation stats with empirical p-values
    
    Returns:
        Updated dictionary with adjusted p-values and significance flags
    """
    taxa = list(correlation_results.keys())
    pvalues = np.array([correlation_results[taxon]['empirical_pvalue'] for taxon in taxa])
    
    # Apply BH correction
    reject, pvals_corrected, _, _ = multipletests(pvalues, alpha=0.05, method='fdr_bh')
    
    for i, taxon in enumerate(taxa):
        correlation_results[taxon]['adj_pvalue'] = float(pvals_corrected[i])
        correlation_results[taxon]['significant'] = bool(reject[i])
    
    logger.info(f"Applied BH correction to {len(taxa)} taxa. "
                f"Significant taxa (p_adj < 0.05): {sum(reject)}")
    
    return correlation_results

def select_significant_taxa(correlation_results: Dict[str, Dict[str, float]], 
                            alpha: float = 0.05) -> List[str]:
    """Select taxa with adjusted p-value below threshold."""
    return [
        taxon for taxon, stats in correlation_results.items()
        if stats.get('significant', False) and stats['adj_pvalue'] < alpha
    ]

def save_results(correlation_results: Dict[str, Dict[str, float]], 
                 significant_taxa: List[str]) -> Path:
    """
    Save correlation results to JSON file.
    
    Args:
        correlation_results: Full correlation statistics for all taxa
        significant_taxa: List of significant taxon names
    
    Returns:
        Path to the saved JSON file
    """
    output_path = get_output_path("correlation_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    results_to_save = {
        'summary': {
            'total_taxa_tested': len(correlation_results),
            'significant_taxa_count': len(significant_taxa),
            'alpha_threshold': 0.05,
            'n_permutations': list(correlation_results.values())[0]['n_permutations'] if correlation_results else 0
        },
        'significant_taxa': significant_taxa,
        'all_results': correlation_results
    }
    
    with open(output_path, 'w') as f:
        json.dump(results_to_save, f, indent=2)
    
    logger.info(f"Saved correlation results to {output_path}")
    return output_path

def run_correlation_pipeline() -> Tuple[Dict[str, Dict[str, float]], List[str], Path]:
    """
    Main pipeline function to run the full correlation analysis.
    
    Returns:
        Tuple of (correlation_results, significant_taxa, output_path)
    """
    # Load data
    df = load_preprocessed_data()
    log_sample_size(len(df))
    
    # Identify and filter zero-variance taxa
    zero_var_taxa = identify_zero_variance_taxa(df)
    df_filtered = filter_zero_variance_taxa(df, zero_var_taxa)
    
    # Get taxon columns (exclude metadata)
    metadata_cols = ['subject_id', 'titer_baseline', 'titer_post', 'log_titer', 'shannon_diversity']
    taxa_cols = [col for col in df_filtered.columns if col not in metadata_cols]
    
    if not taxa_cols:
        raise ValueError("No taxa columns found in the dataset after filtering.")
    
    # Perform permutation test
    correlation_results = perform_permutation_test(
        df_filtered, 
        taxa_cols, 
        'log_titer', 
        n_permutations=1000,
        random_seed=get_random_seed()
    )
    
    # Apply BH correction
    correlation_results = apply_bh_correction(correlation_results)
    
    # Select significant taxa
    significant_taxa = select_significant_taxa(correlation_results)
    
    # Save results
    output_path = save_results(correlation_results, significant_taxa)
    
    # Validate output schema
    validate_correlation_results_schema(output_path)
    
    logger.info(f"Pipeline complete. Found {len(significant_taxa)} significant taxa.")
    
    return correlation_results, significant_taxa, output_path

def main():
    """Entry point for the correlation analysis script."""
    logger.info("Starting correlation analysis with permutation testing...")
    
    try:
        correlation_results, significant_taxa, output_path = run_correlation_pipeline()
        
        logger.info(f"Results saved to: {output_path}")
        logger.info(f"Significant taxa ({len(significant_taxa)}): {', '.join(significant_taxa)}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Correlation analysis failed: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
