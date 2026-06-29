import os
import logging
import tempfile
import shutil
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from pathlib import Path
import requests
from scipy import stats
import networkx as nx

from ..logging_config import get_logger
from ..models import Subject, ConnectivityMatrix, NetworkMetric

logger = get_logger(__name__)

# Constants
SCHAEFER_400_URL = "https://raw.githubusercontent.com/ThomasYeoLab/CBIG/v1.0.0/stable_projects/brain_parcellation/Schaefer2018_LocalGlobal/Parcellations/MNI/Schaefer2018_400Parcels_7Networks_order_FSLMNI152_2mm.nii.gz"
SCHAEFER_400_LABELS_URL = "https://raw.githubusercontent.com/ThomasYeoLab/CBIG/v1.0.0/stable_projects/brain_parcellation/Schaefer2018_LocalGlobal/Parcellations/MNI/Schaefer2018_400Parcels_7Networks_order.txt"

def download_schaefer_atlas(cache_dir: Optional[str] = None) -> Tuple[str, str]:
    """
    Download the Schaefer 400-parcel atlas and label file if not present.
    Returns paths to the NIfTI atlas and the labels text file.
    """
    if cache_dir is None:
        cache_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "atlas")
    
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)
    
    atlas_file = cache_path / "Schaefer2018_400Parcels.nii.gz"
    labels_file = cache_path / "Schaefer2018_400Parcels_order.txt"
    
    if not atlas_file.exists():
        logger.info(f"Downloading Schaefer atlas to {atlas_file}")
        response = requests.get(SCHAEFER_400_URL, stream=True)
        response.raise_for_status()
        with open(atlas_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    
    if not labels_file.exists():
        logger.info(f"Downloading Schaefer labels to {labels_file}")
        response = requests.get(SCHAEFER_400_LABELS_URL, stream=True)
        response.raise_for_status()
        with open(labels_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
    return str(atlas_file), str(labels_file)

def load_atlas(atlas_path: str) -> np.ndarray:
    """
    Load the atlas NIfTI file into a numpy array.
    Returns a 3D or 4D array depending on the file.
    """
    try:
        import nibabel as nib
        img = nib.load(atlas_path)
        data = img.get_fdata()
        return data
    except ImportError:
        logger.error("nibabel is required to load the atlas. Install with: pip install nibabel")
        raise

def extract_time_series(
    nifti_path: str, 
    atlas_data: np.ndarray, 
    mask_value: Optional[int] = None
) -> np.ndarray:
    """
    Extract mean time series for each parcel in the atlas from the fMRI data.
    
    Args:
        nifti_path: Path to the preprocessed fMRI NIfTI file.
        atlas_data: 3D numpy array of the atlas labels.
        mask_value: If provided, only extract parcels matching this value (or non-zero if None).
        
    Returns:
        2D numpy array of shape (n_timepoints, n_parcels).
    """
    try:
        import nibabel as nib
    except ImportError:
        logger.error("nibabel is required to extract time series.")
        raise

    img = nib.load(nifti_path)
    fmri_data = img.get_fdata()
    
    if fmri_data.ndim != 4:
        raise ValueError(f"Expected 4D fMRI data, got {fmri_data.ndim}D")
    
    # Identify unique parcels
    unique_parcels = np.unique(atlas_data)
    if mask_value is not None:
        unique_parcels = unique_parcels[unique_parcels == mask_value]
    elif 0 in unique_parcels:
        unique_parcels = unique_parcels[unique_parcels != 0]
        
    unique_parcels = sorted(unique_parcels)
    n_parcels = len(unique_parcels)
    n_timepoints = fmri_data.shape[3]
    
    time_series = np.zeros((n_timepoints, n_parcels))
    
    for i, parcel_id in enumerate(unique_parcels):
        mask = atlas_data == parcel_id
        # Extract voxels belonging to this parcel
        parcel_voxels = fmri_data[mask, :]
        if parcel_voxels.shape[0] > 0:
            # Mean across voxels for each timepoint
            time_series[:, i] = np.mean(parcel_voxels, axis=0)
        else:
            logger.warning(f"No voxels found for parcel {parcel_id}")
            time_series[:, i] = 0.0
            
    return time_series

def apply_motion_regression(time_series: np.ndarray, motion_params: np.ndarray) -> np.ndarray:
    """
    Regress out motion parameters from the time series.
    
    Args:
        time_series: 2D array (n_timepoints, n_parcels).
        motion_params: 2D array (n_timepoints, n_params).
        
    Returns:
        Cleaned time series (n_timepoints, n_parcels).
    """
    if motion_params.shape[0] != time_series.shape[0]:
        raise ValueError("Motion parameters and time series must have same number of timepoints.")
    
    # Fit linear model for each parcel
    cleaned = np.zeros_like(time_series)
    
    for i in range(time_series.shape[1]):
        y = time_series[:, i]
        X = np.column_stack([np.ones(motion_params.shape[0]), motion_params])
        
        # Solve least squares
        try:
            beta, residuals, rank, s = np.linalg.lstsq(X, y, rcond=None)
            fitted = X @ beta
            residuals = y - fitted
            cleaned[:, i] = residuals
        except np.linalg.LinAlgError:
            logger.warning(f"Could not regress motion for parcel {i}, keeping original.")
            cleaned[:, i] = y
            
    return cleaned

def calculate_connectivity_matrix(time_series: np.ndarray) -> np.ndarray:
    """
    Calculate the Pearson correlation matrix between all parcels.
    
    Args:
        time_series: 2D array (n_timepoints, n_parcels).
        
    Returns:
        2D array (n_parcels, n_parcels) correlation matrix.
    """
    # Use numpy corrcoef which returns (n_parcels, n_parcels)
    # corrcoef expects variables in rows, so we transpose if needed
    # time_series is (time, parcels), so we need (parcels, time)
    corr_matrix = np.corrcoef(time_series.T)
    
    # Handle NaNs (e.g., if a parcel had zero variance)
    corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
    
    return corr_matrix

def calculate_graph_metrics(conn_matrix: np.ndarray, atlas_labels: Optional[List[str]] = None) -> Dict[str, Union[float, np.ndarray]]:
    """
    Calculate graph theoretical metrics from the connectivity matrix.
    
    Args:
        conn_matrix: 2D array (n_nodes, n_nodes).
        atlas_labels: Optional list of labels for nodes (used for debugging/labeling).
        
    Returns:
        Dictionary containing:
            - modularity: float
            - global_efficiency: float
            - participation_coef: np.ndarray (per node)
            - within_module_degree: np.ndarray (per node)
            - community_membership: np.ndarray (per node)
    """
    G = nx.from_numpy_array(conn_matrix)
    
    # Threshold to create an unweighted graph for community detection
    # Keep top X% of edges or use a fixed threshold
    # Here we use a fixed threshold of 0.1 for demonstration
    threshold = 0.1
    G_thresholded = nx.thresholded_graph(G, threshold, 'weight')
    # Convert to unweighted for community detection
    G_unweighted = nx.Graph()
    G_unweighted.add_nodes_from(G_thresholded.nodes())
    G_unweighted.add_edges_from([(u, v) for u, v in G_thresholded.edges()])
    
    if len(G_unweighted.nodes()) == 0:
        logger.warning("Thresholded graph has no edges. Returning zero metrics.")
        n_nodes = conn_matrix.shape[0]
        return {
            'modularity': 0.0,
            'global_efficiency': 0.0,
            'participation_coef': np.zeros(n_nodes),
            'within_module_degree': np.zeros(n_nodes),
            'community_membership': np.zeros(n_nodes, dtype=int)
        }

    # Community detection
    try:
        communities = nx.community.louvain_communities(G_unweighted, seed=42)
        community_membership = np.zeros(len(G.nodes()), dtype=int)
        for i, comm in enumerate(communities):
            for node in comm:
                community_membership[node] = i
    except Exception as e:
        logger.error(f"Community detection failed: {e}. Returning default metrics.")
        n_nodes = conn_matrix.shape[0]
        return {
            'modularity': 0.0,
            'global_efficiency': 0.0,
            'participation_coef': np.zeros(n_nodes),
            'within_module_degree': np.zeros(n_nodes),
            'community_membership': np.zeros(n_nodes, dtype=int)
        }

    # Modularity
    try:
        modularity = nx.community.modularity(G_unweighted, communities)
    except Exception:
        modularity = 0.0

    # Global Efficiency
    try:
        global_efficiency = nx.global_efficiency(G_unweighted)
    except Exception:
        global_efficiency = 0.0

    # Participation Coefficient and Within-Module Degree
    # These require weighted graph and community structure
    # We'll use the original weighted graph but the community structure from unweighted
    
    participation_coef = np.zeros(len(G.nodes()))
    within_module_degree = np.zeros(len(G.nodes()))
    
    for node in G.nodes():
        if community_membership[node] == -1:
            continue
            
        # Get neighbors in the same module
        same_module_neighbors = [n for n in G.neighbors(node) if community_membership[n] == community_membership[node]]
        # Get neighbors in different modules
        diff_module_neighbors = [n for n in G.neighbors(node) if community_membership[n] != community_membership[node]]
        
        # Degree within module
        k_in = sum(G[node][n]['weight'] for n in same_module_neighbors) if same_module_neighbors else 0
        
        # Degree to other modules
        k_out = sum(G[node][n]['weight'] for n in diff_module_neighbors) if diff_module_neighbors else 0
        
        # Total degree
        k_total = k_in + k_out
        
        if k_total > 0:
            # Within-module degree (normalized)
            within_module_degree[node] = k_in / k_total
            
            # Participation coefficient (simplified: 1 - (k_in/k_total)^2)
            # More complex version involves summing over all modules
            participation_coef[node] = 1 - (k_in / k_total) ** 2
        else:
            within_module_degree[node] = 0.0
            participation_coef[node] = 0.0

    return {
        'modularity': modularity,
        'global_efficiency': global_efficiency,
        'participation_coef': participation_coef,
        'within_module_degree': within_module_degree,
        'community_membership': community_membership
    }

def aggregate_node_metrics(node_metrics: np.ndarray) -> float:
    """
    Aggregate node-level metrics into a single scalar per subject.
    
    This function implements the requirement from FR-003 to aggregate
    node-level vectors (Participation Coefficient and Within-Module Degree)
    into a single scalar per subject by taking the mean across nodes.
    
    Args:
        node_metrics: 1D numpy array of node-level metric values.
        
    Returns:
        float: The mean of the node-level metrics.
    """
    if node_metrics.size == 0:
        logger.warning("Node metrics array is empty, returning 0.0")
        return 0.0
        
    return float(np.mean(node_metrics))

def process_subject(
    subject_id: str,
    fmri_path: str,
    atlas_path: str,
    motion_params_path: Optional[str] = None,
    output_dir: Optional[str] = None
) -> Dict[str, Union[str, float, np.ndarray, Dict]]:
    """
    Process a single subject: extract time series, calculate connectivity,
    compute graph metrics, and aggregate node-level metrics.
    
    Args:
        subject_id: Subject identifier.
        fmri_path: Path to preprocessed fMRI NIfTI file.
        atlas_path: Path to atlas NIfTI file.
        motion_params_path: Optional path to motion parameters file.
        output_dir: Optional directory to save intermediate results.
        
    Returns:
        Dictionary containing processed data and metrics.
    """
    logger.info(f"Processing subject {subject_id}")
    
    # Load atlas
    atlas_data = load_atlas(atlas_path)
    
    # Extract time series
    time_series = extract_time_series(fmri_path, atlas_data)
    
    # Apply motion regression if motion parameters are available
    if motion_params_path and os.path.exists(motion_params_path):
        try:
            motion_params = np.loadtxt(motion_params_path)
            if motion_params.ndim == 1:
                motion_params = motion_params.reshape(-1, 1)
            time_series = apply_motion_regression(time_series, motion_params)
        except Exception as e:
            logger.warning(f"Failed to load motion parameters: {e}. Skipping regression.")
    
    # Calculate connectivity matrix
    conn_matrix = calculate_connectivity_matrix(time_series)
    
    # Calculate graph metrics
    graph_metrics = calculate_graph_metrics(conn_matrix)
    
    # Aggregate node-level metrics
    aggregated_participation = aggregate_node_metrics(graph_metrics['participation_coef'])
    aggregated_within_module = aggregate_node_metrics(graph_metrics['within_module_degree'])
    
    result = {
        'subject_id': subject_id,
        'time_series': time_series,
        'connectivity_matrix': conn_matrix,
        'graph_metrics': {
            'modularity': graph_metrics['modularity'],
            'global_efficiency': graph_metrics['global_efficiency'],
            'participation_coef': aggregated_participation,
            'within_module_degree': aggregated_within_module,
            'community_membership': graph_metrics['community_membership']
        },
        'node_metrics': {
            'participation_coef': graph_metrics['participation_coef'],
            'within_module_degree': graph_metrics['within_module_degree']
        }
    }
    
    # Save intermediate results if output_dir is specified
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        # Save connectivity matrix
        np.save(os.path.join(output_dir, f"{subject_id}_conn_matrix.npy"), conn_matrix)
        # Save aggregated metrics
        with open(os.path.join(output_dir, f"{subject_id}_metrics.json"), 'w') as f:
            import json
            json.dump({
                'modularity': result['graph_metrics']['modularity'],
                'global_efficiency': result['graph_metrics']['global_efficiency'],
                'participation_coef': result['graph_metrics']['participation_coef'],
                'within_module_degree': result['graph_metrics']['within_module_degree']
            }, f, indent=2)
    
    return result

def main():
    """
    Main function to demonstrate the metrics pipeline.
    This is a placeholder for actual execution logic.
    """
    logger.info("Running metrics pipeline demonstration")
    # In a real scenario, this would iterate over subjects and process them
    print("Metrics pipeline ready for execution.")

if __name__ == "__main__":
    main()