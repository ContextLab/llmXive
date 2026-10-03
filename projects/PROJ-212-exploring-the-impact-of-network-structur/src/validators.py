"""
Validators for data integrity checks in network synchronization analysis.

This module provides functions to validate graph structures, detect disconnected
components, and ensure simulation inputs meet required criteria.
"""

import logging
from typing import Dict, Any, List, Tuple, Optional, Union
import networkx as nx
import numpy as np
from data_models import NetworkGraph

logger = logging.getLogger(__name__)


def check_disconnected_graph(graph: nx.Graph) -> Tuple[bool, int]:
    """
    Check if a graph is disconnected and count its connected components.
    
    Args:
        graph: A NetworkX graph to check.
        
    Returns:
        Tuple of (is_disconnected, num_components).
        is_disconnected is True if the graph has more than one connected component.
        num_components is the total number of connected components.
        
    Raises:
        ValueError: If the graph is None or empty.
    """
    if graph is None:
        raise ValueError("Graph cannot be None")
        
    if graph.number_of_nodes() == 0:
        raise ValueError("Graph cannot be empty")
        
    num_components = nx.number_connected_components(graph)
    is_disconnected = num_components > 1
    
    if is_disconnected:
        logger.warning(f"Graph has {num_components} connected components. "
                     f"Simulation may return infinity threshold.")
        
    return is_disconnected, num_components


def validate_graph(graph: Union[nx.Graph, NetworkGraph], 
                  min_nodes: int = 2, 
                  max_nodes: int = 10000,
                  allow_self_loops: bool = False,
                  allow_multiple_edges: bool = False) -> Tuple[bool, List[str]]:
    """
    Validate a graph meets structural requirements for simulation.
    
    Args:
        graph: NetworkX graph or NetworkGraph dataclass to validate.
        min_nodes: Minimum number of nodes required.
        max_nodes: Maximum number of nodes allowed.
        allow_self_loops: Whether self-loops are permitted.
        allow_multiple_edges: Whether multiple edges between nodes are permitted.
        
    Returns:
        Tuple of (is_valid, list_of_errors).
        is_valid is True if all checks pass.
        list_of_errors contains descriptive error messages for failed checks.
    """
    errors = []
    
    # Extract NetworkX graph from NetworkGraph if needed
    if isinstance(graph, NetworkGraph):
        nx_graph = graph.graph
    elif isinstance(graph, nx.Graph):
        nx_graph = graph
    else:
        errors.append(f"Invalid graph type: {type(graph)}")
        return False, errors
        
    if nx_graph is None:
        errors.append("Graph is None")
        return False, errors
        
    # Check node count
    num_nodes = nx_graph.number_of_nodes()
    if num_nodes < min_nodes:
        errors.append(f"Graph has {num_nodes} nodes, minimum required is {min_nodes}")
        
    if num_nodes > max_nodes:
        errors.append(f"Graph has {num_nodes} nodes, maximum allowed is {max_nodes}")
        
    # Check for self-loops if not allowed
    if not allow_self_loops:
        self_loops = list(nx.selfloop_edges(nx_graph))
        if self_loops:
            errors.append(f"Graph contains {len(self_loops)} self-loops")
            
    # Check for multiple edges if not allowed
    if not allow_multiple_edges:
        if isinstance(nx_graph, nx.MultiGraph):
            errors.append("Graph is a MultiGraph but multiple edges are not allowed")
        elif isinstance(nx_graph, nx.Graph):
            # Check if it's actually a simple graph
            if not nx.is_graphical(nx_graph.degree()):
                # This check is more for multigraphs, but we already checked type
                pass
                
    # Check for isolated nodes (degree 0)
    isolated_nodes = [n for n, d in nx_graph.degree() if d == 0]
    if isolated_nodes:
        errors.append(f"Graph contains {len(isolated_nodes)} isolated nodes")
        
    # Check for negative edge weights if present
    if hasattr(nx_graph, 'edges') and len(nx_graph.edges()) > 0:
        for u, v, data in nx_graph.edges(data=True):
            if 'weight' in data and data['weight'] < 0:
                errors.append(f"Edge ({u}, {v}) has negative weight: {data['weight']}")
                break
                
    is_valid = len(errors) == 0
    return is_valid, errors


def validate_network_list(networks: List[Union[nx.Graph, NetworkGraph, Dict[str, Any]]]) -> Tuple[bool, List[str]]:
    """
    Validate a list of networks for batch processing.
    
    Args:
        networks: List of graphs or network dictionaries to validate.
        
    Returns:
        Tuple of (is_valid, list_of_errors).
        is_valid is True if all networks pass validation.
        list_of_errors contains descriptive error messages for failed networks.
    """
    errors = []
    
    if not networks:
        errors.append("Network list is empty")
        return False, errors
        
    if len(networks) > 1000:
        logger.warning(f"Large network list detected: {len(networks)} networks")
        
    for idx, network in enumerate(networks):
        # Extract graph from dict if needed
        if isinstance(network, dict):
            if 'graph' not in network:
                errors.append(f"Network at index {idx} is a dict without 'graph' key")
                continue
            graph = network['graph']
        else:
            graph = network
            
        # Validate individual graph
        is_valid, graph_errors = validate_graph(graph)
        if not is_valid:
            network_id = network.get('id', f'index_{idx}') if isinstance(network, dict) else f'index_{idx}'
            for err in graph_errors:
                errors.append(f"Network '{network_id}': {err}")
                
    is_valid = len(errors) == 0
    if not is_valid:
        logger.warning(f"Validation failed for {len(errors)}/{len(networks)} networks")
        
    return is_valid, errors


def validate_simulation_inputs(graph: nx.Graph, 
                              natural_frequencies: Optional[np.ndarray] = None,
                              coupling_strength: Optional[float] = None,
                              time_span: Optional[Tuple[float, float]] = None,
                              num_oscillators: Optional[int] = None) -> Tuple[bool, List[str]]:
    """
    Validate inputs for Kuramoto simulation.
    
    Args:
        graph: NetworkX graph representing oscillator connections.
        natural_frequencies: Array of natural frequencies for each oscillator.
        coupling_strength: Global coupling strength K.
        time_span: Tuple of (start_time, end_time) for simulation.
        num_oscillators: Number of oscillators (should match graph nodes).
        
    Returns:
        Tuple of (is_valid, list_of_errors).
        is_valid is True if all inputs are valid.
        list_of_errors contains descriptive error messages for invalid inputs.
    """
    errors = []
    
    # Validate graph
    if graph is None:
        errors.append("Graph is None")
        return False, errors
        
    num_nodes = graph.number_of_nodes()
    if num_nodes == 0:
        errors.append("Graph has no nodes")
        return False, errors
        
    # Validate number of oscillators
    if num_oscillators is not None:
        if num_oscillators != num_nodes:
            errors.append(f"num_oscillators ({num_oscillators}) does not match graph nodes ({num_nodes})")
    else:
        num_oscillators = num_nodes
        
    # Validate natural frequencies
    if natural_frequencies is not None:
        if len(natural_frequencies) != num_oscillators:
            errors.append(f"Natural frequencies length ({len(natural_frequencies)}) "
                        f"does not match num_oscillators ({num_oscillators})")
        elif not isinstance(natural_frequencies, np.ndarray):
            errors.append("Natural frequencies must be a numpy array")
        elif np.any(np.isnan(natural_frequencies)) or np.any(np.isinf(natural_frequencies)):
            errors.append("Natural frequencies contain NaN or Inf values")
    else:
        # Default to zero frequencies if not provided
        natural_frequencies = np.zeros(num_oscillators)
        
    # Validate coupling strength
    if coupling_strength is not None:
        if not isinstance(coupling_strength, (int, float)):
            errors.append("Coupling strength must be a number")
        elif coupling_strength < 0:
            errors.append("Coupling strength cannot be negative")
            
    # Validate time span
    if time_span is not None:
        if not isinstance(time_span, (tuple, list)) or len(time_span) != 2:
            errors.append("Time span must be a tuple of (start, end)")
        elif time_span[0] >= time_span[1]:
            errors.append("Time span start must be less than end")
        elif time_span[0] < 0:
            errors.append("Time span start cannot be negative")
    else:
        # Default time span
        time_span = (0.0, 100.0)
        
    is_valid = len(errors) == 0
    if not is_valid:
        logger.error(f"Simulation input validation failed: {errors}")
        
    return is_valid, errors
