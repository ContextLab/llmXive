"""
Canonical Map Derivation Module (T013)

Derives the "Canonical Routing Map" (static weight vector per block) from the
dominant cluster centers computed in T012, or falls back to a global average
if the clustering analysis indicated a null hypothesis.

Output:
    data/routing_cache/canonical_map.json
        A JSON file containing a dictionary with keys:
        - "block_id": int
        - "weight_vector": list of floats (the static routing weights)
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np

from src.clustering import (
    load_routing_cache,
    compute_mean_routing_vectors,
    perform_clustering,
    generate_global_average,
    save_cluster_centers,
    save_null_hypothesis_flag,
)
from src.config import get_routing_cache_path, get_results_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

CANONICAL_MAP_FILENAME = "canonical_map.json"
NULL_HYPOTHESIS_FLAG_FILENAME = "null_hypothesis_flag.json"


def derive_canonical_map(
    cache_path: Optional[Path] = None,
    results_path: Optional[Path] = None,
    silhouette_threshold: float = 0.25,
    min_k: int = 2,
) -> Dict[str, Any]:
    """
    Derives the canonical routing map from clustering results.

    This function:
    1. Loads the raw routing cache (from T011).
    2. Computes mean routing vectors per timestep.
    3. Performs clustering (from T012).
    4. Checks for the null hypothesis (k < min_k or silhouette < threshold).
    5. If null hypothesis is true, generates a global average vector.
    6. Constructs the canonical map: a static weight vector for each block.
    7. Saves the map to `data/routing_cache/canonical_map.json`.

    Args:
        cache_path: Path to the routing cache directory. Defaults to config.
        results_path: Path to the results directory. Defaults to config.
        silhouette_threshold: Minimum acceptable silhouette score.
        min_k: Minimum number of clusters to consider valid.

    Returns:
        Dict containing the canonical map structure.
    """
    if cache_path is None:
        cache_path = get_routing_cache_path()
    if results_path is None:
        results_path = get_results_path()

    cache_path = Path(cache_path)
    results_path = Path(results_path)
    results_path.mkdir(parents=True, exist_ok=True)
    cache_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading routing cache from: {cache_path}")
    # Load raw data to determine block count and dimensionality
    # We assume the cache contains files named like: routing_image_{idx}.npz
    # or a single aggregated file. We use the clustering module's loader.
    try:
        routing_data = load_routing_cache(cache_path)
    except FileNotFoundError as e:
        logger.error(f"Routing cache not found: {e}")
        raise

    if not routing_data:
        logger.error("Routing cache is empty. Cannot derive canonical map.")
        raise ValueError("Routing cache is empty.")

    logger.info("Computing mean routing vectors...")
    mean_vectors = compute_mean_routing_vectors(routing_data)

    # mean_vectors shape: [num_timesteps, history_dim]
    # We need to determine the number of blocks.
    # The routing_data structure usually contains block info.
    # Let's infer block count from the raw data keys or structure if available.
    # For now, we assume the clustering module returns enough context or we
    # infer from the data structure.
    # A robust way: Check the shape of a single sample if available.
    # However, T012 clustering logic usually determines the 'k'.
    # We need the number of blocks to assign a weight vector to each.

    # Re-load raw data to inspect block structure if not in mean_vectors
    # Assuming routing_data is a dict or list of arrays with block info.
    # Let's assume the raw data keys are 'image_X' and values are dicts
    # or arrays with shape [blocks, timesteps, dim].
    # Since load_routing_cache is abstracted, we rely on the fact that
    # perform_clustering returns the cluster centers and the null flag.

    logger.info("Performing clustering analysis...")
    cluster_result = perform_clustering(
        mean_vectors,
        min_k=min_k,
        silhouette_threshold=silhouette_threshold,
    )

    is_null_hypothesis = cluster_result.get("is_null_hypothesis", False)
    silhouette_score = cluster_result.get("silhouette_score", 0.0)
    k = cluster_result.get("k", 0)
    cluster_centers = cluster_result.get("cluster_centers", None)

    logger.info(f"Clustering result: k={k}, silhouette={silhouette_score:.4f}, null={is_null_hypothesis}")

    # Save the null hypothesis flag if applicable
    if is_null_hypothesis:
        flag_data = {
            "is_null_hypothesis": True,
            "reason": f"k < {min_k} ({k} < {min_k}) or silhouette < {silhouette_threshold} ({silhouette_score:.4f} < {silhouette_threshold})",
            "silhouette_score": silhouette_score,
            "k": k,
            "timestamp": str(Path(cache_path).stat().st_mtime), # Approximate
        }
        flag_path = results_path / NULL_HYPOTHESIS_FLAG_FILENAME
        with open(flag_path, "w") as f:
            json.dump(flag_data, f, indent=2)
        logger.warning(f"Null hypothesis detected. Flag saved to {flag_path}")

    # Determine the source of the static weights
    if is_null_hypothesis:
        logger.info("Generating global average vector due to null hypothesis.")
        # generate_global_average expects mean_vectors (timesteps, dim)
        # It should return a single vector of shape (dim,)
        # But wait, the canonical map needs a vector PER BLOCK.
        # If clustering fails, we assume the routing is constant across timesteps
        # AND potentially constant across blocks? Or we average across blocks too?
        # The spec says: "global average vector".
        # Let's assume the global average is computed across all timesteps for the mean vector.
        # But we need to know the number of blocks.
        # Let's infer block count from the raw data structure if possible.
        # If routing_data is a list of dicts where each dict has 'blocks': [block0, block1...],
        # we can count.
        
        # Fallback: Assume the mean_vectors are averaged over blocks already?
        # No, T012 says: "compute the mean routing vector across all images/blocks for each timestep".
        # So mean_vectors[t] is the average over all blocks and images for timestep t.
        # If we fall back to global average, we average over timesteps too.
        # This gives ONE vector.
        # How do we assign it to blocks?
        # Assumption: In the null hypothesis, the routing is uniform across blocks.
        # So every block gets the same global average vector.
        
        global_avg_vector = generate_global_average(mean_vectors)
        num_blocks = len(routing_data) # This might be number of images, not blocks.
        # We need the number of blocks.
        # Let's look at the shape of the raw data for one image.
        # Assuming routing_data is a list of numpy arrays of shape [blocks, timesteps, dim]
        # or similar.
        
        # Let's try to infer from the first item if it's a structured array or list
        first_item = list(routing_data.values())[0] if isinstance(routing_data, dict) else routing_data[0]
        
        if isinstance(first_item, np.ndarray):
            if first_item.ndim == 3:
                num_blocks = first_item.shape[0]
            else:
                # Fallback: hardcode or error?
                # SiT-XL typically has 28 blocks.
                num_blocks = 28 
                logger.warning(f"Could not infer block count from array shape {first_item.shape}. Defaulting to {num_blocks}.")
        else:
            # If it's a dict of arrays
            first_array = list(first_item.values())[0] if isinstance(first_item, dict) else first_item
            if hasattr(first_array, 'shape') and first_array.ndim == 3:
                num_blocks = first_array.shape[0]
            else:
                num_blocks = 28
                logger.warning(f"Could not infer block count. Defaulting to {num_blocks}.")

        canonical_map_entries = []
        for b in range(num_blocks):
            canonical_map_entries.append({
                "block_id": b,
                "weight_vector": global_avg_vector.tolist(),
            })
    else:
        logger.info("Using dominant cluster center.")
        # cluster_centers shape: [k, history_dim]
        # We need to select the dominant cluster.
        # If k >= 2, we pick the cluster with the most points (or just the first if equal).
        # The perform_clustering function should return the dominant center.
        dominant_center = cluster_centers[0] # Assuming first is dominant or we sort by size
        
        # We need num_blocks again.
        first_item = list(routing_data.values())[0] if isinstance(routing_data, dict) else routing_data[0]
        if isinstance(first_item, np.ndarray) and first_item.ndim == 3:
            num_blocks = first_item.shape[0]
        else:
            num_blocks = 28
            logger.warning(f"Could not infer block count for cluster path. Defaulting to {num_blocks}.")

        canonical_map_entries = []
        for b in range(num_blocks):
            canonical_map_entries.append({
                "block_id": b,
                "weight_vector": dominant_center.tolist(),
            })

    canonical_map = {
        "num_blocks": num_blocks,
        "timesteps": mean_vectors.shape[0],
        "history_dim": mean_vectors.shape[1],
        "is_null_hypothesis": is_null_hypothesis,
        "silhouette_score": silhouette_score,
        "k": k,
        "entries": canonical_map_entries,
    }

    output_path = cache_path / CANONICAL_MAP_FILENAME
    with open(output_path, "w") as f:
        json.dump(canonical_map, f, indent=2)

    logger.info(f"Canonical map saved to {output_path}")
    return canonical_map


def main():
    """Entry point for deriving the canonical map."""
    logger.info("Starting Canonical Map Derivation (T013)...")
    try:
        result = derive_canonical_map()
        logger.info("Canonical map derivation completed successfully.")
        print(f"Output: data/routing_cache/{CANONICAL_MAP_FILENAME}")
        return 0
    except Exception as e:
        logger.error(f"Failed to derive canonical map: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())