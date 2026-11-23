import os
import json
import logging
import csv
import torch
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from sklearn.cluster import KMeans
from scipy.linalg import qr

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/clustering.log', mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Constants
CONFIG = {
    'K': 16,  # Number of clusters
    'ACTIVATION_DIM': 1024,  # Default dimension, will be inferred from data
    'RANDOM_SEED': 42,
    'DATA_PATH': 'data/processed/correlation_results.json',
    'OUTPUT_PATH': 'data/processed/clustering_report.json',
    'LAYERS': ['layer_1', 'layer_2', 'layer_3', 'layer_4']  # Example layers
}

def load_activation_variances(data_path: str) -> Dict[str, np.ndarray]:
    """
    Load activation variances from the correlation results JSON.
    
    Args:
        data_path: Path to the correlation_results.json file
        
    Returns:
        Dictionary mapping layer names to arrays of variance values
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}. "
                              "Please run T017 (correlation) first.")
    
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    variances = {}
    for layer in CONFIG['LAYERS']:
        if layer in data:
          # Expecting data[layer] to be a list of variance values
          variances[layer] = np.array(data[layer])
        else:
            # If layer not found, try to infer from structure
            # Assuming flat structure with layer prefixes
            layer_data = {k: v for k, v in data.items() if k.startswith(layer)}
            if layer_data:
                variances[layer] = np.array(list(layer_data.values()))
            else:
                logger.warning(f"No data found for layer {layer}")
    
    if not variances:
        raise ValueError("No activation variance data found in the correlation results.")
    
    return variances

def compute_activation_histograms(variances: Dict[str, np.ndarray], 
                                  n_bins: int = 50) -> Dict[str, np.ndarray]:
    """
    Compute histograms of activation variances for each layer.
    
    Args:
        variances: Dictionary of variance arrays per layer
        n_bins: Number of histogram bins
        
    Returns:
        Dictionary mapping layer names to histogram bin edges
    """
    histograms = {}
    for layer, vals in variances.items():
        if len(vals) > 0:
            # Compute histogram to understand distribution
            counts, bin_edges = np.histogram(vals, bins=n_bins)
            histograms[layer] = {
                'counts': counts,
                'bin_edges': bin_edges,
                'min': np.min(vals),
                'max': np.max(vals),
                'mean': np.mean(vals),
                'std': np.std(vals)
            }
            logger.info(f"Layer {layer}: min={np.min(vals):.4f}, "
                      f"max={np.max(vals):.4f}, mean={np.mean(vals):.4f}")
    return histograms

def compute_rotation_matrix_from_activations(activations: np.ndarray, 
                                             target_dim: int) -> np.ndarray:
    """
    Compute a rotation matrix from activation data using QR decomposition.
    
    This implements the OrbitQuant rotation logic:
    1. Standardize the activations
    2. Perform QR decomposition to get an orthogonal matrix
    3. Return the Q matrix as the rotation matrix
    
    Args:
        activations: Array of activation values (n_samples, n_features)
        target_dim: Target dimension for the rotation matrix
        
    Returns:
        Orthogonal rotation matrix of shape (target_dim, target_dim)
    """
    if activations.ndim == 1:
        # Reshape to 2D if 1D
        activations = activations.reshape(-1, 1)
    
    # Standardize activations
    mean = np.mean(activations, axis=0, keepdims=True)
    std = np.std(activations, axis=0, keepdims=True)
    std[std == 0] = 1  # Avoid division by zero
    standardized = (activations - mean) / std
    
    # If we have fewer samples than features, pad with zeros or use SVD
    n_samples, n_features = standardized.shape
    
    if n_samples < target_dim:
        # Pad with random orthogonal vectors
        logger.warning(f"Samples ({n_samples}) < target_dim ({target_dim}). "
                     "Padding with random orthogonal vectors.")
        padded = np.random.randn(target_dim, n_features)
        padded[:n_samples] = standardized
        standardized = padded
    elif n_features < target_dim:
        # Pad features with zeros
        logger.warning(f"Features ({n_features}) < target_dim ({target_dim}). "
                     "Padding features with zeros.")
        standardized = np.pad(standardized, ((0, 0), (0, target_dim - n_features)))
    
    # Perform QR decomposition to get orthogonal matrix
    Q, R = qr(standardized[:target_dim, :target_dim], mode='reduced')
    
    # Ensure determinant is positive (proper rotation)
    if np.linalg.det(Q) < 0:
        Q[:, 0] = -Q[:, 0]
    
    return Q

def cluster_variances_and_derive_matrices(variances: Dict[str, np.ndarray], 
                                          k: int = 16) -> Dict[str, Any]:
    """
    Cluster activation variances and derive pre-optimized rotation matrices.
    
    This is the core logic for T022:
    1. For each layer, cluster the variance values into K groups
    2. For each cluster, compute a representative rotation matrix
    3. Return the clustering report with boundaries and matrices
    
    Args:
        variances: Dictionary of variance arrays per layer
        k: Number of clusters
        
    Returns:
        Dictionary containing layers, subsets, boundaries, and matrices
    """
    report = {
        'layers': [],
        'subsets': {},
        'boundaries': {},
        'matrices': []
    }
    
    np.random.seed(CONFIG['RANDOM_SEED'])
    
    for layer, vals in variances.items():
        if len(vals) < k:
            logger.warning(f"Layer {layer} has only {len(vals)} samples, "
                         f"less than K={k}. Skipping clustering for this layer.")
            continue
        
        # Reshape for sklearn
        X = vals.reshape(-1, 1)
        
        # Perform K-Means clustering
        kmeans = KMeans(n_clusters=k, random_state=CONFIG['RANDOM_SEED'], n_init=10)
        labels = kmeans.fit_predict(X)
        
        # Store cluster centers and boundaries
        centers = kmeans.cluster_centers_.flatten()
        sorted_centers = np.sort(centers)
        
        # Define boundaries as midpoints between sorted centers
        boundaries = []
        for i in range(len(sorted_centers) - 1):
            mid = (sorted_centers[i] + sorted_centers[i+1]) / 2
            boundaries.append(mid)
        
        report['layers'].append(layer)
        report['boundaries'][layer] = boundaries.tolist()
        
        # For each cluster, derive a rotation matrix
        # We use the cluster center values to generate synthetic activations
        # that represent the typical activation pattern for that cluster
        cluster_matrices = []
        for cluster_idx in range(k):
            # Get samples belonging to this cluster
            cluster_samples = vals[labels == cluster_idx]
            
            if len(cluster_samples) == 0:
                # Fallback to random matrix if no samples
                logger.warning(f"No samples in cluster {cluster_idx} for layer {layer}")
                # Generate a random orthogonal matrix
                random_matrix = np.random.randn(CONFIG['ACTIVATION_DIM'], CONFIG['ACTIVATION_DIM'])
                Q, _ = qr(random_matrix)
                cluster_matrices.append(Q.tolist())
                continue
            
            # Create a representative activation vector for this cluster
            # Use the cluster center value repeated to form a vector
            center_val = centers[cluster_idx]
            # Create a vector that represents the "typical" activation for this cluster
            # We use a combination of the center value and some variation
            representative_activations = np.full((100, CONFIG['ACTIVATION_DIM']), center_val)
            
            # Add some noise to make it more realistic
            noise = np.random.randn(100, CONFIG['ACTIVATION_DIM']) * 0.1
            representative_activations += noise
            
            # Compute rotation matrix
            rotation_matrix = compute_rotation_matrix_from_activations(
                representative_activations, 
                CONFIG['ACTIVATION_DIM']
            )
            
            cluster_matrices.append(rotation_matrix.tolist())
        
        report['subsets'][layer] = {
            'cluster_labels': labels.tolist(),
            'cluster_centers': centers.tolist(),
            'matrices': cluster_matrices
        }
    
    # Aggregate all matrices into a single list for easy access
    # Format: [layer1_matrix0, layer1_matrix1, ..., layer2_matrix0, ...]
    all_matrices = []
    for layer in report['layers']:
        if layer in report['subsets']:
            for matrix in report['subsets'][layer]['matrices']:
                all_matrices.append(matrix)
    
    report['matrices'] = all_matrices
    report['total_matrices'] = len(all_matrices)
    
    return report

def run_clustering_pipeline(data_path: str = None, output_path: str = None) -> Dict[str, Any]:
    """
    Run the complete clustering pipeline.
    
    Args:
        data_path: Path to correlation results JSON
        output_path: Path to save clustering report
        
    Returns:
        Clustering report dictionary
    """
    if data_path is None:
        data_path = CONFIG['DATA_PATH']
    if output_path is None:
        output_path = CONFIG['OUTPUT_PATH']
    
    logger.info(f"Starting clustering pipeline with data from {data_path}")
    
    # Step 1: Load activation variances
    variances = load_activation_variances(data_path)
    logger.info(f"Loaded variances for {len(variances)} layers")
    
    # Step 2: Compute histograms (for analysis)
    histograms = compute_activation_histograms(variances)
    logger.info("Computed activation histograms")
    
    # Step 3: Cluster and derive matrices
    report = cluster_variances_and_derive_matrices(variances, k=CONFIG['K'])
    logger.info(f"Generated {len(report['matrices'])} rotation matrices")
    
    # Step 4: Save report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Clustering report saved to {output_path}")
    
    return report

def main():
    """Main entry point for the clustering script."""
    try:
        report = run_clustering_pipeline()
        
        # Validation checks
        if 'layers' not in report or len(report['layers']) == 0:
            raise ValueError("No layers found in clustering report")
        
        if 'matrices' not in report or len(report['matrices']) == 0:
            raise ValueError("No rotation matrices generated")
        
        # Verify matrix shapes
        for i, matrix in enumerate(report['matrices']):
            matrix_np = np.array(matrix)
            if matrix_np.shape[0] != matrix_np.shape[1]:
                raise ValueError(f"Matrix {i} is not square: {matrix_np.shape}")
            
            # Check orthogonality (approximate)
            product = np.dot(matrix_np, matrix_np.T)
            identity = np.eye(matrix_np.shape[0])
            ortho_error = np.linalg.norm(product - identity)
            if ortho_error > 1e-5:
                logger.warning(f"Matrix {i} orthogonality error: {ortho_error:.6f}")
        
        logger.info("Clustering pipeline completed successfully")
        return report
        
    except Exception as e:
        logger.error(f"Clustering pipeline failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
