"""
canonical_map.py

Derives the "Canonical Routing Map" (static weight vector per block) from the
dominant cluster or global average, and saves it to data/routing_cache/canonical_map.json.

Dependency: T012 (clustering.py)
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np

# Import from existing sibling module as per API surface
from src.clustering import load_routing_cache, compute_mean_routing_vectors, perform_clustering, generate_global_average, save_cluster_centers, save_null_hypothesis_flag, run_clustering_analysis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def derive_canonical_map(
    routing_cache_path: Optional[Path] = None,
    cluster_centers_path: Optional[Path] = None,
    null_hypothesis_flag_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    k: int = 5,
    distance_threshold: float = 0.05
) -> Dict[str, Any]:
    """
    Derives the canonical routing map from clustering results or global average.

    Args:
        routing_cache_path: Path to the routing cache directory containing .npy files.
        cluster_centers_path: Path to the cluster centers JSON file (output of T012).
        null_hypothesis_flag_path: Path to the null hypothesis flag JSON file (output of T012).
        output_path: Path where the canonical map JSON will be saved.
        k: Number of clusters for k-means (default 5).
        distance_threshold: Threshold for clustering (default 0.05).

    Returns:
        A dictionary representing the canonical routing map.
        Structure: {
            "block_id": int,
            "weight_vector": List[float],
            "source": "cluster" | "global_average",
            "cluster_id": int (if from cluster),
            "silhouette_score": float (if from cluster),
            "num_timesteps": int
        }
    """
    if routing_cache_path is None:
        routing_cache_path = Path(os.getenv("ROUTING_CACHE_PATH", "data/routing_cache"))
    if cluster_centers_path is None:
        cluster_centers_path = Path(os.getenv("CLUSTER_CENTERS_PATH", "data/routing_cache/cluster_centers.json"))
    if null_hypothesis_flag_path is None:
        null_hypothesis_flag_path = Path(os.getenv("NULL_HYPOTHESIS_FLAG_PATH", "data/results/null_hypothesis_flag.json"))
    if output_path is None:
        output_path = Path(os.getenv("CANONICAL_MAP_PATH", "data/routing_cache/canonical_map.json"))

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading routing cache from: {routing_cache_path}")
    # Load raw routing data to determine block count and history_dim
    # We need to know the structure to construct the final map
    # Re-run the loading logic to get the shape info
    try:
        # Load all routing tensors to infer dimensions
        # This is a simplified re-load for dimension inference
        # In a production scenario, we might cache this metadata
        all_tensors = load_routing_cache(routing_cache_path)
        if not all_tensors:
            raise ValueError("No routing tensors found in the cache.")

        # Infer block count and history_dim from the first tensor
        # Assuming tensors are stored as [block, timestep, history_dim]
        # We need to aggregate across blocks and timesteps to get the mean vector per timestep
        # But for the canonical map, we want a static vector per block.
        # The task description says: "Derive the 'Canonical Routing Map' (static weight vector per block)"
        # However, the clustering is done on the mean routing vector across all images/blocks for each timestep.
        # This implies the clustering result is per-timestep.
        # But the canonical map is supposed to be per-block.
        # Let's re-read T012: "compute the mean routing vector across all images/blocks for each timestep"
        # And T013: "Derive the 'Canonical Routing Map' (static weight vector per block)"
        # There seems to be a mismatch in the task description vs. the clustering logic.
        # Let's assume the canonical map is a single static vector that is used for all blocks,
        # or perhaps the clustering result is applied to each block independently?
        # Given the ambiguity, and the fact that T012 clusters timesteps, the most logical interpretation
        # is that the canonical map is a time-invariant weight vector (i.e., the same for all timesteps).
        # But the output schema in T013 says: {block_id, weight_vector}.
        # This suggests a per-block static map.
        # Let's assume the clustering is done per-block? No, T012 says "across all images/blocks".
        # Perhaps the canonical map is the dominant cluster center, repeated for each block?
        # Or perhaps the canonical map is the global average, repeated for each block?
        # Given the task description "static weight vector per block", and the clustering is on timesteps,
        # I will interpret this as: the canonical map is a single vector (the dominant cluster center or global average)
        # that is used for all blocks and all timesteps. But the output format requires block_id.
        # So I will create an entry for each block, with the same weight vector.
        # This is a reasonable interpretation of "static" (time-invariant) and "per block" (applied to each block).

        # Let's get the number of blocks and history_dim from the data
        # We need to load at least one file to get the shape
        first_file = None
        for file in routing_cache_path.glob("*.npy"):
            first_file = file
            break
        if first_file is None:
            for file in routing_cache_path.glob("*.pt"):
                first_file = file
                break

        if first_file is None:
            raise FileNotFoundError("No .npy or .pt files found in routing cache.")

        first_tensor = np.load(first_file) if str(first_file).endswith('.npy') else torch.load(first_file, map_location='cpu')
        if not isinstance(first_tensor, np.ndarray):
            first_tensor = first_tensor.numpy()

        # Shape should be [block, timestep, history_dim]
        if len(first_tensor.shape) != 3:
            raise ValueError(f"Expected 3D tensor, got shape {first_tensor.shape}")

        num_blocks, num_timesteps, history_dim = first_tensor.shape
        logger.info(f"Detected {num_blocks} blocks, {num_timesteps} timesteps, {history_dim} history_dim")

    except Exception as e:
        logger.error(f"Failed to load routing cache for dimension inference: {e}")
        raise

    # Check if clustering was successful (i.e., not a null hypothesis)
    null_hypothesis = False
    if null_hypothesis_flag_path.exists():
        try:
            with open(null_hypothesis_flag_path, 'r') as f:
                flag_data = json.load(f)
                null_hypothesis = flag_data.get("is_null_hypothesis", False)
                logger.info(f"Null hypothesis flag: {null_hypothesis}")
        except Exception as e:
            logger.warning(f"Could not read null hypothesis flag: {e}")
            null_hypothesis = False

    if null_hypothesis:
        logger.info("Null hypothesis detected. Using global average vector for all blocks.")
        # Generate global average vector
        # We need to compute the global average across all blocks, timesteps, and images
        # Re-load all tensors and compute the mean
        all_data = []
        for file in routing_cache_path.glob("*.npy"):
            tensor = np.load(file)
            all_data.append(tensor)
        for file in routing_cache_path.glob("*.pt"):
            tensor = torch.load(file, map_location='cpu').numpy()
            all_data.append(tensor)

        if not all_data:
            raise ValueError("No data found to compute global average.")

        concatenated = np.concatenate(all_data, axis=0) # Concatenate over images
        global_avg_vector = np.mean(concatenated, axis=(0, 1)) # Mean over blocks and timesteps

        canonical_map = {
            "source": "global_average",
            "num_blocks": num_blocks,
            "num_timesteps": num_timesteps,
            "history_dim": history_dim,
            "entries": []
        }

        for block_id in range(num_blocks):
            canonical_map["entries"].append({
                "block_id": block_id,
                "weight_vector": global_avg_vector.tolist(),
                "source": "global_average"
            })

    else:
        # Clustering was successful
        if not cluster_centers_path.exists():
            raise FileNotFoundError(f"Cluster centers file not found: {cluster_centers_path}")

        with open(cluster_centers_path, 'r') as f:
            cluster_data = json.load(f)

        # Find the dominant cluster (largest cluster size)
        # cluster_data structure: {"clusters": [{"cluster_id": int, "size": int, "center": [...]}, ...]}
        if "clusters" not in cluster_data or not cluster_data["clusters"]:
            logger.warning("No clusters found. Falling back to global average.")
            # Fallback to global average if no clusters
            # Re-compute global average
            all_data = []
            for file in routing_cache_path.glob("*.npy"):
                tensor = np.load(file)
                all_data.append(tensor)
            for file in routing_cache_path.glob("*.pt"):
                tensor = torch.load(file, map_location='cpu').numpy()
                all_data.append(tensor)

            concatenated = np.concatenate(all_data, axis=0)
            global_avg_vector = np.mean(concatenated, axis=(0, 1))

            canonical_map = {
                "source": "global_average",
                "num_blocks": num_blocks,
                "num_timesteps": num_timesteps,
                "history_dim": history_dim,
                "entries": []
            }

            for block_id in range(num_blocks):
                canonical_map["entries"].append({
                    "block_id": block_id,
                    "weight_vector": global_avg_vector.tolist(),
                    "source": "global_average"
                })
        else:
            # Sort clusters by size to find the dominant one
            sorted_clusters = sorted(cluster_data["clusters"], key=lambda x: x["size"], reverse=True)
            dominant_cluster = sorted_clusters[0]
            dominant_center = np.array(dominant_cluster["center"])

            logger.info(f"Using dominant cluster {dominant_cluster['cluster_id']} with size {dominant_cluster['size']}")

            canonical_map = {
                "source": "cluster",
                "dominant_cluster_id": dominant_cluster["cluster_id"],
                "num_blocks": num_blocks,
                "num_timesteps": num_timesteps,
                "history_dim": history_dim,
                "silhouette_score": cluster_data.get("silhouette_score", None),
                "entries": []
            }

            for block_id in range(num_blocks):
                canonical_map["entries"].append({
                    "block_id": block_id,
                    "weight_vector": dominant_center.tolist(),
                    "source": "cluster",
                    "cluster_id": dominant_cluster["cluster_id"]
                })

    # Save the canonical map
    with open(output_path, 'w') as f:
        json.dump(canonical_map, f, indent=2)

    logger.info(f"Canonical map saved to: {output_path}")
    return canonical_map

def main():
    """Main entry point for deriving the canonical map."""
    logger.info("Starting canonical map derivation...")

    try:
        canonical_map = derive_canonical_map()
        logger.info("Canonical map derivation completed successfully.")
        print(f"Canonical map saved to: {os.getenv('CANONICAL_MAP_PATH', 'data/routing_cache/canonical_map.json')}")
    except Exception as e:
        logger.error(f"Failed to derive canonical map: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
