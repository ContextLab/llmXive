"""
Graph construction utilities.
Adjusted to make `sample_id` and `material` optional so that unit tests
which call the function with only coordinates and threshold succeed.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

import numpy as np
import networkx as nx
from scipy.spatial import cKDTree

log = logging.getLogger(__name__)

class GraphConstructionError(RuntimeError):
    """Raised when graph construction fails due to invalid input."""

def build_graph_from_coordinates(
    coordinates: np.ndarray,
    threshold: float,
    sample_id: Optional[str] = None,
    material: str = "graphene",
) -> nx.Graph:
    """
    Construct a network graph from defect coordinates using cKDTree.

    Args:
        coordinates (np.ndarray): Array of shape (N, 2) with (x, y) positions.
        threshold (float): Distance threshold (nm) for adding edges.
        sample_id (Optional[str]): Identifier for the sample; if omitted a
            placeholder is generated.
        material (str): Material name for logging purposes.

    Returns:
        nx.Graph: Graph where nodes are defects and edges connect nodes
        whose Euclidean distance ≤ `threshold`.

    Raises:
        GraphConstructionError: If `coordinates` is empty or malformed.
    """
    if coordinates.size == 0:
        raise GraphConstructionError("No coordinates provided for graph construction.")

    if sample_id is None:
        sample_id = "unspecified"

    # Build KD‑tree for efficient neighbor search
    tree = cKDTree(coordinates)
    pairs = tree.query_pairs(r=threshold, output_type="set")

    G = nx.Graph()
    # Add nodes with position attributes
    for idx, (x, y) in enumerate(coordinates):
        G.add_node(idx, x=float(x), y=float(y), sample_id=sample_id, material=material)

    # Add edges for each pair within the threshold
    for i, j in pairs:
        # Compute Euclidean distance (already ≤ threshold)
        dist = float(np.linalg.norm(coordinates[i] - coordinates[j]))
        G.add_edge(i, j, distance=dist)

    log.debug(
        f"Constructed graph for sample_id={sample_id} with {G.number_of_nodes()} nodes "
        f"and {G.number_of_edges()} edges (threshold={threshold} nm)."
    )
    return G

# The remaining helper functions are unchanged from the original implementation.
def construct_graphs_from_samples(
    samples: List[Dict[str, Any]],
    config: Optional[Dict[str, Any]] = None,
) -> List[Tuple[str, nx.Graph]]:
    """
    Construct graphs from a list of sample dictionaries.

    Each sample should contain:
        - 'sample_id': Unique identifier
        - 'coordinates': numpy array or list of (x, y) coordinates
        - 'material': Optional material name

    Args:
        samples: List of sample dictionaries.
        config: Optional configuration dictionary.

    Returns:
        List of tuples (sample_id, networkx.Graph).

    Raises:
        GraphConstructionError: If any sample fails to construct a graph.
    """
    graphs = []
    for sample in samples:
        sample_id = sample.get("sample_id")
        coords = np.asarray(sample.get("coordinates"))
        material = sample.get("material", "graphene")
        try:
            G = build_graph_from_coordinates(coords, config.get("threshold", 2.5), sample_id, material)
            graphs.append((sample_id, G))
        except Exception as exc:
            raise GraphConstructionError(f"Failed for sample {sample_id}: {exc}") from exc
    return graphs

def export_graph_to_dict(graph: nx.Graph) -> Dict[str, Any]:
    """
    Export a NetworkX graph to a dictionary representation suitable for serialization.

    Args:
        graph (nx.Graph): The graph to export.

    Returns:
        dict: Dictionary containing node and edge data.
    """
    nodes = [
        {"id": n, "x": data["x"], "y": data["y"]} for n, data in graph.nodes(data=True)
    ]
    edges = [
        {"source": u, "target": v, "distance": data["distance"]}
        for u, v, data in graph.edges(data=True)
    ]
    return {"nodes": nodes, "edges": edges}
