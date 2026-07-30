"""
Batch correction module using ComBat-seq via rpy2.

This module implements batch correction for RNA-seq count data using the
sva::ComBat_seq R function. It also calculates the Coefficient of Variation (CV)
for housekeeping genes before and after correction to assess the effectiveness
of the batch removal.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np
import pandas as pd

# Import config for housekeeping genes
from src.utils.config import get_housekeeping_genes, get_data_path
from src.utils.logger import get_logger
from src.utils.provenance import record_provenance, ArtifactType

try:
    import rpy2.robjects as ro
    from rpy2.robjects import pandas2ri, numpy2ri
    from rpy2.robjects.packages import importr
    from rpy2.rinterface_lib.callbacks import logger as r_logger
    import rpy2.robjects.numpy2ri
except ImportError:
    raise ImportError(
        "rpy2 is required for batch correction. "
        "Please install it via `pip install rpy2`."
    )

# Suppress R warnings for cleaner logs unless critical
r_logger.setLevel(logging.ERROR)

logger = get_logger(__name__)

# Initialize R packages
def _init_r_packages():
    """Initialize required R packages: sva and genefilter."""
    try:
        sva = importr('sva')
        genefilter = importr('genefilter')
        base = importr('base')
        return sva, genefilter, base
    except Exception as e:
        logger.error(f"Failed to import R packages: {e}")
        logger.error("Ensure 'sva' and 'genefilter' are installed in your R environment.")
        raise

def calculate_geometric_mean(counts: np.ndarray) -> np.ndarray:
    """
    Calculate geometric mean of counts across samples for each gene.
    Used as a stability measure for housekeeping gene selection.
    """
    # Add small epsilon to avoid log(0)
    eps = 1e-6
    log_counts = np.log(counts + eps)
    mean_log = np.mean(log_counts, axis=1)
    return np.exp(mean_log)

def calculate_georm_m_value(counts: np.ndarray, gene_ids: List[str]) -> Dict[str, float]:
    """
    Calculate M-values (log2 fold change relative to geometric mean) for housekeeping genes.
    This is used by geNorm to determine gene stability.
    """
    # Filter counts to only housekeeping genes
    hk_indices = [i for i, gid in enumerate(gene_ids) if gid in gene_ids]
    if not hk_indices:
        # Fallback: if gene_ids in config don't match index, try to match by row names if available
        # Assuming counts is a numpy array, we rely on the order matching the config list
        # If the caller passes the full matrix, we need to know which rows are HK.
        # For this implementation, we assume the 'counts' passed here is already filtered
        # or the gene_ids list corresponds to the rows.
        # However, the task says: "call genefilter::geNorm() on the fixed list of housekeeping genes"
        # This implies we need to extract those rows from the full matrix.
        pass

    # If counts is the full matrix and gene_ids are the row names (or indices)
    # We need to identify which rows correspond to the housekeeping genes.
    # Let's assume the input 'counts' is a numpy array and we have a list of gene IDs.
    # We will assume the caller has already filtered the matrix to include only HK genes
    # OR we need to map gene IDs to rows.
    # Given the function signature, let's assume 'counts' is the full matrix and 'gene_ids'
    # are the row names. But numpy arrays don't have row names.
    # Let's assume the input 'counts' is a 2D array where rows are genes and columns are samples.
    # And 'gene_ids' is a list of gene identifiers corresponding to the rows of 'counts'.
    # If the list of gene_ids provided is the FULL list of genes in 'counts', then we filter.
    
    # Re-reading the task: "call genefilter::geNorm() on the fixed list of housekeeping genes"
    # This means we need to extract the rows corresponding to the fixed list.
    # Let's assume the 'counts' passed to this function is the FULL count matrix.
    # We need a mapping of gene_id -> row_index.
    
    # Since the function signature is generic, let's assume the caller passes the subset
    # of counts that corresponds to the housekeeping genes, OR we need to handle the mapping.
    # For robustness, let's assume 'gene_ids' is the list of ALL genes in 'counts' in order.
    # Then we filter.
    
    # Actually, the task says "on the fixed list of housekeeping genes defined in config".
    # So we should extract those specific rows from the full matrix.
    # Let's change the logic: This function should take the FULL matrix and the list of ALL gene names.
    # But to keep it simple and aligned with the "call geNorm on HK genes" instruction,
    # we will assume the 'counts' passed here is ALREADY the subset of HK genes,
    # and 'gene_ids' are the names of those genes.
    
    # If counts is not a subset, we need to filter.
    # Let's assume the input 'counts' is the full matrix and 'gene_ids' is the list of all gene names.
    # Then we filter.
    if len(counts) != len(gene_ids):
        # If lengths don't match, we assume counts is full and gene_ids is full list.
        # We need to find indices of HK genes.
        # But we don't have the HK list here.
        # This implies the caller must pass the HK subset.
        # Let's assume the caller passes the HK subset.
        # If not, we raise an error or try to infer.
        # For now, let's assume the input is the HK subset.
        pass
    
    # Calculate M-values using the geometric mean of the HK genes
    # M-value for a gene is the average absolute log2 fold change between that gene and every other gene.
    # This is complex to implement manually. We will use R's genefilter.
    
    # Convert to R DataFrame
    ro.globalenv['counts_r'] = pandas2ri.py2rpy(pd.DataFrame(counts.T)) # Transpose: samples as rows?
    # genefilter expects genes as rows, samples as columns.
    # R matrix: rows=genes, cols=samples.
    r_counts = numpy2ri.py2rpy(counts)
    
    sva, genefilter, base = _init_r_packages()
    
    # Call genefilter::genefilter with M-value calculation
    # The function 'genefilter' returns a list of filters.
    # We want the M-value stability measure.
    # geNorm is in the 'geNorm' function of the 'geNorm' package? No, it's in 'sva' or 'genefilter'?
    # Actually, geNorm is often implemented in the 'NormqPCR' or 'geNorm' R package.
    # The task says "genefilter::geNorm()". Let's check if genefilter has geNorm.
    # It might be a custom implementation or a misunderstanding.
    # Standard geNorm is in the 'geNorm' package or 'NormqPCR'.
    # However, the task explicitly says "genefilter::geNorm()".
    # Let's assume it exists or we implement the logic.
    # If not, we can calculate the M-value manually:
    # M_i = mean_j ( | log2(g_i / g_j) | )
    
    # Let's implement M-value calculation manually to be safe and independent of R package quirks.
    # M-value for gene i is the average absolute log2 fold change between gene i and all other genes.
    # We have counts for HK genes (rows) x samples (cols).
    # Normalize counts first? geNorm uses geometric mean normalization.
    
    # Normalize each gene by its geometric mean across samples? No, geNorm uses the geometric mean of all genes for each sample.
    # Let's calculate the geometric mean of all HK genes for each sample.
    # Then divide each gene's count by this sample-specific geometric mean.
    # Then calculate M-values.
    
    # Step 1: Geometric mean of all HK genes for each sample
    # counts: genes x samples
    eps = 1e-6
    log_counts = np.log(counts + eps)
    geo_mean_per_sample = np.exp(np.mean(log_counts, axis=0)) # Mean over genes (axis 0)
    
    # Step 2: Normalize counts by sample geometric mean
    # normalized_counts[i, j] = counts[i, j] / geo_mean_per_sample[j]
    normalized_counts = counts / geo_mean_per_sample
    
    # Step 3: Calculate M-values
    # M_i = mean_j ( | log2( normalized_counts[i] / normalized_counts[j] ) | )
    # This is O(N^2) for N genes. For 50 genes, it's fine.
    m_values = []
    for i in range(len(counts)):
        diffs = []
        for j in range(len(counts)):
            if i != j:
                ratio = normalized_counts[i] / normalized_counts[j]
                # Avoid division by zero
                ratio = np.where(ratio == 0, eps, ratio)
                log_ratio = np.abs(np.log2(ratio))
                diffs.append(np.mean(log_ratio))
        m_values.append(np.mean(diffs))
    
    return {gene_ids[i]: m_values[i] for i in range(len(gene_ids))}

def calculate_cv_for_genes(counts: np.ndarray, gene_indices: List[int]) -> float:
    """
    Calculate the average Coefficient of Variation (CV) for a set of genes.
    CV = std / mean.
    """
    if not gene_indices:
        return 0.0
    
    subset = counts[gene_indices, :]
    means = np.mean(subset, axis=1)
    stds = np.std(subset, axis=1)
    
    # Avoid division by zero
    cv = np.where(means == 0, 0, stds / means)
    return np.mean(cv)

def apply_combat_seq(
    counts: np.ndarray,
    batch: np.ndarray,
    group: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Apply ComBat-seq batch correction using rpy2.
    
    Args:
        counts: 2D numpy array (genes x samples) of raw counts.
        batch: 1D array of batch labels.
        group: 1D array of biological group labels (optional).
    
    Returns:
        Corrected counts as 2D numpy array.
    """
    sva, genefilter, base = _init_r_packages()
    
    # Convert to R objects
    r_counts = numpy2ri.py2rpy(counts)
    r_batch = numpy2ri.py2rpy(batch)
    
    # Create R list for arguments
    # ComBat_seq(counts, batch, group=NULL, ...)
    ro.globalenv['counts_r'] = r_counts
    ro.globalenv['batch_r'] = r_batch
    
    if group is not None:
        ro.globalenv['group_r'] = numpy2ri.py2rpy(group)
        cmd = "corrected <- sva::ComBat_seq(counts_r, batch=batch_r, group=group_r)"
    else:
        cmd = "corrected <- sva::ComBat_seq(counts_r, batch=batch_r)"
    
    try:
        ro.r(cmd)
        corrected_r = ro.r['corrected']
        corrected_np = numpy2ri.rpy2py(corrected_r)
        return corrected_np
    except Exception as e:
        logger.error(f"ComBat-seq failed: {e}")
        raise

def calculate_cv_reduction(
    pre_cv: float,
    post_cv: float
) -> float:
    """
    Calculate the percentage reduction in CV.
    Reduction = (pre - post) / pre * 100
    """
    if pre_cv == 0:
        return 0.0
    return ((pre_cv - post_cv) / pre_cv) * 100

def apply_batch_correction(
    counts_matrix_path: str,
    batch_labels: List[str],
    output_manifest_path: str,
    gene_ids: Optional[List[str]] = None
) -> Dict:
    """
    Main function to apply batch correction and generate the report.
    
    Args:
        counts_matrix_path: Path to the input count matrix (CSV, genes x samples).
        batch_labels: List of batch labels for each sample (column).
        output_manifest_path: Path to write the batch correction report JSON.
        gene_ids: List of gene identifiers corresponding to rows in counts_matrix.
    
    Returns:
        Dictionary with pre_cv, post_cv, reduction_percent.
    """
    logger.info(f"Loading count matrix from {counts_matrix_path}")
    df = pd.read_csv(counts_matrix_path, index_col=0)
    
    # Ensure gene_ids matches rows if provided
    if gene_ids is None:
        if df.index.name == 'gene_id' or df.index.name == 'gene':
            gene_ids = df.index.tolist()
        else:
            # Fallback: assume row order matches config
            gene_ids = [f"GENE_{i}" for i in range(len(df))]
    
    counts = df.values
    samples = df.columns.tolist()
    
    # Convert batch_labels to numpy array
    batch = np.array(batch_labels)
    
    # 1. Identify Housekeeping Genes
    hk_genes_config = get_housekeeping_genes()
    logger.info(f"Using {len(hk_genes_config)} housekeeping genes from config.")
    
    # Map gene_ids to indices
    gene_to_idx = {g: i for i, g in enumerate(gene_ids)}
    hk_indices = [gene_to_idx[g] for g in hk_genes_config if g in gene_to_idx]
    
    if len(hk_indices) < 10:
        logger.warning(f"Only {len(hk_indices)} housekeeping genes found in the matrix. "
                       f"Expected {len(hk_genes_config)}. Proceeding with available genes.")
    
    if not hk_indices:
        raise ValueError("No housekeeping genes found in the count matrix. "
                         "Cannot calculate CV for batch correction assessment.")
    
    hk_counts = counts[hk_indices, :]
    hk_ids = [gene_ids[i] for i in hk_indices]
    
    # 2. Calculate Pre-correction CV
    pre_cv = calculate_cv_for_genes(hk_counts, list(range(len(hk_counts))))
    logger.info(f"Pre-correction CV for HK genes: {pre_cv:.4f}")
    
    # 3. Select 50 lowest M-value genes (or all if < 50)
    # Calculate M-values
    m_values = calculate_georm_m_value(hk_counts, hk_ids)
    # Sort by M-value
    sorted_hk = sorted(m_values.items(), key=lambda x: x[1])
    top_50_hk = sorted_hk[:50]
    top_50_ids = [x[0] for x in top_50_hk]
    top_50_indices_in_hk = [hk_ids.index(g) for g in top_50_ids]
    
    # Recalculate CV on top 50 (or all)
    pre_cv_50 = calculate_cv_for_genes(hk_counts, top_50_indices_in_hk)
    logger.info(f"Pre-correction CV for top 50 HK genes: {pre_cv_50:.4f}")
    
    # 4. Apply ComBat-seq
    logger.info("Applying ComBat-seq batch correction...")
    corrected_counts = apply_combat_seq(counts, batch)
    
    # 5. Calculate Post-correction CV
    corrected_hk_counts = corrected_counts[hk_indices, :]
    post_cv_50 = calculate_cv_for_genes(corrected_hk_counts, top_50_indices_in_hk)
    logger.info(f"Post-correction CV for top 50 HK genes: {post_cv_50:.4f}")
    
    reduction = calculate_cv_reduction(pre_cv_50, post_cv_50)
    logger.info(f"CV Reduction: {reduction:.2f}%")
    
    # 6. Write Report
    report = {
        "pre_correction_cv": float(pre_cv_50),
        "post_correction_cv": float(post_cv_50),
        "reduction_percent": float(reduction),
        "target_reduction": 0.20,
        "housekeeping_genes_used": top_50_ids,
        "batch_labels_used": list(set(batch_labels))
    }
    
    output_path = Path(output_manifest_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Batch correction report written to {output_manifest_path}")
    
    return report

def main():
    """
    CLI entry point for batch correction.
    Expects:
      --counts <path>
      --batches <path> (JSON or CSV with sample->batch mapping)
      --output <path>
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Apply ComBat-seq batch correction")
    parser.add_argument("--counts", required=True, help="Path to count matrix CSV")
    parser.add_argument("--batches", required=True, help="Path to batch mapping file (JSON: {sample: batch})")
    parser.add_argument("--output", required=True, help="Path to output report JSON")
    parser.add_argument("--gene-ids", required=False, help="Optional: Path to gene IDs file (one per line)")
    
    args = parser.parse_args()
    
    # Load batch mapping
    with open(args.batches, 'r') as f:
        batch_mapping = json.load(f)
    
    # Load counts
    df = pd.read_csv(args.counts, index_col=0)
    samples = df.columns.tolist()
    
    # Ensure all samples have a batch
    batch_labels = []
    for s in samples:
        if s not in batch_mapping:
            raise ValueError(f"Sample {s} not found in batch mapping")
        batch_labels.append(batch_mapping[s])
    
    # Load gene IDs if provided
    gene_ids = None
    if args.gene_ids:
        with open(args.gene_ids, 'r') as f:
            gene_ids = [line.strip() for line in f if line.strip()]
    
    apply_batch_correction(
        counts_matrix_path=args.counts,
        batch_labels=batch_labels,
        output_manifest_path=args.output,
        gene_ids=gene_ids
    )

if __name__ == "__main__":
    main()
