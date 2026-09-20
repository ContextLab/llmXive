"""
Clustering module for deriving canonical routing maps from traced routing tensors.

This module implements the logic to load routing traces, perform per-block k-means clustering,
handle null hypothesis cases (low silhouette score or insufficient clusters), and save
the resulting cluster centers and metadata.
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
NULL_HYPOTHESIS_SILHOUETTE_THRESHOLD = 0.25
MIN_CLUSTERS = 2


def load_routing_cache(cache_dir: str = "data/routing_cache") -> Tuple[np.ndarray, int, int, int]:
    """
    Load all routing tensors from the cache directory into a single 5D tensor.

    Args:
        cache_dir: Path to the directory containing routing_*.npy files.

    Returns:
        A tuple containing:
            - routing_tensor: 5D numpy array of shape [num_images, num_timesteps, num_blocks, history_dim]
            - num_images: Number of images processed
            - num_timesteps: Number of timesteps per image
            - num_blocks: Number of transformer blocks
            - history_dim: Dimension of the history vector
    """
    cache_path = Path(cache_dir)
    if not cache_path.exists():
        raise FileNotFoundError(f"Routing cache directory not found: {cache_path}")

    npy_files = sorted(glob.glob(str(cache_path / "routing_*.npy")))
    
    if not npy_files:
        raise ValueError(f"No routing_*.npy files found in {cache_path}")

    logger.info(f"Found {len(npy_files)} routing files to load.")

    loaded_tensors = []
    for i, file_path in enumerate(npy_files):
        try:
            data = np.load(file_path)
            if data.ndim != 4:
                logger.warning(f"Skipping {file_path}: expected 4D array, got {data.ndim}D")
                continue
            loaded_tensors.append(data)
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            raise

    if not loaded_tensors:
        raise ValueError("No valid routing tensors were loaded.")

    # Concatenate along the first dimension (images)
    routing_tensor = np.concatenate(loaded_tensors, axis=0)
    
    num_images, num_timesteps, num_blocks, history_dim = routing_tensor.shape
    logger.info(f"Loaded routing tensor with shape: {routing_tensor.shape}")
    
    return routing_tensor, num_images, num_timesteps, num_blocks, history_dim


def generate_global_average(routing_tensor: np.ndarray, block_index: int) -> np.ndarray:
    """
    Compute the global average routing vector for a specific block across all images and timesteps.

    Args:
        routing_tensor: 5D tensor [num_images, num_timesteps, num_blocks, history_dim]
        block_index: Index of the block to compute the average for.

    Returns:
        1D numpy array of shape [history_dim] representing the global average.
    """
    # Select data for the specific block: [num_images, num_timesteps, history_dim]
    block_data = routing_tensor[:, :, block_index, :]
    
    # Compute mean across images and timesteps
    global_avg = np.mean(block_data, axis=(0, 1))
    
    return global_avg


def perform_clustering(
    routing_vectors: np.ndarray,
    k: int = 3,
    random_state: int = 42
) -> Tuple[np.ndarray, float]:
    """
    Perform k-means clustering on a set of routing vectors and compute the silhouette score.

    Args:
        routing_vectors: 2D array [num_samples, history_dim]
        k: Number of clusters
        random_state: Random seed for reproducibility

    Returns:
        A tuple containing:
            - centers: 2D array [k, history_dim] of cluster centers
            - silhouette: Silhouette score (or -1.0 if clustering failed)
    """
    if len(routing_vectors) < k:
        logger.warning(f"Cannot cluster {len(routing_vectors)} samples into {k} clusters.")
        return np.array([]), -1.0

    try:
        kmeans = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        labels = kmeans.fit_predict(routing_vectors)
        centers = kmeans.cluster_centers_

        # Compute silhouette score
        # Need at least 2 samples and 2 clusters for silhouette
        if len(np.unique(labels)) >= 2 and len(routing_vectors) > 1:
            sil_score = silhouette_score(routing_vectors, labels)
        else:
            sil_score = -1.0

        return centers, sil_score

    except Exception as e:
        logger.error(f"Clustering failed: {e}")
        return np.array([]), -1.0


def compute_canonical_map(
    routing_tensor: np.ndarray,
    distance_threshold: float = 0.25,
    max_k: int = 5,
    min_k: int = 2,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Compute the canonical routing map by clustering per-block routing vectors.

    For each block, this function:
    1. Aggregates routing vectors across all images and timesteps.
    2. Attempts k-means clustering for k in [min_k, max_k].
    3. Selects the best k based on silhouette score, subject to the distance_threshold.
    4. If no valid clustering is found (silhouette < threshold or < 2 clusters),
       defaults to the global average vector.

    Args:
        routing_tensor: 5D tensor [num_images, num_timesteps, num_blocks, history_dim]
        distance_threshold: Minimum silhouette score required to accept a clustering result.
        max_k: Maximum number of clusters to try.
        min_k: Minimum number of clusters to try.
        random_state: Random seed for reproducibility.

    Returns:
        A dictionary mapping block indices to their canonical vectors and metadata.
        Structure: {
            "block_0": {
                "centers": [...],
                "silhouette": 0.5,
                "null_hypothesis_triggered": false,
                "null_reason": null,
                "k_used": 3
            },
            ...
        }
    """
    num_images, num_timesteps, num_blocks, history_dim = routing_tensor.shape
    logger.info(f"Computing canonical map for {num_blocks} blocks.")

    result = {}

    for b in range(num_blocks):
        block_id = f"block_{b}"
        
        # Extract routing vectors for this block: [num_images * num_timesteps, history_dim]
        # We flatten the first two dimensions to treat every (image, timestep) as a sample
        block_data = routing_tensor[:, :, b, :]
        vectors = block_data.reshape(-1, history_dim)

        # Try different k values to find the best clustering
        best_k = None
        best_silhouette = -1.0
        best_centers = None

        # If we don't have enough samples for even min_k, we must use global average
        if len(vectors) < min_k:
            global_avg = generate_global_average(routing_tensor, b)
            result[block_id] = {
                "centers": global_avg.tolist(),
                "silhouette": -1.0,
                "null_hypothesis_triggered": True,
                "null_reason": f"Insufficient samples ({len(vectors)}) for clustering",
                "k_used": None
            }
            continue

        # Search for best k
        for k in range(min_k, min(max_k + 1, len(vectors))):
            centers, sil = perform_clustering(vectors, k=k, random_state=random_state)
            
            if sil > best_silhouette:
                best_silhouette = sil
                best_k = k
                best_centers = centers

        # Check if the best clustering meets the threshold
        if best_silhouette >= distance_threshold and best_k is not None and best_k >= MIN_CLUSTERS:
            # Valid clustering found
            result[block_id] = {
                "centers": best_centers.tolist(),
                "silhouette": float(best_silhouette),
                "null_hypothesis_triggered": False,
                "null_reason": None,
                "k_used": best_k
            }
        else:
            # Null hypothesis triggered: use global average
            global_avg = generate_global_average(routing_tensor, b)
            reason = "Silhouette score below threshold" if best_silhouette < distance_threshold else "No valid clustering found"
            
            result[block_id] = {
                "centers": global_avg.tolist(),
                "silhouette": float(best_silhouette) if best_silhouette >= 0 else 0.0,
                "null_hypothesis_triggered": True,
                "null_reason": reason,
                "k_used": None
            }

    return result


def save_cluster_centers(
    cluster_data: Dict[str, Any],
    output_path: str = "data/routing_cache/cluster_centers.json"
) -> None:
    """
    Save the cluster centers and metadata to a JSON file.

    Args:
        cluster_data: Dictionary returned by compute_canonical_map.
        output_path: Path to the output JSON file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(cluster_data, f, indent=2)

    logger.info(f"Saved cluster centers to {output_path}")


def save_null_hypothesis_flag(
    cluster_data: Dict[str, Any],
    output_path: str = "data/routing_cache/null_hypothesis_status.json"
) -> None:
    """
    Save a summary of which blocks triggered the null hypothesis.

    Args:
        cluster_data: Dictionary returned by compute_canonical_map.
        output_path: Path to the output JSON file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    status = {
        block_id: {
            "null_hypothesis_triggered": info["null_hypothesis_triggered"],
            "reason": info["null_reason"]
        }
        for block_id, info in cluster_data.items()
    }

    with open(output_file, 'w') as f:
        json.dump(status, f, indent=2)

    logger.info(f"Saved null hypothesis status to {output_path}")


def run_clustering_analysis(
    cache_dir: str = "data/routing_cache",
    output_dir: str = "data/routing_cache",
    distance_threshold: float = 0.25,
    max_k: int = 5,
    min_k: int = 2,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Main entry point for running the full clustering analysis pipeline.

    This function:
    1. Loads all routing tensors from the cache.
    2. Computes the canonical map using the specified parameters.
    3. Saves the results to JSON files.

    Args:
        cache_dir: Directory containing routing_*.npy files.
        output_dir: Directory to save output JSON files.
        distance_threshold: Minimum silhouette score for valid clustering.
        max_k: Maximum number of clusters to try.
        min_k: Minimum number of clusters to try.
        random_state: Random seed.

    Returns:
        The cluster data dictionary.
    """
    logger.info("Starting clustering analysis...")
    
    # Load data
    routing_tensor, num_images, num_timesteps, num_blocks, history_dim = load_routing_cache(cache_dir)
    
    # Compute canonical map
    cluster_data = compute_canonical_map(
        routing_tensor,
        distance_threshold=distance_threshold,
        max_k=max_k,
        min_k=min_k,
        random_state=random_state
    )
    
    # Save results
    output_path_centers = Path(output_dir) / "cluster_centers.json"
    output_path_null = Path(output_dir) / "null_hypothesis_status.json"
    
    save_cluster_centers(cluster_data, str(output_path_centers))
    save_null_hypothesis_flag(cluster_data, str(output_path_null))
    
    logger.info("Clustering analysis complete.")
    return cluster_data


def main():
    """Command-line entry point for clustering analysis."""
    import argparse

    parser = argparse.ArgumentParser(description="Run clustering analysis on routing traces.")
    parser.add_argument("--cache-dir", type=str, default="data/routing_cache", help="Directory with routing_*.npy files")
    parser.add_argument("--output-dir", type=str, default="data/routing_cache", help="Directory to save results")
    parser.add_argument("--threshold", type=float, default=0.25, help="Silhouette threshold for null hypothesis")
    parser.add_argument("--max-k", type=int, default=5, help="Maximum clusters to try")
    parser.add_argument("--min-k", type=int, default=2, help="Minimum clusters to try")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    run_clustering_analysis(
        cache_dir=args.cache_dir,
        output_dir=args.output_dir,
        distance_threshold=args.threshold,
        max_k=args.max_k,
        min_k=args.min_k,
        random_state=args.seed
    )


if __name__ == "__main__":
    main()