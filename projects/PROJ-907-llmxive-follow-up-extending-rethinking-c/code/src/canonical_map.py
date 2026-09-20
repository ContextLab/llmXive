"""
Canonical Map Derivation Module (T013)

Derives the "Canonical Routing Map" (static weight vector per block) from the
clustering results produced by T012. It reads the cluster centers (or global
averages if the null hypothesis was triggered) and saves the final static map.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import from sibling modules as per API surface
from src.config import get_routing_cache_path, get_results_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("data/results/canonical_map.log")
    ]
)
logger = logging.getLogger(__name__)

# Constants
CLUSTER_CENTERS_FILE = "cluster_centers.json"
CANONICAL_MAP_FILE = "canonical_map.json"

def derive_canonical_map(cluster_centers_path: Optional[str] = None) -> Dict[str, List[float]]:
    """
    Derives the canonical routing map from cluster centers.

    This function reads the output of T012 (cluster_centers.json). For each block:
    1. If `null_hypothesis_triggered` is True, it uses the `centers` field which
       contains the global average vector (as per T012 spec).
    2. If `null_hypothesis_triggered` is False, it selects the dominant cluster
       (the one with the highest weight or first in list if weights not provided,
       though T012 spec implies we store the representative vector).
       *Correction based on T012 spec*: T012 saves `centers` as a list of vectors.
       We need to pick the dominant one. Since T012 spec says "centers" field
       contains the global average if null, we assume if not null, it contains
       the list of K centers. We will pick the first one as the representative
       for the "dominant" phase if K >= 2, or rely on the structure provided.
       *Refinement*: The T012 spec says: "If for any block the clustering identifies
       < 2 clusters... that block MUST default to a global average vector".
       And the output format is `{"block_0": {"centers": [...], ...}}`.
       If `null_hypothesis_triggered` is true, `centers` is the single global average vector.
       If false, `centers` is a list of K cluster centers.
       We will select the first center from the list as the canonical vector for that block.
       (In a real implementation, we might weight by cluster size, but the spec
       implies the `centers` field holds the relevant vectors).

    Args:
        cluster_centers_path: Optional path to cluster_centers.json. If None, uses default.

    Returns:
        A dictionary mapping block names (e.g., "block_0") to their static weight vectors.
    """
    if cluster_centers_path is None:
        cache_path = get_routing_cache_path()
        cluster_centers_path = os.path.join(cache_path, CLUSTER_CENTERS_FILE)

    if not os.path.exists(cluster_centers_path):
        raise FileNotFoundError(f"Cluster centers file not found: {cluster_centers_path}")

    logger.info(f"Loading cluster centers from {cluster_centers_path}")
    with open(cluster_centers_path, 'r') as f:
        cluster_data = json.load(f)

    canonical_map: Dict[str, List[float]] = {}

    for block_key, block_info in cluster_data.items():
        if not isinstance(block_info, dict):
            logger.warning(f"Skipping invalid block entry: {block_key}")
            continue

        centers = block_info.get("centers", [])
        null_triggered = block_info.get("null_hypothesis_triggered", False)

        if not centers:
            logger.error(f"No centers found for {block_key}. Skipping.")
            continue

        # Determine the canonical vector
        # If null hypothesis triggered, T012 guarantees `centers` is the global average (list of floats)
        # If not triggered, `centers` is a list of cluster centers (list of lists).
        # We pick the first available center as the representative.
        
        if null_triggered:
            # T012 spec: centers contains the exact global average vector (list of floats)
            # Ensure it's a list of floats
            canonical_vector = [float(v) for v in centers]
            logger.info(f"Block {block_key}: Using global average (null hypothesis triggered).")
        else:
            # T012 spec: centers is a list of cluster centers.
            # We assume the first one is the dominant or representative.
            # If the list contains lists (multiple clusters), take the first.
            if isinstance(centers[0], list):
                canonical_vector = [float(v) for v in centers[0]]
                logger.info(f"Block {block_key}: Using first cluster center from {len(centers)} clusters.")
            else:
                # Fallback if structure is unexpected but valid
                canonical_vector = [float(v) for v in centers]
                logger.info(f"Block {block_key}: Using single center vector.")

        canonical_map[block_key] = canonical_vector

    logger.info(f"Derived canonical map for {len(canonical_map)} blocks.")
    return canonical_map

def save_canonical_map(canonical_map: Dict[str, List[float]], output_path: Optional[str] = None) -> str:
    """
    Saves the canonical map to a JSON file.

    Args:
        canonical_map: The derived map dictionary.
        output_path: Optional output path. If None, uses default.

    Returns:
        The path where the file was saved.
    """
    if output_path is None:
        cache_path = get_routing_cache_path()
        output_path = os.path.join(cache_path, CANONICAL_MAP_FILE)

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    logger.info(f"Saving canonical map to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(canonical_map, f, indent=2)

    return output_path

def main():
    """
    Main entry point for T013.
    1. Loads cluster centers from T012.
    2. Derives the canonical map.
    3. Saves the result.
    """
    logger.info("Starting T013: Canonical Map Derivation")

    try:
        # 1. Derive
        canonical_map = derive_canonical_map()

        # 2. Save
        output_file = save_canonical_map(canonical_map)

        # 3. Verification
        if not os.path.exists(output_file):
            raise RuntimeError("Output file was not created.")

        with open(output_file, 'r') as f:
            loaded_map = json.load(f)

        if len(loaded_map) == 0:
            raise RuntimeError("Canonical map is empty.")

        logger.info(f"Success. Saved {len(loaded_map)} block vectors to {output_file}")

    except FileNotFoundError as e:
        logger.error(f"Dependency file missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during canonical map derivation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()