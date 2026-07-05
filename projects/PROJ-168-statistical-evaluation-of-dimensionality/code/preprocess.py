"""
Preprocessing module for scRNA-seq data.

Implements:
1. Quality Control: Filter genes expressed in <5% of cells.
2. HVG Selection: Select top variable genes.
3. Deterministic Sampling: Hash-based sampling if cell count > 10,000.
"""
import os
import sys
import hashlib
import logging
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.feature_selection import variance_threshold
from sklearn.preprocessing import normalize

# Import project configuration
from config import (
    ensure_paths,
    set_global_seed,
    get_accession_seed,
    set_case_study_mode,
    Config
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
GENE_FILTER_THRESHOLD = 0.05  # 5% of cells
MAX_CELLS = 10000
DEFAULT_N_HVGS = 2000
SEED_PREFIX = "preprocess_"

def _calculate_gene_seeds(matrix: sparse.csr_matrix, accession: str) -> np.ndarray:
    """
    Calculate a deterministic seed for each gene based on the accession and gene index.
    This ensures that the same gene in the same dataset always gets the same seed.
    """
    n_genes = matrix.shape[0]
    seeds = np.zeros(n_genes, dtype=np.int64)
    
    for i in range(n_genes):
        # Create a unique string for this gene index
        unique_str = f"{SEED_PREFIX}{accession}_gene_{i}"
        # Hash it to get a deterministic integer
        hash_obj = hashlib.md5(unique_str.encode('utf-8'))
        seeds[i] = int(hash_obj.hexdigest(), 16) % (2**32)
        
    return seeds

def _filter_genes_by_expression(
    matrix: sparse.csr_matrix,
    threshold: float = GENE_FILTER_THRESHOLD
) -> Tuple[sparse.csr_matrix, np.ndarray]:
    """
    Filter out genes that are expressed in less than `threshold` fraction of cells.
    
    Args:
        matrix: Sparse matrix (genes x cells)
        threshold: Fraction of cells (0.0 to 1.0)
        
    Returns:
        Tuple of (filtered_matrix, boolean_mask)
    """
    n_cells = matrix.shape[1]
    min_cells = int(np.ceil(threshold * n_cells))
    
    # Calculate number of cells each gene is expressed in (non-zero entries)
    # For sparse matrix, this is sum(axis=1) > 0
    # We need to be careful with sparse matrices
    if sparse.issparse(matrix):
        # Convert to CSR if not already for efficient row operations
        if not sparse.isspmatrix_csr(matrix):
            matrix = matrix.tocsr()
        
        # Count non-zero entries per row
        gene_counts = np.diff(matrix.indptr)
    else:
        gene_counts = np.count_nonzero(matrix, axis=1)
    
    # Create mask for genes that pass the threshold
    mask = gene_counts >= min_cells
    
    logger.info(f"Filtering genes: {np.sum(~mask)} genes removed (expressed in < {threshold*100:.1f}% of cells)")
    
    return matrix[mask], mask

def _select_hvgs(
    matrix: sparse.csr_matrix,
    n_top_genes: int = DEFAULT_N_HVGS,
    accession: str = "default"
) -> Tuple[sparse.csr_matrix, np.ndarray]:
    """
    Select top highly variable genes using variance-based selection.
    
    Args:
        matrix: Sparse matrix (genes x cells), already QC filtered
        n_top_genes: Number of top HVGs to select
        accession: Accession ID for deterministic seeding
        
    Returns:
        Tuple of (filtered_matrix, boolean_mask)
    """
    if sparse.issparse(matrix):
        # Convert to dense for variance calculation if memory allows
        # For very large matrices, we might need a streaming approach
        if matrix.shape[0] * matrix.shape[1] > 10**8:
            logger.warning("Matrix too large for dense conversion, using sparse variance approximation")
            # Fallback to sparse variance calculation
            mean_vals = np.array(matrix.mean(axis=1)).flatten()
            var_vals = np.array(matrix.var(axis=1)).flatten()
        else:
            dense_matrix = matrix.toarray()
            mean_vals = np.mean(dense_matrix, axis=1)
            var_vals = np.var(dense_matrix, axis=1)
    else:
        mean_vals = np.mean(matrix, axis=1)
        var_vals = np.var(matrix, axis=1)
    
    # Filter out genes with zero mean (to avoid division by zero in Fano factor)
    valid_mask = mean_vals > 0
    if not np.all(valid_mask):
        logger.info(f"Removing {np.sum(~valid_mask)} genes with zero mean")
    
    # Calculate Fano factor (variance/mean) as a simple HVG metric
    # This is a simplified version; real scRNA-seq often uses more complex normalization
    fano_factors = np.full_like(var_vals, np.nan)
    fano_factors[valid_mask] = var_vals[valid_mask] / mean_vals[valid_mask]
    
    # Get indices of top HVGs
    # We use a deterministic seed for tie-breaking if needed, though top-k is usually unique
    top_indices = np.argsort(fano_factors)[::-1][:n_top_genes]
    
    # Sort indices to ensure deterministic order
    top_indices = np.sort(top_indices)
    
    # Create boolean mask
    mask = np.zeros(matrix.shape[0], dtype=bool)
    mask[top_indices] = True
    
    logger.info(f"Selected {len(top_indices)} highly variable genes")
    
    return matrix[mask], mask

def _sample_cells_deterministic(
    matrix: sparse.csr_matrix,
    accession: str,
    max_cells: int = MAX_CELLS
) -> Tuple[sparse.csr_matrix, List[int]]:
    """
    Deterministically sample cells if count exceeds max_cells.
    Uses hash-based random state derived from accession ID.
    
    Args:
        matrix: Sparse matrix (genes x cells)
        accession: Accession ID for seeding
        max_cells: Maximum number of cells to retain
        
    Returns:
        Tuple of (sampled_matrix, list of sampled cell indices)
    """
    n_cells = matrix.shape[1]
    
    if n_cells <= max_cells:
        logger.info(f"Cell count ({n_cells}) <= max_cells ({max_cells}). No sampling needed.")
        return matrix, list(range(n_cells))
    
    # Create deterministic seed from accession
    seed_str = f"{SEED_PREFIX}{accession}"
    seed = int(hashlib.md5(seed_str.encode('utf-8')).hexdigest(), 16) % (2**32)
    
    logger.info(f"Sampling {n_cells} cells down to {max_cells} using seed {seed}")
    
    # Set random state
    rng = np.random.RandomState(seed)
    
    # Sample cell indices
    sampled_indices = rng.choice(n_cells, size=max_cells, replace=False)
    sampled_indices = np.sort(sampled_indices)  # Sort for reproducibility in downstream steps
    
    # Extract sampled columns
    if sparse.issparse(matrix):
        sampled_matrix = matrix[:, sampled_indices]
    else:
        sampled_matrix = matrix[:, sampled_indices]
    
    logger.info(f"Sampling complete. New shape: {sampled_matrix.shape}")
    
    return sampled_matrix, sampled_indices.tolist()

def preprocess_accession(
    input_path: str,
    output_path: str,
    accession: str,
    n_top_genes: int = DEFAULT_N_HVGS,
    gene_threshold: float = GENE_FILTER_THRESHOLD,
    max_cells: int = MAX_CELLS
) -> Dict[str, Any]:
    """
    Full preprocessing pipeline for a single accession.
    
    Steps:
    1. Load data
    2. Filter genes by expression threshold
    3. Select top HVGs
    4. Sample cells if necessary
    5. Save results
    
    Args:
        input_path: Path to input count matrix (CSV or TSV)
        output_path: Path to save processed matrix
        accession: Dataset accession ID
        n_top_genes: Number of HVGs to select
        gene_threshold: Fraction of cells for gene filtering
        max_cells: Maximum cells to retain
        
    Returns:
        Dictionary with processing statistics
    """
    logger.info(f"Starting preprocessing for accession: {accession}")
    
    # Ensure paths exist
    ensure_paths()
    
    # Load data
    logger.info(f"Loading data from {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Try to load as CSV/TSV
    try:
        df = pd.read_csv(input_path, sep=None, engine='python', index_col=0)
    except Exception as e:
        raise ValueError(f"Failed to load input file: {e}")
    
    # Ensure genes are rows, cells are columns
    # Check if first column looks like gene names (non-numeric)
    if df.columns[0].isdigit():
        # Transpose if cells are rows
        df = df.T
    
    # Convert to sparse matrix (genes x cells)
    matrix = sparse.csr_matrix(df.values)
    gene_names = df.index.tolist()
    cell_names = df.columns.tolist()
    
    logger.info(f"Loaded matrix: {matrix.shape[0]} genes x {matrix.shape[1]} cells")
    
    stats = {
        "accession": accession,
        "initial_genes": matrix.shape[0],
        "initial_cells": matrix.shape[1],
        "final_genes": 0,
        "final_cells": 0,
        "hvg_count": 0,
        "sampled": False
    }
    
    # Step 1: Filter genes by expression
    logger.info("Step 1: Filtering genes by expression threshold")
    matrix, gene_mask = _filter_genes_by_expression(matrix, gene_threshold)
    stats["filtered_genes"] = np.sum(gene_mask)
    
    if matrix.shape[0] == 0:
        raise ValueError(f"No genes remain after filtering for {accession}")
    
    # Step 2: Select HVGs
    logger.info("Step 2: Selecting highly variable genes")
    matrix, hvg_mask = _select_hvgs(matrix, n_top_genes, accession)
    stats["final_genes"] = matrix.shape[0]
    stats["hvg_count"] = matrix.shape[0]
    
    # Update gene names
    filtered_gene_names = [gene_names[i] for i in range(len(gene_names)) if gene_mask[i]]
    final_gene_names = [filtered_gene_names[i] for i in range(len(filtered_gene_names)) if hvg_mask[i]]
    
    # Step 3: Sample cells if necessary
    logger.info("Step 3: Checking cell count for sampling")
    matrix, sampled_indices = _sample_cells_deterministic(matrix, accession, max_cells)
    stats["final_cells"] = matrix.shape[1]
    stats["sampled"] = len(sampled_indices) < stats["initial_cells"]
    
    # Update cell names
    final_cell_names = [cell_names[i] for i in sampled_indices]
    
    # Create DataFrame for output
    output_df = pd.DataFrame(
        matrix.toarray(),
        index=final_gene_names,
        columns=final_cell_names
    )
    
    # Save to output path
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_df.to_csv(output_path)
    logger.info(f"Saved processed data to {output_path}")
    
    # Save metadata
    metadata_path = output_path.replace('.csv', '_metadata.json')
    import json
    with open(metadata_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Preprocessing complete for {accession}")
    return stats

def main():
    """
    Command-line entry point for preprocessing.
    Expects environment variables or command line args for paths.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Preprocess scRNA-seq data")
    parser.add_argument("--input", required=True, help="Input file path")
    parser.add_argument("--output", required=True, help="Output file path")
    parser.add_argument("--accession", required=True, help="Dataset accession ID")
    parser.add_argument("--n-hvgs", type=int, default=DEFAULT_N_HVGS, help="Number of HVGs")
    parser.add_argument("--gene-threshold", type=float, default=GENE_FILTER_THRESHOLD, help="Gene filter threshold")
    parser.add_argument("--max-cells", type=int, default=MAX_CELLS, help="Max cells to retain")
    
    args = parser.parse_args()
    
    try:
        stats = preprocess_accession(
            input_path=args.input,
            output_path=args.output,
            accession=args.accession,
            n_top_genes=args.n_hvgs,
            gene_threshold=args.gene_threshold,
            max_cells=args.max_cells
        )
        print(json.dumps(stats, indent=2))
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
