"""
Outlier detection for extreme topological defects.

Identifies samples where >15% of atoms have coordination number < 3 or > 6.
Writes excluded sample IDs to data/processed/graphs/excluded_samples.json
if config.yaml flag 'enforce_exclusion' is True.
Otherwise, logs a warning but does not exclude.
"""
import json
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Set

import numpy as np

# Import config utilities from existing module
from config import get_config

# Setup logging
logger = logging.getLogger(__name__)

# Constants
COORD_MIN_THRESHOLD = 3
COORD_MAX_THRESHOLD = 6
DEFECT_RATIO_THRESHOLD = 0.15  # 15%

def load_graph_metrics(graph_path: Path) -> Dict[str, Any]:
    """Load graph metrics from a serialized graph file."""
    try:
        with open(graph_path, 'rb') as f:
            data = pickle.load(f)
        return data
    except Exception as e:
        logger.error(f"Failed to load graph metrics from {graph_path}: {e}")
        return {}

def extract_node_degrees(graph_data: Dict[str, Any]) -> List[int]:
    """Extract node degrees from graph data."""
    # Graph data structure typically contains 'nodes' or 'adjacency' info
    # We assume the metrics file contains 'node_degrees' or can be derived
    if 'node_degrees' in graph_data:
        return graph_data['node_degrees']
    
    # Fallback: try to derive from adjacency list if present
    if 'adjacency' in graph_data:
        adjacency = graph_data['adjacency']
        degrees = [len(neighbors) for neighbors in adjacency]
        return degrees
    
    logger.warning("Could not find node degrees in graph data")
    return []

def calculate_defect_ratio(node_degrees: List[int]) -> float:
    """Calculate the ratio of atoms with extreme coordination."""
    if not node_degrees:
        return 0.0
    
    total_atoms = len(node_degrees)
    if total_atoms == 0:
        return 0.0
    
    # Count atoms with coordination < 3 or > 6
    defect_count = sum(
        1 for deg in node_degrees 
        if deg < COORD_MIN_THRESHOLD or deg > COORD_MAX_THRESHOLD
    )
    
    return defect_count / total_atoms

def detect_outliers(graphs_dir: Path, exclude_file: Path) -> Set[str]:
    """
    Detect outlier samples based on topological defects.
    
    Args:
        graphs_dir: Directory containing serialized graph files
        exclude_file: Path to write excluded sample IDs
        
    Returns:
        Set of excluded sample IDs
    """
    config = get_config()
    enforce_exclusion = config.get('enforce_exclusion', False)
    
    excluded_ids: Set[str] = set()
    
    # Find all graph files
    graph_files = list(graphs_dir.glob('*.pkl')) + list(graphs_dir.glob('*.pickle'))
    
    if not graph_files:
        logger.warning(f"No graph files found in {graphs_dir}")
        return excluded_ids
    
    logger.info(f"Processing {len(graph_files)} graph files for outlier detection")
    
    for graph_file in graph_files:
        sample_id = graph_file.stem  # filename without extension
        
        # Load graph metrics
        graph_data = load_graph_metrics(graph_file)
        if not graph_data:
            logger.warning(f"Skipping {sample_id}: could not load graph data")
            continue
        
        # Extract node degrees
        node_degrees = extract_node_degrees(graph_data)
        if not node_degrees:
            logger.warning(f"Skipping {sample_id}: no node degrees found")
            continue
        
        # Calculate defect ratio
        defect_ratio = calculate_defect_ratio(node_degrees)
        
        if defect_ratio > DEFECT_RATIO_THRESHOLD:
            if enforce_exclusion:
                excluded_ids.add(sample_id)
                logger.warning(
                    f"Excluding sample '{sample_id}': "
                    f"defect ratio {defect_ratio:.2%} > {DEFECT_RATIO_THRESHOLD:.2%} "
                    f"({int(defect_ratio * len(node_degrees))}/{len(node_degrees)} atoms)"
                )
            else:
                logger.warning(
                    f"Sample '{sample_id}' has extreme topological defects: "
                    f"defect ratio {defect_ratio:.2%} > {DEFECT_RATIO_THRESHOLD:.2%}. "
                    f"Exclusion disabled (enforce_exclusion=False). Log only."
                )
        else:
            logger.debug(
                f"Sample '{sample_id}' passed outlier check: "
                f"defect ratio {defect_ratio:.2%}"
            )
    
    return excluded_ids

def write_excluded_samples(excluded_ids: Set[str], exclude_file: Path) -> None:
    """Write excluded sample IDs to JSON file."""
    exclude_file.parent.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        "excluded_samples": sorted(list(excluded_ids)),
        "count": len(excluded_ids),
        "reason": "Extreme topological defects (>15% atoms with coord < 3 or > 6)"
    }
    
    with open(exclude_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Wrote {len(excluded_ids)} excluded sample IDs to {exclude_file}")

def main():
    """Main entry point for outlier detection."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get paths from config
    config = get_config()
    graphs_dir = Path(config['paths']['processed_graphs'])
    exclude_file = Path(config['paths']['excluded_samples'])
    
    logger.info(f"Starting outlier detection")
    logger.info(f"Graphs directory: {graphs_dir}")
    logger.info(f"Exclusion file: {exclude_file}")
    logger.info(f"Enforce exclusion: {config.get('enforce_exclusion', False)}")
    
    # Detect outliers
    excluded_ids = detect_outliers(graphs_dir, exclude_file)
    
    # Write results
    if excluded_ids:
        write_excluded_samples(excluded_ids, exclude_file)
    else:
        logger.info("No outliers detected")
        # Still create an empty exclusion file for downstream consistency
        write_excluded_samples(set(), exclude_file)
    
    logger.info("Outlier detection completed")

if __name__ == "__main__":
    main()
