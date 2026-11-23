import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def derive_canonical_map(cluster_centers_path: str) -> Dict[str, List[float]]:
    """
    Derives the canonical routing map from cluster centers.
    Returns a dictionary mapping block indices to their static weight vectors.
    """
    with open(cluster_centers_path, 'r') as f:
        cluster_data = json.load(f)
    
    canonical_map = {}
    for block_key, block_data in cluster_data.items():
        if block_data.get("null_hypothesis_triggered", False):
            # Use global average if null hypothesis was triggered
            # For now, we'll use the center as is (it should be the global average)
            canonical_map[block_key] = block_data["centers"]
        else:
            # Use the dominant cluster center
            canonical_map[block_key] = block_data["centers"][0]
    
    return canonical_map

def save_canonical_map(canonical_map: Dict[str, List[float]], output_path: str):
    """Saves the canonical map to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(canonical_map, f, indent=2)
    logger.info(f"Saved canonical map to {output_path}")

def main():
    """Entry point for the canonical map script."""
    cluster_centers_path = os.getenv('CLUSTER_CENTERS_PATH', 'data/routing_cache/cluster_centers.json')
    output_path = os.getenv('CANONICAL_MAP_PATH', 'data/routing_cache/canonical_map.json')
    
    canonical_map = derive_canonical_map(cluster_centers_path)
    save_canonical_map(canonical_map, output_path)

if __name__ == "__main__":
    main()
