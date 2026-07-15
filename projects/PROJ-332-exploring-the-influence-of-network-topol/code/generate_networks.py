import networkx as nx
import numpy as np
from typing import Tuple, Dict, Any, Optional
import logging
from config import SimulationConfig, load_config, get_simulation_parameters

logger = logging.getLogger(__name__)

def validate_degree_bounds(target_degree: float, N: int) -> bool:
    """Validate that target degree is within valid bounds."""
    if target_degree < 0:
        raise ValueError("Target degree must be non-negative")
    if target_degree > N - 1:
        raise ValueError(f"Target degree cannot exceed N-1 ({N-1})")
    return True

def validate_connection_probability(p: float) -> bool:
    """Validate connection probability is in (0, 1)."""
    if not (0 < p < 1):
        raise ValueError("Connection probability must be strictly between 0 and 1")
    return True

def generate_nanowire_network(N: int, p: float, seed: int, target_degree: Optional[float] = None) -> nx.Graph:
    """
    Generate a nanowire network graph.
    
    Args:
        N: Number of nodes
        p: Connection probability (for Erdos-Renyi)
        seed: Random seed
        target_degree: Optional target average degree (overrides p if provided)
        
    Returns:
        NetworkX graph representing the nanowire network
    """
    np.random.seed(seed)
    
    if target_degree is not None:
        # Validate target degree
        validate_degree_bounds(target_degree, N)
        
        # Calculate p from target degree: p = target_degree / (N-1)
        if N > 1:
            p = target_degree / (N - 1)
        else:
            p = 0
        
        logger.info(f"Using target_degree={target_degree}, derived p={p:.4f}")
    
    validate_connection_probability(p)
    
    # Generate Erdos-Renyi graph
    G = nx.erdos_renyi_graph(N, p, seed=seed)
    
    # Ensure at least some connectivity if target_degree is specified
    if target_degree is not None and len(G.edges()) == 0 and N > 1:
        # Add minimal edges to ensure connectivity
        edges = [(i, (i+1) % N) for i in range(N)]
        G.add_edges_from(edges)
        logger.warning("Added minimal edges to ensure connectivity")
    
    return G

def calculate_average_degree(G: nx.Graph) -> float:
    """Calculate the average degree of the graph."""
    if len(G) == 0:
        return 0.0
    degrees = [d for n, d in G.degree()]
    return float(np.mean(degrees))

def calculate_average_shortest_path_length(G: nx.Graph) -> float:
    """Calculate the average shortest path length."""
    if len(G) == 0 or not nx.is_connected(G):
        return float('inf')
    try:
        return nx.average_shortest_path_length(G)
    except nx.NetworkXError:
        return float('inf')

def calculate_clustering_coefficient(G: nx.Graph) -> float:
    """Calculate the average clustering coefficient."""
    if len(G) == 0:
        return 0.0
    return nx.average_clustering(G)

def generate_network_grid(N_values: list, p_values: list, seeds: list) -> list:
    """
    Generate a list of (N, p, seed) tuples for grid search.
    
    Args:
        N_values: List of node counts
        p_values: List of connection probabilities
        seeds: List of random seeds
        
    Returns:
        List of parameter tuples
    """
    grid = []
    for N in N_values:
        for p in p_values:
            for seed in seeds:
                grid.append({'N': N, 'p': p, 'seed': seed})
    return grid
