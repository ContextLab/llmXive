import logging
from typing import Dict, Any, List, Tuple, Optional, Union
import networkx as nx
import numpy as np
from data_models import NetworkGraph

logger = logging.getLogger(__name__)

def check_disconnected_graph(graph: Union[nx.Graph, NetworkGraph]) -> bool:
    """
    Check if the provided graph is disconnected.

    Args:
        graph: A NetworkX graph or a NetworkGraph dataclass instance.

    Returns:
        True if the graph is disconnected (has more than one connected component),
        False otherwise.

    Raises:
        ValueError: If the graph is empty.
    """
    if isinstance(graph, NetworkGraph):
        nx_graph = graph.graph
    else:
        nx_graph = graph

    if nx_graph.number_of_nodes() == 0:
        logger.warning("Graph is empty; treating as disconnected.")
        return True

    try:
        num_components = nx.number_connected_components(nx_graph)
        is_disconnected = num_components > 1
        if is_disconnected:
            logger.warning(
                f"Graph has {num_components} connected components. "
                "Synchronization simulation will likely fail or return infinity."
            )
        return is_disconnected
    except nx.NetworkXError as e:
        logger.error(f"Error checking connected components: {e}")
        raise

def validate_graph(graph: Union[nx.Graph, NetworkGraph]) -> Dict[str, Any]:
    """
    Perform basic integrity validation on a graph.

    Checks:
    - Graph is not empty
    - No self-loops (optional, logged as warning)
    - No isolated nodes (optional, logged as warning)
    - Graph is undirected (required for Kuramoto in this project context)

    Args:
        graph: A NetworkX graph or NetworkGraph instance.

    Returns:
        A dictionary with validation results:
        {
            "is_valid": bool,
            "errors": List[str],
            "warnings": List[str],
            "node_count": int,
            "edge_count": int
        }
    """
    if isinstance(graph, NetworkGraph):
        nx_graph = graph.graph
    else:
        nx_graph = graph

    result = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "node_count": nx_graph.number_of_nodes(),
        "edge_count": nx_graph.number_of_edges()
    }

    # Check for empty graph
    if result["node_count"] == 0:
        result["errors"].append("Graph is empty.")
        result["is_valid"] = False
        return result

    # Check for self-loops
    self_loops = list(nx.selfloop_edges(nx_graph))
    if self_loops:
        msg = f"Graph contains {len(self_loops)} self-loop(s)."
        result["warnings"].append(msg)
        logger.warning(msg)

    # Check for isolated nodes
    isolated = list(nx.isolates(nx_graph))
    if isolated:
        msg = f"Graph contains {len(isolated)} isolated node(s)."
        result["warnings"].append(msg)
        logger.warning(msg)

    # Check if undirected (Kuramoto typically assumes undirected for symmetric coupling)
    if not isinstance(nx_graph, nx.Graph):
        msg = "Graph is directed. Kuramoto simulation may not behave as expected for directed graphs."
        result["warnings"].append(msg)
        logger.warning(msg)

    # Check connectivity (soft check, not a hard error for validity, but important for simulation)
    if not nx.is_connected(nx_graph):
        msg = "Graph is not connected. Synchronization threshold may be infinity."
        result["warnings"].append(msg)
        logger.warning(msg)
        # We do not set is_valid=False here because the simulation handles disconnected graphs by returning infinity.

    return result

def validate_network_list(
    graphs: List[Union[nx.Graph, NetworkGraph]]
) -> Dict[str, Any]:
    """
    Validate a list of graphs.

    Args:
        graphs: A list of NetworkX graphs or NetworkGraph instances.

    Returns:
        A dictionary with validation results:
        {
            "is_valid": bool,
            "total_count": int,
            "valid_count": int,
            "invalid_indices": List[int],
            "details": List[Dict[str, Any]]
        }
    """
    if not isinstance(graphs, list):
        raise TypeError("Input must be a list of graphs.")

    result = {
        "is_valid": True,
        "total_count": len(graphs),
        "valid_count": 0,
        "invalid_indices": [],
        "details": []
    }

    for idx, graph in enumerate(graphs):
        validation = validate_graph(graph)
        result["details"].append(validation)
        if validation["is_valid"]:
            result["valid_count"] += 1
        else:
            result["invalid_indices"].append(idx)
            result["is_valid"] = False

    return result

def validate_simulation_inputs(
    graph: Union[nx.Graph, NetworkGraph],
    coupling_range: Tuple[float, float] = (0.0, 5.0),
    tolerance: float = 0.001
) -> Dict[str, Any]:
    """
    Validate inputs specifically for the Kuramoto simulation.

    Checks:
    - Graph validity (via validate_graph)
    - Graph connectivity (warns if disconnected)
    - Coupling range validity
    - Tolerance validity

    Args:
        graph: The network graph.
        coupling_range: Tuple (min_k, max_k).
        tolerance: Convergence tolerance for bisection.

    Returns:
        A dictionary with validation results:
        {
            "is_valid": bool,
            "errors": List[str],
            "warnings": List[str],
            "ready_for_simulation": bool
        }
    """
    result = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "ready_for_simulation": True
    }

    # Validate graph
    graph_validation = validate_graph(graph)
    if not graph_validation["is_valid"]:
        result["errors"].extend(graph_validation["errors"])
        result["warnings"].extend(graph_validation["warnings"])
        result["is_valid"] = False
        result["ready_for_simulation"] = False
    else:
        result["warnings"].extend(graph_validation["warnings"])

    # Check coupling range
    min_k, max_k = coupling_range
    if min_k >= max_k:
        msg = f"Invalid coupling range: min ({min_k}) must be less than max ({max_k})."
        result["errors"].append(msg)
        result["is_valid"] = False
        result["ready_for_simulation"] = False
    elif min_k < 0:
        msg = f"Invalid coupling range: min ({min_k}) cannot be negative."
        result["errors"].append(msg)
        result["is_valid"] = False
        result["ready_for_simulation"] = False

    # Check tolerance
    if tolerance <= 0:
        msg = f"Invalid tolerance: {tolerance} must be positive."
        result["errors"].append(msg)
        result["is_valid"] = False
        result["ready_for_simulation"] = False

    # Specific check for disconnected graph (simulation will return infinity, but we warn)
    if check_disconnected_graph(graph):
        msg = "Graph is disconnected. Simulation will return infinity for threshold."
        result["warnings"].append(msg)
        # We do not block simulation here, as the simulation logic handles this case.

    return result
