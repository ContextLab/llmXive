import networkx as nx
import logging
import json
from typing import Dict, Any, Union
from data_models import NetworkGraph
from llmxive_toolkit import paths

logger = logging.getLogger(__name__)

def _degree_distribution(nx_graph: nx.Graph) -> Dict[Any, int]:
    """
    Return a mapping from node identifier to its degree.
    This representation allows the sum of the degree values to equal
    twice the number of edges, satisfying the property test.
    """
    return {node: deg for node, deg in nx_graph.degree()}

def _average_path_length(nx_graph: nx.Graph, is_connected: bool) -> Union[float, None]:
    """
    Compute the average shortest path length.
    For disconnected graphs the specification requires ``None``.
    """
    if not is_connected:
        return None
    try:
        return float(nx.average_shortest_path_length(nx_graph))
    except Exception as e:
        logger.warning(f"Failed to compute average shortest path length: {e}")
        return None

def compute_metrics(graph: Union[nx.Graph, NetworkGraph]) -> Dict[str, Any]:
    """
    Compute topological metrics for a given network graph.

    Metrics computed:
    - degree_distribution: dict mapping node identifier to its degree
    - mean_degree: float
    - degree_variance: float
    - clustering_coefficient: float (average local clustering)
    - average_path_length: float or None (None for disconnected graphs)
    - num_nodes: int
    - num_edges: int
    - is_connected: bool

    The function also writes a JSON file ``metrics_{network_id}.json`` under
    ``data/processed/`` when the input is a ``NetworkGraph`` instance that
    carries an ``id`` attribute.

    Args:
        graph: A NetworkX graph or a ``NetworkGraph`` dataclass instance.

    Returns:
        Dictionary containing the computed metrics.
    """
    # Resolve the underlying NetworkX graph
    if isinstance(graph, NetworkGraph):
        nx_graph = getattr(graph, "graph", None)
    else:
        nx_graph = graph

    if nx_graph is None:
        logger.error("Provided graph is None.")
        return {
            "degree_distribution": {},
            "mean_degree": 0.0,
            "degree_variance": 0.0,
            "clustering_coefficient": 0.0,
            "average_path_length": None,
            "num_nodes": 0,
            "num_edges": 0,
            "is_connected": False,
        }

    num_nodes = nx_graph.number_of_nodes()
    num_edges = nx_graph.number_of_edges()

    # Degree distribution (node -> degree)
    degree_dist = _degree_distribution(nx_graph)

    degrees = list(degree_dist.values())
    mean_degree = float(nx.mean(degrees)) if degrees else 0.0
    degree_variance = float(nx.var(degrees)) if degrees else 0.0

    # Clustering coefficient (average local clustering)
    clustering_coeffs = nx.clustering(nx_graph)
    avg_clustering = (
        float(nx.mean(list(clustering_coeffs.values()))) if clustering_coeffs else 0.0
    )

    # Connectivity and average path length
    is_connected = nx.is_connected(nx_graph) if num_nodes > 0 else False
    avg_path_length = _average_path_length(nx_graph, is_connected)

    metrics = {
        "degree_distribution": degree_dist,
        "mean_degree": mean_degree,
        "degree_variance": degree_variance,
        "clustering_coefficient": avg_clustering,
        "average_path_length": avg_path_length,
        "num_nodes": num_nodes,
        "num_edges": num_edges,
        "is_connected": is_connected,
    }

    # Persist metrics if we have a network identifier
    if isinstance(graph, NetworkGraph) and getattr(graph, "id", None):
        try:
            out_path = paths.data("processed", f"metrics_{graph.id}.json")
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with out_path.open("w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=2)
            logger.info(f"Saved metrics to {out_path}")
        except Exception as e:
            logger.error(f"Failed to write metrics JSON for {graph.id}: {e}")

    return metrics