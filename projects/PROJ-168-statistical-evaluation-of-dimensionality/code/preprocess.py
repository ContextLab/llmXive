import os
import sys
import logging
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union
import numpy as np
import pandas as pd
import scipy.sparse as sp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PreprocessingError(Exception):
    """Custom exception for preprocessing errors."""
    pass

def load_count_matrix(file_path: str) -> sp.csr_matrix:
    """
    Load a count matrix from a file (supports .mtx, .csv, .tsv, .h5ad).
    
    Args:
        file_path: Path to the count matrix file.
        
    Returns:
        A sparse CSR matrix of counts.
        
    Raises:
        PreprocessingError: If the file format is unsupported or loading fails.
    """
    path = Path(file_path)
    if not path.exists():
        raise PreprocessingError(f"File not found: {file_path}")
    
    suffix = path.suffix.lower()
    
    try:
        if suffix == '.mtx' or suffix == '.mtx.gz':
            # Load Matrix Market format
            # Matrix Market usually stores data in COO format
            mtx = sp.load_npz(file_path) if suffix == '.npy' else sp.io.mmread(str(path))
            if not isinstance(mtx, sp.coo_matrix):
                mtx = sp.coo_matrix(mtx)
            return sp.csr_matrix(mtx)
        
        elif suffix in ['.csv', '.tsv']:
            # Load CSV/TSV
            sep = ',' if suffix == '.csv' else '\t'
            df = pd.read_csv(path, sep=sep, index_col=0)
            # Ensure numeric
            df = df.apply(pd.to_numeric, errors='coerce').fillna(0)
            return sp.csr_matrix(df.values)
        
        elif suffix == '.h5ad':
            import anndata
            adata = anndata.read_h5ad(str(path))
            return sp.csr_matrix(adata.X)
        
        else:
            raise PreprocessingError(f"Unsupported file format: {suffix}")
    except Exception as e:
        raise PreprocessingError(f"Failed to load count matrix from {file_path}: {str(e)}")

def filter_low_expr_genes(count_matrix: sp.csr_matrix, min_pct: float = 0.05) -> Tuple[sp.csr_matrix, np.ndarray]:
    """
    Filter out genes that are expressed in less than `min_pct` of cells.
    
    Args:
        count_matrix: Sparse CSR matrix of shape (n_cells, n_genes).
        min_pct: Minimum percentage of cells a gene must be expressed in (0.0 to 1.0).
        
    Returns:
        Tuple of (filtered_matrix, gene_mask) where gene_mask is a boolean array.
    """
    if count_matrix.shape[0] == 0 or count_matrix.shape[1] == 0:
        raise PreprocessingError("Empty matrix provided to filter_low_expr_genes")
    
    n_cells = count_matrix.shape[0]
    threshold = int(np.ceil(n_cells * min_pct))
    
    # Calculate number of non-zero entries per gene (column)
    # Since matrix is (cells, genes), we sum along axis 0
    non_zero_counts = (count_matrix > 0).sum(axis=0)
    
    # Flatten the result (it comes as a matrix)
    if hasattr(non_zero_counts, 'A1'):
        non_zero_counts = non_zero_counts.A1
    else:
        non_zero_counts = np.asarray(non_zero_counts).flatten()
    
    gene_mask = non_zero_counts >= threshold
    
    filtered_matrix = count_matrix[:, gene_mask]
    
    logger.info(f"Filtered genes: kept {gene_mask.sum()} of {len(gene_mask)} genes "
                f"(expressed in >= {min_pct*100}% of cells)")
                
    return filtered_matrix, gene_mask

def calculate_variance_stabilized_variance(count_matrix: sp.csr_matrix) -> np.ndarray:
    """
    Calculate variance of log-counts (variance-stabilized) for each gene.
    Uses log1p transformation to handle zeros.
    
    Args:
        count_matrix: Sparse CSR matrix of shape (n_cells, n_genes).
        
    Returns:
        Array of variances for each gene.
    """
    # Convert to dense for log calculation if sparse operations are too complex
    # or use log1p on sparse if supported (scipy sparse doesn't support log directly)
    # For large matrices, we might need to iterate or use a dense intermediate if memory allows.
    # Given the sampling constraint later, we assume this runs on a manageable size or we convert.
    
    # Efficient approach: convert to dense if it fits, otherwise chunk.
    # For now, assuming the matrix is pre-sampled or small enough for this step,
    # or we rely on the fact that we only need variance of log(count+1).
    
    # To avoid OOM on huge matrices before sampling, we convert to dense only if necessary
    # or use a sparse-aware variance calculation.
    # Here we convert to dense for the log step as log is not element-wise on sparse in scipy.
    # If the matrix is too large, the caller should sample first.
    
    try:
        dense_matrix = count_matrix.toarray()
    except MemoryError:
        raise PreprocessingError("Matrix too large for variance calculation. Please sample first.")
    
    log_counts = np.log1p(dense_matrix)
    variances = np.var(log_counts, axis=0)
    
    return variances

def detect_elbow_knee(variances: np.ndarray) -> int:
    """
    Detect the elbow/knee point in the sorted variance plot to select HVGs.
    Uses the 'knee' detection algorithm (distance from line connecting endpoints).
    
    Args:
        variances: Array of variances for each gene.
        
    Returns:
        Index of the elbow point (number of HVGs to keep).
    """
    # Sort variances in descending order
    sorted_indices = np.argsort(variances)[::-1]
    sorted_variances = variances[sorted_indices]
    
    n = len(sorted_variances)
    if n == 0:
        return 0
    if n <= 2:
        return n
        
    # Normalize to [0, 1] for both axes
    x = np.arange(n)
    y = sorted_variances
    
    # Normalize
    x_norm = (x - x.min()) / (x.max() - x.min() + 1e-8)
    y_norm = (y - y.min()) / (y.max() - y.min() + 1e-8)
    
    # Line from (0, 1) to (1, 0) in normalized space?
    # Actually, we want the point farthest from the line connecting (0, y_max) and (n-1, y_min)
    # In normalized space: (0, 1) to (1, 0)
    
    # Vector from (0,1) to (1,0)
    line_vec = np.array([1, -1])
    line_len = np.sqrt(2)
    
    max_dist = -1
    elbow_idx = 0
    
    for i in range(n):
        # Point (x_norm[i], y_norm[i])
        # Vector from (0,1) to point
        point_vec = np.array([x_norm[i], y_norm[i] - 1])
        
        # Distance from point to line
        # Cross product magnitude / length of line vector
        cross = abs(line_vec[0] * point_vec[1] - line_vec[1] * point_vec[0])
        dist = cross / line_len
        
        if dist > max_dist:
            max_dist = dist
            elbow_idx = i
            
    logger.info(f"Detected elbow at index {elbow_idx} with distance {max_dist:.4f}")
    return elbow_idx + 1  # +1 because index is 0-based, we want count

def select_hvgs(count_matrix: sp.csr_matrix, min_pct: float = 0.05, 
                max_hvgs: Optional[int] = None) -> Tuple[sp.csr_matrix, np.ndarray]:
    """
    Select Highly Variable Genes (HVGs) using variance-stabilizing selection.
    
    1. Filter low expression genes.
    2. Calculate variance of log-counts.
    3. Detect elbow point.
    4. Select top N genes.
    
    Args:
        count_matrix: Sparse CSR matrix.
        min_pct: Minimum percentage of cells for gene filtering.
        max_hvgs: Maximum number of HVGs to select. If None, uses elbow detection.
        
    Returns:
        Tuple of (HVG_matrix, hvg_mask).
    """
    # Step 1: Filter low expression
    filtered_matrix, gene_mask = filter_low_expr_genes(count_matrix, min_pct)
    
    if filtered_matrix.shape[1] == 0:
        raise PreprocessingError("No genes passed the low expression filter.")
    
    # Step 2: Calculate variance
    variances = calculate_variance_stabilized_variance(filtered_matrix)
    
    # Step 3: Select top genes
    if max_hvgs is not None:
        # Use fixed count
        n_select = min(max_hvgs, len(variances))
        top_indices = np.argsort(variances)[::-1][:n_select]
    else:
        # Use elbow detection
        n_select = detect_elbow_knee(variances)
        n_select = min(n_select, len(variances))
        top_indices = np.argsort(variances)[::-1][:n_select]
    
    # Create mask for the filtered matrix
    hvg_mask_filtered = np.zeros(len(variances), dtype=bool)
    hvg_mask_filtered[top_indices] = True
    
    # Map back to original gene mask
    # We need to reconstruct the full mask for the original matrix
    full_hvg_mask = np.zeros(gene_mask.shape[0], dtype=bool)
    original_indices = np.where(gene_mask)[0]
    full_hvg_mask[original_indices[top_indices]] = True
    
    hvg_matrix = count_matrix[:, full_hvg_mask]
    
    logger.info(f"Selected {n_select} HVGs out of {gene_mask.sum()} filtered genes")
    
    return hvg_matrix, full_hvg_mask

def deterministic_sample_cells(count_matrix: sp.csr_matrix, accession: str, 
                               max_cells: int = 10000, seed: Optional[int] = None) -> sp.csr_matrix:
    """
    Deterministically sample cells from the count matrix if it exceeds max_cells.
    Uses a hash of the accession string to generate a reproducible random seed.
    
    Args:
        count_matrix: Sparse CSR matrix of shape (n_cells, n_genes).
        accession: GSE accession string (e.g., "GSE131907").
        max_cells: Maximum number of cells to retain.
        seed: Optional explicit seed (overrides hash).
        
    Returns:
        Sampled sparse CSR matrix.
        
    Raises:
        PreprocessingError: If matrix dimensions are invalid.
    """
    n_cells = count_matrix.shape[0]
    
    if n_cells <= max_cells:
        logger.info(f"Dataset has {n_cells} cells (<= {max_cells}). No sampling needed.")
        return count_matrix
    
    # Determine seed
    if seed is None:
        # Hash the accession string to get a deterministic integer seed
        # Use SHA256 and take first 8 bytes as int
        hash_obj = hashlib.sha256(accession.encode('utf-8'))
        hash_bytes = hash_obj.digest()[:8]
        seed = int.from_bytes(hash_bytes, byteorder='big')
    
    logger.info(f"Sampling {n_cells} cells down to {max_cells} using seed {seed} (accession: {accession})")
    
    # Generate deterministic random indices
    rng = np.random.default_rng(seed)
    sample_indices = rng.choice(n_cells, size=max_cells, replace=False)
    sample_indices.sort()
    
    # Slice the matrix
    sampled_matrix = count_matrix[sample_indices, :]
    
    logger.info(f"Sampled matrix shape: {sampled_matrix.shape}")
    return sampled_matrix

def run_preprocessing(count_matrix: sp.csr_matrix, accession: str, 
                      min_pct: float = 0.05, max_hvgs: Optional[int] = None,
                      max_cells: int = 10000) -> Dict[str, Any]:
    """
    Run the full preprocessing pipeline:
    1. Deterministic sampling (if needed).
    2. Filter low expression genes.
    3. Select HVGs.
    
    Args:
        count_matrix: Raw count matrix.
        accession: GSE accession string.
        min_pct: Minimum percentage for gene filtering.
        max_hvgs: Max HVGs to keep.
        max_cells: Max cells to keep (for sampling).
        
    Returns:
        Dictionary with processed matrix and metadata.
    """
    # Step 1: Sample cells if necessary
    sampled_matrix = deterministic_sample_cells(count_matrix, accession, max_cells)
    
    # Step 2: Filter genes and select HVGs
    hvg_matrix, hvg_mask = select_hvgs(sampled_matrix, min_pct, max_hvgs)
    
    return {
        "matrix": hvg_matrix,
        "hvg_mask": hvg_mask,
        "original_shape": count_matrix.shape,
        "sampled_shape": sampled_matrix.shape,
        "final_shape": hvg_matrix.shape,
        "accession": accession
    }

def main():
    """
    Entry point for command-line execution.
    Expects: python preprocess.py <input_path> <accession> <output_path>
    """
    if len(sys.argv) < 4:
        print("Usage: python preprocess.py <input_path> <accession> <output_path>")
        sys.exit(1)
    
    input_path = sys.argv[1]
    accession = sys.argv[2]
    output_path = sys.argv[3]
    
    try:
        logger.info(f"Loading count matrix from {input_path}")
        matrix = load_count_matrix(input_path)
        
        logger.info("Running preprocessing pipeline")
        result = run_preprocessing(matrix, accession)
        
        # Save the processed matrix (as .npz for sparse)
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        sp.save_npz(output_path, result["matrix"])
        
        # Save metadata
        meta_path = Path(output_path).with_suffix('.json')
        with open(meta_path, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        logger.info(f"Preprocessing complete. Output saved to {output_path}")
        
    except PreprocessingError as e:
        logger.error(f"Preprocessing failed: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()