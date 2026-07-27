"""
Metric extraction module for network topology analysis.

Computes degree distribution, clustering coefficients, and average path length
for generated graphs and writes results to the global batch manifest.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx
import numpy as np
from scipy import stats

from code.src.generators.base import BaseGenerator

logger = logging.getLogger(__name__)

def compute_degree_distribution(graph: nx.Graph) -> Dict[str, Any]:
    """
    Compute degree distribution statistics.
    
    Args:
        graph: NetworkX graph instance
        
    Returns:
        Dictionary containing degree distribution statistics
    """
    degrees = [d for n, d in graph.degree()]
    
    # Basic statistics
    degree_mean = float(np.mean(degrees))
    degree_std = float(np.std(degrees))
    degree_max = int(max(degrees))
    degree_min = int(min(degrees))
    
    # Degree histogram (binned)
    degree_counts = dict(graph.degree())
    unique_degrees, counts = np.unique(degrees, return_counts=True)
    degree_histogram = {int(k): int(v) for k, v in zip(unique_degrees, counts)}
    
    # Power-law fit for scale-free networks
    # Using only nodes with degree >= 1 to avoid log(0)
    positive_degrees = [d for d in degrees if d > 0]
    if len(positive_degrees) > 1:
        try:
            # Fit power law: P(k) ~ k^(-gamma)
            gamma, loglikelihood, r_squared = fit_power_law(positive_degrees)
            is_power_law = r_squared >= 0.95
        except Exception:
            gamma = None
            loglikelihood = None
            r_squared = None
            is_power_law = False
    else:
        gamma = None
        loglikelihood = None
        r_squared = None
        is_power_law = False
    
    return {
        "mean": degree_mean,
        "std": degree_std,
        "max": degree_max,
        "min": degree_min,
        "histogram": degree_histogram,
        "power_law_fit": {
            "gamma": gamma,
            "log_likelihood": loglikelihood,
            "r_squared": r_squared,
            "is_power_law": is_power_law
        }
    }

def fit_power_law(degrees: List[int]) -> Tuple[float, float, float]:
    """
    Fit a power-law distribution to degree data.
    
    Args:
        degrees: List of degree values
        
    Returns:
        Tuple of (gamma, log_likelihood, r_squared)
    """
    # Use log-log regression for simplicity
    log_degrees = np.log(degrees)
    log_counts = np.log(np.bincount(degrees)[np.bincount(degrees) > 0])
    
    if len(log_degrees) < 2:
        raise ValueError("Not enough data points for power-law fit")
    
    # Fit linear regression on log-log scale
    slope, intercept, r_value, p_value, std_err = stats.linregress(log_degrees, log_counts)
    
    gamma = -slope
    log_likelihood = float(np.sum(log_counts - (intercept + slope * log_degrees) ** 2))
    r_squared = float(r_value ** 2)
    
    return gamma, log_likelihood, r_squared

def compute_clustering_metrics(graph: nx.Graph) -> Dict[str, Any]:
    """
    Compute clustering coefficient metrics.
    
    Args:
        graph: NetworkX graph instance
        
    Returns:
        Dictionary containing clustering coefficient statistics
    """
    # Global clustering coefficient
    global_clustering = nx.transitivity(graph)
    
    # Local clustering coefficients
    local_clustering = nx.clustering(graph)
    local_values = list(local_clustering.values())
    
    local_mean = float(np.mean(local_values))
    local_std = float(np.std(local_values))
    local_max = float(max(local_values)) if local_values else 0.0
    local_min = float(min(local_values)) if local_values else 0.0
    
    # Distribution of local clustering coefficients
    unique_clustering, counts = np.unique(local_values, return_counts=True)
    clustering_histogram = {float(k): int(v) for k, v in zip(unique_clustering, counts)}
    
    return {
        "global": global_clustering,
        "local_mean": local_mean,
        "local_std": local_std,
        "local_max": local_max,
        "local_min": local_min,
        "histogram": clustering_histogram
    }

def compute_path_length_metrics(graph: nx.Graph) -> Dict[str, Any]:
    """
    Compute average path length and related metrics.
    
    Args:
        graph: NetworkX graph instance
        
    Returns:
        Dictionary containing path length statistics
    """
    # Check if graph is connected
    if nx.is_connected(graph):
        try:
            avg_path_length = nx.average_shortest_path_length(graph)
            max_path_length = nx.diameter(graph)
            is_finite = True
        except nx.NetworkXError:
            avg_path_length = None
            max_path_length = None
            is_finite = False
    else:
        # For disconnected graphs, compute average over largest component
        try:
            largest_cc = max(nx.connected_components(graph), key=len)
            subgraph = graph.subgraph(largest_cc)
            avg_path_length = nx.average_shortest_path_length(subgraph)
            max_path_length = nx.diameter(subgraph)
            is_finite = True
        except nx.NetworkXError:
            avg_path_length = None
            max_path_length = None
            is_finite = False
    
    # Characteristic path length
    characteristic_path_length = avg_path_length if avg_path_length is not None else None
    
    return {
        "average_shortest_path_length": avg_path_length,
        "diameter": max_path_length,
        "characteristic_path_length": characteristic_path_length,
        "is_finite": is_finite
    }

def extract_all_metrics(graph: nx.Graph, graph_id: str, topology_type: str) -> Dict[str, Any]:
    """
    Extract all topological metrics for a graph.
    
    Args:
        graph: NetworkX graph instance
        graph_id: Unique identifier for the graph
        topology_type: Type of topology (ER, WS, SF)
        
    Returns:
        Dictionary containing all extracted metrics
    """
    logger.info(f"Extracting metrics for graph {graph_id} ({topology_type})")
    
    metrics = {
        "graph_id": graph_id,
        "topology_type": topology_type,
        "num_nodes": graph.number_of_nodes(),
        "num_edges": graph.number_of_edges(),
        "is_connected": nx.is_connected(graph) if graph.number_of_nodes() > 0 else False,
        "degree_distribution": compute_degree_distribution(graph),
        "clustering_metrics": compute_clustering_metrics(graph),
        "path_length_metrics": compute_path_length_metrics(graph)
    }
    
    return metrics

def write_metrics_to_manifest(
    metrics_list: List[Dict[str, Any]],
    manifest_path: Path
) -> None:
    """
    Write metrics to the global batch manifest JSON file.
    
    Args:
        metrics_list: List of metric dictionaries to write
        manifest_path: Path to the manifest file
    """
    # Ensure directory exists
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing manifest if it exists
    if manifest_path.exists():
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not load existing manifest: {e}")
            manifest = {"batches": [], "metrics": [], "metadata": {}}
    else:
        manifest = {"batches": [], "metrics": [], "metadata": {}}
    
    # Ensure metrics list exists
    if "metrics" not in manifest:
        manifest["metrics"] = []
    
    # Append new metrics
    manifest["metrics"].extend(metrics_list)
    
    # Update metadata
    manifest["metadata"]["total_metrics"] = len(manifest["metrics"])
    manifest["metadata"]["last_updated"] = str(Path(manifest_path).stat().st_mtime)
    
    # Write back to file
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Wrote {len(metrics_list)} metrics to {manifest_path}")

def update_manifest_with_metrics(
    graph: nx.Graph,
    graph_id: str,
    topology_type: str,
    manifest_path: Path
) -> Dict[str, Any]:
    """
    Extract metrics for a graph and update the manifest.
    
    Args:
        graph: NetworkX graph instance
        graph_id: Unique identifier for the graph
        topology_type: Type of topology (ER, WS, SF)
        manifest_path: Path to the manifest file
        
    Returns:
        The extracted metrics dictionary
    """
    metrics = extract_all_metrics(graph, graph_id, topology_type)
    write_metrics_to_manifest([metrics], manifest_path)
    
    return metrics

def main() -> None:
    """
    Main entry point for metrics extraction.
    
    This function is intended to be called from batch generation scripts
    to ensure metrics are computed and written to the manifest.
    """
    logger.info("Metrics extraction module loaded")
    logger.info("Use extract_all_metrics() and write_metrics_to_manifest() to process graphs")