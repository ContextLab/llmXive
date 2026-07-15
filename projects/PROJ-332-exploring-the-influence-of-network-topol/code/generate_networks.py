import networkx as nx
import numpy as np
from typing import Tuple, Dict, Any, Optional
import logging

from config import SimulationConfig, load_config, get_simulation_parameters

logger = logging.getLogger(__name__)

def validate_degree_bounds(target_degree: float, N: int) -> bool:
    """Validate that target degree is within valid bounds."""
    # Max degree is N-1, min is 0
    if target_degree < 0 or target_degree > N - 1:
        logger.error(f"Target degree {target_degree} out of bounds for N={N}")
        return False
    return True

def validate_connection_probability(p: float) -> bool:
    """Validate connection probability is in [0, 1]."""
    if p < 0 or p > 1:
        logger.error(f"Connection probability {p} out of bounds [0, 1]")
        return False
    return True

def generate_nanowire_network(N: int, p: float, seed: int, 
                              target_degree: Optional[float] = None) -> nx.Graph:
    """
    Generate a nanowire network graph.
    If target_degree is specified, adjust p to achieve it.
    """
    logger.info(f"Generating network: N={N}, p={p}, target_degree={target_degree}")
    
    # Validate inputs
    if not validate_connection_probability(p):
        raise ValueError("Invalid connection probability")
    
    if target_degree is not None and not validate_degree_bounds(target_degree, N):
        raise ValueError("Invalid target degree")
    
    # Set random seed
    np.random.seed(seed)
    
    # If target_degree is specified, adjust p
    if target_degree is not None:
        # Expected degree in Erdos-Renyi is (N-1)*p
        # So p = target_degree / (N-1)
        adjusted_p = target_degree / (N - 1) if N > 1 else 0
        adjusted_p = min(max(adjusted_p, 0), 1)  # Clamp to [0, 1]
        logger.info(f"Adjusted p from {p} to {adjusted_p} to achieve target degree {target_degree}")
        p = adjusted_p
    
    # Generate Erdos-Renyi graph
    G = nx.erdos_renyi_graph(N, p, seed=seed)
    
    # Ensure graph is not empty
    if G.number_of_nodes() == 0:
        G.add_node(0)
    
    logger.info(f"Generated graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    return G

def calculate_average_degree(graph: nx.Graph) -> float:
    """Calculate average degree of the graph."""
    if graph.number_of_nodes() == 0:
        return 0.0
    return sum(dict(graph.degree()).values()) / graph.number_of_nodes()

def calculate_average_shortest_path_length(graph: nx.Graph) -> float:
    """Calculate average shortest path length."""
    if not nx.is_connected(graph) or graph.number_of_nodes() <= 1:
        return float('inf')
    return nx.average_shortest_path_length(graph)

def calculate_clustering_coefficient(graph: nx.Graph) -> float:
    """Calculate average clustering coefficient."""
    if graph.number_of_nodes() == 0:
        return 0.0
    return nx.average_clustering(graph)

def generate_network_grid(N_values: list, p_values: list, seeds: list, 
                          target_degree: Optional[float] = None) -> list:
    """Generate a grid of networks with different parameters."""
    networks = []
    for N in N_values:
        for p in p_values:
            for seed in seeds:
                G = generate_nanowire_network(N, p, seed, target_degree)
                networks.append({
                    'graph': G,
                    'N': N,
                    'p': p,
                    'seed': seed
                })
    return networks
