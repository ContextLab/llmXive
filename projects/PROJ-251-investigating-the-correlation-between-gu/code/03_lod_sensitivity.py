"""
LOD Handling Sensitivity Analysis (T013b)

This script implements the sensitivity analysis for Limit of Detection (LOD) handling.
It runs the correlation analysis pipeline twice:
1. Branch A (Exclude): Drops subjects with titers < LOD.
2. Branch B (Impute): Imputes titers < LOD as 0.5 * LOD.

It then compares the sets of significant taxa (adj-p < 0.05) between the two branches
using the Jaccard Index.

Output: data/results/lod_sensitivity.json
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Set, Dict, Any, Tuple, List

import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from statsmodels.stats.multitest import multipletests

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.utils.config import get_processed_path, get_output_path, get_random_seed, get_lod_exclude_threshold
from code.utils.logging_config import get_logger

logger = get_logger(__name__)

def load_preprocessed_data() -> pd.DataFrame:
    """
    Loads the filtered dataset.
    Expected input: data/processed/filtered_data.csv
    """
    input_path = get_processed_path() / "filtered_data.csv"
    if not input_path.exists():
        raise FileNotFoundError(f"Required input file not found: {input_path}")
    
    logger.info(f"Loading preprocessed data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Ensure subject_id is string for consistency
    if 'subject_id' in df.columns:
        df['subject_id'] = df['subject_id'].astype(str)
    
    return df

def apply_lod_handling(df: pd.DataFrame, method: str, lod_threshold: float) -> pd.DataFrame:
    """
    Applies LOD handling to the dataset.
    
    Args:
        df: Input dataframe with 'titer_baseline' and 'titer_post' columns.
        method: 'exclude' or 'impute'.
        lod_threshold: The Limit of Detection value.
        
    Returns:
        Processed dataframe.
    """
    df_clean = df.copy()
    
    # Identify subjects with titers < LOD (in either baseline or post)
    # We consider a subject to have LOD issues if ANY titer is below threshold
    mask_lod = (df_clean['titer_baseline'] < lod_threshold) | (df_clean['titer_post'] < lod_threshold)
    count_lod = mask_lod.sum()
    
    if method == 'exclude':
        logger.info(f"Excluding {count_lod} subjects with titers < LOD ({lod_threshold})")
        df_clean = df_clean[~mask_lod]
    elif method == 'impute':
        logger.info(f"Imputing {count_lod} subjects with titers < LOD ({lod_threshold}) as 0.5 * LOD")
        # Impute values < LOD with 0.5 * LOD
        impute_value = 0.5 * lod_threshold
        df_clean.loc[df_clean['titer_baseline'] < lod_threshold, 'titer_baseline'] = impute_value
        df_clean.loc[df_clean['titer_post'] < lod_threshold, 'titer_post'] = impute_value
    else:
        raise ValueError(f"Unknown LOD handling method: {method}")
    
    return df_clean

def run_correlation_pipeline(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Runs the full correlation pipeline on the given dataframe.
    Calculates Spearman correlation between taxa abundances and log-transformed titers.
    Applies Benjamini-Hochberg correction.
    
    Returns:
        Dictionary containing:
            - significant_taxa: Set of taxa with adj-p < 0.05
            - results_df: Full dataframe of correlation results
    """
    if df.empty:
        return {"significant_taxa": set(), "results_df": pd.DataFrame()}
    
    # Identify taxonomic columns (all columns except metadata)
    # Assuming metadata columns are: subject_id, titer_baseline, titer_post
    # Taxa columns are everything else
    metadata_cols = ['subject_id', 'titer_baseline', 'titer_post']
    taxa_cols = [col for col in df.columns if col not in metadata_cols]
    
    if not taxa_cols:
        logger.warning("No taxonomic columns found in dataframe.")
        return {"significant_taxa": set(), "results_df": pd.DataFrame()}
    
    # Prepare data
    X = df[taxa_cols].values
    y_baseline = df['titer_baseline'].values
    y_post = df['titer_post'].values
    
    # Log-transform titers (add small epsilon to avoid log(0))
    epsilon = 1e-6
    log_baseline = np.log1p(y_baseline + epsilon)
    log_post = np.log1p(y_post + epsilon)
    
    results = []
    
    # Calculate Spearman correlation for each taxon against both titers
    # We will aggregate results. For this sensitivity analysis, we focus on 
    # the set of significant taxa. We'll combine significance from either baseline or post.
    
    p_values = []
    corr_coeffs = []
    taxa_names = []
    titer_types = []
    
    for i, taxon in enumerate(taxa_cols):
        x_taxon = X[:, i]
        
        # Correlate with baseline
        try:
            corr_b, p_b = spearmanr(x_taxon, log_baseline)
            if not np.isnan(corr_b):
                results.append({
                    'taxon': taxon,
                    'titer_type': 'baseline',
                    'corr': corr_b,
                    'p_raw': p_b
                })
                p_values.append(p_b)
                corr_coeffs.append(corr_b)
                taxa_names.append(taxon)
                titer_types.append('baseline')
        except Exception as e:
            logger.debug(f"Correlation failed for {taxon} vs baseline: {e}")
        
        # Correlate with post
        try:
            corr_p, p_p = spearmanr(x_taxon, log_post)
            if not np.isnan(corr_p):
                results.append({
                    'taxon': taxon,
                    'titer_type': 'post',
                    'corr': corr_p,
                    'p_raw': p_p
                })
                p_values.append(p_p)
                corr_coeffs.append(corr_p)
                taxa_names.append(taxon)
                titer_types.append('post')
        except Exception as e:
            logger.debug(f"Correlation failed for {taxon} vs post: {e}")
    
    if not p_values:
        return {"significant_taxa": set(), "results_df": pd.DataFrame()}
        
    p_values = np.array(p_values)
    # BH Correction
    try:
        reject, p_adj, _, _ = multipletests(p_values, method='fdr_bh')
    except Exception as e:
        logger.error(f"Multiple testing correction failed: {e}")
        reject = np.zeros(len(p_values), dtype=bool)
        p_adj = np.ones(len(p_values))
    
    # Build results dataframe
    results_df = pd.DataFrame({
        'taxon': taxa_names,
        'titer_type': titer_types,
        'corr': corr_coeffs,
        'p_raw': p_values,
        'p_adj': p_adj,
        'significant': reject
    })
    
    # Identify significant taxa (adj-p < 0.05)
    # A taxon is significant if it shows significance in EITHER baseline or post
    significant_mask = results_df['significant']
    significant_taxa_set = set(results_df.loc[significant_mask, 'taxon'].unique())
    
    return {
        "significant_taxa": significant_taxa_set,
        "results_df": results_df
    }

def calculate_jaccard(set_a: Set[str], set_b: Set[str]) -> float:
    """
    Calculates the Jaccard Index between two sets.
    Jaccard = |A ∩ B| / |A ∪ B|
    """
    if not set_a and not set_b:
        return 1.0  # Both empty is perfect match
    if not set_a or not set_b:
        return 0.0
    
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    
    if union == 0:
        return 0.0
        
    return intersection / union

def main():
    logger.info("Starting LOD Handling Sensitivity Analysis (T013b)")
    
    # Load configuration
    lod_threshold = get_lod_exclude_threshold()
    random_seed = get_random_seed()
    np.random.seed(random_seed)
    
    # Load data
    df = load_preprocessed_data()
    initial_count = len(df)
    logger.info(f"Loaded {initial_count} subjects")
    
    # Branch A: Exclude
    logger.info("--- Branch A: Exclude LOD subjects ---")
    df_exclude = apply_lod_handling(df, method='exclude', lod_threshold=lod_threshold)
    count_exclude = len(df_exclude)
    logger.info(f"Branch A retained {count_exclude} subjects")
    
    if count_exclude < 50:
        logger.warning(f"Branch A sample size ({count_exclude}) is below 50. Results may be unreliable.")
    
    results_exclude = run_correlation_pipeline(df_exclude)
    significant_taxa_exclude = results_exclude['significant_taxa']
    logger.info(f"Branch A found {len(significant_taxa_exclude)} significant taxa")
    
    # Branch B: Impute
    logger.info("--- Branch B: Impute LOD subjects ---")
    df_impute = apply_lod_handling(df, method='impute', lod_threshold=lod_threshold)
    count_impute = len(df_impute)
    logger.info(f"Branch B retained {count_impute} subjects")
    
    results_impute = run_correlation_pipeline(df_impute)
    significant_taxa_impute = results_impute['significant_taxa']
    logger.info(f"Branch B found {len(significant_taxa_impute)} significant taxa")
    
    # Calculate Jaccard Index
    jaccard_index = calculate_jaccard(significant_taxa_exclude, significant_taxa_impute)
    robust = jaccard_index > 0.5
    
    logger.info(f"Jaccard Index: {jaccard_index:.4f}")
    logger.info(f"Robust (Jaccard > 0.5): {robust}")
    
    # Prepare output
    output_data = {
        "method": "LOD Sensitivity Analysis",
        "lod_threshold": lod_threshold,
        "branch_a": {
            "method": "exclude",
            "initial_count": initial_count,
            "final_count": count_exclude,
            "significant_taxa_count": len(significant_taxa_exclude),
            "significant_taxa": sorted(list(significant_taxa_exclude))
        },
        "branch_b": {
            "method": "impute",
            "initial_count": initial_count,
            "final_count": count_impute,
            "significant_taxa_count": len(significant_taxa_impute),
            "significant_taxa": sorted(list(significant_taxa_impute))
        },
        "comparison": {
            "jaccard_index": jaccard_index,
            "robust": robust
        }
    }
    
    # Write output
    output_dir = get_output_path()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "lod_sensitivity.json"
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Results written to {output_path}")
    return output_data

if __name__ == "__main__":
    main()