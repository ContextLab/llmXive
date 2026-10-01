import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np

# Import from sibling modules as per API surface
from src.clustering import compute_canonical_map as clustering_compute_canonical_map, load_routing_cache
from src.config import get_routing_cache_path, get_results_path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def derive_canonical_map(cluster_centers_path: str) -> Dict[str, List[float]]:
    """
    Derives the Canonical Routing Map from the cluster centers JSON produced by T012.
    
    For each block, if 'null_hypothesis_triggered' is true, the 'centers' field 
    contains the global average vector. If false, it contains the dominant cluster center 
    (or the list of centers if multiple, but we select the first/dominant one for static map).
    
    The task specifies the output schema as a single vector per block. 
    We select the first center provided in the 'centers' list for each block.
    If the list is empty (should not happen with valid logic), we raise an error.
    
    Args:
        cluster_centers_path: Path to data/routing_cache/cluster_centers.json
        
    Returns:
        A dictionary mapping block names (e.g., "block_0") to a list of floats 
        representing the static weight vector.
    """
    if not os.path.exists(cluster_centers_path):
        raise FileNotFoundError(f"Cluster centers file not found: {cluster_centers_path}")
    
    with open(cluster_centers_path, 'r') as f:
        cluster_data = json.load(f)
    
    canonical_map = {}
    
    for block_key, block_info in cluster_data.items():
        centers = block_info.get("centers", [])
        
        if not centers:
            logger.warning(f"Block {block_key} has empty centers. Skipping.")
            continue
        
        # Select the dominant cluster center. 
        # The clustering logic in T012 puts the dominant cluster first or the global average 
        # if null hypothesis triggered. We take the first one.
        dominant_vector = centers[0]
        
        # Ensure it's a list of floats
        canonical_map[block_key] = [float(v) for v in dominant_vector]
        
        logger.info(f"Block {block_key}: Derived static vector of length {len(dominant_vector)}")
    
    if not canonical_map:
        raise ValueError("No valid blocks found in cluster data to derive canonical map.")
        
    return canonical_map

def save_canonical_map(canonical_map: Dict[str, List[float]], output_path: str) -> None:
    """
    Saves the canonical map to a JSON file.
    
    Args:
        canonical_map: The dictionary of block vectors.
        output_path: Path to save the JSON file.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(canonical_map, f, indent=2)
    
    logger.info(f"Canonical map saved to {output_path}")

def main() -> None:
    """
    Main entry point for T013.
    Loads cluster centers from T012, derives the canonical map, and saves it.
    """
    # Paths
    routing_cache_path = get_routing_cache_path()
    cluster_centers_file = os.path.join(routing_cache_path, "cluster_centers.json")
    canonical_map_file = os.path.join(routing_cache_path, "canonical_map.json")
    
    logger.info(f"Loading cluster centers from: {cluster_centers_file}")
    
    try:
        canonical_map = derive_canonical_map(cluster_centers_file)
        save_canonical_map(canonical_map, canonical_map_file)
        logger.info("T013 completed successfully.")
    except Exception as e:
        logger.error(f"Failed to derive canonical map: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()