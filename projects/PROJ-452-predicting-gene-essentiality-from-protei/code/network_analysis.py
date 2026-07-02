"""
Network Analysis Module for Gene Essentiality Prediction.

This module computes topological centrality metrics (degree, betweenness, eigenvector)
from Protein-Protein Interaction (PPI) networks. It implements k-sampling for
betweenness centrality on large networks (>5,000 nodes) to ensure runtime compliance
with FR-004 (<30min).
"""

import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

import networkx as nx
import numpy as np

from utils import setup_logging, safe_join
from config import load_config, get_path, ensure_dirs

logger = setup_logging(__name__)

# Threshold for switching to k-sampling for betweenness centrality
# Per FR-004: ensure <30min runtime on large networks
BETWEENNESS_SAMPLING_THRESHOLD = 5000
# Number of random nodes to sample for approximation
K_SAMPLES = 1000


class NetworkAnalysisError(Exception):
    """Custom exception for network analysis failures."""
    pass


def load_graph_from_adjacency_list(
    data: Dict[str, List[str]], 
    directed: bool = False
) -> nx.Graph:
    """
    Construct a NetworkX graph from an adjacency list dictionary.
    
    Args:
        data: Dictionary mapping node IDs to lists of neighbor IDs.
        directed: If True, creates a DiGraph; otherwise, a Graph.
        
    Returns:
        A NetworkX graph object.
    """
    if directed:
        G = nx.DiGraph()
    else:
        G = nx.Graph()
    
    for node, neighbors in data.items():
        G.add_node(node)
        for neighbor in neighbors:
            G.add_edge(node, neighbor)
    
    return G


def compute_degree_centrality(G: nx.Graph) -> Dict[str, float]:
    """
    Compute degree centrality for all nodes in the graph.
    
    Args:
        G: NetworkX graph.
        
    Returns:
        Dictionary mapping node IDs to degree centrality scores.
    """
    if G.number_of_nodes() == 0:
        return {}
    
    try:
        return nx.degree_centrality(G)
    except Exception as e:
        logger.error(f"Failed to compute degree centrality: {e}")
        raise NetworkAnalysisError(f"Degree centrality computation failed: {e}")


def compute_eigenvector_centrality(G: nx.Graph, max_iter: int = 100) -> Dict[str, float]:
    """
    Compute eigenvector centrality for all nodes in the graph.
    
    Note: Eigenvector centrality may fail for disconnected graphs or graphs
    with certain structural properties. In such cases, we fall back to
    a zero-initialized dictionary or raise a specific warning.
    
    Args:
        G: NetworkX graph.
        max_iter: Maximum iterations for power iteration method.
        
    Returns:
        Dictionary mapping node IDs to eigenvector centrality scores.
    """
    if G.number_of_nodes() == 0:
        return {}
    
    try:
        # NetworkX eigenvector_centrality can fail on disconnected components
        # We attempt to compute it; if it fails, we return zeros for all nodes
        return nx.eigenvector_centrality(G, max_iter=max_iter)
    except nx.PowerIterationFailedConvergence:
        logger.warning("Eigenvector centrality failed to converge. Returning zeros.")
        return {node: 0.0 for node in G.nodes()}
    except Exception as e:
        logger.error(f"Failed to compute eigenvector centrality: {e}")
        # Return zeros as a safe fallback rather than crashing the whole pipeline
        return {node: 0.0 for node in G.nodes()}


def compute_betweenness_centrality(G: nx.Graph, k: Optional[int] = None) -> Dict[str, float]:
    """
    Compute betweenness centrality with automatic sampling for large graphs.
    
    Per FR-004: Use k-sampling for networks > 5,000 nodes to ensure <30min runtime.
    
    Args:
        G: NetworkX graph.
        k: Number of nodes to sample. If None, uses default threshold logic.
           If k=0 or k is not provided and graph is small, exact calculation is used.
           
    Returns:
        Dictionary mapping node IDs to betweenness centrality scores.
    """
    if G.number_of_nodes() == 0:
        return {}
    
    n_nodes = G.number_of_nodes()
    
    # Determine if we should use sampling
    use_sampling = False
    if k is None:
        if n_nodes > BETWEENNESS_SAMPLING_THRESHOLD:
            use_sampling = True
            k = K_SAMPLES
        else:
            k = 0 # 0 means exact calculation in NetworkX
    else:
        if k > 0:
            use_sampling = True
        else:
            use_sampling = False
    
    start_time = time.time()
    
    try:
        if use_sampling:
            logger.info(f"Computing approximate betweenness centrality on {n_nodes} nodes with k={k} samples.")
            # NetworkX betweenness_centrality with k parameter performs sampling
            betweenness = nx.betweenness_centrality(G, k=k, normalized=True)
        else:
            logger.info(f"Computing exact betweenness centrality on {n_nodes} nodes.")
            betweenness = nx.betweenness_centrality(G, normalized=True)
        
        elapsed = time.time() - start_time
        logger.info(f"Betweenness centrality computed in {elapsed:.2f}s.")
        return betweenness
        
    except Exception as e:
        logger.error(f"Failed to compute betweenness centrality: {e}")
        raise NetworkAnalysisError(f"Betweenness centrality computation failed: {e}")


def compute_all_centrality_metrics(
    G: nx.Graph
) -> Dict[str, Dict[str, float]]:
    """
    Compute all required centrality metrics for a given graph.
    
    Args:
        G: NetworkX graph.
        
    Returns:
        Dictionary with keys 'degree', 'betweenness', 'eigenvector',
        each containing a mapping of node_id -> score.
    """
    logger.info(f"Starting centrality computation for graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    
    if G.number_of_nodes() == 0:
        logger.warning("Empty graph provided. Returning empty centrality metrics.")
        return {
            'degree': {},
            'betweenness': {},
            'eigenvector': {}
        }
    
    # Handle disconnected components by computing on the largest connected component
    # or warn if the graph is highly fragmented.
    # For now, we compute on the full graph as per standard practice, 
    # but eigenvector centrality handles disconnectedness via fallback.
    
    metrics = {
        'degree': compute_degree_centrality(G),
        'betweenness': compute_betweenness_centrality(G),
        'eigenvector': compute_eigenvector_centrality(G)
    }
    
    logger.info("All centrality metrics computed successfully.")
    return metrics


def process_organism_networks(
    organisms_data: Dict[str, Dict[str, Any]],
    output_dir: Optional[Union[str, Path]] = None
) -> Dict[str, Dict[str, float]]:
    """
    Process networks for multiple organisms and compute centrality metrics.
    
    Args:
        organisms_data: Dictionary mapping organism IDs to their network data.
                        Expected structure: {org_id: {'nodes': [...], 'edges': [...]} or adjacency list}
        output_dir: Optional directory to save results (JSON). If None, returns dict only.
                    
    Returns:
        Dictionary mapping organism IDs to their centrality metrics.
    """
    all_results = {}
    
    for org_id, data in organisms_data.items():
        logger.info(f"Processing network for organism: {org_id}")
        
        # Determine input format. Assuming data contains an adjacency list or edges.
        # Based on data_loader, we expect 'adjacency_list' or 'edges' list.
        if 'adjacency_list' in data:
            adj_list = data['adjacency_list']
        elif 'edges' in data:
            # Convert edge list to adjacency list if necessary, or pass directly to Graph
            edges = data['edges']
            adj_list = {}
            for u, v in edges:
                adj_list.setdefault(u, []).append(v)
                adj_list.setdefault(v, []).append(u)
        else:
            logger.warning(f"No valid network data found for {org_id}. Skipping.")
            continue
        
        # Build Graph
        G = load_graph_from_adjacency_list(adj_list)
        
        if G.number_of_nodes() == 0:
            logger.warning(f"Graph for {org_id} is empty after loading.")
            continue
        
        # Compute metrics
        metrics = compute_all_centrality_metrics(G)
        
        # Store results
        all_results[org_id] = metrics
        
        # Save individual results if output_dir is provided
        if output_dir:
            out_path = Path(output_dir)
            ensure_dirs(out_path)
            file_path = out_path / f"centrality_{org_id}.json"
            import json
            with open(file_path, 'w') as f:
                json.dump(metrics, f, indent=2)
            logger.info(f"Saved centrality metrics for {org_id} to {file_path}")
    
    return all_results


def main():
    """
    Main entry point for running network analysis.
    Reads configuration, loads networks (via data_loader), computes centralities,
    and saves results.
    """
    # Setup logging
    logger = setup_logging(__name__)
    
    try:
        config = load_config()
        organisms = get_organisms(config)
        output_dir = get_path(config, "results")
        ensure_dirs(output_dir)
        
        # We need to load the data first. Since data_loader is a sibling module,
        # we import the necessary function.
        # Note: In a real pipeline, data_loader might return the raw data structures.
        # Here we assume data_loader has a function to get all networks.
        # If not, we might need to call fetch/load for each organism.
        # For T015, we assume the data is already fetched and available in data/raw or via API.
        # To make this script runnable independently as per T015 scope, 
        # we will simulate the data loading or import the loader.
        
        # Importing data_loader to fetch networks
        from data_loader import load_essentiality_for_all_organisms, fetch_string_network
        
        # We need to fetch networks for all organisms.
        # Let's assume we have a list of organisms from config.
        # We will fetch networks one by one.
        
        organisms_data = {}
        for org_id in organisms:
            logger.info(f"Fetching network for {org_id}...")
            try:
                # Attempt to fetch from STRING, fallback to local
                # This call might need adjustment based on exact data_loader signature
                network_data = fetch_string_network(org_id, config)
                if network_data:
                    organisms_data[org_id] = network_data
                else:
                    logger.warning(f"No network data for {org_id} from STRING or local.")
            except Exception as e:
                logger.error(f"Failed to fetch network for {org_id}: {e}")
                continue
        
        if not organisms_data:
            logger.error("No network data available for any organism. Exiting.")
            return
        
        # Compute centralities
        results = process_organism_networks(organisms_data, output_dir)
        
        # Save aggregate results
        aggregate_path = Path(output_dir) / "centrality_all.json"
        import json
        with open(aggregate_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Saved aggregate centrality results to {aggregate_path}")
        
        logger.info("Network analysis completed successfully.")
        
    except Exception as e:
        logger.exception(f"Network analysis failed: {e}")
        raise


if __name__ == "__main__":
    main()
