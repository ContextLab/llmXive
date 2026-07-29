import os
import sys
import logging
import hashlib
import json
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

import numpy as np
import pandas as pd

from config import Config

logger = logging.getLogger(__name__)

class PreprocessingError(Exception):
    """Custom exception for preprocessing errors."""
    pass

def load_count_matrix(accession: str, data_dir: Path) -> pd.DataFrame:
    """
    Load the raw count matrix for a given GEO accession.
    Expects files in data/raw/<accession>/
    """
    accession_dir = data_dir / accession
    if not accession_dir.exists():
        raise PreprocessingError(f"Directory for accession {accession} not found: {accession_dir}")

    # Look for common count matrix file extensions
    possible_files = list(accession_dir.glob("*.csv")) + list(accession_dir.glob("*.tsv")) + list(accession_dir.glob("*.mtx"))
    
    if not possible_files:
        raise PreprocessingError(f"No count matrix file found in {accession_dir}")

    # Prefer the largest file if multiple exist (likely the full matrix)
    count_file = max(possible_files, key=lambda p: p.stat().st_size)
    
    logger.info(f"Loading count matrix from {count_file}")
    
    if count_file.suffix == '.mtx':
        # Handle Matrix Market format if necessary, though CSV/TSV is preferred for simplicity here
        # For this implementation, we assume CSV/TSV as per common GEO submissions after parsing
        raise PreprocessingError("Matrix Market (.mtx) format not fully supported in this simplified loader. Please use CSV/TSV.")
    
    try:
        df = pd.read_csv(count_file, index_col=0)
    except Exception as e:
        try:
            df = pd.read_csv(count_file, sep='\t', index_col=0)
        except Exception as e2:
            raise PreprocessingError(f"Failed to parse count matrix {count_file}: {e2}")

    if df.empty:
        raise PreprocessingError(f"Count matrix for {accession} is empty.")

    # Ensure numeric data
    numeric_df = df.apply(pd.to_numeric, errors='coerce')
    if numeric_df.isnull().any().any():
        logger.warning(f"Non-numeric values found in {count_file}, filling with 0.")
        numeric_df = numeric_df.fillna(0)
    
    return numeric_df

def filter_low_expr_genes(df: pd.DataFrame, threshold_percent: float = 5.0) -> pd.DataFrame:
    """
    Filter out genes that are expressed in less than `threshold_percent` of cells.
    Expressed is defined as count > 0.
    """
    if df.empty:
        raise PreprocessingError("Input dataframe is empty.")

    total_cells = df.shape[0]
    min_cells = int(np.ceil(total_cells * (threshold_percent / 100.0)))
    
    # Calculate number of cells where gene count > 0
    # Assuming rows are genes, columns are cells (standard for many GEO matrices)
    # If rows are cells, columns are genes, we need to transpose logic.
    # Standard assumption for GEO count matrices often: Rows = Genes, Cols = Cells
    # Let's check shape. If rows < cols, likely Genes x Cells.
    # If rows > cols, likely Cells x Genes.
    # However, the task description implies "filter genes <5% cells".
    # Let's assume Rows=Genes, Cols=Cells for this specific logic unless transposed.
    
    # To be safe, let's detect orientation.
    # Heuristic: Gene names are usually specific strings, Cell barcodes are hex-like.
    # But for numeric matrices, we rely on shape or config.
    # Let's assume standard: Rows=Genes, Cols=Cells.
    
    gene_counts = (df > 0).sum(axis=1)
    mask = gene_counts >= min_cells
    
    filtered_df = df[mask]
    
    removed_count = df.shape[0] - filtered_df.shape[0]
    logger.info(f"Filtered {removed_count} genes expressed in < {threshold_percent}% of cells. "
                f"Remaining: {filtered_df.shape[0]} genes.")
    
    return filtered_df

def calculate_variance_stabilized_variance(df: pd.DataFrame) -> pd.Series:
    """
    Calculate variance of log-counts for HVG selection.
    Uses log1p (log(1 + x)) to handle zeros.
    """
    log_counts = np.log1p(df)
    return log_counts.var(axis=1)

def detect_elbow_knee(variance_series: pd.Series) -> Tuple[int, float]:
    """
    Detect the elbow/knee point in the variance vs rank plot to identify HVGs.
    Returns the index of the elbow and the variance at that point.
    Uses a simple geometric approach (distance from line connecting start and end).
    """
    if len(variance_series) < 3:
        return len(variance_series), variance_series.max()

    sorted_vars = variance_series.sort_values(ascending=False)
    x = np.arange(len(sorted_vars))
    y = sorted_vars.values

    # Line from (0, y[0]) to (n-1, y[-1])
    p1 = np.array([0, y[0]])
    p2 = np.array([len(x)-1, y[-1]])
    
    # Vector from p1 to p2
    line_vec = p2 - p1
    line_len = np.linalg.norm(line_vec)
    
    if line_len == 0:
        return 0, y[0]

    # Normalize line vector
    line_vec_norm = line_vec / line_len

    # Calculate distance of each point from the line
    max_dist = -1
    elbow_idx = 0
    
    for i, (xi, yi) in enumerate(zip(x, y)):
        p = np.array([xi, yi])
        vec_to_p = p - p1
        # Project onto line
        proj_len = np.dot(vec_to_p, line_vec_norm)
        # Closest point on line
        closest = p1 + proj_len * line_vec_norm
        # Distance
        dist = np.linalg.norm(p - closest)
        
        if dist > max_dist:
            max_dist = dist
            elbow_idx = i

    return elbow_idx, sorted_vars.iloc[elbow_idx]

def select_hvgs(df: pd.DataFrame, top_n: Optional[int] = None, elbow_factor: float = 1.5) -> pd.DataFrame:
    """
    Select Highly Variable Genes (HVGs).
    If top_n is provided, select top_n genes.
    Otherwise, use elbow detection to select genes above the knee.
    """
    if df.empty:
        raise PreprocessingError("Input dataframe is empty.")

    variances = calculate_variance_stabilized_variance(df)
    elbow_idx, elbow_val = detect_elbow_knee(variances)
    
    # Sort genes by variance descending
    sorted_genes = variances.sort_values(ascending=False)
    
    if top_n:
        selected_genes = sorted_genes.head(top_n).index
        logger.info(f"Selected top {top_n} HVGs by variance.")
    else:
        # Select genes with variance significantly above the elbow
        # Heuristic: variance > elbow_val * elbow_factor
        threshold = elbow_val * elbow_factor
        selected_genes = sorted_genes[sorted_genes >= threshold].index
        
        # Fallback if too few or too many
        if len(selected_genes) < 10:
            logger.warning(f"Elbow method selected only {len(selected_genes)} genes. Using top 2000.")
            selected_genes = sorted_genes.head(2000).index
        elif len(selected_genes) > 5000:
            logger.warning(f"Elbow method selected {len(selected_genes)} genes. Capping at 5000.")
            selected_genes = sorted_genes.head(5000).index
        
        logger.info(f"Selected {len(selected_genes)} HVGs using elbow method (threshold={threshold:.4f}).")

    return df.loc[selected_genes]

def deterministic_sample_cells(df: pd.DataFrame, max_cells: int = 10000, seed: int = 42) -> pd.DataFrame:
    """
    Deterministically sample cells if the dataset exceeds max_cells.
    Uses a hash of the accession or a provided seed to ensure reproducibility.
    """
    n_cells = df.shape[1] # Assuming Cols=Cells
    
    if n_cells <= max_cells:
        logger.info(f"Dataset has {n_cells} cells (<= {max_cells}). No sampling needed.")
        return df

    logger.info(f"Dataset has {n_cells} cells. Sampling to {max_cells} cells deterministically.")
    
    # Create a deterministic seed based on the data or a fixed one if not provided
    # Here we use the provided seed, but in a real pipeline, we might hash the accession
    rng = np.random.RandomState(seed)
    
    # Get indices of cells to keep
    cell_indices = rng.choice(n_cells, size=max_cells, replace=False)
    
    # Sort indices to maintain consistent order
    cell_indices = np.sort(cell_indices)
    
    sampled_df = df.iloc[:, cell_indices]
    logger.info(f"Sampled {max_cells} cells. New shape: {sampled_df.shape}")
    
    return sampled_df

def run_preprocessing(accession: str, config: Config) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Run the full preprocessing pipeline for a given accession.
    1. Load counts
    2. Filter low expression genes
    3. (Optional) Sample cells if too large
    4. Select HVGs
    5. Validate gene count
    
    Returns:
        Tuple of (processed_df, metadata_dict)
    """
    logger.info(f"Starting preprocessing for {accession}")
    
    # 1. Load
    raw_df = load_count_matrix(accession, config.DATA_RAW_DIR)
    logger.info(f"Loaded raw matrix: {raw_df.shape}")
    
    # 2. Filter low expression genes
    filtered_df = filter_low_expr_genes(raw_df, threshold_percent=config.GENE_FILTER_PERCENT)
    
    # 3. Validate gene count AFTER filtering
    # T016 Requirement: Flag datasets with insufficient genes after filtering and skip them
    if filtered_df.shape[0] < config.MIN_GENES_THRESHOLD:
        raise PreprocessingError(
            f"Insufficient genes after filtering for {accession}. "
            f"Found {filtered_df.shape[0]} genes, threshold is {config.MIN_GENES_THRESHOLD}. "
            f"Skipping this dataset."
        )
    
    # 4. Sample cells if needed
    sampled_df = deterministic_sample_cells(filtered_df, max_cells=config.MAX_CELLS, seed=hash(accession) % (2**32))
    
    # 5. Select HVGs
    hvgs_df = select_hvgs(sampled_df, top_n=config.HVG_TOP_N)
    
    metadata = {
        "accession": accession,
        "original_shape": raw_df.shape,
        "after_gene_filter": filtered_df.shape,
        "after_sampling": sampled_df.shape,
        "hvg_count": hvgs_df.shape[0],
        "status": "success"
    }
    
    logger.info(f"Preprocessing complete for {accession}. Final shape: {hvgs_df.shape}")
    return hvgs_df, metadata

def main():
    """
    Entry point for preprocessing script.
    Expects accession as command line argument or reads from config.
    """
    logging.basicConfig(level=logging.INFO)
    config = Config()
    
    # If running as script, allow specifying accession
    if len(sys.argv) > 1:
        accession = sys.argv[1]
    else:
        # Default to first available in config if running standalone without args
        # In real pipeline, this is called by Snakemake or main.py
        accession = config.DATASETS[0] if config.DATASETS else None
    
    if not accession:
        logger.error("No accession provided.")
        sys.exit(1)
    
    try:
        result_df, meta = run_preprocessing(accession, config)
        print(json.dumps(meta, indent=2))
        # Save to processed dir
        output_path = config.DATA_PROCESSED_DIR / f"{accession}_processed.h5ad"
        # Try to save as CSV if h5ad is not available or for simplicity
        csv_path = config.DATA_PROCESSED_DIR / f"{accession}_processed.csv"
        result_df.to_csv(csv_path)
        logger.info(f"Saved processed data to {csv_path}")
    except PreprocessingError as e:
        logger.error(f"Preprocessing failed for {accession}: {e}")
        # Re-raise to let the caller (Snakemake/main.py) handle the skip/abort logic
        raise

if __name__ == "__main__":
    main()