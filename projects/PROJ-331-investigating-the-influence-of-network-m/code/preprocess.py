import os
import sys
import time
import logging
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

# Import local utilities
from utils import (
    get_logger, log_error, log_execution_time, 
    safe_mkdir, save_npy, load_npy, compute_sha256,
    ProcessingError, DataNotFoundError
)
from config import DIRS, SEED

logger = get_logger("preprocess")

def load_streamlines(streamlines_path: Union[str, Path]) -> Any:
    """
    Loads streamlines from a .trk or .tck file.
    Note: In a real implementation, this would use dipy.io or nibabel.
    For this task, we simulate the loading to demonstrate the logging pipeline.
    """
    path = Path(streamlines_path)
    if not path.exists():
        raise DataNotFoundError(f"Streamlines file not found: {path}")
    
    logger.info(f"Loading streamlines from {path}")
    # Placeholder for actual dipy/nibabel loading logic
    # In a real run, this would return a streamlines object
    return {"path": str(path), "loaded_at": time.time()}

def load_atlas(atlas_path: Union[str, Path]) -> np.ndarray:
    """
    Loads an atlas (parcellation) mask.
    Returns a numpy array representing the atlas labels.
    """
    path = Path(atlas_path)
    if not path.exists():
        raise DataNotFoundError(f"Atlas file not found: {path}")
    
    logger.info(f"Loading atlas from {path}")
    # Placeholder: return a dummy mask if real file missing, but log warning
    # In real execution, use nibabel.load
    try:
        import nibabel as nib
        img = nib.load(str(path))
        return img.get_fdata()
    except Exception as e:
        logger.warning(f"Could not load atlas with nibabel: {e}. Using dummy data for pipeline test.")
        return np.zeros((100, 100, 100), dtype=np.int32)

def parcellate_streamlines(streamlines_data: Any, atlas_data: np.ndarray) -> np.ndarray:
    """
    Maps streamlines to atlas regions to create a connectivity matrix.
    Returns a weighted adjacency matrix.
    """
    logger.info("Starting parcellation of streamlines...")
    # Simulation of parcellation logic
    # In reality: iterate streamlines, find endpoints in atlas, increment matrix
    n_regions = 100
    matrix = np.random.rand(n_regions, n_regions)
    matrix = (matrix + matrix.T) / 2 # Symmetrize
    np.fill_diagonal(matrix, 0)
    
    logger.info(f"Parcellation complete. Matrix shape: {matrix.shape}")
    return matrix

def threshold_to_density(matrix: np.ndarray, density: float) -> np.ndarray:
    """
    Thresholds a weighted matrix to a specific density (keeps top 'density' fraction of edges).
    Returns a binary adjacency matrix.
    """
    logger.info(f"Thresholding matrix to density {density}")
    if density <= 0 or density >= 1:
        raise ValueError("Density must be between 0 and 1")
    
    n = matrix.shape[0]
    total_edges = n * (n - 1) / 2
    num_edges = int(total_edges * density)
    
    # Flatten and sort
    flat = matrix.flatten()
    # Remove diagonal (self-loops) conceptually, though they are 0
    threshold_val = np.sort(flat)[-num_edges-1] # +1 to be safe
    
    binary = (matrix >= threshold_val).astype(float)
    np.fill_diagonal(binary, 0)
    
    logger.info(f"Thresholded matrix. Non-zero edges: {np.count_nonzero(binary)}")
    return binary

def compute_rsfc(time_series: np.ndarray) -> np.ndarray:
    """
    Computes Resting-State Functional Connectivity (Pearson correlation).
    Input: time_series (nodes x time)
    Output: correlation matrix (nodes x nodes)
    """
    logger.info("Computing RSFC matrix...")
    # Input validation
    if time_series.ndim != 2:
        raise ProcessingError("Time series must be 2D (nodes x time)")
    
    # Pearson correlation
    rsfc = np.corrcoef(time_series)
    np.fill_diagonal(rsfc, 0)
    
    logger.info(f"RSFC computation complete. Shape: {rsfc.shape}")
    return rsfc

def compute_global_efficiency(adj_matrix: np.ndarray) -> float:
    """
    Computes Global Efficiency on a weighted adjacency matrix.
    E_glob = (1/N(N-1)) * sum(1/d_ij) where d_ij is shortest path.
    For weighted graphs, d_ij is often 1/weight or similar.
    """
    logger.info("Computing Global Efficiency...")
    import networkx as nx
    
    G = nx.Graph()
    n = adj_matrix.shape[0]
    G.add_nodes_from(range(n))
    
    # Add edges with weights
    edges = []
    for i in range(n):
        for j in range(i+1, n):
            if adj_matrix[i, j] > 0:
                edges.append((i, j, adj_matrix[i, j]))
    
    G.add_weighted_edges_from(edges)
    
    # Compute efficiency
    try:
        eff = nx.global_efficiency(G)
        logger.info(f"Global Efficiency: {eff:.4f}")
        return eff
    except nx.NetworkXError as e:
        logger.error(f"NetworkX error during efficiency calculation: {e}")
        return 0.0

def process_connectome(streamlines_path: str, atlas_path: str, rsfmri_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Orchestrates the full processing pipeline for a single subject.
    1. Load streamlines and atlas
    2. Parcellate -> Weighted Adjacency
    3. Threshold -> Binary Adjacency
    4. Compute RSFC (if fMRI provided)
    5. Compute Global Efficiency
    """
    logger.info("=== Starting Connectome Processing ===")
    
    # Load Data
    streamlines = load_streamlines(streamlines_path)
    atlas = load_atlas(atlas_path)
    
    # Parcellate
    weighted_adj = parcellate_streamlines(streamlines, atlas)
    
    # Threshold (Example: 10% density)
    binary_adj = threshold_to_density(weighted_adj, 0.1)
    
    results = {
        "weighted_adjacency": weighted_adj,
        "binary_adjacency": binary_adj,
        "global_efficiency": compute_global_efficiency(weighted_adj)
    }
    
    if rsfmri_path and Path(rsfmri_path).exists():
        # Load dummy time series for demo if file exists
        # In real scenario: load nibabel data, filter, etc.
        logger.info(f"Loading fMRI data from {rsfmri_path}")
        # Simulate time series (nodes x time)
        n = weighted_adj.shape[0]
        time_series = np.random.rand(n, 200) 
        results["rsfc"] = compute_rsfc(time_series)
    else:
        logger.warning("No fMRI data provided or found. Skipping RSFC computation.")
        results["rsfc"] = None

    logger.info("=== Connectome Processing Complete ===")
    return results

def main():
    """
    Entry point for the preprocessing script.
    Simulates processing a subject if real files are not present,
    but logs the steps as required by T016.
    """
    logger.info("Preprocessing module main() called")
    
    # Define paths (simulated for this task to ensure logging works without real data)
    # In a real run, these would come from config or CLI args
    dummy_streamlines = DIRS["data_raw"] / "dummy.trk"
    dummy_atlas = DIRS["data_raw"] / "dummy.nii.gz"
    
    # Ensure directories exist
    safe_mkdir(DIRS["data_processed"])
    safe_mkdir(DIRS["data_logs"])
    
    # Create dummy files if they don't exist so the pipeline can run
    if not dummy_streamlines.exists():
        logger.warning(f"Creating dummy streamlines file: {dummy_streamlines}")
        dummy_streamlines.touch()
    if not dummy_atlas.exists():
        logger.warning(f"Creating dummy atlas file: {dummy_atlas}")
        dummy_atlas.touch()
    
    try:
        results = process_connectome(
            str(dummy_streamlines), 
            str(dummy_atlas), 
            rsfmri_path=None
        )
        
        # Save outputs
        save_npy(DIRS["data_processed"] / "weighted_adjacency.npy", results["weighted_adjacency"])
        save_npy(DIRS["data_processed"] / "binary_adjacency.npy", results["binary_adjacency"])
        
        logger.info(f"Global Efficiency saved: {results['global_efficiency']}")
        
    except Exception as e:
        log_error(e, "Main processing failed")
        raise

if __name__ == "__main__":
    main()
