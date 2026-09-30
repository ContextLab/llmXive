import logging
from typing import Dict, Any, List, Tuple, Optional, Union
import networkx as nx
import numpy as np
from data_models import NetworkGraph

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_disconnected_graph(graph: nx.Graph) -> bool:
    """
    Checks if a graph is disconnected.
    """
    if graph.number_of_nodes() == 0:
        return True
    return not nx.is_connected(graph)

def validate_graph(graph: nx.Graph) -> Tuple[bool, str]:
    """
    Validates a graph for basic properties.
    Returns (is_valid, error_message)
    """
    if graph.number_of_nodes() == 0:
        return False, "Graph has no nodes."
    
    if graph.number_of_edges() == 0:
        return False, "Graph has no edges."
    
    # Check for self-loops if required (optional)
    # if any(u == v for u, v in graph.edges()):
    #     return False, "Graph contains self-loops."
    
    return True, "Graph is valid."

def validate_network_list(network_list: List[tuple]) -> Tuple[bool, str]:
    """
    Validates a list of networks.
    """
    if not network_list:
        return False, "Network list is empty."
    
    for graph_id, graph_data in network_list:
        if 'graph' not in graph_data:
            return False, f"Graph data for {graph_id} is missing 'graph' key."
        is_valid, msg = validate_graph(graph_data['graph'])
        if not is_valid:
            return False, f"Invalid graph for {graph_id}: {msg}"
    
    return True, "All networks are valid."

def validate_simulation_inputs(graph: nx.Graph, config: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validates inputs for simulation.
    """
    if graph.number_of_nodes() == 0:
        return False, "Cannot simulate on an empty graph."
    
    if graph.number_of_nodes() > 10000:
        logger.warning("Large graph detected. Simulation may take a long time.")
    
    return True, "Simulation inputs are valid."