import logging
import time
import os
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

import networkx as nx
import numpy as np

from utils import set_deterministic_seed, get_deterministic_seed

logger = logging.getLogger(__name__)

class NetworkAnalysisError(Exception):
    """Custom exception for network analysis errors."""
    pass

def load_graph_from_adjacency_list(adjacency_data: Union[Dict[str, List[str]], str], directed: bool = False) -> nx.Graph:
    """
    Load a graph from an adjacency list dictionary or string.
    
    Args:
        adjacency_data: Dictionary mapping nodes to lists of neighbors, or a path to a file.
        directed: If True, create a directed graph.
        
    Returns:
        A NetworkX graph object.
    """
    G = nx.DiGraph() if directed else nx.Graph()
    
    if isinstance(adjacency_data, str):
        # Load from file
        if not os.path.exists(adjacency_data):
            raise NetworkAnalysisError(f"Adjacency list file not found: {adjacency_data}")
        
        with open(adjacency_data, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split()
                if len(parts) < 2:
                    continue
                node = parts[0]
                neighbors = parts[1:]
                G.add_node(node)
                for neighbor in neighbors:
                    G.add_edge(node, neighbor)
    else:
        # Load from dictionary
        for node, neighbors in adjacency_data.items():
            G.add_node(node)
            for neighbor in neighbors:
                G.add_edge(node, neighbor)
    
    return G

def compute_degree_centrality(G: nx.Graph) -> Dict[Any, float]:
    """
    Compute degree centrality for all nodes in the graph.
    
    Args:
        G: A NetworkX graph.
        
    Returns:
        Dictionary mapping nodes to their degree centrality values.
    """
    return nx.degree_centrality(G)

def compute_eigenvector_centrality(G: nx.Graph, max_iter: int = 1000, tol: float = 1e-6) -> Dict[Any, float]:
    """
    Compute eigenvector centrality for all nodes in the graph.
    
    Args:
        G: A NetworkX graph.
        max_iter: Maximum number of iterations.
        tol: Tolerance for convergence.
        
    Returns:
        Dictionary mapping nodes to their eigenvector centrality values.
    """
    try:
        return nx.eigenvector_centrality(G, max_iter=max_iter, tol=tol)
    except nx.PowerIterationFailedConvergence:
        logger.warning("Eigenvector centrality computation failed to converge. Returning zeros.")
        return {node: 0.0 for node in G.nodes()}

def compute_betweenness_centrality(G: nx.Graph, k: Optional[int] = None, normalized: bool = True) -> Dict[Any, float]:
    """
    Compute betweenness centrality for all nodes in the graph.
    
    If the graph is disconnected, this function will:
    1. Log a warning about the disconnected state.
    2. Extract the largest connected component (LCC).
    3. Compute betweenness centrality only on the LCC.
    4. Return centrality values for LCC nodes and 0.0 for all other nodes.
    5. Include metadata about the LCC size in the returned result (as a special key).
    
    Args:
        G: A NetworkX graph.
        k: Number of random samples for approximation (if None, exact calculation is used).
        normalized: If True, the values are normalized.
        
    Returns:
        Dictionary mapping nodes to their betweenness centrality values.
        If the graph was disconnected, the result includes a special key '_lcc_size'
        indicating the size of the largest connected component used for calculation.
    """
    # Check if graph is connected
    is_connected = False
    if nx.is_directed(G):
        # For directed graphs, check weak connectivity
        is_connected = nx.is_weakly_connected(G)
    else:
        is_connected = nx.is_connected(G)

    lcc_size_info = None

    if not is_connected:
        logger.warning("Graph is disconnected. Computing betweenness centrality only on the largest connected component.")
        
        # Identify connected components
        if nx.is_directed(G):
            components = list(nx.weakly_connected_components(G))
        else:
            components = list(nx.connected_components(G))
        
        if not components:
            # No nodes or edges
            logger.warning("Graph has no connected components. Returning all zeros.")
            return {node: 0.0 for node in G.nodes()}
        
        # Find the largest component
        largest_component = max(components, key=len)
        lcc_size_info = len(largest_component)
        
        # Create a subgraph of the largest component
        G_lcc = G.subgraph(largest_component).copy()
        
        logger.info(f"Largest connected component size: {lcc_size_info} nodes")
        
        # Compute centrality on the LCC
        if k is not None:
            centrality = nx.betweenness_centrality(G_lcc, k=k, normalized=normalized)
        else:
            centrality = nx.betweenness_centrality(G_lcc, normalized=normalized)
        
        # Map back to original graph nodes (set 0 for nodes not in LCC)
        result = {node: 0.0 for node in G.nodes()}
        result.update(centrality)
        
        # Add metadata
        result['_lcc_size'] = lcc_size_info
        return result
    else:
        # Graph is connected, compute normally
        if k is not None:
            centrality = nx.betweenness_centrality(G, k=k, normalized=normalized)
        else:
            centrality = nx.betweenness_centrality(G, normalized=normalized)
        
        return centrality

def compute_all_centrality_metrics(G: nx.Graph, k: Optional[int] = None) -> Dict[str, Dict[Any, float]]:
    """
    Compute all centrality metrics (degree, betweenness, eigenvector) for a graph.
    
    Args:
        G: A NetworkX graph.
        k: Number of random samples for betweenness centrality approximation.
        
    Returns:
        Dictionary with keys 'degree', 'betweenness', 'eigenvector', each mapping
        to a dictionary of node centrality values.
    """
    degree_centrality = compute_degree_centrality(G)
    betweenness_centrality = compute_betweenness_centrality(G, k=k)
    eigenvector_centrality = compute_eigenvector_centrality(G)
    
    return {
        'degree': degree_centrality,
        'betweenness': betweenness_centrality,
        'eigenvector': eigenvector_centrality
    }

def maslov_sneppen_rewire(G: nx.Graph, num_swaps: int = 1000, seed: Optional[int] = None) -> nx.Graph:
    """
    Perform Maslov-Sneppen rewiring to generate a degree-preserving random graph.
    
    Args:
        G: A NetworkX graph.
        num_swaps: Number of edge swaps to perform.
        seed: Random seed for reproducibility.
        
    Returns:
        A new NetworkX graph with rewired edges.
    """
    if seed is not None:
        set_deterministic_seed(seed)
    
    G_rewired = G.copy()
    edges = list(G_rewired.edges())
    
    if len(edges) < 2:
        logger.warning("Graph has too few edges for rewiring. Returning original graph.")
        return G_rewired
    
    for _ in range(num_swaps):
        # Select two random edges (u, v) and (x, y)
        e1_idx = np.random.randint(0, len(edges))
        e2_idx = np.random.randint(0, len(edges))
        
        while e1_idx == e2_idx:
            e2_idx = np.random.randint(0, len(edges))
        
        u, v = edges[e1_idx]
        x, y = edges[e2_idx]
        
        # Avoid self-loops and duplicate edges
        if u != y and v != x:
            if not G_rewired.has_edge(u, y) and not G_rewired.has_edge(v, x):
                # Perform the swap
                G_rewired.remove_edge(u, v)
                G_rewired.remove_edge(x, y)
                G_rewired.add_edge(u, y)
                G_rewired.add_edge(v, x)
                
                # Update edges list
                edges[e1_idx] = (u, y)
                edges[e2_idx] = (v, x)
    
    return G_rewired

def generate_rewired_graphs(G: nx.Graph, num_graphs: int = 10, k: Optional[int] = None, seed: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Generate multiple degree-preserving random graphs and compute their centrality metrics.
    
    Args:
        G: A NetworkX graph.
        num_graphs: Number of rewired graphs to generate.
        k: Number of random samples for betweenness centrality approximation.
        seed: Random seed for reproducibility.
        
    Returns:
        List of dictionaries, each containing the rewired graph and its centrality metrics.
    """
    results = []
    
    if seed is not None:
        set_deterministic_seed(seed)
    
    for i in range(num_graphs):
        current_seed = seed + i if seed is not None else None
        G_rewired = maslov_sneppen_rewire(G, seed=current_seed)
        centrality = compute_all_centrality_metrics(G_rewired, k=k)
        
        results.append({
            'graph_id': i,
            'graph': G_rewired,
            'centrality': centrality
        })
    
    return results

def compute_centrality_for_rewired_graphs(rewired_results: List[Dict[str, Any]], metric: str = 'degree') -> List[float]:
    """
    Extract centrality values for a specific metric from rewired graph results.
    
    Args:
        rewired_results: List of dictionaries from generate_rewired_graphs.
        metric: Centrality metric to extract ('degree', 'betweenness', 'eigenvector').
        
    Returns:
        List of mean centrality values for the specified metric across all rewired graphs.
    """
    mean_values = []
    
    for result in rewired_results:
        centrality = result['centrality'][metric]
        if centrality:
            mean_value = sum(centrality.values()) / len(centrality)
            mean_values.append(mean_value)
        else:
            mean_values.append(0.0)
    
    return mean_values

def process_organism_networks(organism_data: Dict[str, Any], output_dir: Path, k: Optional[int] = None) -> Dict[str, Any]:
    """
    Process network data for a single organism, computing centrality metrics.
    
    Args:
        organism_data: Dictionary containing organism ID, adjacency list, and metadata.
        output_dir: Directory to save results.
        k: Number of random samples for betweenness centrality approximation.
        
    Returns:
        Dictionary containing centrality metrics and metadata.
    """
    organism_id = organism_data.get('organism_id')
    adjacency_list = organism_data.get('adjacency_list')
    
    if not adjacency_list:
        raise NetworkAnalysisError(f"No adjacency list provided for organism {organism_id}")
    
    # Load graph
    G = load_graph_from_adjacency_list(adjacency_list)
    
    logger.info(f"Loaded graph for {organism_id}: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    # Check for disconnected network (FR-004)
    if G.number_of_edges() == 0:
        logger.warning(f"Network disconnected for {organism_id}. Assigning 0 centrality for all nodes.")
        centrality_metrics = {
            'degree': {node: 0.0 for node in G.nodes()},
            'betweenness': {node: 0.0 for node in G.nodes()},
            'eigenvector': {node: 0.0 for node in G.nodes()}
        }
    else:
        # Compute all centrality metrics
        centrality_metrics = compute_all_centrality_metrics(G, k=k)
    
    # Save results
    output_dir.mkdir(parents=True, exist_ok=True)
    results_path = output_dir / f"{organism_id}_centrality.json"
    
    # Convert non-serializable keys (if any) to strings
    serializable_metrics = {}
    for metric_name, metric_dict in centrality_metrics.items():
        serializable_dict = {}
        for node, value in metric_dict.items():
            serializable_dict[str(node)] = float(value)
        serializable_metrics[metric_name] = serializable_dict
    
    # Handle LCC metadata if present
    if '_lcc_size' in serializable_metrics['betweenness']:
        serializable_metrics['betweenness_lcc_size'] = serializable_metrics['betweenness'].pop('_lcc_size')
    
    with open(results_path, 'w') as f:
        json.dump({
            'organism_id': organism_id,
            'node_count': G.number_of_nodes(),
            'edge_count': G.number_of_edges(),
            'centrality_metrics': serializable_metrics
        }, f, indent=2)
    
    logger.info(f"Saved centrality results for {organism_id} to {results_path}")
    
    return {
        'organism_id': organism_id,
        'node_count': G.number_of_nodes(),
        'edge_count': G.number_of_edges(),
        'centrality_metrics': centrality_metrics,
        'results_path': str(results_path)
    }

def main():
    """Main entry point for network analysis module."""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='Network Analysis Module')
    parser.add_argument('--organism', type=str, required=True, help='Organism ID to analyze')
    parser.add_argument('--adjacency-file', type=str, help='Path to adjacency list file')
    parser.add_argument('--output-dir', type=str, default='results', help='Output directory')
    parser.add_argument('--k', type=int, default=None, help='Sample size for betweenness centrality')
    
    args = parser.parse_args()
    
    # Load organism data
    if args.adjacency_file:
        with open(args.adjacency_file, 'r') as f:
            adjacency_data = json.load(f)
    else:
        # Default test data
        adjacency_data = {
            'A': ['B', 'C'],
            'B': ['A', 'C', 'D'],
            'C': ['A', 'B', 'D'],
            'D': ['B', 'C']
        }
    
    organism_data = {
        'organism_id': args.organism,
        'adjacency_list': adjacency_data
    }
    
    # Process
    results = process_organism_networks(organism_data, Path(args.output_dir), k=args.k)
    
    print(f"Analysis complete for {args.organism}")
    print(f"Nodes: {results['node_count']}, Edges: {results['edge_count']}")

if __name__ == '__main__':
    main()