"""
Preprocessing module for scRNA-seq data.
Handles QC, HVG selection, and deterministic sampling.
"""
import os
import sys
import logging
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.feature_selection import VarianceThreshold

from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PreprocessingError(Exception):
    """Raised when preprocessing fails."""
    pass

def load_count_matrix(file_path: Path) -> sparse.csr_matrix:
    """
    Loads a count matrix from a file (CSV, TSV, or MTX).
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Count matrix file not found: {file_path}")

    suffix = file_path.suffix.lower()
    
    if suffix in ['.csv', '.tsv']:
        sep = ',' if suffix == '.csv' else '\t'
        df = pd.read_csv(file_path, sep=sep, index_col=0)
        # Ensure numeric
        df = df.apply(pd.to_numeric, errors='coerce').fillna(0)
        return sparse.csr_matrix(df.values)
    elif suffix == '.mtx':
        # Simplified MTX loading - assumes standard format
        # In a real scenario, use scipy.io.mmread
        raise NotImplementedError("MTX loading requires scipy.io.mmread")
    else:
        raise ValueError(f"Unsupported file format: {suffix}")

def filter_low_expr_genes(count_matrix: sparse.csr_matrix, threshold_percent: float = 5.0) -> sparse.csr_matrix:
    """
    Filters out genes expressed in less than threshold_percent of cells.
    """
    if not isinstance(count_matrix, sparse.csr_matrix):
        count_matrix = sparse.csr_matrix(count_matrix)
    
    # Calculate number of cells with non-zero expression for each gene
    n_cells = count_matrix.shape[1]
    gene_counts = np.array(count_matrix.sum(axis=1)).flatten() > 0
    # Actually, we need to count non-zero entries per row
    gene_counts = np.diff(count_matrix.indptr) > 0
    
    # Calculate percentage
    percent = (gene_counts / n_cells) * 100
    
    # Keep genes above threshold
    keep_mask = percent >= threshold_percent
    
    logger.info(f"Filtering genes: {np.sum(~keep_mask)} genes removed (< {threshold_percent}% cells)")
    
    return count_matrix[keep_mask, :]

def calculate_variance_stabilized_variance(count_matrix: sparse.csr_matrix) -> np.ndarray:
    """
    Calculates variance-stabilized variance for HVG selection.
    Uses log-transformation to stabilize variance.
    """
    # Add pseudocount
    data = count_matrix.toarray() + 1
    log_data = np.log2(data)
    
    # Calculate variance across cells for each gene
    variances = np.var(log_data, axis=1)
    return variances

def detect_elbow_knee(variances: np.ndarray) -> int:
    """
    Detects the elbow/knee point in the sorted variance plot.
    Uses a simple knee detection algorithm based on curvature.
    """
    # Sort variances in descending order
    sorted_vars = np.sort(variances)[::-1]
    n_genes = len(sorted_vars)
    
    if n_genes < 3:
        return n_genes
    
    # Normalize to [0, 1]
    x = np.arange(n_genes) / n_genes
    y = sorted_vars / sorted_vars[0] if sorted_vars[0] > 0 else np.zeros(n_genes)
    
    # Calculate distances from the line connecting (0,1) and (1,0)
    # The point with maximum distance is the knee
    line = 1 - x
    distances = y - line
    
    knee_idx = np.argmax(distances)
    return knee_idx

def select_hvgs(count_matrix: sparse.csr_matrix, n_top: Optional[int] = None) -> sparse.csr_matrix:
    """
    Selects highly variable genes (HVGs) based on variance-stabilized variance.
    """
    variances = calculate_variance_stabilized_variance(count_matrix)
    
    if n_top is None:
        # Auto-detect using elbow method
        n_top = detect_elbow_knee(variances)
        logger.info(f"Auto-detected {n_top} HVGs using elbow method")
    else:
        logger.info(f"Selecting top {n_top} HVGs")
    
    # Get indices of top n_top genes
    top_indices = np.argsort(variances)[-n_top:]
    
    return count_matrix[top_indices, :]

def deterministic_sample_cells(count_matrix: sparse.csr_matrix, 
                               max_cells: int = 10000, 
                               accession: str = "") -> sparse.csr_matrix:
    """
    Performs deterministic sampling of cells if count exceeds max_cells.
    Uses a hash of the accession to ensure reproducibility.
    """
    n_cells = count_matrix.shape[1]
    
    if n_cells <= max_cells:
        logger.info(f"Cell count ({n_cells}) <= max_cells ({max_cells}). No sampling needed.")
        return count_matrix
    
    # Generate deterministic seed from accession
    if not accession:
        accession = "default"
    seed = int(hashlib.md5(accession.encode()).hexdigest(), 16) % (2**32)
    
    logger.info(f"Sampling cells from {n_cells} to {max_cells} using seed {seed}")
    
    # Set random state
    rng = np.random.RandomState(seed)
    
    # Sample indices
    sample_indices = rng.choice(n_cells, size=max_cells, replace=False)
    sample_indices.sort()
    
    return count_matrix[:, sample_indices]

def run_preprocessing(count_matrix: sparse.csr_matrix, 
                      accession: str, 
                      config: Config) -> Tuple[sparse.csr_matrix, Dict[str, Any]]:
    """
    Runs the full preprocessing pipeline.
    Returns the preprocessed matrix and metadata.
    """
    metadata = {
        'accession': accession,
        'original_shape': count_matrix.shape,
        'steps': []
    }
    
    # Step 1: Filter low expression genes
    logger.info("Step 1: Filtering low expression genes...")
    count_matrix = filter_low_expr_genes(count_matrix, threshold_percent=config.GENE_FILTER_PERCENT)
    metadata['steps'].append({'step': 'filter_genes', 'shape': count_matrix.shape})
    
    # Step 2: Sample cells if necessary
    logger.info("Step 2: Sampling cells if necessary...")
    count_matrix = deterministic_sample_cells(count_matrix, max_cells=config.MAX_CELLS, accession=accession)
    metadata['steps'].append({'step': 'sample_cells', 'shape': count_matrix.shape})
    
    # Step 3: Select HVGs
    logger.info("Step 3: Selecting HVGs...")
    count_matrix = select_hvgs(count_matrix, n_top=config.N_TOP_HVGS)
    metadata['steps'].append({'step': 'select_hvgs', 'shape': count_matrix.shape})
    
    logger.info(f"Preprocessing complete. Final shape: {count_matrix.shape}")
    return count_matrix, metadata

def main():
    """Main entry point for preprocessing script."""
    config = Config()
    
    # Example usage - in reality, this would be called by the workflow
    # with actual file paths
    logger.info("Preprocessing module loaded successfully.")
    return 0

if __name__ == '__main__':
    sys.exit(main())