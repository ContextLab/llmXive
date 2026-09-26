import os
import json
import logging
import csv
import torch
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist, squareform
from sklearn.preprocessing import StandardScaler

from config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def compute_activation_histograms(activations: torch.Tensor, bins: int = 50) -> np.ndarray:
    """
    Compute a normalized histogram of activation values.
    
    Args:
        activations: Tensor of shape (batch, channels) or (batch, seq_len, channels)
        bins: Number of histogram bins
        
    Returns:
        Normalized histogram array
    """
    if activations.dim() > 2:
        activations = activations.view(activations.size(0), -1)
    
    # Flatten to 1D for histogramming across all samples
    flat = activations.detach().cpu().numpy().flatten()
    
    # Compute histogram
    hist, _ = np.histogram(flat, bins=bins, density=True)
    return hist

def compute_rotation_matrix_from_activations(activations: torch.Tensor, k: int = 16) -> np.ndarray:
    """
    Compute a rotation matrix based on the covariance structure of activations.
    Uses PCA-like decomposition to find principal axes, then constructs a rotation.
    
    Args:
        activations: Tensor of shape (batch, features)
        k: Number of principal components to use for rotation basis
        
    Returns:
        Rotation matrix of shape (features, features)
    """
    if activations.dim() > 2:
        activations = activations.view(activations.size(0), -1)
    
    X = activations.detach().cpu().numpy().astype(np.float32)
    
    # Center the data
    mean = np.mean(X, axis=0, keepdims=True)
    X_centered = X - mean
    
    # Compute covariance matrix
    cov = np.cov(X_centered.T)
    
    # Eigendecomposition
    eigenvalues, eigenvectors = np.linalg.eigh(cov)
    
    # Sort by eigenvalues descending
    idx = np.argsort(eigenvalues)[::-1]
    eigenvectors = eigenvectors[:, idx]
    
    # Take top k eigenvectors
    top_k = eigenvectors[:, :k]
    
    # Construct a rotation matrix (orthogonal basis)
    # For k < d, we need to complete the basis. We'll use the top k eigenvectors
    # and fill the rest with identity-like orthogonal vectors for stability.
    d = X.shape[1]
    rotation = np.eye(d, dtype=np.float32)
    
    # Replace the first k columns with top eigenvectors
    rotation[:, :k] = top_k
    
    return rotation

def run_clustering_pipeline(
    activations_path: str,
    output_path: str,
    k_clusters: int = 16,
    n_bins: int = 50
) -> Dict[str, Any]:
    """
    Main pipeline to cluster activations and generate rotation matrices.
    
    1. Load activations from CSV
    2. Compute histograms for each sample
    3. Cluster histograms into K groups
    4. Compute a representative rotation matrix for each cluster
    5. Save results to JSON
    
    Args:
        activations_path: Path to CSV containing activation data
        output_path: Path to save the clustering report JSON
        k_clusters: Number of clusters (K)
        n_bins: Number of histogram bins
        
    Returns:
        Dictionary containing the clustering report
    """
    logger.info(f"Loading activations from {activations_path}")
    
    # Load activations
    # Expected CSV format: sample_id, layer_name, activation_values (comma-separated floats)
    # Or: sample_id, layer_name, val1, val2, ..., valN
    
    layers_data = {}
    
    with open(activations_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sample_id = row['sample_id']
            layer_name = row['layer_name']
            
            # Parse activation values
            if 'activations' in row:
                # If stored as a string of comma-separated values
                vals = np.array([float(x) for x in row['activations'].split(',')])
            else:
                # If stored as separate columns
                val_cols = [k for k in row.keys() if k.startswith('val_')]
                if val_cols:
                    vals = np.array([float(row[c]) for c in sorted(val_cols)])
                else:
                    # Fallback: try to parse all numeric columns
                    vals = np.array([float(v) for k, v in row.items() if k not in ['sample_id', 'layer_name'] and v.replace('.', '').replace('-', '').isdigit()])
            
            if layer_name not in layers_data:
                layers_data[layer_name] = []
            layers_data[layer_name].append(vals)
    
    logger.info(f"Loaded activations for {len(layers_data)} layers")
    
    report = {
        "layers": [],
        "clusters_per_layer": k_clusters,
        "histogram_bins": n_bins
    }
    
    for layer_name, samples in layers_data.items():
        logger.info(f"Processing layer: {layer_name}")
        
        if not samples:
            continue
        
        # Stack into a matrix: (n_samples, n_features)
        # Ensure all samples have same length
        max_len = max(len(s) for s in samples)
        padded_samples = []
        for s in samples:
            if len(s) < max_len:
                s = np.pad(s, (0, max_len - len(s)), mode='constant', constant_values=0)
            padded_samples.append(s)
        
        X = np.stack(padded_samples, axis=0)
        X_tensor = torch.from_numpy(X)
        
        # Compute histograms for clustering features
        histograms = []
        for i in range(X.shape[0]):
            hist = compute_activation_histograms(X_tensor[i:i+1], bins=n_bins)
            histograms.append(hist)
        
        H = np.array(histograms)
        
        # Scale histograms for clustering
        scaler = StandardScaler()
        H_scaled = scaler.fit_transform(H)
        
        # Hierarchical clustering
        # Compute pairwise distances
        distances = pdist(H_scaled, metric='euclidean')
        linkage_matrix = linkage(distances, method='ward')
        
        # Form flat clusters
        labels = fcluster(linkage_matrix, k_clusters, criterion='maxclust')
        
        # Create cluster subsets
        subsets = {}
        for k in range(1, k_clusters + 1):
            indices = np.where(labels == k)[0].tolist()
            subsets[str(k)] = {
                "size": len(indices),
                "sample_indices": indices
            }
        
        # Compute rotation matrices for each cluster
        cluster_matrices = {}
        boundaries = {}
        
        for k in range(1, k_clusters + 1):
            indices = np.where(labels == k)[0]
            if len(indices) == 0:
                continue
            
            cluster_X = X_tensor[indices]
            rotation_matrix = compute_rotation_matrix_from_activations(cluster_X, k=16)
            
            cluster_matrices[str(k)] = rotation_matrix.tolist()
            
            # Define boundaries based on histogram centroids
            cluster_hists = H[indices]
            centroid = np.mean(cluster_hists, axis=0)
            boundaries[str(k)] = centroid.tolist()
        
        layer_report = {
            "name": layer_name,
            "n_samples": len(samples),
            "feature_dim": X.shape[1],
            "subsets": subsets,
            "boundaries": boundaries,
            "matrices": cluster_matrices
        }
        
        report["layers"].append(layer_report)
        logger.info(f"Completed layer {layer_name}: {len(subsets)} clusters")
    
    # Save report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Clustering report saved to {output_path}")
    return report

def main():
    """
    Entry point for the clustering pipeline.
    Reads activations from data/processed/activations_for_clustering.csv
    and writes report to data/processed/clustering_report.json
    """
    config = Config()
    
    activations_path = config.activated_data_path / "activations_for_clustering.csv"
    output_path = config.processed_data_path / "clustering_report.json"
    
    if not activations_path.exists():
        raise FileNotFoundError(
            f"Activations file not found: {activations_path}. "
            "Please run code/data/generate_activations_for_clustering.py first."
        )
    
    logger.info("Starting clustering pipeline...")
    report = run_clustering_pipeline(
        activations_path=str(activations_path),
        output_path=str(output_path),
        k_clusters=16,
        n_bins=50
    )
    
    logger.info("Clustering pipeline completed successfully.")
    return report

if __name__ == "__main__":
    main()