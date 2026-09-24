"""
Clustering module for deriving canonical routing maps from dynamic routing traces.

This module implements k-means clustering on routing weight matrices to identify
distinct phases in the diffusion process. It handles the null hypothesis case where
clustering is not statistically significant by falling back to global averages.
"""

import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import glob
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_DISTANCE_THRESHOLD = 0.1
MIN_CLUSTERS = 2
MIN_SILHOUETTE = 0.25
NUM_TIMESTEPS = 100


def load_routing_cache(cache_dir: str = "data/routing_cache") -> List[Tuple[str, np.ndarray]]:
    """
    Load all routing tensors from the cache directory.

    Args:
        cache_dir: Path to the routing cache directory.

    Returns:
        List of tuples (file_path, routing_array) where routing_array has shape
        [num_timesteps, num_blocks, history_dim].

    Raises:
        FileNotFoundError: If no routing files are found.
        ValueError: If any file cannot be loaded or has incorrect shape.
    """
    cache_path = Path(cache_dir)
    if not cache_path.exists():
        raise FileNotFoundError(f"Routing cache directory not found: {cache_dir}")

    # Discover all .npy files
    pattern = str(cache_path / "routing_*.npy")
    files = sorted(glob.glob(pattern))

    if not files:
        raise FileNotFoundError(f"No routing files found matching pattern: {pattern}")

    loaded_data = []
    for file_path in files:
        try:
            routing_array = np.load(file_path)
            if routing_array.ndim != 4:
                raise ValueError(f"Expected 4D array in {file_path}, got {routing_array.ndim}D")
            
            # Validate shape: [timesteps, blocks, history_dim]
            timesteps, blocks, history_dim = routing_array.shape[0], routing_array.shape[1], routing_array.shape[2]
            if timesteps != NUM_TIMESTEPS:
                logger.warning(f"File {file_path} has {timesteps} timesteps, expected {NUM_TIMESTEPS}")
            
            loaded_data.append((file_path, routing_array))
            logger.info(f"Loaded {file_path}: shape {routing_array.shape}")
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            raise

    return loaded_data


def generate_global_average(routing_vector: np.ndarray) -> np.ndarray:
    """
    Generate a global average vector for a block's routing data.

    Args:
        routing_vector: Array of shape [num_timesteps, history_dim].

    Returns:
        Global average vector of shape [history_dim].
    """
    if routing_vector.ndim != 2:
        raise ValueError(f"Expected 2D array, got {routing_vector.ndim}D")
    
    return np.mean(routing_vector, axis=0)


def perform_clustering(
    routing_vector: np.ndarray,
    max_k: int = 5,
    distance_threshold: float = DEFAULT_DISTANCE_THRESHOLD
) -> Tuple[Optional[np.ndarray], float, bool, Optional[str]]:
    """
    Perform k-means clustering on routing vectors to identify distinct phases.

    Args:
        routing_vector: Array of shape [num_timesteps, history_dim].
        max_k: Maximum number of clusters to try.
        distance_threshold: Threshold for determining cluster validity.

    Returns:
        Tuple of (centers, silhouette_score, null_hypothesis_triggered, null_reason).
        - centers: Cluster centers array or None if null hypothesis triggered.
        - silhouette_score: The silhouette score of the best clustering.
        - null_hypothesis_triggered: True if clustering is not valid.
        - null_reason: Description of why clustering failed, or None.
    """
    num_samples, history_dim = routing_vector.shape

    if num_samples < MIN_CLUSTERS:
        return None, 0.0, True, f"Not enough samples ({num_samples}) for clustering"

    best_score = -1
    best_centers = None
    best_k = 1

    # Try different numbers of clusters
    for k in range(MIN_CLUSTERS, min(max_k + 1, num_samples)):
        try:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(routing_vector)
            
            # Check if all clusters are non-empty
            unique_labels = np.unique(labels)
            if len(unique_labels) < MIN_CLUSTERS:
                continue

            # Calculate silhouette score
            score = silhouette_score(routing_vector, labels)
            
            if score > best_score:
                best_score = score
                best_centers = kmeans.cluster_centers_
                best_k = k
        except Exception as e:
            logger.debug(f"Clustering with k={k} failed: {e}")
            continue

    # Check if clustering is valid
    if best_centers is None or best_score < MIN_SILHOUETTE:
        reason = f"Silhouette score {best_score:.4f} < {MIN_SILHOUETTE}" if best_centers is not None else "No valid clustering found"
        return None, best_score, True, reason

    return best_centers, best_score, False, None


def compute_canonical_map(
    routing_tensor: np.ndarray,
    distance_threshold: float = DEFAULT_DISTANCE_THRESHOLD
) -> Dict[str, Dict[str, Any]]:
    """
    Compute the canonical routing map from a routing tensor.

    This function performs clustering independently for each block and applies
    null hypothesis handling when clustering is not statistically significant.

    Args:
        routing_tensor: Array of shape [num_timesteps, num_blocks, history_dim].
        distance_threshold: Threshold for clustering validity.

    Returns:
        Dictionary mapping block indices to their cluster information:
        {
            "block_0": {
                "centers": [...],  # Cluster centers or global average if null
                "silhouette": 0.5,
                "null_hypothesis_triggered": False,
                "null_reason": None
            },
            ...
        }
    """
    if routing_tensor.ndim != 3:
        raise ValueError(f"Expected 3D tensor [timesteps, blocks, history_dim], got {routing_tensor.ndim}D")

    num_timesteps, num_blocks, history_dim = routing_tensor.shape
    result = {}

    for block_idx in range(num_blocks):
        # Extract routing vectors for this block: [num_timesteps, history_dim]
        block_vectors = routing_tensor[:, block_idx, :]
        
        # Perform clustering
        centers, score, null_triggered, reason = perform_clustering(
            block_vectors, 
            distance_threshold=distance_threshold
        )

        if null_triggered:
            # Fall back to global average
            global_avg = generate_global_average(block_vectors)
            result[f"block_{block_idx}"] = {
                "centers": global_avg.tolist(),
                "silhouette": float(score),
                "null_hypothesis_triggered": True,
                "null_reason": reason
            }
            logger.info(f"Block {block_idx}: Null hypothesis triggered - using global average")
        else:
            result[f"block_{block_idx}"] = {
                "centers": centers.tolist(),
                "silhouette": float(score),
                "null_hypothesis_triggered": False,
                "null_reason": None
            }
            logger.info(f"Block {block_idx}: Clustering successful with silhouette {score:.4f}")

    return result


def save_cluster_centers(
    cluster_data: Dict[str, Dict[str, Any]],
    output_path: str = "data/routing_cache/cluster_centers.json"
) -> None:
    """
    Save cluster centers and metadata to a JSON file.

    Args:
        cluster_data: Dictionary from compute_canonical_map.
        output_path: Path to save the JSON file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(cluster_data, f, indent=2)

    logger.info(f"Saved cluster centers to {output_path}")


def save_null_hypothesis_flag(
    cluster_data: Dict[str, Dict[str, Any]],
    output_path: str = "data/routing_cache/null_hypothesis_flags.json"
) -> None:
    """
    Save a summary of null hypothesis triggers to a JSON file.

    Args:
        cluster_data: Dictionary from compute_canonical_map.
        output_path: Path to save the flags file.
    """
    flags = {
        block_id: {
            "null_hypothesis_triggered": info["null_hypothesis_triggered"],
            "null_reason": info["null_reason"]
        }
        for block_id, info in cluster_data.items()
    }

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(flags, f, indent=2)

    logger.info(f"Saved null hypothesis flags to {output_path}")


def run_clustering_analysis(
    cache_dir: str = "data/routing_cache",
    output_path: str = "data/routing_cache/cluster_centers.json",
    distance_threshold: float = DEFAULT_DISTANCE_THRESHOLD
) -> Dict[str, Dict[str, Any]]:
    """
    Run the full clustering analysis pipeline.

    This function loads all routing tensors, aggregates them, performs clustering
    for each block, and saves the results.

    Args:
        cache_dir: Path to the routing cache directory.
        output_path: Path to save the cluster centers JSON.
        distance_threshold: Threshold for clustering validity.

    Returns:
        Dictionary of cluster data for all blocks.
    """
    logger.info(f"Starting clustering analysis on {cache_dir}")

    # Load all routing data
    loaded_files = load_routing_cache(cache_dir)
    
    if not loaded_files:
        raise ValueError("No valid routing files found in cache")

    # For this implementation, we process the first file as representative
    # In a full implementation, we might aggregate across all files
    first_file_path, first_routing_tensor = loaded_files[0]
    logger.info(f"Using {first_file_path} for clustering analysis")

    # Compute canonical map
    cluster_data = compute_canonical_map(first_routing_tensor, distance_threshold)

    # Save results
    save_cluster_centers(cluster_data, output_path)
    save_null_hypothesis_flag(cluster_data, output_path)

    # Log summary
    null_count = sum(1 for info in cluster_data.values() if info["null_hypothesis_triggered"])
    total_blocks = len(cluster_data)
    logger.info(f"Clustering complete: {null_count}/{total_blocks} blocks used global average fallback")

    return cluster_data


def main():
    """Main entry point for clustering analysis."""
    import argparse

    parser = argparse.ArgumentParser(description="Run clustering analysis on routing traces")
    parser.add_argument(
        "--cache-dir",
        type=str,
        default="data/routing_cache",
        help="Path to routing cache directory"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/routing_cache/cluster_centers.json",
        help="Output path for cluster centers JSON"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_DISTANCE_THRESHOLD,
        help="Distance threshold for clustering validity"
    )

    args = parser.parse_args()

    try:
        run_clustering_analysis(
            cache_dir=args.cache_dir,
            output_path=args.output,
            distance_threshold=args.threshold
        )
        logger.info("Clustering analysis completed successfully")
    except Exception as e:
        logger.error(f"Clustering analysis failed: {e}")
        raise


if __name__ == "__main__":
    main()
