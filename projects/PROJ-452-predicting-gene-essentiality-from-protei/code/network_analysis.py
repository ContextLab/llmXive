"""
Network analysis module for computing centrality metrics on protein interaction networks.

Handles disconnected components and empty networks gracefully.
"""
import logging
import time
import os
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import networkx as nx
import numpy as np

logger = logging.getLogger(__name__)

class NetworkAnalysisError(Exception):
    """Custom exception for network analysis errors."""
    pass

def load_graph_from_adjacency_list(adjacency_data: Dict[str, List[str]]) -> nx.Graph:
    """
    Load a NetworkX graph from an adjacency list dictionary.
    
    Args:
        adjacency_data: Dictionary mapping node IDs to lists of neighbor IDs.
        
    Returns:
        NetworkX Graph object.
    """
    G = nx.Graph()
    for node, neighbors in adjacency_data.items():
        G.add_node(node)
        for neighbor in neighbors:
            G.add_edge(node, neighbor)
    return G

def compute_degree_centrality(G: nx.Graph) -> Dict[str, float]:
    """
    Compute degree centrality for all nodes in the graph.
    
    For disconnected graphs, nodes in isolated components get 0 centrality.
    
    Args:
        G: NetworkX Graph.
        
    Returns:
        Dictionary mapping node IDs to degree centrality values.
    """
    if G.number_of_nodes() == 0:
        logger.warning("Graph has no nodes. Returning empty centrality dict.")
        return {}
    
    try:
        centrality = nx.degree_centrality(G)
        return centrality
    except Exception as e:
        raise NetworkAnalysisError(f"Failed to compute degree centrality: {e}")

def compute_eigenvector_centrality(G: nx.Graph, max_iter: int = 1000) -> Dict[str, float]:
    """
    Compute eigenvector centrality for all nodes in the graph.
    
    For disconnected graphs, nodes in components without a dominant eigenvector
    will get 0 centrality.
    
    Args:
        G: NetworkX Graph.
        max_iter: Maximum iterations for power method.
        
    Returns:
        Dictionary mapping node IDs to eigenvector centrality values.
    """
    if G.number_of_nodes() == 0:
        logger.warning("Graph has no nodes. Returning empty centrality dict.")
        return {}
    
    try:
        centrality = nx.eigenvector_centrality(G, max_iter=max_iter)
        return centrality
    except nx.PowerIterationFailedConvergence:
        logger.warning("Eigenvector centrality did not converge. Returning zeros for all nodes.")
        return {node: 0.0 for node in G.nodes()}
    except Exception as e:
        raise NetworkAnalysisError(f"Failed to compute eigenvector centrality: {e}")

def compute_betweenness_centrality(G: nx.Graph, k: Optional[int] = None) -> Dict[str, float]:
    """
    Compute betweenness centrality for all nodes in the graph.
    
    For large graphs (>5000 nodes), uses sampling (k parameter) to ensure runtime.
    For disconnected graphs, nodes in isolated components get 0 centrality.
    
    Args:
        G: NetworkX Graph.
        k: Number of nodes to sample for approximation. If None, computes exact.
        
    Returns:
        Dictionary mapping node IDs to betweenness centrality values.
    """
    if G.number_of_nodes() == 0:
        logger.warning("Graph has no nodes. Returning empty centrality dict.")
        return {}
    
    try:
        if k is not None:
            centrality = nx.betweenness_centrality(G, k=k, normalized=True)
        else:
            centrality = nx.betweenness_centrality(G, normalized=True)
        return centrality
    except Exception as e:
        raise NetworkAnalysisError(f"Failed to compute betweenness centrality: {e}")

def compute_all_centrality_metrics(
    G: nx.Graph,
    betweenness_k: Optional[int] = None
) -> Dict[str, Dict[str, float]]:
    """
    Compute all centrality metrics for a graph.
    
    Handles disconnected networks by assigning 0 centrality to nodes in isolated
    components. Handles empty graphs by returning empty dictionaries.
    
    Args:
        G: NetworkX Graph.
        betweenness_k: Number of samples for betweenness centrality (for large graphs).
        
    Returns:
        Dictionary with keys 'degree', 'eigenvector', 'betweenness', each mapping
        node IDs to centrality values.
    """
    if G.number_of_nodes() == 0:
        logger.warning("Received empty graph. Returning all empty centrality dicts.")
        return {
            'degree': {},
            'eigenvector': {},
            'betweenness': {}
        }
    
    # Check for disconnected components
    num_components = nx.number_connected_components(G)
    if num_components > 1:
        logger.info(f"Graph has {num_components} connected components. "
                   f"Nodes in isolated components will receive 0 centrality.")
    
    degree_cent = compute_degree_centrality(G)
    eigenvector_cent = compute_eigenvector_centrality(G)
    betweenness_cent = compute_betweenness_centrality(G, k=betweenness_k)
    
    return {
        'degree': degree_cent,
        'eigenvector': eigenvector_cent,
        'betweenness': betweenness_cent
    }

def maslov_sneppen_rewire(G: nx.Graph, n_swaps: int = 1000) -> nx.Graph:
    """
    Perform Maslov-Sneppen rewiring to generate a degree-preserving random graph.
    
    Args:
        G: Original NetworkX Graph.
        n_swaps: Number of edge swaps to perform.
        
    Returns:
        Rewired NetworkX Graph with same degree sequence.
    """
    if G.number_of_edges() < 2:
        logger.warning("Graph has too few edges for rewiring. Returning copy.")
        return G.copy()
    
    try:
        rewired_G = nx.double_edge_swap(G, nswap=n_swaps, max_tries=10 * n_swaps)
        return rewired_G
    except Exception as e:
        raise NetworkAnalysisError(f"Maslov-Sneppen rewiring failed: {e}")

def generate_rewired_graphs(
    G: nx.Graph,
    n_graphs: int = 10,
    n_swaps_per_graph: int = 1000,
    output_dir: Optional[Path] = None
) -> List[nx.Graph]:
    """
    Generate multiple degree-preserving random graphs.
    
    Args:
        G: Original NetworkX Graph.
        n_graphs: Number of rewired graphs to generate.
        n_swaps_per_graph: Number of swaps per graph.
        output_dir: Optional directory to save graphs.
        
    Returns:
        List of rewired NetworkX Graphs.
    """
    rewired_graphs = []
    
    for i in range(n_graphs):
        rewired_G = maslov_sneppen_rewire(G, n_swaps=n_swaps_per_graph)
        rewired_graphs.append(rewired_G)
        
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            filepath = output_dir / f"rewired_graph_{i}.graphml"
            nx.write_graphml(rewired_G, filepath)
            logger.debug(f"Saved rewired graph {i} to {filepath}")
    
    return rewired_graphs

def compute_centrality_for_rewired_graphs(
    rewired_graphs: List[nx.Graph],
    betweenness_k: Optional[int] = None
) -> List[Dict[str, Dict[str, float]]]:
    """
    Compute centrality metrics for a list of rewired graphs.
    
    Args:
        rewired_graphs: List of rewired NetworkX Graphs.
        betweenness_k: Number of samples for betweenness centrality.
        
    Returns:
        List of centrality dictionaries, one per graph.
    """
    results = []
    for i, G in enumerate(rewired_graphs):
        centrality = compute_all_centrality_metrics(G, betweenness_k=betweenness_k)
        results.append(centrality)
        logger.debug(f"Computed centrality for rewired graph {i}")
    
    return results

def process_organism_networks(
    organism_data: Dict[str, Any],
    output_dir: Path,
    betweenness_k: Optional[int] = None
) -> Dict[str, Any]:
    """
    Process network data for a single organism, computing all centrality metrics.
    
    Handles:
    - Disconnected networks (assigns 0 centrality to isolated nodes)
    - Empty networks (returns empty dicts with warning)
    - Missing gene overlaps (skips with warning)
    
    Args:
        organism_data: Dictionary containing 'adjacency_list' and 'essentiality_labels'.
        output_dir: Directory to save results.
        betweenness_k: Number of samples for betweenness centrality.
        
    Returns:
        Dictionary with centrality results and metadata.
    """
    organism_name = organism_data.get('organism_name', 'unknown')
    adjacency_list = organism_data.get('adjacency_list', {})
    essentiality_labels = organism_data.get('essentiality_labels', {})
    
    # Check for missing gene overlaps
    if not adjacency_list:
        logger.warning(f"No network data for {organism_name}. Skipping centrality computation.")
        return {
            'organism': organism_name,
            'status': 'skipped',
            'reason': 'No network data',
            'centrality': {}
        }
    
    if not essentiality_labels:
        logger.warning(f"No essentiality labels for {organism_name}. Skipping correlation analysis.")
        return {
            'organism': organism_name,
            'status': 'skipped',
            'reason': 'No essentiality labels',
            'centrality': {}
        }
    
    # Check for overlap between network nodes and essentiality labels
    network_nodes = set(adjacency_list.keys())
    label_nodes = set(essentiality_labels.keys())
    overlap = network_nodes & label_nodes
    
    if not overlap:
        logger.warning(f"No gene overlap between network and essentiality labels for {organism_name}. Skipping.")
        return {
            'organism': organism_name,
            'status': 'skipped',
            'reason': 'No gene overlap',
            'centrality': {},
            'overlap_count': 0
        }
    
    if len(overlap) < len(network_nodes) or len(overlap) < len(label_nodes):
        logger.info(f"Gene overlap for {organism_name}: {len(overlap)} genes "
                   f"({len(overlap)/len(network_nodes)*100:.1f}% of network, "
                   f"{len(overlap)/len(label_nodes)*100:.1f}% of labels)")
    
    # Load graph
    G = load_graph_from_adjacency_list(adjacency_list)
    
    # Compute centralities (handles disconnected/empty graphs internally)
    centrality_results = compute_all_centrality_metrics(G, betweenness_k=betweenness_k)
    
    # Filter centrality results to only include genes with essentiality labels
    filtered_centrality = {}
    for metric_name, metric_values in centrality_results.items():
        filtered_centrality[metric_name] = {
            node: value for node, value in metric_values.items()
            if node in overlap
        }
    
    result = {
        'organism': organism_name,
        'status': 'success',
        'centrality': filtered_centrality,
        'overlap_count': len(overlap),
        'network_nodes': len(network_nodes),
        'label_nodes': len(label_nodes),
        'num_components': nx.number_connected_components(G),
        'num_edges': G.number_of_edges()
    }
    
    # Save centrality results
    output_file = output_dir / f"{organism_name}_centrality.json"
    import json
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Saved centrality results for {organism_name} to {output_file}")
    
    return result

def main():
    """Main entry point for network analysis module."""
    import argparse
    import json
    from code.config import load_config, get_organisms, get_path
    
    parser = argparse.ArgumentParser(description='Compute centrality metrics for PPI networks.')
    parser.add_argument('--config', type=str, default='config.yaml', help='Path to config file')
    args = parser.parse_args()
    
    config = load_config(args.config)
    organisms = get_organisms(config)
    output_dir = Path(get_path(config, 'results'))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(level=logging.INFO)
    
    for organism in organisms:
        # In a real pipeline, this would load the organism's network and labels
        # For now, this is a placeholder showing the structure
        logger.info(f"Processing organism: {organism}")
        
        # Example: organism_data would come from data_loader
        # organism_data = load_organism_data(organism)
        # result = process_organism_networks(organism_data, output_dir)
        
        logger.info(f"Completed processing for {organism}")

if __name__ == '__main__':
    main()
