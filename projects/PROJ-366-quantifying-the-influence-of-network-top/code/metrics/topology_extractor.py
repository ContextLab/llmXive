"""
Topology Extractor Module (US2 - T021)

Computes topological metrics per atom from AtomicGraph objects:
- Node degree
- Local clustering coefficient
- Shortest-path statistics (mean, max, diameter of local neighborhood)

Implements FR-002.
"""
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import networkx as nx

# Import from sibling modules as per API surface
from config import get_config, get_paths
from ingest.graph_builder import build_graph_from_xyz

logger = logging.getLogger(__name__)

def compute_local_clustering_coefficient(graph: nx.Graph, node: int) -> float:
    """
    Compute the local clustering coefficient for a specific node.
    This is the ratio of existing edges between neighbors to possible edges.
    """
    return nx.clustering(graph, node)

def compute_shortest_path_stats(graph: nx.Graph, node: int, radius: int = 3) -> Dict[str, float]:
    """
    Compute shortest-path statistics for a node within a local neighborhood.
    
    Args:
        graph: The atomic graph.
        node: The target node index.
        radius: Maximum distance to consider neighbors.
    
    Returns:
        Dictionary with 'mean', 'max', and 'count' of shortest paths.
    """
    try:
        # Get neighbors within radius
        lengths = nx.single_source_shortest_path_length(graph, node, cutoff=radius)
        
        # Filter out the node itself (distance 0)
        distances = [d for n, d in lengths.items() if n != node and d > 0]
        
        if not distances:
            return {
                "mean": 0.0,
                "max": 0.0,
                "count": 0
            }
        
        return {
            "mean": float(np.mean(distances)),
            "max": float(np.max(distances)),
            "count": len(distances)
        }
    except Exception as e:
        logger.warning(f"Could not compute shortest path stats for node {node}: {e}")
        return {
            "mean": 0.0,
            "max": 0.0,
            "count": 0
        }

def extract_metrics_for_graph(graph: nx.Graph) -> List[Dict[str, Any]]:
    """
    Extract topological metrics for every node in the graph.
    
    Args:
        graph: NetworkX graph representing atomic structure.
    
    Returns:
        List of dictionaries, one per node, containing:
        - node_id
        - degree
        - clustering_coefficient
        - shortest_path_stats (mean, max, count)
    """
    metrics = []
    nodes = sorted(graph.nodes())
    
    for node in nodes:
        degree = graph.degree[node]
        clustering = compute_local_clustering_coefficient(graph, node)
        sp_stats = compute_shortest_path_stats(graph, node)
        
        metrics.append({
            "node_id": node,
            "degree": degree,
            "clustering_coefficient": clustering,
            "shortest_path_stats": sp_stats
        })
    
    return metrics

def process_graph_file(
    input_path: Path,
    output_dir: Path,
    cutoff: float = 3.0
) -> Tuple[Path, Dict[str, Any]]:
    """
    Process a single graph file (pickle), extract metrics, and save results.
    
    Args:
        input_path: Path to the pickled graph file.
        output_dir: Directory to save output metrics.
        cutoff: Bond cutoff distance (unused here as graph is pre-built, but kept for signature).
    
    Returns:
        Tuple of (output_path, summary_stats).
    """
    # Load the graph
    logger.info(f"Loading graph from {input_path}")
    with open(input_path, 'rb') as f:
        graph_data = pickle.load(f)
    
    # The graph data structure from graph_builder/serializer usually contains:
    # {'graph': nx.Graph, 'metadata': {...}, 'atoms': [...]}
    if isinstance(graph_data, dict) and 'graph' in graph_data:
        graph = graph_data['graph']
    else:
        # Fallback: assume the file contains the graph directly or handle error
        if isinstance(graph_data, nx.Graph):
            graph = graph_data
        else:
            raise ValueError(f"Unrecognized graph data format in {input_path}")

    # Extract metrics
    node_metrics = extract_metrics_for_graph(graph)
    
    # Compute global stats for this graph
    degrees = [m['degree'] for m in node_metrics]
    clusterings = [m['clustering_coefficient'] for m in node_metrics]
    
    global_stats = {
        "num_nodes": len(node_metrics),
        "num_edges": graph.number_of_edges(),
        "mean_degree": float(np.mean(degrees)) if degrees else 0.0,
        "std_degree": float(np.std(degrees)) if degrees else 0.0,
        "mean_clustering": float(np.mean(clusterings)) if clusterings else 0.0,
        "diameter": nx.diameter(graph) if nx.is_connected(graph) else -1
    }
    
    # Prepare output
    output_filename = f"{input_path.stem}_metrics.json"
    output_path = output_dir / output_filename
    
    result = {
        "source_file": str(input_path),
        "global_stats": global_stats,
        "node_metrics": node_metrics
    }
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Saved metrics to {output_path}")
    return output_path, global_stats

def extract_topology_metrics(
    input_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    config: Optional[Dict] = None
) -> List[Path]:
    """
    Main entry point to extract topology metrics for all graphs in a directory.
    
    Args:
        input_dir: Directory containing .pkl graph files. Defaults to config paths.
        output_dir: Directory to save .json metrics. Defaults to config paths.
        config: Optional config dict. If None, loads from get_config().
    
    Returns:
        List of output file paths.
    """
    cfg = config or get_config()
    paths = get_paths()
    
    if input_dir is None:
        input_dir = paths['processed_graphs']
    if output_dir is None:
        output_dir = paths['processed_graphs'] / "topology_metrics"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    input_files = list(input_dir.glob("*.pkl"))
    if not input_files:
        logger.warning(f"No .pkl files found in {input_dir}")
        return []
    
    logger.info(f"Processing {len(input_files)} graph files...")
    output_paths = []
    
    for file_path in input_files:
        try:
            out_path, _ = process_graph_file(file_path, output_dir)
            output_paths.append(out_path)
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            # Continue processing other files
            continue
    
    return output_paths

def main():
    """CLI entry point for topology extraction."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting Topology Extraction (T021)")
    
    try:
        output_files = extract_topology_metrics()
        logger.info(f"Completed. Generated {len(output_files)} metric files.")
    except Exception as e:
        logger.error(f"Topology extraction failed: {e}")
        raise

if __name__ == "__main__":
    main()
