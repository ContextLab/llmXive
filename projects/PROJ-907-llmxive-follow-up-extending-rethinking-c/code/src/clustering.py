"""
Clustering module for analyzing routing tensors and deriving canonical maps.

This module implements the logic to:
1. Load routing tensors from the cache.
2. Perform k-means clustering on per-block routing vectors.
3. Handle the null hypothesis (low silhouette score or < 2 clusters) by falling back to global averages.
4. Save cluster centers and metadata to JSON.
"""

import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
SILHOUETTE_THRESHOLD = 0.25
MIN_CLUSTERS = 2

def load_routing_cache(cache_dir: str = "data/routing_cache") -> np.ndarray:
    """
    Load all routing tensors from the cache directory into a single 5D tensor.
    
    Args:
        cache_dir: Path to the routing cache directory.
        
    Returns:
        A 5D numpy array of shape [num_images, num_timesteps, num_blocks, history_dim].
        
    Raises:
        FileNotFoundError: If no routing files are found.
    """
    cache_path = Path(cache_dir)
    if not cache_path.exists():
        raise FileNotFoundError(f"Routing cache directory not found: {cache_path}")
        
    files = sorted(cache_path.glob("routing_*.npy"))
    if not files:
        raise FileNotFoundError(f"No routing files found in {cache_path}")
        
    logger.info(f"Loading {len(files)} routing files from {cache_path}")
    
    tensors = []
    for i, file_path in enumerate(files):
        try:
            data = np.load(file_path)
            tensors.append(data)
            logger.debug(f"Loaded {file_path.name}: shape {data.shape}")
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            raise
            
    if len(tensors) == 0:
        raise ValueError("No valid tensors loaded.")
        
    # Stack into 5D tensor [num_images, num_timesteps, num_blocks, history_dim]
    routing_tensor = np.stack(tensors, axis=0)
    logger.info(f"Combined routing tensor shape: {routing_tensor.shape}")
    return routing_tensor

def generate_global_average(routing_tensor: np.ndarray, block_idx: int) -> np.ndarray:
    """
    Compute the global average routing vector for a specific block across all images and timesteps.
    
    Args:
        routing_tensor: The 5D tensor [num_images, num_timesteps, num_blocks, history_dim].
        block_idx: The index of the block to compute the average for.
        
    Returns:
        A 1D numpy array of shape [history_dim] representing the global average.
    """
    # Select the block: [num_images, num_timesteps, 1, history_dim]
    block_data = routing_tensor[:, :, block_idx, :]
    # Reshape to [num_images * num_timesteps, history_dim]
    flat_data = block_data.reshape(-1, block_data.shape[-1])
    # Compute mean across all samples
    global_avg = np.mean(flat_data, axis=0)
    return global_avg

def perform_clustering(
    routing_tensor: np.ndarray, 
    distance_threshold: float = SILHOUETTE_THRESHOLD
) -> Dict[str, Any]:
    """
    Perform k-means clustering on routing vectors for each block.
    
    For each block, we cluster the routing vectors (rows of [num_timesteps, history_dim])
    to identify distinct phases. If the clustering is poor (silhouette < threshold or < 2 clusters),
    we fall back to the global average for that block.
    
    Args:
        routing_tensor: 5D tensor [num_images, num_timesteps, num_blocks, history_dim].
        distance_threshold: Minimum silhouette score required to accept clustering.
        
    Returns:
        A dictionary mapping block indices to their clustering results.
    """
    num_images, num_timesteps, num_blocks, history_dim = routing_tensor.shape
    logger.info(f"Performing clustering on tensor of shape {routing_tensor.shape}")
    
    results = {}
    
    for b in range(num_blocks):
        block_key = f"block_{b}"
        logger.info(f"Processing {block_key}...")
        
        # Extract data for this block: [num_images, num_timesteps, history_dim]
        block_data = routing_tensor[:, :, b, :]
        # Reshape to [num_samples, history_dim] where num_samples = num_images * num_timesteps
        samples = block_data.reshape(-1, history_dim)
        
        # Determine optimal k or try a range? 
        # For this task, we will try k=2 first. If that fails, we might try higher or just fallback.
        # However, the spec says "identify distinct phases". Let's try k=2 first.
        # If silhouette is too low, we fallback.
        
        k = 2
        if samples.shape[0] < k:
            # Not enough samples for k=2
            global_avg = generate_global_average(routing_tensor, b)
            results[block_key] = {
                "centers": global_avg.tolist(),
                "silhouette": -1.0,
                "null_hypothesis_triggered": True,
                "null_reason": "Insufficient samples for clustering"
            }
            logger.warning(f"{block_key}: Insufficient samples ({samples.shape[0]}) for k={k}. Fallback to global average.")
            continue
        
        try:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(samples)
            centers = kmeans.cluster_centers_
            
            # Compute silhouette score
            # Need at least 2 clusters and > 1 sample per cluster for silhouette
            unique_labels = np.unique(labels)
            if len(unique_labels) < 2:
                score = -1.0
            else:
                score = silhouette_score(samples, labels)
            
            null_triggered = False
            null_reason = None
            
            if score < distance_threshold:
                null_triggered = True
                null_reason = f"Silhouette score {score:.4f} < threshold {distance_threshold}"
                # Fallback to global average
                global_avg = generate_global_average(routing_tensor, b)
                centers = global_avg
                logger.warning(f"{block_key}: Silhouette score {score:.4f} too low. Fallback to global average.")
            elif len(unique_labels) < 2:
                null_triggered = True
                null_reason = f"Only {len(unique_labels)} cluster(s) found"
                global_avg = generate_global_average(routing_tensor, b)
                centers = global_avg
                logger.warning(f"{block_key}: Only {len(unique_labels)} cluster found. Fallback to global average.")
            else:
                logger.info(f"{block_key}: Silhouette score {score:.4f}. Clustering accepted.")
            
            results[block_key] = {
                "centers": centers.tolist(),
                "silhouette": float(score),
                "null_hypothesis_triggered": null_triggered,
                "null_reason": null_reason
            }
            
        except Exception as e:
            logger.error(f"{block_key}: Clustering failed with error {e}. Fallback to global average.")
            global_avg = generate_global_average(routing_tensor, b)
            results[block_key] = {
                "centers": global_avg.tolist(),
                "silhouette": -1.0,
                "null_hypothesis_triggered": True,
                "null_reason": f"Clustering error: {str(e)}"
            }
            
    return results

def compute_canonical_map(routing_tensor: np.ndarray, distance_threshold: float = SILHOUETTE_THRESHOLD) -> Dict[str, List[float]]:
    """
    Pure function to compute the canonical map (static weight vector per block).
    
    This function performs clustering and returns the resulting map without file I/O.
    If clustering fails for a block, it returns the global average for that block.
    
    Args:
        routing_tensor: 5D tensor [num_images, num_timesteps, num_blocks, history_dim].
        distance_threshold: Minimum silhouette score required.
        
    Returns:
        A dictionary mapping block keys to their canonical weight vectors (lists of floats).
    """
    clustering_results = perform_clustering(routing_tensor, distance_threshold)
    
    canonical_map = {}
    for block_key, data in clustering_results.items():
        canonical_map[block_key] = data["centers"]
        
    return canonical_map

def save_cluster_centers(results: Dict[str, Any], output_path: str = "data/routing_cache/cluster_centers.json") -> None:
    """
    Save cluster centers and metadata to a JSON file.
    
    Args:
        results: Dictionary of clustering results per block.
        output_path: Path to save the JSON file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Saved cluster centers to {output_path}")

def save_null_hypothesis_flag(results: Dict[str, Any], output_path: str = "data/results/null_hypothesis_flag.json") -> None:
    """
    Save a flag indicating if the null hypothesis was triggered for any block.
    
    Args:
        results: Dictionary of clustering results per block.
        output_path: Path to save the JSON file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if any block triggered null hypothesis
    triggered = any(r.get("null_hypothesis_triggered", False) for r in results.values())
    
    flag_data = {
        "null_hypothesis_triggered_globally": triggered,
        "details": {
            block_key: {
                "null_hypothesis_triggered": data.get("null_hypothesis_triggered", False),
                "null_reason": data.get("null_reason")
            }
            for block_key, data in results.items()
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(flag_data, f, indent=2)
        
    logger.info(f"Saved null hypothesis flag to {output_path}")

def run_clustering_analysis(
    cache_dir: str = "data/routing_cache",
    output_dir: str = "data/routing_cache",
    results_dir: str = "data/results",
    distance_threshold: float = SILHOUETTE_THRESHOLD
) -> Dict[str, Any]:
    """
    Main function to run the full clustering analysis pipeline.
    
    1. Load routing tensors.
    2. Perform clustering.
    3. Save cluster centers.
    4. Save null hypothesis flags.
    
    Args:
        cache_dir: Path to routing cache.
        output_dir: Path to save cluster centers.
        results_dir: Path to save null hypothesis flags.
        distance_threshold: Silhouette threshold.
        
    Returns:
        Dictionary of clustering results.
    """
    # Ensure directories exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path(results_dir).mkdir(parents=True, exist_ok=True)
    
    # Load data
    routing_tensor = load_routing_cache(cache_dir)
    
    # Perform clustering
    results = perform_clustering(routing_tensor, distance_threshold)
    
    # Save outputs
    cluster_centers_path = Path(output_dir) / "cluster_centers.json"
    save_cluster_centers(results, str(cluster_centers_path))
    
    null_flag_path = Path(results_dir) / "null_hypothesis_flag.json"
    save_null_hypothesis_flag(results, str(null_flag_path))
    
    return results

def main():
    """Entry point for the clustering analysis script."""
    import os
    
    # Use environment variables or defaults
    cache_dir = os.getenv("ROUTING_CACHE_DIR", "data/routing_cache")
    output_dir = os.getenv("OUTPUT_DIR", "data/routing_cache")
    results_dir = os.getenv("RESULTS_DIR", "data/results")
    threshold_str = os.getenv("CLUSTERING_THRESHOLD", str(SILHOUETTE_THRESHOLD))
    distance_threshold = float(threshold_str)
    
    logger.info(f"Starting clustering analysis with threshold={distance_threshold}")
    
    try:
        results = run_clustering_analysis(
            cache_dir=cache_dir,
            output_dir=output_dir,
            results_dir=results_dir,
            distance_threshold=distance_threshold
        )
        
        # Print summary
        num_blocks = len(results)
        null_count = sum(1 for r in results.values() if r.get("null_hypothesis_triggered", False))
        logger.info(f"Analysis complete. Processed {num_blocks} blocks. Null hypothesis triggered for {null_count} blocks.")
        
    except Exception as e:
        logger.error(f"Clustering analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
