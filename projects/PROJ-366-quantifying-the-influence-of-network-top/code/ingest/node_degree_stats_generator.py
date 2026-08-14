import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, List
from collections import Counter

from config import get_paths, get_config

# Configure logger
logger = logging.getLogger(__name__)

def load_graphs(graph_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all serialized graph files from the specified directory.
    
    Args:
        graph_dir: Path to the directory containing serialized graphs (.pkl files)
        
    Returns:
        List of graph dictionaries containing 'nodes' and 'edges'
        
    Raises:
        FileNotFoundError: If no graph files are found
        ValueError: If a graph file is corrupted or missing required keys
    """
    if not graph_dir.exists():
        raise FileNotFoundError(f"Graph directory not found: {graph_dir}")
        
    graph_files = list(graph_dir.glob("*.pkl"))
    if not graph_files:
        raise FileNotFoundError(f"No .pkl graph files found in {graph_dir}")
        
    graphs = []
    for graph_file in graph_files:
        try:
            with open(graph_file, 'rb') as f:
                graph_data = pickle.load(f)
            
            # Validate required keys
            if 'nodes' not in graph_data or 'edges' not in graph_data:
                raise ValueError(f"Graph file {graph_file} missing 'nodes' or 'edges' keys")
            
            graphs.append(graph_data)
            logger.info(f"Loaded graph from {graph_file}: {len(graph_data['nodes'])} nodes, {len(graph_data['edges'])} edges")
            
        except Exception as e:
            logger.error(f"Failed to load graph {graph_file}: {e}")
            raise
            
    return graphs

def calculate_global_degree_distribution(graphs: List[Dict[str, Any]]) -> Dict[int, int]:
    """
    Calculate the global node-degree distribution across all graphs.
    
    Args:
        graphs: List of graph dictionaries
        
    Returns:
        Dictionary mapping degree values to their counts
    """
    degree_counts = Counter()
    
    for graph in graphs:
        nodes = graph['nodes']
        edges = graph['edges']
        
        # Calculate degree for each node
        node_degrees = {node_id: 0 for node_id in nodes}
        
        for edge in edges:
            # Handle both [u, v] and {'u': u, 'v': v} formats
            if isinstance(edge, (list, tuple)):
                u, v = edge[0], edge[1]
            elif isinstance(edge, dict):
                u, v = edge.get('u'), edge.get('v')
                if u is None or v is None:
                    raise ValueError(f"Edge {edge} missing 'u' or 'v' keys")
            else:
                raise ValueError(f"Unsupported edge format: {type(edge)}")
            
            if u in node_degrees:
                node_degrees[u] += 1
            if v in node_degrees:
                node_degrees[v] += 1
        
        # Count degrees
        for degree in node_degrees.values():
            degree_counts[degree] += 1
            
    return dict(degree_counts)

def compute_mode_and_stats(degree_distribution: Dict[int, int]) -> Dict[str, Any]:
    """
    Compute the mode and other statistical properties of the degree distribution.
    
    Args:
        degree_distribution: Dictionary mapping degrees to counts
        
    Returns:
        Dictionary containing mode, mean, median, min, max, and total nodes
    """
    if not degree_distribution:
        raise ValueError("Degree distribution is empty")
        
    # Flatten to list for statistical calculations
    all_degrees = []
    for degree, count in degree_distribution.items():
        all_degrees.extend([degree] * count)
        
    if not all_degrees:
        raise ValueError("No degrees found in distribution")
        
    # Calculate mode
    mode_degree = max(degree_distribution, key=degree_distribution.get)
    
    # Calculate mean
    mean_degree = sum(all_degrees) / len(all_degrees)
    
    # Calculate median
    sorted_degrees = sorted(all_degrees)
    n = len(sorted_degrees)
    if n % 2 == 0:
        median_degree = (sorted_degrees[n//2 - 1] + sorted_degrees[n//2]) / 2
    else:
        median_degree = sorted_degrees[n//2]
        
    # Calculate min and max
    min_degree = min(all_degrees)
    max_degree = max(all_degrees)
    
    # Calculate standard deviation
    variance = sum((d - mean_degree) ** 2 for d in all_degrees) / len(all_degrees)
    std_dev = variance ** 0.5
    
    return {
        "mode": mode_degree,
        "mean": round(mean_degree, 4),
        "median": round(median_degree, 4),
        "min": min_degree,
        "max": max_degree,
        "std_dev": round(std_dev, 4),
        "total_nodes": len(all_degrees),
        "distribution": degree_distribution
    }

def validate_mode_for_amorphous_silicon(mode: int, stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate that the mode falls within the expected range for amorphous silicon.
    
    Amorphous silicon typically has a coordination number (degree) distribution
    centered around 4, with most atoms having 3-5 neighbors.
    
    Args:
        mode: The mode degree value
        stats: Full statistics dictionary
        
    Returns:
        Validation result dictionary
    """
    # Expected range for amorphous silicon: 3-5 (typically 4)
    # This is based on literature values for tetrahedral amorphous silicon
    expected_min = 3
    expected_max = 5
    
    is_valid = expected_min <= mode <= expected_max
    
    validation_result = {
        "mode": mode,
        "expected_range": [expected_min, expected_max],
        "is_valid": is_valid,
        "message": f"Mode {mode} is within expected range [{expected_min}, {expected_max}] for amorphous silicon" if is_valid 
                  else f"Mode {mode} is OUTSIDE expected range [{expected_min}, {expected_max}] for amorphous silicon"
    }
    
    return validation_result

def main():
    """Main entry point for generating node-degree statistics."""
    # Get paths from config
    config = get_config()
    paths = get_paths()
    
    graph_dir = paths.get("graphs_dir", paths["data_dir"] / "processed" / "graphs")
    output_file = paths.get("node_degree_stats_file", graph_dir / "node_degree_stats.json")
    
    logger.info(f"Starting node degree statistics generation")
    logger.info(f"Graph directory: {graph_dir}")
    logger.info(f"Output file: {output_file}")
    
    try:
        # Load all graphs
        graphs = load_graphs(graph_dir)
        logger.info(f"Loaded {len(graphs)} graphs")
        
        if not graphs:
            raise ValueError("No graphs found to process")
        
        # Calculate global degree distribution
        degree_distribution = calculate_global_degree_distribution(graphs)
        logger.info(f"Calculated degree distribution with {len(degree_distribution)} unique degrees")
        
        # Compute mode and statistics
        stats = compute_mode_and_stats(degree_distribution)
        logger.info(f"Mode: {stats['mode']}, Mean: {stats['mean']}, Median: {stats['median']}")
        
        # Validate mode for amorphous silicon
        validation = validate_mode_for_amorphous_silicon(stats['mode'], stats)
        logger.info(validation['message'])
        
        # Prepare final output
        output_data = {
            "mode": stats['mode'],
            "mean": stats['mean'],
            "median": stats['median'],
            "min": stats['min'],
            "max": stats['max'],
            "std_dev": stats['std_dev'],
            "total_nodes": stats['total_nodes'],
            "distribution": stats['distribution'],
            "validation": validation,
            "metadata": {
                "num_graphs_processed": len(graphs),
                "graph_directory": str(graph_dir),
                "cutoff_distance": config.get("bond_cutoff", 3.0)
            }
        }
        
        # Ensure output directory exists
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write output
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Successfully wrote node degree statistics to {output_file}")
        
        # Print summary to stdout for quick verification
        print(f"Node Degree Statistics Generated:")
        print(f"  Mode: {stats['mode']}")
        print(f"  Mean: {stats['mean']}")
        print(f"  Median: {stats['median']}")
        print(f"  Total Nodes: {stats['total_nodes']}")
        print(f"  Validation: {validation['message']}")
        
    except Exception as e:
        logger.error(f"Failed to generate node degree statistics: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()
