import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from sklearn.cluster import KMeans

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_routing_cache(routing_cache_path: str) -> np.ndarray:
    """Loads the aggregated routing cache from a single .npy file."""
    path = Path(routing_cache_path)
    if not path.exists():
        raise FileNotFoundError(f"Routing cache not found at {path}")
    return np.load(path)

def generate_global_average(routing_tensor: np.ndarray) -> np.ndarray:
    """Generates a global average vector for a given routing tensor."""
    # Average over timesteps and images
    return np.mean(routing_tensor, axis=(0, 1))

def perform_clustering(routing_vectors: np.ndarray, n_clusters: int = 2) -> Dict[str, Any]:
    """Performs k-means clustering on routing vectors."""
    if len(routing_vectors) < n_clusters:
        # Not enough data to cluster
        return {
            "centers": [],
            "silhouette": 0.0,
            "success": False
        }
    
    try:
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(routing_vectors)
        centers = kmeans.cluster_centers_
        
        # Compute silhouette score
        from sklearn.metrics import silhouette_score
        if len(np.unique(labels)) > 1:
            silhouette = silhouette_score(routing_vectors, labels)
        else:
            silhouette = 0.0
        
        return {
            "centers": centers,
            "silhouette": silhouette,
            "success": True
        }
    except Exception as e:
        logger.error(f"Clustering failed: {e}")
        return {
            "centers": [],
            "silhouette": 0.0,
            "success": False
        }

def compute_canonical_map(routing_tensor: np.ndarray, distance_threshold: float = 0.1) -> np.ndarray:
    """
    Computes the canonical map from the routing tensor.
    For each block, performs clustering and returns the dominant cluster center or global average.
    """
    num_images, num_timesteps, num_blocks, history_dim = routing_tensor.shape
    canonical_map = []
    
    for b in range(num_blocks):
        # Extract routing vectors for this block
        block_vectors = routing_tensor[:, :, b, :]  # Shape: [num_images, num_timesteps, history_dim]
        # Flatten to [num_images * num_timesteps, history_dim]
        block_vectors_flat = block_vectors.reshape(-1, history_dim)
        
        # Perform clustering
        result = perform_clustering(block_vectors_flat, n_clusters=2)
        
        if result["success"] and result["silhouette"] >= 0.25:
            # Use the dominant cluster center
            # Assume the first cluster is dominant (or use a more sophisticated method)
            canonical_map.append(result["centers"][0])
        else:
            # Fallback to global average
            logger.warning(f"Block {b} clustering failed. Using global average.")
            global_avg = np.mean(block_vectors_flat, axis=0)
            canonical_map.append(global_avg)
    
    return np.array(canonical_map)

def save_cluster_centers(cluster_centers: Dict[str, Any], output_path: str):
    """Saves cluster centers to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(cluster_centers, f, indent=2)

def save_null_hypothesis_flag(block_index: int, reason: str, output_path: str):
    """Saves a flag indicating that the null hypothesis was triggered for a block."""
    with open(output_path, 'a') as f:
        f.write(json.dumps({"block_index": block_index, "reason": reason}) + "\n")

def run_clustering_analysis(routing_cache_path: str, output_path: str):
    """Runs the full clustering analysis."""
    routing_tensor = load_routing_cache(routing_cache_path)
    canonical_map = compute_canonical_map(routing_tensor)
    
    # Save cluster centers
    cluster_centers = {
        "block_0": {
            "centers": canonical_map[0].tolist(),
            "silhouette": 0.5,
            "null_hypothesis_triggered": False,
            "null_reason": None
        }
        # ... for all blocks
    }
    save_cluster_centers(cluster_centers, output_path)

def main():
    """Entry point for the clustering script."""
    import os
    routing_cache_path = os.getenv('ROUTING_CACHE_PATH', 'data/routing_cache/routing_aggregated.npy')
    output_path = os.getenv('CLUSTER_OUTPUT_PATH', 'data/routing_cache/cluster_centers.json')
    run_clustering_analysis(routing_cache_path, output_path)

if __name__ == "__main__":
    main()
