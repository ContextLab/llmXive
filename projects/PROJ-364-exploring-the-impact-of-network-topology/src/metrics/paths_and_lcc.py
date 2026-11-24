"""
Metric calculations related to graph connectivity:
- Largest Connected Component (LCC) fraction
- Connectivity flag
- Average shortest‑path length (computed on the LCC when the graph is disconnected)
"""

import networkx as nx
from typing import Dict, Any

def calculate_path_length_and_lcc(graph: nx.Graph) -> Dict[str, Any]:
    """
    Compute connectivity‑related metrics for a NetworkX graph.

    Returns a dictionary with:
        - is_connected (bool): True if the graph is fully connected.
        - lcc_fraction (float): |LCC| / total_nodes.
        - average_path_length (float): Average shortest‑path length on the LCC.
          For a single‑node LCC this is 0.0. For an empty graph this is None.

    The function follows the expectations encoded in the unit tests.
    """
    total_nodes = graph.number_of_nodes()
    if total_nodes == 0:
        # Edge case – no nodes at all
        return {
            "is_connected": True,
            "lcc_fraction": 0.0,
            "average_path_length": None,
        }

    # Determine connected components
    components = list(nx.connected_components(graph))
    lcc_nodes = max(components, key=len)
    lcc_size = len(lcc_nodes)
    lcc_fraction = lcc_size / total_nodes

    is_connected = graph.is_connected()

    # Build subgraph for LCC
    lcc_subgraph = graph.subgraph(lcc_nodes)

    # Average shortest path length
    if lcc_subgraph.number_of_nodes() <= 1:
        avg_path = 0.0
    else:
        avg_path = nx.average_shortest_path_length(lcc_subgraph)

    return {
        "is_connected": is_connected,
        "lcc_fraction": float(lcc_fraction),
        "average_path_length": float(avg_path),
    }
