"""
Data integrity validators for network synchronization research.

This module provides functions to validate graph structures and simulation inputs,
ensuring data integrity before running expensive computations.
"""
import logging
from typing import Dict, Any, List, Tuple, Optional, Union
import networkx as nx
import numpy as np
from data_models import NetworkGraph

logger = logging.getLogger(__name__)


def check_disconnected_graph(G: nx.Graph) -> Tuple[bool, List[int]]:
    """
    Check if a graph is disconnected and identify connected components.
    
    Args:
        G: NetworkX graph to check
        
    Returns:
        Tuple of (is_disconnected, list of component sizes)
        
    Raises:
        ValueError: If G is not a valid NetworkX graph
    """
    if not isinstance(G, nx.Graph):
        raise ValueError(f"Expected NetworkX graph, got {type(G)}")
        
    if G.number_of_nodes() == 0:
        logger.warning("Empty graph detected")
        return True, []
        
    if G.number_of_nodes() == 1:
        # Single node is technically connected
        return False, [1]
        
    try:
        components = list(nx.connected_components(G))
        num_components = len(components)
        component_sizes = [len(c) for c in components]
        
        is_disconnected = num_components > 1
        
        if is_disconnected:
            logger.warning(
                f"Graph is disconnected with {num_components} components. "
                f"Sizes: {component_sizes}"
            )
            
        return is_disconnected, component_sizes
        
    except Exception as e:
        logger.error(f"Error checking connectivity: {e}")
        raise


def validate_graph(
    G: nx.Graph, 
    min_nodes: int = 2, 
    max_nodes: Optional[int] = None,
    allow_self_loops: bool = False,
    allow_multiple_edges: bool = False
) -> Dict[str, Any]:
    """
    Validate a graph for simulation readiness.
    
    Args:
        G: NetworkX graph to validate
        min_nodes: Minimum number of nodes required
        max_nodes: Maximum number of nodes allowed (None for no limit)
        allow_self_loops: Whether self-loops are permitted
        allow_multiple_edges: Whether multiple edges are permitted
        
    Returns:
        Dictionary with validation results:
            - valid: bool
            - errors: list of error messages
            - warnings: list of warning messages
            - stats: dict of graph statistics
            
    Raises:
        ValueError: If G is not a NetworkX graph
    """
    if not isinstance(G, nx.Graph):
        raise ValueError(f"Expected NetworkX graph, got {type(G)}")
        
    errors = []
    warnings = []
    stats = {}
    
    # Basic statistics
    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    stats['num_nodes'] = n_nodes
    stats['num_edges'] = n_edges
    
    # Check node count
    if n_nodes < min_nodes:
        errors.append(f"Graph has {n_nodes} nodes, minimum is {min_nodes}")
        
    if max_nodes is not None and n_nodes > max_nodes:
        errors.append(f"Graph has {n_nodes} nodes, maximum is {max_nodes}")
        
    # Check for self-loops
    if not allow_self_loops:
        self_loops = list(nx.self_loop_edges(G))
        if self_loops:
            errors.append(f"Graph contains {len(self_loops)} self-loops")
            
    # Check for multiple edges (for MultiGraph)
    if not allow_multiple_edges and isinstance(G, nx.MultiGraph):
        multiedges = [e for e in G.edges(keys=True) if G.number_of_edges(*e[:2]) > 1]
        if multiedges:
            errors.append(f"Graph contains {len(multiedges)} multiple edges")
            
    # Check for isolated nodes
    isolated = list(nx.isolates(G))
    if isolated:
        warnings.append(f"Graph has {len(isolated)} isolated nodes")
        stats['isolated_nodes'] = len(isolated)
        
    # Check connectivity
    is_disconnected, component_sizes = check_disconnected_graph(G)
    stats['is_disconnected'] = is_disconnected
    stats['component_sizes'] = component_sizes
    
    if is_disconnected:
        warnings.append(
            f"Graph is disconnected with {len(component_sizes)} components"
        )
        
    # Check degree distribution
    if n_nodes > 0:
        degrees = [d for n, d in G.degree()]
        stats['mean_degree'] = float(np.mean(degrees))
        stats['max_degree'] = int(np.max(degrees))
        stats['min_degree'] = int(np.min(degrees))
        
        if stats['min_degree'] == 0:
            warnings.append("Graph contains nodes with degree 0")
            
    # Check for valid edge weights if present
    if G.number_of_edges() > 0:
        if 'weight' in G.edges[0]:
            weights = [e[2]['weight'] for e in G.edges(data=True)]
            stats['mean_weight'] = float(np.mean(weights))
            stats['min_weight'] = float(np.min(weights))
            stats['max_weight'] = float(np.max(weights))
            
            if any(w <= 0 for w in weights):
                warnings.append("Graph contains non-positive edge weights")
                
    valid = len(errors) == 0
    
    result = {
        'valid': valid,
        'errors': errors,
        'warnings': warnings,
        'stats': stats
    }
    
    if valid:
        logger.info("Graph validation passed")
    else:
        logger.error(f"Graph validation failed: {errors}")
        
    return result


def validate_network_list(
    networks: List[Union[nx.Graph, NetworkGraph]],
    min_networks: int = 1,
    max_networks: Optional[int] = None
) -> Dict[str, Any]:
    """
    Validate a list of networks for batch processing.
    
    Args:
        networks: List of NetworkX graphs or NetworkGraph dataclasses
        min_networks: Minimum number of networks required
        max_networks: Maximum number of networks allowed
        
    Returns:
        Dictionary with validation results:
            - valid: bool
            - errors: list of error messages
            - warnings: list of warning messages
            - stats: dict of aggregate statistics
    """
    errors = []
    warnings = []
    stats = {}
    
    n_networks = len(networks)
    stats['num_networks'] = n_networks
    
    # Check count
    if n_networks < min_networks:
        errors.append(f"Only {n_networks} networks provided, minimum is {min_networks}")
        
    if max_networks is not None and n_networks > max_networks:
        errors.append(f"{n_networks} networks provided, maximum is {max_networks}")
        
    if n_networks == 0:
        return {
            'valid': False,
            'errors': errors,
            'warnings': warnings,
            'stats': stats
        }
        
    # Validate each network
    valid_counts = 0
    invalid_counts = 0
    total_nodes = 0
    total_edges = 0
    disconnected_counts = 0
    
    for i, net in enumerate(networks):
        # Convert NetworkGraph to nx.Graph if needed
        if isinstance(net, NetworkGraph):
            G = net.graph
            net_id = net.id or f"network_{i}"
        elif isinstance(net, nx.Graph):
            G = net
            net_id = f"network_{i}"
        else:
            errors.append(f"Network {i} is not a valid graph type: {type(net)}")
            invalid_counts += 1
            continue
            
        # Validate the graph
        validation_result = validate_graph(G)
        
        if validation_result['valid']:
            valid_counts += 1
        else:
            invalid_counts += 1
            
        # Aggregate stats
        total_nodes += validation_result['stats'].get('num_nodes', 0)
        total_edges += validation_result['stats'].get('num_edges', 0)
        
        if validation_result['stats'].get('is_disconnected', False):
            disconnected_counts += 1
            
        # Collect warnings
        for w in validation_result['warnings']:
            warnings.append(f"[{net_id}] {w}")
            
    stats['valid_networks'] = valid_counts
    stats['invalid_networks'] = invalid_counts
    stats['total_nodes'] = total_nodes
    stats['total_edges'] = total_edges
    stats['disconnected_networks'] = disconnected_counts
    
    if disconnected_counts > 0:
        warnings.append(
            f"{disconnected_counts} out of {n_networks} networks are disconnected"
        )
        
    valid = len(errors) == 0 and valid_counts > 0
    
    result = {
        'valid': valid,
        'errors': errors,
        'warnings': warnings,
        'stats': stats
    }
    
    if valid:
        logger.info(f"Network list validation passed: {valid_counts}/{n_networks} valid")
    else:
        logger.error(f"Network list validation failed: {errors}")
        
    return result


def validate_simulation_inputs(
    G: nx.Graph,
    K_values: List[float],
    t_max: float,
    dt: float,
    initial_conditions: Optional[np.ndarray] = None
) -> Dict[str, Any]:
    """
    Validate inputs for Kuramoto simulation.
    
    Args:
        G: NetworkX graph representing the network
        K_values: List of coupling strengths to sweep
        t_max: Maximum simulation time
        dt: Time step for integration
        initial_conditions: Optional initial phase angles
        
    Returns:
        Dictionary with validation results:
            - valid: bool
            - errors: list of error messages
            - warnings: list of warning messages
            - suggestions: list of recommendations
    """
    errors = []
    warnings = []
    suggestions = []
    
    # Validate graph
    graph_validation = validate_graph(G, min_nodes=2)
    if not graph_validation['valid']:
        errors.extend(graph_validation['errors'])
    warnings.extend(graph_validation['warnings'])
    
    # Check for disconnected graph
    is_disconnected, _ = check_disconnected_graph(G)
    if is_disconnected:
        warnings.append(
            "Graph is disconnected. Synchronization threshold will likely be infinite. "
            "Consider using only the largest connected component."
        )
        suggestions.append(
            "Use nx.connected_components() to extract the largest component before simulation"
        )
        
    # Validate K_values
    if not K_values:
        errors.append("K_values list is empty")
    else:
        if any(k < 0 for k in K_values):
            errors.append("K_values contains negative coupling strengths")
            
        if len(set(K_values)) != len(K_values):
            warnings.append("K_values contains duplicate values")
            
        if not all(isinstance(k, (int, float)) for k in K_values):
            errors.append("K_values must contain numeric values")
            
    # Validate t_max
    if t_max <= 0:
        errors.append(f"t_max must be positive, got {t_max}")
        
    # Validate dt
    if dt <= 0:
        errors.append(f"dt must be positive, got {dt}")
        
    if dt > t_max:
        errors.append(f"dt ({dt}) cannot exceed t_max ({t_max})")
        
    # Check time steps
    n_steps = int(t_max / dt)
    if n_steps < 100:
        warnings.append(f"Simulation will have only {n_steps} time steps. "
                      "Consider reducing dt for better resolution.")
                      
    # Validate initial conditions if provided
    if initial_conditions is not None:
        n_nodes = G.number_of_nodes()
        if len(initial_conditions) != n_nodes:
            errors.append(
                f"Initial conditions length ({len(initial_conditions)}) "
                f"does not match number of nodes ({n_nodes})"
            )
            
        if not isinstance(initial_conditions, np.ndarray):
            warnings.append("Initial conditions should be a numpy array")
            
        if not np.all(np.isfinite(initial_conditions)):
            errors.append("Initial conditions contain non-finite values")
            
    # Suggest reasonable defaults if K_values seem inappropriate
    if K_values:
        k_min, k_max = min(K_values), max(K_values)
        if k_max < 1.0:
            suggestions.append(
                "Maximum K value is low (< 1.0). "
                "For many networks, synchronization occurs at higher coupling. "
                "Consider increasing K_max."
            )
        if k_min > 2.0:
            suggestions.append(
                "Minimum K value is high (> 2.0). "
                "Consider starting from K=0 to capture the transition."
            )
            
    valid = len(errors) == 0
    
    result = {
        'valid': valid,
        'errors': errors,
        'warnings': warnings,
        'suggestions': suggestions,
        'simulation_info': {
            'n_nodes': G.number_of_nodes(),
            'n_edges': G.number_of_edges(),
            'n_k_values': len(K_values),
            't_max': t_max,
            'dt': dt,
            'n_steps': n_steps
        }
    }
    
    if valid:
        logger.info("Simulation inputs validation passed")
    else:
        logger.error(f"Simulation inputs validation failed: {errors}")
        
    return result
