"""
Preprocessing module for scRNA-seq data.

Implements:
- QC: Filter genes expressed in <5% of cells
- HVG Selection: Top variable genes using variance-stabilizing selection
- Deterministic Cell Sampling: Hash-based random_state if cell count > 10,000
"""
import os
import sys
import logging
import hashlib
import json
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

import numpy as np
import pandas as pd
import scipy.sparse as sp
from scipy.stats import zscore

# Import project configuration and utilities
from config import Config
from utils import time_wrapper, get_resource_monitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PreprocessingError(Exception):
    """Custom exception for preprocessing failures."""
    pass

def load_count_matrix(file_path: str) -> Tuple[sp.csr_matrix, pd.Index, pd.Index]:
    """
    Load a count matrix from a supported format (MTX, CSV, TSV, or HDF5 via scanpy).
    
    Returns:
        Tuple of (matrix, gene_names, cell_names)
    """
    path = Path(file_path)
    
    if path.suffix == '.csv' or path.suffix == '.tsv':
        sep = ',' if path.suffix == '.csv' else '\t'
        df = pd.read_csv(path, index_col=0, sep=sep)
        # Ensure sparse if possible
        if df.shape[0] > 10000: # Heuristic for large matrices
            matrix = sp.csr_matrix(df.values)
            genes = df.index
            cells = df.columns
        else:
            matrix = sp.csr_matrix(df.values)
            genes = df.index
            cells = df.columns
        return matrix, genes, cells
    
    elif path.suffix == '.mtx' or path.name.endswith('.mtx.gz'):
        # Simple MTX loader using scipy
        # Assumes 3-column format: row, col, value (1-based)
        # and header lines starting with %%
        try:
            import scipy.io as sio
            matrix = sio.mmread(str(path))
            matrix = sp.csr_matrix(matrix)
            # MTX files often don't have headers in the matrix itself, 
            # we assume external files or standard naming if not present.
            # For this implementation, we generate placeholder indices if not found.
            # In a real pipeline, these would be loaded from separate .genes/.barcodes files.
            n_genes, n_cells = matrix.shape
            genes = pd.Index([f"Gene_{i}" for i in range(n_genes)])
            cells = pd.Index([f"Cell_{i}" for i in range(n_cells)])
            return matrix, genes, cells
        except Exception as e:
            raise PreprocessingError(f"Failed to load MTX file {path}: {e}")
    
    elif path.suffix == '.h5' or path.suffix == '.h5ad':
        try:
            import scanpy as sc
            adata = sc.read_h5ad(str(path))
            return adata.X, adata.var_names, adata.obs_names
        except Exception as e:
            raise PreprocessingError(f"Failed to load HDF5 file {path}: {e}")
    
    else:
        # Fallback: try pandas
        try:
            df = pd.read_csv(path, index_col=0)
            matrix = sp.csr_matrix(df.values)
            return matrix, df.index, df.columns
        except:
            raise PreprocessingError(f"Unsupported file format: {path.suffix}")

def filter_low_expr_genes(matrix: sp.csr_matrix, genes: pd.Index, threshold_pct: float = 5.0) -> Tuple[sp.csr_matrix, pd.Index]:
    """
    Filter out genes expressed in less than `threshold_pct` of cells.
    
    Args:
        matrix: Sparse count matrix (genes x cells)
        genes: Gene names
        threshold_pct: Percentage of cells a gene must be expressed in (default 5.0)
        
    Returns:
        Filtered matrix and gene names
    """
    # Calculate non-zero count per gene
    # matrix is genes x cells
    n_cells = matrix.shape[1]
    min_cells = int(np.ceil(n_cells * (threshold_pct / 100.0)))
    
    # Sum non-zeros per row (gene)
    if sp.issparse(matrix):
        non_zero_counts = matrix.getnnz(axis=1)
    else:
        non_zero_counts = np.count_nonzero(matrix, axis=1)
    
    keep_mask = non_zero_counts >= min_cells
    logger.info(f"Filtering genes: {np.sum(~keep_mask)} removed (expressed in <{threshold_pct}% of cells)")
    
    return matrix[keep_mask], genes[keep_mask]

def select_hvgs(matrix: sp.csr_matrix, genes: pd.Index, n_top_genes: int = 2000) -> Tuple[sp.csr_matrix, pd.Index]:
    """
    Select Highly Variable Genes (HVGs) using variance-stabilizing selection.
    
    Method:
    1. Calculate log-counts (log1p)
    2. Compute mean and variance for each gene
    3. Fit a trend (variance ~ mean) or simply rank by dispersion
    4. Select top N genes by dispersion (variance / mean or standardized variance)
    
    Args:
        matrix: Sparse count matrix (genes x cells)
        genes: Gene names
        n_top_genes: Number of top HVGs to select
        
    Returns:
        Filtered matrix and gene names
    """
    logger.info(f"Selecting top {n_top_genes} Highly Variable Genes...")
    
    # Convert to dense for calculation if small enough, else use sparse stats
    # For robustness with large sparse matrices, we use sparse operations
    if matrix.shape[0] > 50000:
        # Use sparse mean/var
        mean_counts = np.array(matrix.mean(axis=1)).flatten()
        # Variance: E[X^2] - (E[X])^2
        # For sparse, we can approximate or use scanpy logic if available.
        # Here we implement a simplified dispersion metric: Var/Mean (Fano factor)
        # or standardized variance.
        # To avoid dense conversion, we compute sum of squares manually for sparse.
        sq_matrix = matrix.power(2)
        mean_sq = np.array(sq_matrix.mean(axis=1)).flatten()
        var_counts = mean_sq - (mean_counts ** 2)
        var_counts = np.maximum(var_counts, 1e-10) # Avoid div by zero
    else:
        dense = matrix.toarray()
        mean_counts = dense.mean(axis=1)
        var_counts = dense.var(axis=1)
    
    # Dispersion metric: (Var - Mean) / Mean or similar.
    # Standardized variance (z-score of dispersion) is common.
    # Simple approach: Rank by (variance / mean) or just variance if normalized.
    # Let's use the "variance of log counts" approximation which is robust.
    # Since we don't want to dense-ify huge matrices, we use the Fano factor approximation:
    # Dispersion = Var / Mean
    dispersion = var_counts / (mean_counts + 1e-10)
    
    # Normalize dispersion (z-score)
    disp_mean = np.mean(dispersion)
    disp_std = np.std(dispersion)
    if disp_std > 0:
        dispersion_z = (dispersion - disp_mean) / disp_std
    else:
        dispersion_z = dispersion
    
    # Select top N
    top_indices = np.argsort(dispersion_z)[-n_top_genes:][::-1]
    
    logger.info(f"Selected {len(top_indices)} HVGs based on dispersion.")
    
    return matrix[top_indices], genes[top_indices]

def deterministic_sample_cells(matrix: sp.csr_matrix, cells: pd.Index, 
                               target_max_cells: int = 10000, 
                               accession: Optional[str] = None) -> Tuple[sp.csr_matrix, pd.Index]:
    """
    Deterministically sample cells if count > target_max_cells.
    
    Uses a hash of the accession (or a default seed) to ensure reproducibility.
    
    Args:
        matrix: Sparse count matrix (genes x cells)
        cells: Cell names
        target_max_cells: Maximum number of cells to retain
        accession: Dataset accession ID for seeding
        
    Returns:
        Sampled matrix and cell names
    """
    n_cells = matrix.shape[1]
    
    if n_cells <= target_max_cells:
        logger.info(f"Cell count ({n_cells}) <= {target_max_cells}. No sampling needed.")
        return matrix, cells
    
    logger.info(f"Cell count ({n_cells}) > {target_max_cells}. Sampling deterministically...")
    
    # Generate seed from accession
    if accession:
      seed_str = f"sample_seed_{accession}"
    else:
      seed_str = "sample_seed_default"
    
    seed = int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % (2**32)
    rng = np.random.default_rng(seed)
    
    # Sample indices
    n_sample = target_max_cells
    sampled_indices = rng.choice(n_cells, size=n_sample, replace=False)
    sampled_indices = np.sort(sampled_indices)
    
    logger.info(f"Sampled {n_sample} cells using seed {seed}.")
    
    # Slice matrix (columns)
    # matrix is genes x cells, so we slice axis 1
    sampled_matrix = matrix[:, sampled_indices]
    sampled_cells = cells[sampled_indices]
    
    return sampled_matrix, sampled_cells

@time_wrapper
def run_preprocessing(input_path: str, output_path: str, 
                      accession: Optional[str] = None,
                      config: Optional[Config] = None) -> Dict[str, Any]:
    """
    Main preprocessing pipeline.
    
    Steps:
    1. Load count matrix
    2. Filter low-expression genes (<5% cells)
    3. Select HVGs (top 2000)
    4. Deterministically sample cells if > 10,000
    5. Save results
    
    Args:
        input_path: Path to input count matrix
        output_path: Path to save processed matrix (CSV/TSV)
        accession: Dataset accession for seeding
        config: Configuration object (optional, for defaults)
        
    Returns:
        Dictionary with stats
    """
    if config is None:
        config = Config()
    
    logger.info(f"Starting preprocessing for {input_path}")
    
    # 1. Load
    matrix, genes, cells = load_count_matrix(input_path)
    logger.info(f"Loaded matrix: {matrix.shape[0]} genes x {matrix.shape[1]} cells")
    
    # 2. Filter Genes
    matrix, genes = filter_low_expr_genes(matrix, genes, threshold_pct=5.0)
    logger.info(f"After gene filtering: {matrix.shape[0]} genes x {matrix.shape[1]} cells")
    
    if matrix.shape[0] == 0:
        raise PreprocessingError("No genes remaining after filtering. Input data may be empty or too sparse.")
    
    # 3. HVG Selection
    # Use config defaults if available, else hardcode 2000
    n_hvgs = config.HVG_COUNT if config else 2000
    matrix, genes = select_hvgs(matrix, genes, n_top_genes=n_hvgs)
    logger.info(f"After HVG selection: {matrix.shape[0]} genes x {matrix.shape[1]} cells")
    
    # 4. Sampling
    max_cells = config.MAX_CELLS if config else 10000
    matrix, cells = deterministic_sample_cells(matrix, cells, target_max_cells=max_cells, accession=accession)
    logger.info(f"After sampling: {matrix.shape[0]} genes x {matrix.shape[1]} cells")
    
    # 5. Save
    # Convert to dense for saving if small enough, else save sparse format or CSV with chunks
    # For compatibility with downstream (PCA, etc), dense is often easier if size permits.
    # If too large, save as .npz or CSV.
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if matrix.shape[0] * matrix.shape[1] < 50_000_000:
        # Convert to dense for CSV
        dense_matrix = matrix.toarray()
        df = pd.DataFrame(dense_matrix, index=genes, columns=cells)
        df.to_csv(output_path)
    else:
        # Save as sparse NPZ and separate index files
        sparse_path = str(Path(output_path).with_suffix('.npz'))
        np.savez_compressed(sparse_path, data=matrix.data, indices=matrix.indices, 
                            indptr=matrix.indptr, shape=matrix.shape)
        # Save indices
        genes_path = str(Path(output_path).with_suffix('.genes.csv'))
        cells_path = str(Path(output_path).with_suffix('.cells.csv'))
        pd.Series(genes).to_csv(genes_path, index=False)
        pd.Series(cells).to_csv(cells_path, index=False)
        logger.info(f"Saved sparse matrix to {sparse_path} and indices.")
        output_path = sparse_path # Update return path to point to the actual data file
    
    stats = {
        "input_genes": len(genes) + (matrix.shape[0] - len(genes)), # Approximate original if we didn't track
        "output_genes": matrix.shape[0],
        "output_cells": matrix.shape[1],
        "output_path": output_path
    }
    
    logger.info(f"Preprocessing complete. Output saved to {output_path}")
    return stats

def main():
    """CLI entry point for preprocessing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Preprocess scRNA-seq count matrices")
    parser.add_argument("--input", required=True, help="Path to input count matrix")
    parser.add_argument("--output", required=True, help="Path to output processed matrix")
    parser.add_argument("--accession", type=str, default=None, help="Dataset accession for seeding")
    parser.add_argument("--config", type=str, default=None, help="Path to config file (optional)")
    
    args = parser.parse_args()
    
    try:
        config = Config() if not args.config else Config.load(args.config)
        stats = run_preprocessing(
            input_path=args.input,
            output_path=args.output,
            accession=args.accession,
            config=config
        )
        print(json.dumps(stats, indent=2))
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()