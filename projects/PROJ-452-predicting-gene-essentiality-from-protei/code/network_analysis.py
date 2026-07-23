import logging
import time
import os
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import networkx as nx
import numpy as np
import pandas as pd

from config import load_config, get_organisms, get_path, ensure_dirs
from utils import setup_logging, compute_sha256

class NetworkAnalysisError(Exception):
    """Custom exception for network analysis errors."""
    pass

def load_graph_from_adjacency_list(adjacency_list: Dict[Any, List[Any]]) -> nx.Graph:
    """
    Load a NetworkX graph from an adjacency list dictionary.

    Args:
        adjacency_list: Dictionary mapping nodes to lists of neighbors.

    Returns:
        A NetworkX Graph object.
    """
    G = nx.Graph()
    for node, neighbors in adjacency_list.items():
        G.add_node(node)
        for neighbor in neighbors:
            G.add_edge(node, neighbor)
    return G

def compute_degree_centrality(G: nx.Graph) -> Dict[Any, float]:
    """
    Compute degree centrality for all nodes in the graph.

    Args:
        G: A NetworkX Graph.

    Returns:
        Dictionary mapping nodes to their degree centrality values.
    """
    if G.number_of_nodes() == 0:
        return {}
    return nx.degree_centrality(G)

def compute_eigenvector_centrality(G: nx.Graph, max_iter: int = 1000) -> Dict[Any, float]:
    """
    Compute eigenvector centrality for all nodes in the graph.

    Args:
        G: A NetworkX Graph.
        max_iter: Maximum number of iterations for the power method.

    Returns:
        Dictionary mapping nodes to their eigenvector centrality values.
        Returns empty dict if computation fails (e.g., disconnected components).
    """
    if G.number_of_nodes() == 0:
        return {}
    try:
        return nx.eigenvector_centrality(G, max_iter=max_iter)
    except nx.PowerIterationFailedConvergence:
        logging.warning("Eigenvector centrality computation failed to converge. Returning empty dict.")
        return {}

def compute_betweenness_centrality(G: nx.Graph, k: Optional[int] = None) -> Dict[Any, float]:
    """
    Compute betweenness centrality. Uses sampling (k) for large graphs to ensure performance.

    Args:
        G: A NetworkX Graph.
        k: Number of nodes to sample for betweenness calculation. If None, exact calculation is used.
           For graphs > 5000 nodes, k is recommended to be set (e.g., 100) to keep runtime < 30min.

    Returns:
        Dictionary mapping nodes to their betweenness centrality values.
    """
    if G.number_of_nodes() == 0:
        return {}
    if k is not None:
        return nx.betweenness_centrality(G, k=k, normalized=True)
    else:
        return nx.betweenness_centrality(G, normalized=True)

def compute_all_centrality_metrics(G: nx.Graph, k: Optional[int] = None) -> Dict[str, Dict[Any, float]]:
    """
    Compute all centrality metrics (degree, eigenvector, betweenness) for a graph.

    Args:
        G: A NetworkX Graph.
        k: Sampling parameter for betweenness centrality.

    Returns:
        Dictionary containing keys 'degree', 'eigenvector', 'betweenness',
        each mapping to a dict of node -> centrality value.
    """
    results = {
        'degree': compute_degree_centrality(G),
        'eigenvector': compute_eigenvector_centrality(G),
        'betweenness': compute_betweenness_centrality(G, k=k)
    }
    return results

def maslov_sneppen_rewire(G: nx.Graph, n_swaps: int, seed: Optional[int] = None) -> nx.Graph:
    """
    Perform Maslov-Sneppen rewiring on a graph to preserve degree distribution.

    Args:
        G: The input NetworkX Graph.
        n_swaps: Number of edge swaps to perform.
        seed: Random seed for reproducibility.

    Returns:
        A new NetworkX Graph with the same degree distribution but randomized connectivity.
    """
    if seed is not None:
        np.random.seed(seed)
    
    if G.number_of_edges() < 2:
        raise NetworkAnalysisError("Graph has too few edges to rewire.")

    # Create a copy to avoid modifying the original
    G_rewired = G.copy()
    
    # Perform swaps
    for _ in range(n_swaps):
        # Select two random edges (a, b) and (c, d)
        edges = list(G_rewired.edges())
        if len(edges) < 2:
            break
        
        e1 = edges[np.random.randint(len(edges))]
        e2 = edges[np.random.randint(len(edges))]
        
        a, b = e1
        c, d = e2
        
        # Ensure nodes are distinct
        if len({a, b, c, d}) < 4:
            continue
        
        # Check if new edges exist to avoid multi-edges
        if G_rewired.has_edge(a, c) or G_rewired.has_edge(b, d):
            continue
        
        # Perform the swap: remove (a,b), (c,d); add (a,c), (b,d)
        G_rewired.remove_edge(a, b)
        G_rewired.remove_edge(c, d)
        G_rewired.add_edge(a, c)
        G_rewired.add_edge(b, d)
    
    return G_rewired

def generate_rewired_graphs(G: nx.Graph, n_graphs: int, n_swaps_per_graph: int, output_dir: Path, seed: Optional[int] = None) -> List[nx.Graph]:
    """
    Generate a set of degree-preserving random graphs using the Maslov-Sneppen algorithm.

    Args:
        G: The input NetworkX Graph.
        n_graphs: Number of rewired graphs to generate.
        n_swaps_per_graph: Number of swaps per rewired graph.
        output_dir: Directory to save the rewired graphs (as adjacency lists/CSV).
        seed: Random seed for reproducibility.

    Returns:
        List of generated NetworkX Graph objects.
    """
    ensure_dirs(output_dir)
    rewired_graphs = []
    
    base_seed = seed if seed is not None else int(time.time())
    
    for i in range(n_graphs):
        current_seed = base_seed + i
        try:
            G_new = maslov_sneppen_rewire(G, n_swaps_per_graph, seed=current_seed)
            rewired_graphs.append(G_new)
            
            # Save the graph
            file_path = output_dir / f"rewired_graph_{i}.csv"
            # Save as edge list for simplicity and compatibility
            nx.write_edgelist(G_new, str(file_path), data=False)
            
        except NetworkAnalysisError as e:
            logging.warning(f"Skipping rewired graph {i} due to error: {e}")
            continue
    
    return rewired_graphs

def compute_centrality_for_rewired_graphs(rewired_graphs: List[nx.Graph], output_dir: Path) -> pd.DataFrame:
    """
    Compute degree centrality for each rewired graph and save results.
    
    This function implements T019b: centrality computation on rewired graphs.
    It calculates degree centrality for each graph in the list and saves
    the results to a CSV file.

    Args:
        rewired_graphs: List of rewired NetworkX Graph objects.
        output_dir: Directory to save the results.

    Returns:
        DataFrame containing centrality results for all rewired graphs.
    """
    if not rewired_graphs:
        logging.warning("No rewired graphs provided for centrality computation.")
        return pd.DataFrame()

    ensure_dirs(output_dir)
    results = []

    for i, G in enumerate(rewired_graphs):
        if G.number_of_nodes() == 0:
            logging.warning(f"Rewired graph {i} is empty, skipping centrality computation.")
            continue

        # Compute degree centrality as per T019b requirement
        centrality = compute_degree_centrality(G)
        
        # Store results: graph_id, node, centrality_value
        for node, value in centrality.items():
            results.append({
                'graph_id': i,
                'node': node,
                'degree_centrality': value
            })

    df = pd.DataFrame(results)
    output_file = output_dir / "rewired_degree_centrality.csv"
    df.to_csv(output_file, index=False)
    logging.info(f"Saved rewired degree centrality results to {output_file}")
    
    return df

def process_organism_networks(organism_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process networks for a specific organism: load, compute centralities, and handle null models.
    
    This is a placeholder for the main orchestration logic for a single organism.
    It integrates with the pipeline defined in main.py.

    Args:
        organism_id: The ID of the organism to process.
        config: Configuration dictionary.

    Returns:
        Dictionary containing analysis results for the organism.
    """
    logging.info(f"Processing organism: {organism_id}")
    
    # This function would typically:
    # 1. Load the network from data_loader
    # 2. Compute centralities (T015)
    # 3. Generate rewired graphs (T019a)
    # 4. Compute centralities on rewired graphs (T019b - implemented above)
    # 5. Calculate correlations (T019c - in statistics.py)
    
    # For now, return a minimal structure
    return {
        'organism_id': organism_id,
        'status': 'processed',
        'network_loaded': True,
        'rewired_graphs_generated': True
    }

def main():
    """
    Main entry point for network analysis tasks.
    This script can be run to generate rewired graphs and compute their centralities.
    """
    logging.info("Starting network analysis main script.")
    
    config = load_config()
    organisms = get_organisms(config)
    
    # Example: Process the first organism for demonstration
    if not organisms:
        logging.error("No organisms found in configuration.")
        return
    
    target_organism = organisms[0]
    logging.info(f"Target organism: {target_organism}")
    
    # Load network (simulated here, actual loading from data_loader)
    # In a real scenario, this would call fetch_string_network or load_local_network
    G = nx.erdos_renyi_graph(100, 0.05) # Placeholder for real network
    
    # Generate rewired graphs (T019a)
    n_rewired = 10
    n_swaps = 1000
    output_dir = get_path(config, 'results', 'null_distribution', 'rewired_graphs')
    ensure_dirs(output_dir)
    
    rewired_graphs = generate_rewired_graphs(G, n_rewired, n_swaps, output_dir)
    logging.info(f"Generated {len(rewired_graphs)} rewired graphs.")
    
    # Compute centralities on rewired graphs (T019b)
    centrality_dir = get_path(config, 'results', 'null_distribution')
    centrality_df = compute_centrality_for_rewired_graphs(rewired_graphs, centrality_dir)
    
    logging.info(f"Computed centralities for {len(rewired_graphs)} rewired graphs.")
    logging.info("Network analysis main script completed.")

if __name__ == "__main__":
    setup_logging()
    main()