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

from utils.config import get_random_seed, get_min_sample_size
from utils.logging_config import get_logger, log_error_context

logger = get_logger(__name__)

def load_preprocessed_data(input_path: Path) -> pd.DataFrame:
    """
    Load the CLR-transformed dataset containing taxa abundances and log-transformed titers.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded data from {input_path}. Shape: {df.shape}")
    return df

def identify_zero_variance_taxa(df: pd.DataFrame) -> List[str]:
    """
    Identify taxa columns with zero variance (variance < 1e-9).
    These are usually constant or all-zero features.
    """
    zero_var_taxa = []
    # Assume taxa columns are those ending in '_clr' or starting with 'taxon'
    # We need to identify which columns are taxa. Based on pipeline, they are likely the CLR columns.
    # Let's assume all columns except subject_id, titer_baseline, titer_post, log_titer, shannon_diversity are taxa.
    exclude_cols = {'subject_id', 'titer_baseline', 'titer_post', 'log_titer', 'shannon_diversity'}
    taxa_cols = [col for col in df.columns if col not in exclude_cols]
    
    for col in taxa_cols:
        if col not in df.columns:
            continue
        try:
            var = df[col].var()
            if var < 1e-9:
                zero_var_taxa.append(col)
        except (TypeError, ValueError):
            # Non-numeric column
            zero_var_taxa.append(col)
    
    logger.info(f"Identified {len(zero_var_taxa)} zero-variance taxa: {zero_var_taxa[:5]}...")
    return zero_var_taxa

def filter_zero_variance_taxa(df: pd.DataFrame, zero_var_taxa: List[str]) -> pd.DataFrame:
    """
    Remove zero-variance taxa from the dataframe.
    """
    cols_to_keep = [col for col in df.columns if col not in zero_var_taxa]
    return df[cols_to_keep]

def perform_permutation_test(df: pd.DataFrame, n_permutations: int = 1000, seed: int = 42) -> Dict[str, Any]:
    """
    Perform a permutation test to generate empirical p-values for comparison.
    Shuffles log_titer labels and recalculates Spearman correlations.
    """
    logger.info(f"Starting permutation test with {n_permutations} permutations.")
    np.random.seed(seed)
    
    exclude_cols = {'subject_id', 'titer_baseline', 'titer_post', 'log_titer', 'shannon_diversity'}
    taxa_cols = [col for col in df.columns if col not in exclude_cols]
    
    if not taxa_cols:
        logger.warning("No taxa columns found for permutation test.")
        return {}
    
    results = {}
    target_col = 'log_titer'
    
    # Calculate observed correlations
    observed_corrs = {}
    observed_pvals = {}
    for taxon in taxa_cols:
        corr, pval = spearmanr(df[taxon], df[target_col])
        observed_corrs[taxon] = corr
        observed_pvals[taxon] = pval
    
    # Permutation loop
    permuted_pvals = {taxon: [] for taxon in taxa_cols}
    
    for i in range(n_permutations):
        # Shuffle target
        shuffled_target = df[target_col].sample(frac=1, random_state=seed + i).reset_index(drop=True)
        
        for taxon in taxa_cols:
            _, pval = spearmanr(df[taxon], shuffled_target)
            permuted_pvals[taxon].append(pval)
    
    # Calculate empirical p-values: proportion of permuted p-values <= observed p-value
    empirical_pvals = {}
    for taxon in taxa_cols:
        obs_p = observed_pvals[taxon]
        perm_p_list = permuted_pvals[taxon]
        # Count how many permuted p-values are <= observed p-value
        count = sum(1 for p in perm_p_list if p <= obs_p)
        empirical_p = (count + 1) / (n_permutations + 1)
        empirical_pvals[taxon] = empirical_p
    
    return {
        "observed_correlations": observed_corrs,
        "observed_pvalues": observed_pvals,
        "empirical_pvalues": empirical_pvals,
        "n_permutations": n_permutations
    }

def apply_bh_correction(pvalues: List[float]) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Apply Benjamini-Hochberg correction to raw p-values.
    Returns: corrected p-values, rejected mask, critical values, alpha/2
    """
    if not pvalues:
        return np.array([]), np.array([]), np.array([]), 0.0
    
    reject, pvals_corrected, alphacSidak, alphacBH = multipletests(
        pvalues, alpha=0.05, method='fdr_bh'
    )
    return reject, pvals_corrected, alphacSidak, alphacBH

def select_significant_taxa(df: pd.DataFrame, reject: np.ndarray, pvals_corrected: np.ndarray, taxa_cols: List[str]) -> List[str]:
    """
    Select taxa with adjusted p-value < 0.05.
    """
    significant = []
    for i, taxon in enumerate(taxa_cols):
        if reject[i] and pvals_corrected[i] < 0.05:
            significant.append(taxon)
    return significant

def save_results(results: Dict[str, Any], output_path: Path):
    """
    Save correlation results to JSON.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Saved correlation results to {output_path}")

def run_correlation_pipeline(input_path: Path, output_path: Path, permutation_path: Path):
    """
    Main pipeline for correlation analysis and feature selection.
    1. Load CLR data.
    2. Filter zero-variance taxa (fallback).
    3. Perform Spearman correlation.
    4. Apply BH correction.
    5. Select significant taxa.
    6. Perform permutation test (secondary).
    7. Save results.
    """
    logger.info("Starting correlation analysis pipeline.")
    
    # Load data
    df = load_preprocessed_data(input_path)
    
    # Identify taxa columns
    exclude_cols = {'subject_id', 'titer_baseline', 'titer_post', 'log_titer', 'shannon_diversity'}
    taxa_cols = [col for col in df.columns if col not in exclude_cols]
    
    if not taxa_cols:
        raise ValueError("No taxa columns found in the dataset.")
    
    # Step 1: Global Unsupervised Filter (Zero Variance)
    zero_var_taxa = identify_zero_variance_taxa(df)
    if zero_var_taxa:
        df_filtered = filter_zero_variance_taxa(df, zero_var_taxa)
        logger.info(f"Filtered {len(zero_var_taxa)} zero-variance taxa.")
    else:
        df_filtered = df
    
    # Step 2: Primary Correlation (Spearman)
    logger.info("Performing Spearman correlation.")
    raw_pvalues = []
    coefficients = []
    significant_taxa = []
    
    for taxon in taxa_cols:
        if taxon in zero_var_taxa:
            # Skip zero-variance taxa for correlation
            raw_pvalues.append(1.0)
            coefficients.append(0.0)
            continue
        
        corr, pval = spearmanr(df_filtered[taxon], df_filtered['log_titer'])
        raw_pvalues.append(pval)
        coefficients.append(corr)
    
    # Step 3: BH Correction
    reject, pvals_corrected, _, _ = apply_bh_correction(raw_pvalues)
    
    # Step 4: Selection
    significant_indices = np.where(reject & (pvals_corrected < 0.05))[0]
    significant_taxa = [taxa_cols[i] for i in significant_indices]
    
    logger.info(f"Found {len(significant_taxa)} significant taxa (adj p < 0.05).")
    
    # Fallback: if no significant taxa, select top-k by raw magnitude
    if len(significant_taxa) == 0:
        logger.warning("No significant taxa found. Falling back to top-k (k=10) by raw magnitude.")
        k = min(10, len(taxa_cols))
        # Sort by absolute coefficient magnitude
        abs_coeffs = [abs(c) for c in coefficients]
        top_k_indices = np.argsort(abs_coeffs)[::-1][:k]
        significant_taxa = [taxa_cols[i] for i in top_k_indices]
        logger.info(f"Selected top-{k} taxa: {significant_taxa}")
    
    # Step 5: Permutation Test (Secondary)
    permutation_results = perform_permutation_test(df_filtered, n_permutations=1000)
    
    # Compile results
    results = {
        "method": "Spearman Correlation with BH Correction",
        "n_taxa_initial": len(taxa_cols),
        "n_taxa_filtered": len(taxa_cols) - len(zero_var_taxa),
        "n_significant": len(significant_taxa),
        "significant_taxa": significant_taxa,
        "correlation_details": [],
        "fallback_used": len(significant_taxa) == 0 and len(significant_taxa) == k
    }
    
    for i, taxon in enumerate(taxa_cols):
        results["correlation_details"].append({
            "taxon": taxon,
            "coefficient": coefficients[i],
            "raw_pvalue": raw_pvalues[i],
            "adj_pvalue": float(pvals_corrected[i]) if i < len(pvals_corrected) else None,
            "is_significant": taxon in significant_taxa
        })
    
    # Save primary results
    save_results(results, output_path)
    
    # Save secondary results
    save_results(permutation_results, permutation_path)
    
    logger.info("Correlation analysis pipeline completed.")

def main():
    """
    Entry point for the correlation analysis script.
    """
    input_path = Path("data/processed/data_clr.csv")
    output_path = Path("data/results/correlation_results.json")
    permutation_path = Path("data/results/permutation_comparison.json")
    
    try:
        run_correlation_pipeline(input_path, output_path, permutation_path)
    except Exception as e:
        log_error_context(logger, "Correlation pipeline failed", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
