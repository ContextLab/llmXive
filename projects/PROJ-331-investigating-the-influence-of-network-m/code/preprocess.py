import os
import sys
import time
import logging
import json
import numpy as np
from pathlib import Path

# Import from utils as per API surface
from utils import (
    get_logger,
    save_npy,
    load_npy,
    PipelineError,
    ProcessingError,
    safe_mkdir
)
# Import from config as per API surface
from config import ensure_dirs

# Logger setup
logger = get_logger(__name__)

def load_streamlines(streamlines_path):
    """
    Load streamlines from a .trk or .tck file.
    Uses nibabel for .trk and dipy for .tck.
    Returns a list of numpy arrays (one per streamline) or a single array.
    """
    path = Path(streamlines_path)
    if not path.exists():
        raise FileNotFoundError(f"Streamlines file not found: {streamlines_path}")

    logger.info(f"Loading streamlines from {streamlines_path}")

    if path.suffix == '.trk':
        import nibabel as nib
        tractogram = nib.streamlines.load(str(path))
        # tractogram.streamlines is an ArraySequence
        return tractogram.streamlines
    elif path.suffix == '.tck':
        from dipy.io.streamline import load_tractogram
        # Load with reference to 'same' (self) or 'empty' if no reference needed
        # We assume the file is self-contained for coordinate extraction
        tractogram = load_tractogram(str(path), 'same')
        return tractogram.streamlines
    else:
        raise ValueError(f"Unsupported streamlines format: {path.suffix}. Use .trk or .tck")

def load_atlas(atlas_path):
    """
    Load the Schaefer parcellation atlas from a .nii.gz file.
    Returns a 3D numpy array where each voxel value represents a region ID.
    """
    path = Path(atlas_path)
    if not path.exists():
        raise FileNotFoundError(f"Atlas file not found: {atlas_path}")

    logger.info(f"Loading atlas from {atlas_path}")

    import nibabel as nib
    img = nib.load(str(path))
    data = img.get_fdata()
    
    # Ensure integer type for region IDs
    if data.dtype != np.int32:
        data = data.astype(np.int32)
    
    return data

def parcellate_streamlines(streamlines_path, atlas_path):
    """
    Apply Schaefer parcellation to DWI streamlines to create a Weighted Adjacency Matrix.
    
    This function counts the number of streamlines connecting each pair of regions
    defined in the atlas. The output is an unthresholded, weighted adjacency matrix
    where W[i, j] = count of streamlines between region i and region j.
    
    Args:
        streamlines_path (str): Path to .trk or .tck file containing streamlines.
        atlas_path (str): Path to .nii.gz file containing the parcellation atlas.
    
    Returns:
        np.ndarray: Weighted adjacency matrix of shape (N, N), where N is the number
                    of regions in the atlas.
    
    Raises:
        PipelineError: If processing fails.
        FileNotFoundError: If input files are missing.
    """
    try:
        logger.info(f"Starting parcellation: {streamlines_path} -> {atlas_path}")
        
        # Load data
        streamlines = load_streamlines(streamlines_path)
        atlas = load_atlas(atlas_path)
        
        # Determine number of regions (max value in atlas + 1, assuming 0 is background)
        # Or strictly count unique non-zero values
        unique_regions = np.unique(atlas)
        # Filter out background (0) if present
        if 0 in unique_regions:
            region_ids = unique_regions[unique_regions != 0]
        else:
            region_ids = unique_regions
        
        n_regions = len(region_ids)
        logger.info(f"Detected {n_regions} regions in atlas")
        
        # Create mapping from region_id (value in atlas) to index (0..N-1)
        # This handles cases where region IDs are not contiguous 1..N
        id_to_idx = {rid: idx for idx, rid in enumerate(region_ids)}
        
        # Initialize weighted adjacency matrix
        adj_matrix = np.zeros((n_regions, n_regions), dtype=np.float32)
        
        # Process streamlines
        count = 0
        total = len(streamlines)
        logger.info(f"Processing {total} streamlines")
        
        for i, streamline in enumerate(streamlines):
            # streamline is an (N_points, 3) array of coordinates
            # We need to map these coordinates to voxel indices in the atlas
            
            # Get unique region IDs visited by this streamline
            # We sample the streamline at regular intervals or check every point
            # To be robust, we check every point
            voxel_coords = np.floor(streamline).astype(np.int32)
            
            # Ensure coordinates are within atlas bounds
            # Atlas shape is (X, Y, Z)
            shape = atlas.shape
            valid_mask = (
                (voxel_coords[:, 0] >= 0) & (voxel_coords[:, 0] < shape[0]) &
                (voxel_coords[:, 1] >= 0) & (voxel_coords[:, 1] < shape[1]) &
                (voxel_coords[:, 2] >= 0) & (voxel_coords[:, 2] < shape[2])
            )
            
            valid_coords = voxel_coords[valid_mask]
            
            if len(valid_coords) == 0:
                continue
            
            # Get region IDs at these coordinates
            region_vals = atlas[valid_coords[:, 0], valid_coords[:, 1], valid_coords[:, 2]]
            
            # Filter out background (0)
            valid_region_vals = region_vals[region_vals != 0]
            
            if len(valid_region_vals) < 2:
                # Not enough regions to form a connection
                continue
            
            # Find unique pairs of regions connected by this streamline
            # We use a set to avoid double counting the same region pair within one streamline
            # if the streamline loops back
            visited_regions = set(valid_region_vals)
            
            if len(visited_regions) < 2:
                continue
            
            # Convert to list for iteration
            region_list = list(visited_regions)
            
            # Increment count for all pairs
            for r1 in region_list:
                for r2 in region_list:
                    if r1 == r2:
                        continue # Skip self-loops for standard connectome
                    
                    idx1 = id_to_idx[r1]
                    idx2 = id_to_idx[r2]
                    
                    adj_matrix[idx1, idx2] += 1
            
            count += 1
            if count % 1000 == 0:
                logger.debug(f"Processed {count}/{total} streamlines")
        
        logger.info(f"Parcellation complete. Processed {count} streamlines with connections.")
        logger.info(f"Adjacency matrix shape: {adj_matrix.shape}")
        
        return adj_matrix
        
    except Exception as e:
        logger.error(f"Error in parcellate_streamlines: {e}", exc_info=True)
        raise ProcessingError(f"Failed to parcellate streamlines: {e}")

def threshold_to_density(weighted_path, thresholds=[0.1, 0.2, 0.3]):
    """
    Generate Binary Adjacencies at varying density thresholds.
    
    Args:
        weighted_path (str): Path to weighted adjacency matrix (.npy).
        thresholds (list): List of density thresholds (e.g., [0.1, 0.2, 0.3]).
    
    Returns:
        dict: Dictionary mapping threshold string (e.g., '10p') to binary matrix.
    """
    try:
        adj = load_npy(weighted_path)
        n = adj.shape[0]
        max_edges = n * (n - 1) # Directed graph, no self loops
        
        results = {}
        
        for t in thresholds:
            # Calculate number of edges to keep
            k = int(max_edges * t)
            
            # Flatten and sort edges
            # We want to keep the strongest connections
            flat_adj = adj.flatten()
            # Create a mask for non-zero edges
            non_zero_mask = flat_adj > 0
            non_zero_edges = flat_adj[non_zero_mask]
            
            if len(non_zero_edges) == 0:
                logger.warning(f"No edges found for threshold {t}")
                binary_mat = np.zeros_like(adj)
            else:
                # Sort descending to keep strongest
                sorted_edges = np.sort(non_zero_edges)[::-1]
                threshold_val = sorted_edges[min(k, len(sorted_edges)-1)]
                
                # Create binary matrix
                binary_mat = (adj >= threshold_val).astype(np.float32)
                # Ensure diagonal is 0
                np.fill_diagonal(binary_mat, 0)
                
                # Verify density
                actual_density = np.sum(binary_mat) / max_edges
                logger.info(f"Threshold {t}: kept {np.sum(binary_mat)} edges (density: {actual_density:.4f})")
            
            key = f"{int(t*100)}p"
            results[key] = binary_mat
            
        return results
    except Exception as e:
        logger.error(f"Error in threshold_to_density: {e}", exc_info=True)
        raise ProcessingError(f"Failed to threshold matrix: {e}")

def compute_rsfc(time_series_path):
    """
    Compute Resting-State Functional Connectivity (rsFC) matrix.
    Assumes input is a time-series file (e.g., .npy or .csv) of shape (time_points, regions).
    
    Args:
        time_series_path (str): Path to time series data.
    
    Returns:
        np.ndarray: Pearson correlation matrix.
    """
    try:
        if time_series_path.endswith('.npy'):
            ts = load_npy(time_series_path)
        elif time_series_path.endswith('.csv'):
            import pandas as pd
            ts = pd.read_csv(time_series_path).values
        else:
            raise ValueError("Unsupported time series format")
        
        # Compute correlation
        # corrcoef returns (N, N) matrix
        rsfc = np.corrcoef(ts, rowvar=False)
        return rsfc
    except Exception as e:
        logger.error(f"Error in compute_rsfc: {e}", exc_info=True)
        raise ProcessingError(f"Failed to compute rsFC: {e}")

def compute_global_efficiency(adj_matrix):
    """
    Compute Global Efficiency of a network.
    Formula: Average of node-wise global efficiency.
    Node efficiency: sum(1/d_ij) for all j != i, where d_ij is shortest path distance.
    
    Args:
        adj_matrix (np.ndarray): Adjacency matrix (weighted or binary).
    
    Returns:
        float: Global efficiency value.
    """
    try:
        import networkx as nx
        
        # Create graph
        G = nx.from_numpy_array(adj_matrix)
        
        # Compute shortest path lengths
        # For weighted graphs, weight is the value in the matrix
        # If binary, weight is 1 (default)
        # We need to handle disconnected components
        try:
            lengths = nx.shortest_path_length(G, weight='weight')
        except nx.NetworkXError:
            # If graph is disconnected, we might need to handle it
            # For global efficiency, we usually consider only connected components
            # or use harmonic mean for infinite distances
            lengths = {}
            for i in range(G.number_of_nodes()):
                for j in range(G.number_of_nodes()):
                    if i == j:
                        continue
                    try:
                        l = nx.shortest_path_length(G, i, j, weight='weight')
                        if (i, j) not in lengths:
                            lengths[(i, j)] = []
                        lengths[(i, j)].append(l)
                    except nx.NetworkXNoPath:
                        lengths[(i, j)] = float('inf')
        
        # Calculate efficiency
        total_eff = 0.0
        count = 0
        for i in range(G.number_of_nodes()):
            node_eff = 0.0
            for j in range(G.number_of_nodes()):
                if i == j:
                    continue
                if (i, j) in lengths:
                    d = lengths[(i, j)]
                    if isinstance(d, list):
                        d = d[0] # Take first if multiple
                else:
                    d = float('inf')
                
                if d != float('inf') and d > 0:
                    node_eff += 1.0 / d
            
            total_eff += node_eff
            count += 1
        
        global_eff = total_eff / count if count > 0 else 0.0
        return float(global_eff)
        
    except Exception as e:
        logger.error(f"Error in compute_global_efficiency: {e}", exc_info=True)
        raise ProcessingError(f"Failed to compute global efficiency: {e}")

def process_connectome(subject_id, dwi_path, atlas_path, output_dir):
    """
    Main orchestration function for processing a single subject's connectome.
    
    1. Parcellate streamlines -> weighted adjacency
    2. Threshold weighted adjacency -> binary adjacencies
    3. Compute global efficiency on weighted adjacency
    4. Save all outputs
    
    Args:
        subject_id (str): Subject identifier.
        dwi_path (str): Path to DWI streamlines file.
        atlas_path (str): Path to atlas file.
        output_dir (str): Directory to save outputs.
    
    Returns:
        dict: Metadata about processed files.
    """
    try:
        safe_mkdir(output_dir)
        
        # 1. Parcellate
        logger.info(f"Processing subject {subject_id}")
        weighted_adj = parcellate_streamlines(dwi_path, atlas_path)
        
        # Save weighted adjacency
        weighted_path = os.path.join(output_dir, "weighted_adjacency.npy")
        save_npy(weighted_adj, weighted_path)
        logger.info(f"Saved weighted adjacency to {weighted_path}")
        
        # 2. Threshold
        thresholds = [0.1, 0.2, 0.3]
        binary_mats = threshold_to_density(weighted_path, thresholds)
        
        for key, mat in binary_mats.items():
            out_path = os.path.join(output_dir, f"binary_adj_{key}.npy")
            save_npy(mat, out_path)
            logger.info(f"Saved binary adjacency {key} to {out_path}")
        
        # 3. Compute Global Efficiency (on weighted)
        global_eff = compute_global_efficiency(weighted_adj)
        
        # 4. Save Global Efficiency
        eff_path = os.path.join(output_dir, "global_efficiency.json")
        eff_data = {"subject_id": subject_id, "global_efficiency": global_eff}
        with open(eff_path, 'w') as f:
            json.dump(eff_data, f, indent=2)
        logger.info(f"Saved global efficiency to {eff_path}")
        
        return {
            "weighted_path": weighted_path,
            "binary_paths": {k: os.path.join(output_dir, f"binary_adj_{k}.npy") for k in binary_mats},
            "efficiency_path": eff_path,
            "global_efficiency": global_eff
        }
        
    except Exception as e:
        logger.error(f"Error in process_connectome for {subject_id}: {e}", exc_info=True)
        raise ProcessingError(f"Failed to process connectome for {subject_id}: {e}")

def main():
    """
    Entry point for CLI execution.
    Expects environment variables or config for paths.
    For this task, we assume paths are passed or loaded from config.
    """
    logger.info("Starting preprocessing pipeline")
    
    # Example usage (to be replaced with actual CLI args or config loading)
    # This is a placeholder to ensure the script runs
    # In a real scenario, we would load subject list from config
    
    # Mock data for testing if real data is not available in CI
    # NOTE: In production, this should be removed or replaced with real data loading
    # The task T013 handles data downloading, so we assume data exists here.
    
    # Check if we have a subject to process
    # For now, we just log success if the functions are callable
    logger.info("Preprocessing module loaded successfully.")
    logger.info("Functions available: parcellate_streamlines, threshold_to_density, compute_global_efficiency")
    
    # If running as script, we might want to process a specific subject
    # This would require command line arguments
    if len(sys.argv) > 1:
        subject = sys.argv[1]
        # Logic to process subject would go here
        logger.info(f"Processing subject: {subject}")
    else:
        logger.info("No subject provided. Run with subject_id argument.")

if __name__ == "__main__":
    main()
