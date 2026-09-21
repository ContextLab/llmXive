import os
import json
import logging
import csv
import torch
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from sklearn.cluster import KMeans
from scipy.spatial.distance import cdist

from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def compute_activation_histograms(activations: torch.Tensor, num_bins: int = 50) -> np.ndarray:
    """
    Compute a histogram of activation values for a given tensor.
    
    Args:
        activations: Tensor of shape (batch, channels, height, width) or (batch, seq_len, dim)
        num_bins: Number of bins for the histogram
        
    Returns:
        Normalized histogram as a numpy array
    """
    if not isinstance(activations, torch.Tensor):
        activations = torch.tensor(activations)
    
    # Flatten all dimensions except batch
    flat_activations = activations.view(activations.shape[0], -1)
    
    histograms = []
    for i in range(flat_activations.shape[0]):
        # Compute histogram
        hist, _ = np.histogram(flat_activations[i].detach().cpu().numpy(), bins=num_bins)
        # Normalize
        hist = hist / (hist.sum() + 1e-8)
        histograms.append(hist)
    
    return np.array(histograms)

def compute_rotation_matrix_from_activations(activations: np.ndarray, k: int = 16) -> np.ndarray:
    """
    Compute a rotation matrix based on clustering of activation histograms.
    
    This implements the OrbitQuant data-agnostic rotation logic:
    1. Cluster activation histograms into K clusters
    2. Compute the mean activation vector for each cluster
    3. Construct a rotation matrix that aligns with these principal directions
    
    Args:
        activations: Array of activation histograms (batch_size, num_bins)
        k: Number of clusters (and resulting rotation matrix components)
        
    Returns:
        Rotation matrix of shape (k, num_features)
    """
    if activations.shape[0] < k:
        logger.warning(f"Number of samples ({activations.shape[0]}) is less than K ({k}). Adjusting K.")
        k = max(1, activations.shape[0] // 2)
    
    # Perform K-means clustering on the activation histograms
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(activations)
    
    # Get cluster centers
    centers = kmeans.cluster_centers_
    
    # Normalize centers to create rotation vectors
    norms = np.linalg.norm(centers, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)  # Avoid division by zero
    rotation_vectors = centers / norms
    
    return rotation_vectors

def run_clustering_pipeline(
    activation_data_path: str,
    output_path: str,
    k: int = 16,
    num_bins: int = 50,
    layer_subset: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Run the full clustering pipeline to generate rotation matrices.
    
    This function:
    1. Loads activation histograms from the specified path (generated trajectories)
    2. Clusters them into K groups
    3. Computes rotation matrices for each cluster
    4. Saves the results to a JSON report
    
    Args:
        activation_data_path: Path to CSV containing activation histograms
        output_path: Path to save the clustering report JSON
        k: Number of clusters/rotation matrices
        num_bins: Number of histogram bins
        layer_subset: Optional list of layer names to process
        
    Returns:
        Dictionary containing the clustering results
    """
    logger.info(f"Starting clustering pipeline with K={k}")
    
    # Load activation data
    if not os.path.exists(activation_data_path):
        raise FileNotFoundError(f"Activation data file not found: {activation_data_path}")
    
    logger.info(f"Loading activation data from {activation_data_path}")
    
    # Read CSV data
    activations_list = []
    layer_names = []
    subset_ids = []
    
    with open(activation_data_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            layer_name = row.get('layer_name', 'default_layer')
            subset_id = row.get('subset_id', '0')
            # Parse activation histogram from comma-separated string
            hist_str = row.get('histogram', '')
            if hist_str:
                hist = np.array([float(x) for x in hist_str.split(',')])
                activations_list.append(hist)
                layer_names.append(layer_name)
                subset_ids.append(subset_id)
    
    if not activations_list:
        raise ValueError("No valid activation data found in the input file")
    
    activations = np.array(activations_list)
    logger.info(f"Loaded {len(activations)} activation histograms")
    
    # Filter by layer subset if specified
    if layer_subset:
        mask = [name in layer_subset for name in layer_names]
        activations = activations[mask]
        layer_names = [name for i, name in enumerate(layer_names) if mask[i]]
        subset_ids = [sid for i, sid in enumerate(subset_ids) if mask[i]]
        logger.info(f"Filtered to {len(activations)} activations for specified layers")
    
    # Compute K-means clustering and rotation matrices
    logger.info(f"Computing K-means clustering with K={k}")
    rotation_matrices = compute_rotation_matrix_from_activations(activations, k=k)
    
    # Identify boundaries for each cluster
    # Assign each sample to its nearest cluster center
    from sklearn.metrics.pairwise import pairwise_distances
    distances = pairwise_distances(activations, rotation_matrices)
    cluster_assignments = np.argmin(distances, axis=1)
    
    # Compute boundaries (min/max values for each cluster)
    boundaries = {}
    for i in range(k):
        cluster_mask = cluster_assignments == i
        if np.any(cluster_mask):
            cluster_data = activations[cluster_mask]
            boundaries[str(i)] = {
                'min': float(np.min(cluster_data)),
                'max': float(np.max(cluster_data)),
                'mean': float(np.mean(cluster_data)),
                'std': float(np.std(cluster_data)),
                'count': int(np.sum(cluster_mask))
            }
    
    # Build the report
    report = {
        'layers': list(set(layer_names)),
        'subsets': list(set(subset_ids)),
        'boundaries': boundaries,
        'k': k,
        'num_bins': num_bins,
        'rotation_matrices': {
            str(i): rotation_matrices[i].tolist() 
            for i in range(rotation_matrices.shape[0])
        },
        'metadata': {
            'total_samples': len(activations),
            'unique_layers': len(set(layer_names)),
            'unique_subsets': len(set(subset_ids)),
            'clustering_algorithm': 'KMeans',
            'timestamp': None  # Will be set by caller if needed
        }
    }
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Save report
    logger.info(f"Saving clustering report to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Clustering pipeline completed. Generated {k} rotation matrices.")
    return report

def main():
    """
    Main entry point for the clustering pipeline.
    Reads configuration and runs the clustering process on the MS-COCO train split
    activation histograms (generated trajectories).
    """
    config = Config()
    
    # Define paths
    # The activation data should be generated by the DiT generation loop (T017/T008)
    # For now, we assume it's in data/processed/activations.csv
    activation_data_path = config.data_dir / "processed" / "activations.csv"
    output_path = config.data_dir / "processed" / "clustering_report.json"
    
    # Check if activation data exists
    if not activation_data_path.exists():
        logger.error(f"Activation data not found at {activation_data_path}")
        logger.error("Please run the DiT generation pipeline (T017) first to generate activations.")
        raise FileNotFoundError(f"Activation data file not found: {activation_data_path}")
    
    # Run clustering pipeline
    report = run_clustering_pipeline(
        activation_data_path=str(activation_data_path),
        output_path=str(output_path),
        k=16,  # K=16 as specified in the task
        num_bins=50
    )
    
    logger.info("Clustering report generated successfully")
    print(f"Report saved to: {output_path}")
    print(f"Generated {len(report['rotation_matrices'])} rotation matrices")

if __name__ == "__main__":
    main()
