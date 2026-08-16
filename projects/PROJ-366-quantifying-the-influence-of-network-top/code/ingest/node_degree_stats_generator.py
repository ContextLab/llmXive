"""
Module to generate node-degree distribution statistics from serialized atomic graphs.

This module implements Task T016: Generate node-degree distribution stats.
It calculates the mode of the global degree distribution across all loaded graphs
and outputs the results to data/processed/graphs/node_degree_stats.json.
"""
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import Counter

from config import get_config, get_paths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_graphs(graph_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load all serialized graphs from the specified directory.
    
    Args:
        graph_dir: Path to directory containing serialized graph files.
                  If None, uses the configured path from config.yaml.
                  
    Returns:
        List of graph dictionaries.
        
    Raises:
        FileNotFoundError: If the directory does not exist.
        ValueError: If no graph files are found.
    """
    if graph_dir is None:
        paths = get_paths()
        graph_dir = paths['processed_graphs']
    else:
        graph_dir = Path(graph_dir)
        
    if not graph_dir.exists():
        raise FileNotFoundError(f"Graph directory not found: {graph_dir}")
        
    graph_files = list(graph_dir.glob("*.pkl"))
    if not graph_files:
        raise ValueError(f"No graph files (.pkl) found in {graph_dir}")
        
    logger.info(f"Loading {len(graph_files)} graph files from {graph_dir}")
    
    graphs = []
    for graph_file in graph_files:
        try:
            with open(graph_file, 'rb') as f:
                graph_data = pickle.load(f)
                graphs.append(graph_data)
                logger.debug(f"Loaded graph from {graph_file.name}")
        except Exception as e:
            logger.error(f"Failed to load graph file {graph_file}: {e}")
            raise
            
    return graphs


def calculate_global_degree_distribution(graphs: List[Dict[str, Any]]) -> Dict[int, int]:
    """
    Calculate the global degree distribution across all nodes in all graphs.
    
    Args:
        graphs: List of graph dictionaries, each containing a 'nodes' list
               where each node has a 'degree' field.
               
    Returns:
        Dictionary mapping degree values to their counts.
    """
    degree_counts: Dict[int, int] = Counter()
    total_nodes = 0
    
    for graph in graphs:
        if 'nodes' not in graph:
            logger.warning(f"Graph missing 'nodes' key, skipping: {graph.get('id', 'unknown')}")
            continue
            
        for node in graph['nodes']:
            if 'degree' in node:
                degree_counts[node['degree']] += 1
                total_nodes += 1
            else:
                logger.warning(f"Node missing 'degree' field, skipping")
                
    logger.info(f"Calculated degree distribution for {total_nodes} total nodes")
    return dict(degree_counts)


def compute_mode_and_stats(degree_distribution: Dict[int, int]) -> Dict[str, Any]:
    """
    Compute the mode of the degree distribution and related statistics.
    
    Args:
        degree_distribution: Dictionary mapping degree values to their counts.
        
    Returns:
        Dictionary containing mode, mean, median, min, max, and total nodes.
    """
    if not degree_distribution:
        raise ValueError("Cannot compute statistics from empty degree distribution")
        
    # Calculate mode (degree with highest count)
    mode_degree = max(degree_distribution, key=degree_distribution.get)
    mode_count = degree_distribution[mode_degree]
    
    # Calculate total nodes and total degree sum
    total_nodes = sum(degree_distribution.values())
    total_degree_sum = sum(deg * count for deg, count in degree_distribution.items())
    
    # Calculate mean degree
    mean_degree = total_degree_sum / total_nodes if total_nodes > 0 else 0.0
    
    # Calculate median
    sorted_degrees = sorted(degree_distribution.keys())
    cumulative_count = 0
    median_degree = None
    for deg in sorted_degrees:
        cumulative_count += degree_distribution[deg]
        if cumulative_count >= total_nodes / 2:
            median_degree = deg
            break
            
    # Calculate min and max degrees
    min_degree = min(degree_distribution.keys())
    max_degree = max(degree_distribution.keys())
    
    stats = {
        "mode": mode_degree,
        "mode_count": mode_count,
        "mean": round(mean_degree, 4),
        "median": median_degree,
        "min": min_degree,
        "max": max_degree,
        "total_nodes": total_nodes,
        "degree_distribution": degree_distribution
    }
    
    logger.info(f"Computed statistics: mode={mode_degree}, mean={mean_degree:.4f}, median={median_degree}")
    return stats


def validate_mode_for_amorphous_silicon(mode: int, min_allowed: int = 2, max_allowed: int = 6) -> bool:
    """
    Validate that the calculated mode falls within expected range for amorphous silicon.
    
    Args:
        mode: The calculated mode degree.
        min_allowed: Minimum allowed mode value (default 2).
        max_allowed: Maximum allowed mode value (default 6).
        
    Returns:
        True if mode is within expected range, False otherwise.
    """
    is_valid = min_allowed <= mode <= max_allowed
    if not is_valid:
        logger.warning(f"Mode {mode} outside expected range [{min_allowed}, {max_allowed}] for amorphous silicon")
    else:
        logger.info(f"Mode {mode} is within expected range for amorphous silicon")
    return is_valid


def main():
    """
    Main entry point for generating node-degree distribution statistics.
    
    This function:
    1. Loads all serialized graphs from the configured directory
    2. Calculates the global degree distribution
    3. Computes the mode and other statistics
    4. Validates the mode against expected values for amorphous silicon
    5. Saves the results to data/processed/graphs/node_degree_stats.json
    """
    try:
        # Get configuration
        config = get_config()
        paths = get_paths()
        
        # Load graphs
        graph_dir = paths.get('processed_graphs', paths['processed_graphs'])
        graphs = load_graphs(graph_dir)
        
        if not graphs:
            raise ValueError("No graphs loaded, cannot compute statistics")
        
        # Calculate degree distribution
        degree_distribution = calculate_global_degree_distribution(graphs)
        
        # Compute statistics
        stats = compute_mode_and_stats(degree_distribution)
        
        # Validate mode
        min_mode = config.get('node_degree', {}).get('min_allowed_mode', 2)
        max_mode = config.get('node_degree', {}).get('max_allowed_mode', 6)
        is_valid = validate_mode_for_amorphous_silicon(
            stats['mode'], 
            min_mode, 
            max_mode
        )
        
        # Prepare output
        output_data = {
            "mode": stats['mode'],
            "mode_count": stats['mode_count'],
            "mean": stats['mean'],
            "median": stats['median'],
            "min": stats['min'],
            "max": stats['max'],
            "total_nodes": stats['total_nodes'],
            "is_valid_for_amorphous_silicon": is_valid,
            "degree_distribution": stats['degree_distribution']
        }
        
        # Ensure output directory exists
        output_dir = paths.get('processed_graphs', paths['processed_graphs'])
        output_path = Path(output_dir) / "node_degree_stats.json"
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)
        
        # Save results
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
            
        logger.info(f"Successfully saved node-degree statistics to {output_path}")
        print(f"Node-degree statistics saved to: {output_path}")
        print(f"Mode: {stats['mode']} (count: {stats['mode_count']})")
        print(f"Mean: {stats['mean']:.4f}")
        print(f"Median: {stats['median']}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to generate node-degree statistics: {e}")
        raise


if __name__ == "__main__":
    import sys
    sys.exit(main())