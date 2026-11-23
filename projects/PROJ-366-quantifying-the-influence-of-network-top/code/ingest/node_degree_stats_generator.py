import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import Counter

from config import get_config, get_paths

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_graphs(graph_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all serialized graph files (.pkl) from the specified directory.
    
    Args:
        graph_dir: Path to the directory containing graph pickle files.
        
    Returns:
        List of graph dictionaries.
        
    Raises:
        FileNotFoundError: If no graph files are found.
    """
    graph_files = list(graph_dir.glob("graph_*.pkl"))
    if not graph_files:
        raise FileNotFoundError(f"No graph files found in {graph_dir}")
    
    graphs = []
    for f_path in sorted(graph_files):
        try:
            with open(f_path, 'rb') as f:
                graph_data = pickle.load(f)
                graphs.append(graph_data)
                logger.info(f"Loaded graph: {f_path.name}")
        except Exception as e:
            logger.error(f"Failed to load {f_path}: {e}")
            raise
    
    return graphs


def calculate_global_degree_distribution(graphs: List[Dict[str, Any]]) -> Counter:
    """
    Aggregate node degrees from all graphs to calculate the global distribution.
    
    Args:
        graphs: List of graph dictionaries, each containing a 'nodes' list.
        
    Returns:
        Counter mapping degree (int) to frequency (int).
    """
    degree_counts = Counter()
    total_nodes = 0
    
    for graph in graphs:
        if 'nodes' not in graph:
            logger.warning(f"Graph missing 'nodes' key: {graph.get('id', 'unknown')}")
            continue
        
        for node in graph['nodes']:
            if 'degree' not in node:
                logger.warning(f"Node missing 'degree' key in graph {graph.get('id', 'unknown')}")
                continue
            
            deg = node['degree']
            degree_counts[deg] += 1
            total_nodes += 1
    
    if total_nodes == 0:
        raise ValueError("No valid nodes found across all graphs.")
        
    logger.info(f"Calculated degree distribution for {total_nodes} total nodes.")
    return degree_counts


def compute_mode_and_stats(degree_counts: Counter) -> Dict[str, Any]:
    """
    Compute the mode of the degree distribution and basic statistics.
    
    Args:
        degree_counts: Counter of degree frequencies.
        
    Returns:
        Dictionary containing 'mode', 'distribution', and 'total_nodes'.
    """
    if not degree_counts:
        raise ValueError("Degree counts are empty.")
    
    # Calculate mode: the degree with the highest frequency
    # In case of a tie, Counter.most_common() returns the first one encountered
    mode, frequency = degree_counts.most_common(1)[0]
    
    # Convert Counter to a sorted dict for JSON serialization
    distribution = dict(sorted(degree_counts.items()))
    
    stats = {
        "mode": mode,
        "mode_frequency": frequency,
        "distribution": distribution,
        "total_nodes": sum(degree_counts.values()),
        "unique_degrees": len(degree_counts)
    }
    
    logger.info(f"Computed mode: {mode} (frequency: {frequency})")
    return stats


def validate_mode_for_amorphous_silicon(mode: int) -> bool:
    """
    Validate that the calculated mode is physically plausible for amorphous silicon.
    
    Amorphous silicon typically has a coordination number (degree) centered around 4.
    A mode between 3 and 5 is considered valid.
    
    Args:
        mode: The calculated mode (integer).
        
    Returns:
        True if valid, False otherwise.
    """
    is_valid = 3 <= mode <= 5
    status = "VALID" if is_valid else "WARNING: OUT OF EXPECTED RANGE"
    logger.info(f"Mode validation ({status}): {mode}")
    return is_valid


def main():
    """
    Main entry point for generating node-degree distribution statistics.
    
    Reads all serialized graphs from data/processed/graphs/, calculates
    the global degree distribution, determines the mode, and writes the
    result to data/processed/graphs/node_degree_stats.json.
    """
    config = get_config()
    paths = get_paths()
    
    graph_dir = paths["processed_graphs"]
    output_file = graph_dir / "node_degree_stats.json"
    
    logger.info(f"Starting node degree stats generation.")
    logger.info(f"Input directory: {graph_dir}")
    logger.info(f"Output file: {output_file}")
    
    try:
        # 1. Load all graphs
        graphs = load_graphs(graph_dir)
        if not graphs:
            raise ValueError("No graphs loaded. Cannot compute statistics.")
        
        # 2. Calculate global degree distribution
        degree_counts = calculate_global_degree_distribution(graphs)
        
        # 3. Compute mode and stats
        stats = compute_mode_and_stats(degree_counts)
        
        # 4. Validate mode
        if not validate_mode_for_amorphous_silicon(stats["mode"]):
            logger.warning("The calculated mode is outside the expected range for amorphous silicon.")
        
        # 5. Write output
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"Successfully wrote node degree stats to {output_file}")
        logger.info(f"Mode: {stats['mode']}")
        
    except Exception as e:
        logger.error(f"Failed to generate node degree stats: {e}")
        raise


if __name__ == "__main__":
    main()