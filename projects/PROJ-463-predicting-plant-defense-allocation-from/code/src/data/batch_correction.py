"""
Batch correction module for RNA-seq data.

Implements ComBat-seq logic (or a simplified approximation for environments
without R/rpy2) to remove batch effects while preserving biological variance.
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger
from src.utils.config import get_housekeeping_genes

logger = get_logger("batch_correction")

def calculate_cv_reduction(
    df: pd.DataFrame,
    batch_labels: List[str],
    housekeeping_genes: Optional[List[str]] = None,
    apply_correction: bool = False
) -> Dict[str, float]:
    """
    Calculates the Coefficient of Variation (CV) for specified genes (default: housekeeping)
    and computes the reduction after batch correction.
    
    Args:
        df: DataFrame of expression values (genes x samples).
        batch_labels: List of batch labels for each sample.
        housekeeping_genes: List of genes to use for stability check.
        apply_correction: If True, applies correction before calculation (for testing).
        
    Returns:
        Dictionary with 'cv_before', 'cv_after', and 'reduction_pct'.
    """
    if housekeeping_genes is None:
        housekeeping_genes = get_housekeeping_genes()
    
    # Filter for housekeeping genes that exist in the dataframe
    hk_genes = [g for g in housekeeping_genes if g in df.index]
    if not hk_genes:
        logger.warning("No housekeeping genes found in dataframe. Using all genes.")
        hk_genes = list(df.index)
    
    hk_df = df.loc[hk_genes]
    
    # Calculate CV before correction
    # CV = std / mean
    means_before = hk_df.mean(axis=1)
    stds_before = hk_df.std(axis=1)
    cvs_before = stds_before / means_before
    avg_cv_before = cvs_before.mean()
    
    if apply_correction:
        # Apply a simple correction (mean centering per batch) for testing
        corrected_df = pd.DataFrame()
        for batch in np.unique(batch_labels):
            mask = np.array(batch_labels) == batch
            batch_df = hk_df.loc[:, mask]
            batch_mean = batch_df.mean(axis=1)
            # Subtract batch mean from each column in the batch
            corrected_batch = batch_df.sub(batch_mean, axis=0)
            corrected_df[batch_df.columns] = corrected_batch
        
        means_after = corrected_df.mean(axis=1)
        stds_after = corrected_df.std(axis=1)
        cvs_after = stds_after / means_after
        avg_cv_after = cvs_after.mean()
    else:
        avg_cv_after = avg_cv_before
    
    if avg_cv_before == 0:
        reduction_pct = 0.0
    else:
        reduction_pct = (avg_cv_before - avg_cv_after) / avg_cv_before * 100
    
    return {
        "cv_before": avg_cv_before,
        "cv_after": avg_cv_after,
        "reduction_pct": reduction_pct
    }

def apply_batch_correction(
    df: pd.DataFrame,
    batch_labels: List[str],
    housekeeping_genes: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Applies batch correction to the expression matrix.
    
    This function implements a simplified version of ComBat-seq logic:
    1. Estimate batch effects using housekeeping genes.
    2. Adjust all genes to remove the estimated batch effect.
    
    For a full implementation, this would call `rpy2` to run `sva::ComBat_seq`.
    Here, we use a robust scaling approach suitable for integration testing.
    
    Args:
        df: Expression matrix (genes x samples).
        batch_labels: List of batch labels.
        housekeeping_genes: Genes to use for estimating batch effect.
        
    Returns:
        Corrected expression matrix.
    """
    if housekeeping_genes is None:
        housekeeping_genes = get_housekeeping_genes()
    
    hk_genes = [g for g in housekeeping_genes if g in df.index]
    if not hk_genes:
        logger.warning("No housekeeping genes found. Applying global correction.")
        hk_genes = list(df.index)
    
    hk_df = df.loc[hk_genes]
    
    # Estimate batch effect: difference between batch means and global mean
    global_means = hk_df.mean(axis=1)
    batch_effects = {}
    
    unique_batches = np.unique(batch_labels)
    for batch in unique_batches:
        mask = np.array(batch_labels) == batch
        batch_means = hk_df.loc[:, mask].mean(axis=1)
        batch_effects[batch] = batch_means - global_means
    
    # Apply correction to all genes
    corrected_df = df.copy()
    for col_idx, batch in enumerate(batch_labels):
        if batch in batch_effects:
            # We need to subtract the effect for each gene
            # Since we don't have gene-specific effects for non-HK, we use the HK effect
            # This is a simplification.
            # For HK genes: subtract the specific HK effect
            # For others: subtract the median HK effect
            hk_effect = batch_effects[batch]
            median_effect = hk_effect.median()
            
            # Apply to HK genes
            for gene in hk_genes:
                if gene in corrected_df.index:
                    corrected_df.loc[gene, corrected_df.columns[col_idx]] -= hk_effect[gene]
            
            # Apply median effect to others
            other_genes = [g for g in corrected_df.index if g not in hk_genes]
            for gene in other_genes:
                corrected_df.loc[gene, corrected_df.columns[col_idx]] -= median_effect
    
    return corrected_df
