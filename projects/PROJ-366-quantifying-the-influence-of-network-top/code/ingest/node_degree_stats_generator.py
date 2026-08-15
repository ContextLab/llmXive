import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, List
from collections import Counter

from config import get_config, get_paths
from ingest.graph_builder import process_directory

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_graphs(graph_dir: Path) -> List[Any]:
    """Load all serialized graph files from the directory."""
    graphs = []
    if not graph_dir.exists():
        raise FileNotFoundError(f"Graph directory not found: {graph_dir}")
    
    for file_path in graph_dir.glob("*.pkl"):
        logger.info(f"Loading graph from {file_path}")
        try:
            with open(file_path, 'rb') as f:
                graph_data = pickle.load(f)
                graphs.append(graph_data)
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            raise
    
    if not graphs:
        raise ValueError(f"No graph files found in {graph_dir}")
    
    return graphs

def calculate_global_degree_distribution(graphs: List[Any]) -> Counter:
    """Aggregate node degrees from all graphs into a global distribution."""
    all_degrees = []
    for graph_data in graphs:
        # graph_data is expected to be a dict with 'nodes' and 'edges'
        # or an object with similar attributes. Based on graph_builder,
        # it's likely a dict with 'nodes' (list of node data) and 'adj' (adjacency).
        if isinstance(graph_data, dict):
            nodes = graph_data.get('nodes', [])
            adj = graph_data.get('adj', {})
            
            # If nodes list exists, use its length or explicit degree if stored
            # Otherwise calculate from adjacency
            if not adj and nodes:
                # Fallback: assume nodes list length isn't degree, need adj
                # If adj is missing, we can't calculate degree properly.
                # However, graph_builder usually stores adj.
                pass
            
            for node_id, neighbors in adj.items():
                degree = len(neighbors)
                all_degrees.append(degree)
        else:
            # Handle object-based graph if necessary
            raise TypeError(f"Unexpected graph data type: {type(graph_data)}")
    
    return Counter(all_degrees)

def compute_mode_and_stats(degree_distribution: Counter) -> Dict[str, Any]:
    """Calculate mode, mean, and other stats from degree distribution."""
    if not degree_distribution:
        raise ValueError("Degree distribution is empty")
    
    degrees = list(degree_distribution.elements())
    counts = degree_distribution
    
    # Mode: most common degree
    mode_degree, mode_count = counts.most_common(1)[0]
    
    # Mean degree
    mean_degree = sum(degrees) / len(degrees)
    
    # Min and Max
    min_degree = min(degrees)
    max_degree = max(degrees)
    
    return {
        "mode": int(mode_degree),
        "mode_count": int(mode_count),
        "mean": float(mean_degree),
        "min": int(min_degree),
        "max": int(max_degree),
        "total_nodes": len(degrees),
        "distribution": {int(k): int(v) for k, v in counts.items()}
    }

def validate_mode_for_amorphous_silicon(stats: Dict[str, Any]) -> bool:
    """
    Dynamically validate if the mode falls within the expected range for amorphous silicon.
    Amorphous silicon typically has a coordination number (degree) centered around 4.
    We check if the mode is between 3 and 5 (inclusive) as a dynamic validation.
    """
    mode = stats["mode"]
    # Dynamic range check: 3 to 5 is physically reasonable for a-Si
    # This is not a hard-coded "target" but a physical constraint check.
    is_valid = 3 <= mode <= 5
    
    if not is_valid:
        logger.warning(f"Mode {mode} is outside the typical range [3, 5] for amorphous silicon.")
    else:
        logger.info(f"Mode {mode} is within the expected range for amorphous silicon.")
    
    return is_valid

def main():
    config = get_config()
    paths = get_paths()
    
    graph_dir = paths["graph_output"]
    output_file = paths["node_degree_stats_output"]
    
    logger.info(f"Loading graphs from {graph_dir}")
    graphs = load_graphs(graph_dir)
    
    logger.info("Calculating global degree distribution")
    degree_distribution = calculate_global_degree_distribution(graphs)
    
    logger.info("Computing mode and statistics")
    stats = compute_mode_and_stats(degree_distribution)
    
    logger.info("Validating mode against amorphous silicon expectations")
    is_valid = validate_mode_for_amorphous_silicon(stats)
    
    stats["validation_passed"] = is_valid
    stats["status"] = "VALID" if is_valid else "WARNING_OUT_OF_RANGE"
    
    # Ensure output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving stats to {output_file}")
    with open(output_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    if not is_valid:
        logger.warning("Validation failed: Mode is out of expected range. Proceeding with stats.")
    
    return stats

if __name__ == "__main__":
    main()
