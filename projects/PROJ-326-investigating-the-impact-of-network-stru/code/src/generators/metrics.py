import json
import logging
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

import networkx as nx
import numpy as np

from code.src.utils.logging import log_metric, log_run

logger = logging.getLogger(__name__)

def compute_degree_distribution(G: nx.Graph) -> Dict[str, Any]:
    """
    Compute the degree distribution of the graph.
    Returns a dictionary with 'distribution' (list of counts) and 'mean', 'std'.
    """
    degrees = [d for _, d in G.degree()]
    counts = Counter(degrees)
    
    # Normalize to probability distribution
    total_nodes = len(degrees)
    distribution = {k: v / total_nodes for k, v in sorted(counts.items())}
    
    mean_degree = np.mean(degrees)
    std_degree = np.std(degrees)
    
    return {
        "distribution": distribution,
        "mean": float(mean_degree),
        "std": float(std_degree),
        "max_degree": int(max(degrees)) if degrees else 0,
        "min_degree": int(min(degrees)) if degrees else 0
    }

def compute_clustering_coefficients(G: nx.Graph) -> Dict[str, float]:
    """
    Compute clustering coefficients.
    Returns average clustering and a sample of local coefficients.
    """
    avg_clustering = nx.average_clustering(G)
    local_clustering = nx.clustering(G)
    
    # Store a representative sample of local coefficients (first 10 or all if <10)
    nodes = list(G.nodes())
    sample_size = min(10, len(nodes))
    sample_nodes = nodes[:sample_size]
    local_samples = {str(n): local_clustering[n] for n in sample_nodes}
    
    return {
        "average": float(avg_clustering),
        "local_sample": local_samples
    }

def compute_path_lengths(G: nx.Graph) -> Dict[str, float]:
    """
    Compute average path length and diameter.
    Returns NaN for disconnected graphs where path length is undefined.
    """
    if not nx.is_connected(G):
        return {
            "average_path_length": float('nan'),
            "diameter": float('nan'),
            "is_connected": False
        }
    
    try:
        avg_path = nx.average_shortest_path_length(G)
        diameter = nx.diameter(G)
    except Exception as e:
        logger.warning(f"Error computing path lengths: {e}")
        avg_path = float('nan')
        diameter = float('nan')
    
    return {
        "average_path_length": float(avg_path),
        "diameter": float(diameter),
        "is_connected": True
    }

def extract_graph_metrics(graph_id: str, G: nx.Graph, generation_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extract all required metrics for a single graph as per FR-004.
    
    Returns a dictionary containing:
    - graph_id
    - generation_algorithm
    - parameter_values
    - node_count
    - edge_count
    - degree_distribution
    - clustering_coefficients
    - path_lengths
    - is_connected
    """
    logger.info(f"Extracting metrics for graph {graph_id}")
    
    degree_dist = compute_degree_distribution(G)
    clustering = compute_clustering_coefficients(G)
    path_lengths = compute_path_lengths(G)
    
    metrics = {
        "graph_id": graph_id,
        "generation_algorithm": generation_params.get("algorithm", "unknown") if generation_params else "unknown",
        "parameter_values": generation_params.get("params", {}) if generation_params else {},
        "node_count": G.number_of_nodes(),
        "edge_count": G.number_of_edges(),
        "degree_distribution": degree_dist,
        "clustering_coefficients": clustering,
        "path_lengths": path_lengths,
        "is_connected": path_lengths.get("is_connected", False)
    }
    
    return metrics

def write_metrics_to_manifest(metrics_list: List[Dict[str, Any]], manifest_path: str) -> None:
    """
    Write a list of metric dictionaries to the global batch manifest JSON file.
    Creates the parent directory if it doesn't exist.
    """
    manifest_file = Path(manifest_path)
    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    
    # If file exists, load existing data; otherwise start fresh
    if manifest_file.exists():
        try:
            with open(manifest_file, 'r') as f:
                existing_data = json.load(f)
                if not isinstance(existing_data, list):
                    existing_data = []
        except (json.JSONDecodeError, IOError):
            existing_data = []
    else:
        existing_data = []
    
    # Append new metrics
    existing_data.extend(metrics_list)
    
    # Write back
    with open(manifest_file, 'w') as f:
        json.dump(existing_data, f, indent=2)
    
    logger.info(f"Wrote {len(metrics_list)} metric entries to {manifest_path}")

def log_graph_generation_event(
    graph_id: str, 
    run_id: str, 
    seed: int, 
    status: str, 
    duration_seconds: float,
    algorithm: str,
    is_connected: bool
) -> None:
    """
    Log the graph generation event to the run log.
    """
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": "graph_generated",
        "run_id": run_id,
        "seed": seed,
        "status": status,
        "duration_seconds": duration_seconds,
        "algorithm": algorithm,
        "is_connected": is_connected
    }
    log_metric(event)
