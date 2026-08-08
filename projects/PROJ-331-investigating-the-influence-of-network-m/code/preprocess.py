import os
import sys
import time
import logging
import json
import numpy as np
from pathlib import Path

from config import ensure_dirs
from utils import get_logger, save_npy, load_npy, safe_write_json, PipelineError

def load_streamlines(streamlines_path: Path) -> np.ndarray:
    """
    Load streamlines from a .trk or .tck file.
    Note: This is a placeholder for the actual loading logic which would
    require dipy or nibabel. For T014 completion, we assume the weighted
    adjacency matrix already exists as per the task dependency chain.
    This function is kept for API compatibility but T015 focuses on
    consuming the output of T014.
    """
    # In a real implementation, this would use dipy.io.streamline.load
    raise NotImplementedError("Streamline loading requires dipy/nibabel. "
                              "T015 assumes T014 has already produced weighted_adjacency.npy")

def load_atlas(atlas_path: Path) -> np.ndarray:
    """
    Load atlas NIfTI file.
    """
    raise NotImplementedError("Atlas loading requires nibabel.")

def parcellate_streamlines(streamlines: np.ndarray, atlas: np.ndarray) -> np.ndarray:
    """
    Parcellate streamlines to create a weighted adjacency matrix.
    This is the core logic of T014, assumed to be completed.
    """
    raise NotImplementedError("Parcellation logic is in T014.")

def threshold_to_density(adj_matrix: np.ndarray, density: float) -> np.ndarray:
    """
    Threshold a weighted adjacency matrix to a specific density.
    Keeps the top 'density' fraction of edges.
    """
    if density <= 0 or density > 1:
        raise ValueError("Density must be between 0 and 1.")
    
    # Flatten and sort
    flat = adj_matrix.flatten()
    # Filter out zeros if we want density of non-zero edges, 
    # but typically density refers to the fraction of possible edges kept.
    # We assume the matrix includes all possible edges (dense representation).
    
    # Calculate threshold value
    threshold_val = np.percentile(flat, (1 - density) * 100)
    
    # Create binary mask
    binary_mask = adj_matrix >= threshold_val
    
    # Apply mask
    return binary_mask.astype(float)

def compute_rsfc(bold_timeseries: np.ndarray) -> np.ndarray:
    """
    Compute the Resting-State Functional Connectivity (rsFC) matrix.
    
    Parameters
    ----------
    bold_timeseries : np.ndarray
        Array of shape (N_regions, N_timepoints) containing BOLD signals.
        
    Returns
    -------
    np.ndarray
        Correlation matrix of shape (N_regions, N_regions).
    """
    # Pearson correlation of time series
    # np.corrcoef expects variables in rows
    if bold_timeseries.shape[0] != bold_timeseries.shape[1]:
        # If shape is (timepoints, regions), transpose
        if bold_timeseries.shape[0] > bold_timeseries.shape[1]:
            bold_timeseries = bold_timeseries.T
    
    rsfc_matrix = np.corrcoef(bold_timeseries)
    
    # Handle NaNs (can occur if a time series is constant)
    rsfc_matrix = np.nan_to_num(rsfc_matrix, nan=0.0)
    
    return rsfc_matrix

def compute_global_efficiency(adj_matrix: np.ndarray) -> float:
    """
    Compute the Global Efficiency of the weighted adjacency matrix.
    
    Global Efficiency E_glob is defined as the average of the inverse 
    shortest path lengths between all pairs of nodes.
    E_glob = (1 / (N*(N-1))) * sum_{i!=j} (1 / d_ij)
    
    For weighted matrices, we typically use the inverse of weights as 
    distances (assuming weights represent connection strength).
    d_ij = 1 / w_ij
    
    Parameters
    ----------
    adj_matrix : np.ndarray
        Weighted adjacency matrix of shape (N, N).
        
    Returns
    -------
    float
        Global efficiency value.
    """
    n = adj_matrix.shape[0]
    if n < 2:
        return 0.0
    
    # Convert weights to distances: d = 1/w
    # Avoid division by zero
    # We use a small epsilon or treat zero weights as infinite distance
    # For efficiency calculation, we usually ignore disconnected components 
    # or treat them as infinite distance (contributing 0 to the sum).
    
    # Create distance matrix
    # Invert non-zero weights
    with np.errstate(divide='ignore', invalid='ignore'):
        dist_matrix = 1.0 / adj_matrix
    
    # Set infinite distances (from zero weights) to a large number or handle them
    # In efficiency calculation, 1/d where d is infinite is 0.
    # So we can just set infinite values to 0 in the final sum.
    
    # Set diagonal to infinity (distance to self is 0, so 1/0 is inf, but we skip i=j)
    np.fill_diagonal(dist_matrix, np.inf)
    
    # Replace inf with a large number or handle via masking
    # Actually, 1/inf = 0, so we want 1/d_ij where d_ij = 1/w_ij.
    # If w_ij = 0, d_ij = inf, 1/d_ij = 0.
    # So we just need to handle the 1/0 case in the inversion.
    # np.where(adj_matrix > 0, 1/adj_matrix, np.inf) -> then 1/d = adj_matrix?
    # Wait. E = sum(1/d_ij). If d_ij = 1/w_ij, then 1/d_ij = w_ij.
    # So for weighted graphs where weight = strength, Global Efficiency 
    # is often approximated as the average weight? 
    # NO. Standard definition: E = (1/N(N-1)) sum_{i!=j} (1/L_ij)
    # where L_ij is the shortest path length.
    # If we assume direct connection weight w_ij implies length L_ij = 1/w_ij.
    # Then 1/L_ij = w_ij.
    # But this is only for direct connections. We need shortest paths.
    
    # Floyd-Warshall to compute all-pairs shortest paths
    # Initialize dist matrix
    dist = np.full((n, n), np.inf)
    np.fill_diagonal(dist, 0.0)
    
    # Set direct distances
    # We only consider edges where weight > 0
    mask = adj_matrix > 0
    dist[mask] = 1.0 / adj_matrix[mask]
    
    # Floyd-Warshall Algorithm
    for k in range(n):
        # Use broadcasting for speed
        # dist[i, j] = min(dist[i, j], dist[i, k] + dist[k, j])
        # Avoid overflow in addition
        term = dist[:, k:k+1] + dist[k:k+1, :]
        dist = np.minimum(dist, term)
    
    # Compute efficiency
    # Exclude diagonal (dist to self is 0, 1/0 is inf, but we skip i=j)
    # Sum of 1/d_ij for i != j
    # Replace inf in dist with 0 for the inverse calculation (since 1/inf = 0)
    inv_dist = np.zeros_like(dist)
    finite_mask = np.isfinite(dist)
    inv_dist[finite_mask] = 1.0 / dist[finite_mask]
    
    # Set diagonal to 0 (already 0 in inv_dist because dist diagonal is 0 -> 1/0 handled by finite_mask? No)
    # dist diagonal is 0. 1/0 is inf. finite_mask is False. inv_dist diagonal is 0. Correct.
    
    total_efficiency = np.sum(inv_dist) - np.trace(inv_dist) # Subtract diagonal if any non-zero (should be 0)
    # Actually trace is 0.
    
    # Normalize
    global_eff = total_efficiency / (n * (n - 1))
    
    return float(global_eff)

def process_connectome(
    weighted_adj_path: Path,
    rsfc_output_path: Path,
    efficiency_output_path: Path,
    bold_timeseries: np.ndarray = None
) -> dict:
    """
    Main processing function for T015.
    
    1. Loads the weighted adjacency matrix from T014.
    2. Computes Global Efficiency on it.
    3. Computes rsFC (if BOLD data is provided) or loads a pre-computed rsFC if available.
       *Note: The task description says "compute rsFC (Pearson correlation of BOLD time-series)".
       Since T014 only produces structural data, and T015 input is specified as 
       `data/processed/weighted_adjacency.npy`, there is a logical gap: 
       rsFC requires BOLD data, not structural adjacency.
       
       However, looking at the task dependencies:
       T014 produces structural matrices.
       T015 input: `data/processed/weighted_adjacency.npy`.
       T015 output: `data/processed/rsfc.npy`, `data/processed/global_efficiency.json`.
       
       If the task implies that we must compute rsFC, we need BOLD data.
       If BOLD data is not available in `data/processed/`, we must fetch it or 
       assume the task description implies a mock/simulated step for the pipeline 
       (which contradicts "Real data only").
       
       RE-READING T015: "compute rsFC (Pearson correlation of BOLD time‑series)".
       But the INPUT listed is ONLY `data/processed/weighted_adjacency.npy`.
       This is a contradiction in the task spec unless the BOLD data is 
       expected to be loaded from `data/raw/` or similar inside this function.
       
       Given the constraint "Real data only", we must attempt to load BOLD data.
       Since T013 (download) handles fetching, we assume the BOLD data 
       (preprocessed time series) might be available or we need to simulate the 
       loading step.
       
       However, T013 only mentions downloading DWI and rs-fMRI. 
       We assume the pipeline expects the BOLD time series to be extracted 
       and available. 
       
       To satisfy the "Real data" constraint without a specific path provided 
       for BOLD in the task input, we will:
       1. Load the weighted adjacency.
       2. Compute Global Efficiency.
       3. Attempt to load a `bold_timeseries.npy` from a standard location 
          (e.g., `data/processed/`) or raise an error if missing.
       
       If the task implies that rsFC should be derived from the structural matrix 
       (which is scientifically invalid), we would fail. 
       We assume the task expects us to load the BOLD data that T013 downloaded.
       
       Let's assume the BOLD data is stored at `data/processed/bold_timeseries.npy`
       or similar. If not found, we raise an error.
       
       Wait, the task says: "input: data/processed/weighted_adjacency.npy".
       It does NOT list BOLD data as input.
       This suggests the task might be flawed or implies a specific mock scenario 
       for the "rsFC" part if real data isn't there.
       
       BUT, the constraint says: "Real data only — obtain it from a real source."
       If the input doesn't provide BOLD, and we can't find it, we must fail loudly.
       
       However, in many pipelines, the rsFC is computed from the raw rs-fMRI 
       which was downloaded in T013.
       We will check for `data/raw/` or `data/processed/` for BOLD data.
       
       Let's assume the existence of `data/processed/bold_timeseries.npy` 
       as the preprocessed BOLD data for the subject.
       
       If this file is missing, we raise FileNotFoundError.
    """
    logger = get_logger("preprocess")
    
    # 1. Load Weighted Adjacency
    if not weighted_adj_path.exists():
        raise FileNotFoundError(f"Weighted adjacency matrix not found: {weighted_adj_path}")
    
    weighted_adj = load_npy(weighted_adj_path)
    logger.info(f"Loaded weighted adjacency: shape {weighted_adj.shape}")
    
    # 2. Compute Global Efficiency
    global_eff = compute_global_efficiency(weighted_adj)
    logger.info(f"Computed Global Efficiency: {global_eff:.6f}")
    
    # 3. Compute rsFC
    # We need BOLD timeseries.
    # Check for standard location.
    bold_path = weighted_adj_path.parent / "bold_timeseries.npy"
    
    if not bold_path.exists():
        # Try to find any npy file that might be the time series?
        # Or raise error.
        logger.error(f"BOLD timeseries not found at {bold_path}. Cannot compute rsFC.")
        raise FileNotFoundError(f"BOLD timeseries required for rsFC computation not found at {bold_path}")
    
    bold_timeseries = load_npy(bold_path)
    logger.info(f"Loaded BOLD timeseries: shape {bold_timeseries.shape}")
    
    rsfc_matrix = compute_rsfc(bold_timeseries)
    logger.info(f"Computed rsFC matrix: shape {rsfc_matrix.shape}")
    
    # 4. Save Outputs
    ensure_dirs([rsfc_output_path, efficiency_output_path])
    
    save_npy(rsfc_matrix, rsfc_output_path)
    logger.info(f"Saved rsFC to {rsfc_output_path}")
    
    eff_data = {
        "global_efficiency": global_eff,
        "matrix_shape": list(weighted_adj.shape),
        "source": str(weighted_adj_path)
    }
    safe_write_json(eff_data, efficiency_output_path)
    logger.info(f"Saved global efficiency to {efficiency_output_path}")
    
    return {
        "rsfc_path": str(rsfc_output_path),
        "efficiency_path": str(efficiency_output_path),
        "global_efficiency": global_eff
    }

def main():
    """
    Entry point for T015 execution.
    """
    logger = get_logger("preprocess")
    logger.info("Starting T015: Compute rsFC and Global Efficiency")
    
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    processed_dir = project_root / "data" / "processed"
    
    weighted_adj_path = processed_dir / "weighted_adjacency.npy"
    rsfc_output_path = processed_dir / "rsfc.npy"
    efficiency_output_path = processed_dir / "global_efficiency.json"
    
    try:
        result = process_connectome(
            weighted_adj_path=weighted_adj_path,
            rsfc_output_path=rsfc_output_path,
            efficiency_output_path=efficiency_output_path
        )
        logger.info("T015 completed successfully.")
        print(json.dumps(result, indent=2))
    except FileNotFoundError as e:
        logger.error(f"Data missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during processing: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
