"""
Clustering analysis for routing tensors.

This module loads recorded routing tensors from the tracing phase,
computes mean routing vectors across all images/blocks for each timestep,
applies k-means clustering to group timesteps, computes silhouette scores,
and handles the null hypothesis case.
"""
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_routing_cache(cache_dir: str) -> List[np.ndarray]:
    """
    Load all routing tensors from the cache directory.
    
    Args:
        cache_dir: Path to the routing cache directory.
        
    Returns:
        Dictionary mapping image indices to routing tensors.
        Each tensor has shape [num_blocks, num_timesteps, history_dim].
    """
    cache_path = Path(cache_dir)
    if not cache_path.exists():
        raise FileNotFoundError(f"Routing cache directory not found: {cache_dir}")
    
    routing_data = {}
    npy_files = list(cache_path.glob("*.npy"))
    pt_files = list(cache_path.glob("*.pt"))
    
    if not npy_files and not pt_files:
        raise ValueError(f"No routing data files (.npy or .pt) found in {cache_dir}")
    
    logger.info(f"Loading {len(npy_files)} .npy files and {len(pt_files)} .pt files")
    
    for file_path in npy_files:
        try:
            tensor = np.load(file_path)
            # Extract index from filename (e.g., "image_001.npy" -> 1)
            index = int(file_path.stem.split('_')[1])
            routing_data[index] = tensor
            logger.debug(f"Loaded {file_path.name}: shape {tensor.shape}")
        except Exception as e:
            logger.warning(f"Failed to load {file_path}: {e}")
    
    for file_path in pt_files:
        try:
            import torch
            tensor = torch.load(file_path, map_location='cpu')
            if isinstance(tensor, torch.Tensor):
                tensor = tensor.numpy()
            index = int(file_path.stem.split('_')[1])
            routing_data[index] = tensor
            logger.debug(f"Loaded {file_path.name}: shape {tensor.shape}")
        except Exception as e:
            logger.warning(f"Failed to load {file_path}: {e}")
    
    if not routing_data:
        raise ValueError(f"No valid routing data could be loaded from {cache_dir}")
    
    logger.info(f"Successfully loaded routing data for {len(routing_data)} images")
    return routing_data

    routing_tensors = []
    files = sorted([f for f in cache_path.iterdir() if f.suffix in ['.npy', '.pt']])
    
    Args:
        routing_data: Dictionary mapping image indices to routing tensors of shape
                    [num_blocks, num_timesteps, history_dim].
                    
    Returns:
        Mean routing vector of shape [num_timesteps, history_dim].
    """
    if not routing_data:
        raise ValueError("No routing data provided")
    
    # Collect all tensors
    all_tensors = list(routing_data.values())
    
    # Determine dimensions from the first tensor
    first_shape = all_tensors[0].shape
    if len(first_shape) != 3:
        raise ValueError(f"Expected 3D tensors [blocks, timesteps, history_dim], got shape {first_shape}")
    
    num_blocks, num_timesteps, history_dim = first_shape
    
    # Stack all tensors: [num_images, num_blocks, num_timesteps, history_dim]
    stacked = np.stack(all_tensors, axis=0)
    
    # Mean across images and blocks: [num_timesteps, history_dim]
    mean_vectors = np.mean(stacked, axis=(0, 1))
    
    logger.info(f"Computed mean routing vectors: shape {mean_vectors.shape}")
    return mean_vectors

def perform_clustering(
    mean_vectors: np.ndarray,
    distance_threshold: float = 0.1,
    max_clusters: int = 10
) -> Tuple[Optional[KMeans], int, float]:
    """
    Apply k-means clustering to group timesteps based on mean routing vectors.
    Returns (model, k, silhouette_score) or (None, 0, -1.0) if clustering fails.
    """
    num_timesteps = mean_vectors.shape[0]
    
    Args:
        mean_vectors: Mean routing vectors of shape [num_timesteps, history_dim].
        max_k: Maximum number of clusters to try.
        
    Returns:
        Tuple of (best_kmeans_model, silhouette_score, best_k)
        Returns (None, -1.0, 0) if clustering is not feasible.
    """
    num_timesteps = mean_vectors.shape[0]
    
    # Cannot cluster if we have fewer than 2 timesteps
    if num_timesteps < 2:
        logger.warning("Not enough timesteps to perform clustering (need >= 2)")
        return None, -1.0, 0
    
    # Try different k values and pick the one with best silhouette score
    best_score = -1
    best_k = 1
    best_model = None
    
    # Only try k from 2 to min(max_k, num_timesteps)
    k_range = range(2, min(max_k + 1, num_timesteps + 1))
    
    logger.info(f"Trying k values from 2 to {min(max_k, num_timesteps)}")
    
    for k in k_range:
        try:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
            labels = kmeans.fit_predict(mean_vectors)
            
            # Compute silhouette score
            score = silhouette_score(mean_vectors, labels)
            logger.info(f"k={k}: silhouette_score={score:.4f}")
            
            if score > best_score:
                best_score = score
                best_k = k
                best_model = kmeans
        except Exception as e:
            logger.warning(f"Failed to cluster with k={k}: {e}")
            continue
    
    logger.info(f"Best clustering: k={best_k}, silhouette_score={best_score:.4f}")
    return best_model, best_k, best_score

def generate_global_average(mean_vectors: np.ndarray) -> np.ndarray:
    """
    Generate a global average routing vector as a fallback.
    
    Args:
        mean_vectors: Mean routing vectors of shape [num_timesteps, history_dim].
        
    Returns:
        Global average vector of shape [history_dim].
    """
    global_avg = np.mean(mean_vectors, axis=0)
    logger.info(f"Generated global average vector: shape {global_avg.shape}")
    return global_avg

def save_cluster_centers(model: KMeans, output_path: str) -> None:
    """
    Save cluster centers to a JSON file.
    
    Args:
        model: Trained KMeans model.
        output_path: Path to save the cluster centers.
    """
    centers = model.cluster_centers_
    output_data = {
        "num_clusters": model.n_clusters,
        "cluster_centers": centers.tolist(),
        "feature_dim": centers.shape[1]
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Saved cluster centers to {output_path}")

def save_null_hypothesis_flag(score: float, k: int, output_path: str) -> None:
    """
    Save a flag indicating whether the null hypothesis was triggered.
    
    Args:
        score: Silhouette score.
        k: Number of clusters found.
        output_path: Path to save the flag file.
    """
    is_null = (k < 2) or (score < 0.25)
    
    flag_data = {
        "null_hypothesis_triggered": is_null,
        "silhouette_score": float(score),
        "num_clusters": k,
        "threshold": 0.25,
        "reason": "Silhouette score below threshold" if score < 0.25 else ("Insufficient clusters" if k < 2 else "None")
    }
    
    with open(output_path, 'w') as f:
        json.dump(flag_data, f, indent=2)
    
    logger.info(f"Saved null hypothesis flag to {output_path}: {is_null}")

def run_clustering_analysis(
    cache_dir: str,
    cluster_output_path: str,
    flag_output_path: str,
    max_k: int = 10
) -> Dict[str, Any]:
    """
    Run the full clustering analysis pipeline.
    
    Args:
        cache_dir: Path to routing cache directory.
        cluster_output_path: Path to save cluster centers.
        flag_output_path: Path to save null hypothesis flag.
        max_k: Maximum number of clusters to try.
        
    Returns:
        Dictionary with analysis results.
    """
    logger.info("Starting clustering analysis")
    
    # Load routing tensors
    logger.info(f"Loading routing tensors from {cache_dir}")
    routing_tensors = load_routing_cache(str(cache_path))
    
    # Compute mean routing vectors
    logger.info("Computing mean routing vectors")
    mean_vectors = compute_mean_routing_vectors(routing_tensors)
    
    # Perform clustering
    model, score, k = perform_clustering(mean_vectors, max_k)
    
    # Check for null hypothesis
    is_null = (k < 2) or (score < 0.25)
    
    if is_null:
        logger.warning(f"Null hypothesis triggered: k={k}, score={score:.4f}")
        # Generate global average
        global_avg = generate_global_average(mean_vectors)
        
        # Save null hypothesis flag
        save_null_hypothesis_flag(score, k, flag_output_path)
        
        # For null case, we save the global average as a single "cluster"
        # This allows downstream tasks to use it
        output_data = {
            "num_clusters": 1,
            "cluster_centers": [global_avg.tolist()],
            "feature_dim": global_avg.shape[0],
            "is_null_hypothesis": True,
            "silhouette_score": float(score)
        }
        
        with open(cluster_output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Saved global average to {cluster_output_path}")
        
        return {
            "is_null": True,
            "silhouette_score": score,
            "num_clusters": 1,
            "global_average": global_avg.tolist()
        }
    else:
        logger.info(f"Clustering successful: k={k}, score={score:.4f}")
        
        # Save cluster centers
        save_cluster_centers(model, cluster_output_path)
        
        # Save null hypothesis flag (not triggered)
        save_null_hypothesis_flag(score, k, flag_output_path)
        
        return {
            "is_null": False,
            "silhouette_score": score,
            "num_clusters": k,
            "cluster_centers": model.cluster_centers_.tolist()
        }
    
    # Save cluster centers for valid clustering
    centers_path = Path(output_dir) / "cluster_centers.json"
    save_cluster_centers(model, silhouette_score, str(centers_path))
    
    logger.info(f"Silhouette score: {silhouette_score:.4f}")
    
    return {
        "is_null_hypothesis": False,
        "k": k,
        "silhouette_score": float(silhouette_score),
        "centers_path": str(centers_path),
        "model": model
    }

def main():
    """Main entry point for clustering analysis."""
    # Get paths from environment or use defaults
    cache_dir = os.environ.get("ROUTING_CACHE_DIR", "data/routing_cache")
    cluster_output = os.environ.get("CLUSTER_OUTPUT_PATH", "data/routing_cache/cluster_centers.json")
    flag_output = os.environ.get("NULL_FLAG_PATH", "data/results/null_hypothesis_flag.json")
    max_k = int(os.environ.get("MAX_CLUSTERS", 10))
    
    # Ensure output directories exist
    Path(cluster_output).parent.mkdir(parents=True, exist_ok=True)
    Path(flag_output).parent.mkdir(parents=True, exist_ok=True)
    
    try:
        results = run_clustering_analysis(
            cache_dir=cache_dir,
            cluster_output_path=cluster_output,
            flag_output_path=flag_output,
            max_k=max_k
        )
        
        # Print silhouette score as required
        print(f"Silhouette Score: {results['silhouette_score']:.4f}")
        print(f"Number of Clusters: {results['num_clusters']}")
        print(f"Null Hypothesis Triggered: {results['is_null']}")
        
        logger.info("Clustering analysis completed successfully")
        
    except Exception as e:
        logger.error(f"Clustering analysis failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
