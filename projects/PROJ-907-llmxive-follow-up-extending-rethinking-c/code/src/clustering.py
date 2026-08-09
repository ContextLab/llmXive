import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_routing_cache(cache_dir: str) -> List[np.ndarray]:
    """
    Load all .npy or .pt files from the routing cache directory.
    Returns a list of numpy arrays.
    """
    cache_path = Path(cache_dir)
    if not cache_path.exists():
        raise FileNotFoundError(f"Routing cache directory not found: {cache_path}")
    
    tensors = []
    for file_path in cache_path.glob("*.npy"):
        logger.info(f"Loading {file_path}")
        tensors.append(np.load(file_path))
    
    for file_path in cache_path.glob("*.pt"):
        import torch
        logger.info(f"Loading {file_path}")
        tensor = torch.load(file_path, map_location='cpu')
        if isinstance(tensor, torch.Tensor):
            tensors.append(tensor.numpy())
        else:
            # Handle dict/list structures if necessary, assuming single tensor per file for now
            logger.warning(f"Skipping non-tensor object in {file_path}")
    
    if not tensors:
        raise ValueError(f"No routing tensors found in {cache_path}")
    
    return tensors

def compute_mean_routing_vectors(tensors: List[np.ndarray]) -> np.ndarray:
    """
    Compute the mean routing vector across all images/blocks for each timestep.
    Input: List of arrays with shape [blocks, timesteps, history_dim]
    Output: Array with shape [timesteps, history_dim]
    """
    if not tensors:
        raise ValueError("No tensors provided to compute mean routing vectors.")
    
    # Stack all tensors: shape [num_images, blocks, timesteps, history_dim]
    stacked = np.stack(tensors, axis=0)
    num_images, num_blocks, num_timesteps, history_dim = stacked.shape
    
    logger.info(f"Stacked shape: {stacked.shape}")
    
    # Mean over images and blocks -> [timesteps, history_dim]
    # axis 0 (images) and axis 1 (blocks)
    mean_vectors = np.mean(stacked, axis=(0, 1))
    
    logger.info(f"Mean vectors shape: {mean_vectors.shape}")
    return mean_vectors

def perform_clustering(mean_vectors: np.ndarray, min_k: int = 2, max_k: int = 10) -> Tuple[Optional[np.ndarray], Optional[int], float]:
    """
    Apply k-means clustering to group timesteps based on the mean vector.
    Returns (cluster_centers, best_k, silhouette_score) or (None, None, -1.0) if null hypothesis.
    """
    n_timesteps = mean_vectors.shape[0]
    
    # Null hypothesis check 1: Not enough timesteps to cluster meaningfully
    if n_timesteps < min_k:
        logger.warning(f"Null Hypothesis: Number of timesteps ({n_timesteps}) < min_k ({min_k}).")
        return None, None, -1.0
    
    best_score = -1.0
    best_k = None
    best_centers = None
    best_labels = None
    
    # Try different k values to find the best silhouette score
    # We only care if we can find a valid clustering (k >= 2 and score >= 0.25)
    search_range = range(min_k, min(max_k + 1, n_timesteps))
    
    for k in search_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(mean_vectors)
        score = silhouette_score(mean_vectors, labels)
        
        logger.info(f"K={k}, Silhouette Score={score:.4f}")
        
        if score > best_score:
            best_score = score
            best_k = k
            best_centers = kmeans.cluster_centers_
            best_labels = labels
    
    # Null hypothesis check 2: Silhouette score too low
    if best_score < 0.25:
        logger.warning(f"Null Hypothesis: Best silhouette score ({best_score:.4f}) < 0.25.")
        return None, None, best_score
    
    logger.info(f"Clustering successful: k={best_k}, score={best_score:.4f}")
    return best_centers, best_k, best_score

def generate_global_average(mean_vectors: np.ndarray) -> np.ndarray:
    """
    Generate a global average vector as a fallback for the canonical map.
    Returns an array of shape [history_dim] (or [1, history_dim] for consistency).
    """
    # Mean over timesteps -> [history_dim]
    global_avg = np.mean(mean_vectors, axis=0)
    logger.info(f"Generated global average vector of shape {global_avg.shape}")
    return global_avg

def save_cluster_centers(centers: np.ndarray, k: int, score: float, output_path: str):
    """
    Save cluster centers to a JSON file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        "k": k,
        "silhouette_score": float(score),
        "cluster_centers": centers.tolist()
    }
    
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved cluster centers to {output_file}")

def save_null_hypothesis_flag(score: float, output_path: str):
    """
    Save a flag indicating the null hypothesis condition was met.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        "null_hypothesis_detected": True,
        "reason": "Silhouette score below threshold (0.25) or insufficient timesteps",
        "silhouette_score": float(score),
        "fallback_action": "global_average_vector"
    }
    
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved null hypothesis flag to {output_file}")

def run_clustering_analysis(cache_dir: str, output_dir: str):
    """
    Main orchestration function for clustering analysis.
    1. Load routing tensors.
    2. Compute mean routing vectors.
    3. Perform clustering.
    4. Handle null hypothesis or save results.
    """
    logger.info(f"Starting clustering analysis on {cache_dir}")
    
    # 1. Load
    tensors = load_routing_cache(cache_dir)
    
    # 2. Compute Mean
    mean_vectors = compute_mean_routing_vectors(tensors)
    
    # 3. Cluster
    centers, k, score = perform_clustering(mean_vectors)
    
    # 4. Output
    centers_path = Path(output_dir) / "cluster_centers.json"
    flag_path = Path(output_dir) / "null_hypothesis_flag.json"
    
    if centers is not None and k is not None:
        save_cluster_centers(centers, k, score, str(centers_path))
        print(f"Silhouette score: {score:.4f}")
        logger.info("Clustering completed successfully.")
    else:
        # Null hypothesis case
        logger.warning("Null hypothesis detected. Generating global average vector.")
        save_null_hypothesis_flag(score, str(flag_path))
        
        # Even in null case, we might want to save the global average for downstream use
        # The canonical_map.py task will likely read this or the flag.
        # Let's save the global average as a single cluster center for compatibility
        global_avg = generate_global_average(mean_vectors)
        global_avg_path = Path(output_dir) / "cluster_centers.json" # Overwrite or specific name?
        # T012 spec says: "handle null hypothesis ... by generating global average vector"
        # And "Save cluster centers to data/routing_cache/cluster_centers.json"
        # We will save the global average as the 'center' if null, but flag it.
        # Actually, the spec says "handle ... by generating global average vector".
        # It implies the output should be the global average if clustering fails.
        # Let's save the global average to the same file but note the fallback.
        
        fallback_data = {
            "k": 1,
            "silhouette_score": float(score),
            "fallback": True,
            "cluster_centers": global_avg.tolist()
        }
        with open(global_avg_path, 'w') as f:
            json.dump(fallback_data, f, indent=2)
        
        print(f"Silhouette score: {score:.4f} (Null Hypothesis: Global Average Used)")
        logger.info("Null hypothesis handled. Global average saved.")
    
    return centers, k, score

def main():
    # Default paths relative to project root (assuming script runs from code/)
    # Or use environment variables/config if available.
    # For T012, we assume standard paths defined in tasks.md
    cache_dir = "data/routing_cache"
    output_dir = "data/routing_cache"
    
    run_clustering_analysis(cache_dir, output_dir)

if __name__ == "__main__":
    main()