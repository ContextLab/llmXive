import networkx as nx
import numpy as np
from typing import Tuple, Dict, Any, Optional
import logging
from config import SimulationConfig, load_config, get_simulation_parameters

logger = logging.getLogger(__name__)

def validate_degree_bounds(target_degree: float, N: int) -> Tuple[bool, str]:
    """Validate that target degree is within valid bounds."""
    if N <= 1:
        return False, "N must be greater than 1"
    max_degree = N - 1
    if target_degree < 0 or target_degree > max_degree:
        return False, f"Target degree {target_degree} out of bounds [0, {max_degree}]"
    return True, "OK"

def validate_connection_probability(p: float) -> Tuple[bool, str]:
    """Validate connection probability."""
    if p < 0 or p > 1:
        return False, f"Probability {p} out of bounds [0, 1]"
    return True, "OK"

def generate_nanowire_network(N: int, p: float, seed: Optional[int] = None) -> nx.Graph:
    """
    Generate a random nanowire network graph using Erdos-Renyi model.
    """
    if seed is not None:
        np.random.seed(seed)

    valid, msg = validate_connection_probability(p)
    if not valid:
        raise ValueError(msg)

    # Generate Erdos-Renyi graph
    G = nx.erdos_renyi_graph(N, p, seed=seed)

    # Ensure graph is not empty
    if G.number_of_nodes() == 0:
        G.add_node(0)

    return G

def calculate_average_degree(graph: nx.Graph) -> float:
    """Calculate average degree of the graph."""
    if graph.number_of_nodes() == 0:
        return 0.0
    degrees = [d for n, d in graph.degree()]
    return float(np.mean(degrees))

def calculate_average_shortest_path_length(graph: nx.Graph) -> Optional[float]:
    """Calculate average shortest path length."""
    try:
        return nx.average_shortest_path_length(graph)
    except:
        return None

def calculate_clustering_coefficient(graph: nx.Graph) -> float:
    """Calculate average clustering coefficient."""
    return nx.average_clustering(graph)

def generate_network_grid(config: SimulationConfig) -> list:
    """Generate a grid of networks with varying parameters."""
    networks = []
    seeds = range(config.seed, config.seed + 10)
    for seed in seeds:
        G = generate_nanowire_network(config.N, config.p, seed=seed)
        networks.append({
            "graph": G,
            "seed": seed,
            "avg_degree": calculate_average_degree(G)
        })
    return networks
