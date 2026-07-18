"""
Graph construction module for network topology analysis.

Implements efficient graph building from defect coordinates using
scipy.spatial.cKDTree for O(N log N) edge creation within a specified threshold.
"""

import logging
import numpy as np
import networkx as nx
from scipy.spatial import cKDTree
from typing import Dict, List, Any, Tuple, Optional

from src.logging_config import get_data_ingestion_logger

logger = get_data_ingestion_logger()


class GraphConstructionError(Exception):
    """Custom exception for graph construction failures."""
    pass


def build_graph_from_coordinates(
    coordinates: np.ndarray,
    threshold: float,
    sample_id: Optional[str] = None
) -> nx.Graph:
    """
    Build a NetworkX graph from 2D defect coordinates using a distance threshold.

    Uses cKDTree for efficient O(N log N) neighbor search to create edges
    between nodes (defects) that are within the specified threshold distance.

    Args:
        coordinates: numpy array of shape (N, 2) containing x, y coordinates.
        threshold: Maximum distance (in nm) for two defects to be connected.
        sample_id: Optional identifier for the sample being processed.

    Returns:
        nx.Graph: A NetworkX graph where nodes are defects and edges represent
                  proximity within the threshold.

    Raises:
        GraphConstructionError: If coordinates are invalid or empty.
    """
    if coordinates is None or coordinates.size == 0:
        raise GraphConstructionError(
            f"Cannot build graph from empty or None coordinates. "
            f"Sample ID: {sample_id}"
        )

    if coordinates.ndim != 2 or coordinates.shape[1] != 2:
        raise GraphConstructionError(
            f"Coordinates must be a 2D array of shape (N, 2). "
            f"Got shape: {coordinates.shape}. Sample ID: {sample_id}"
        )

    n_nodes = coordinates.shape[0]
    logger.debug(f"Building graph for sample {sample_id}: {n_nodes} nodes, "
                 f"threshold={threshold} nm")

    # Create the graph
    G = nx.Graph()

    # Add nodes with position attributes
    for i, (x, y) in enumerate(coordinates):
        G.add_node(i, x=float(x), y=float(y))

    # Use cKDTree for efficient neighbor search
    tree = cKDTree(coordinates)

    # Find all pairs within threshold (returns pairs where i < j to avoid duplicates)
    # query_pairs returns a set of tuples (i, j) where distance(i, j) <= threshold
    pairs = tree.query_pairs(r=threshold, output_type='set')

    logger.debug(f"Found {len(pairs)} edge pairs within threshold {threshold} nm")

    # Add edges to the graph
    for i, j in pairs:
        # Calculate actual distance for edge attribute
        dist = np.linalg.norm(coordinates[i] - coordinates[j])
        G.add_edge(i, j, weight=float(dist))

    logger.info(f"Graph built for sample {sample_id}: "
                f"{G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    return G


def construct_graphs_from_samples(
    samples: List[Dict[str, Any]],
    threshold: float
) -> List[Dict[str, Any]]:
    """
    Construct graphs from a list of sample data dictionaries.

    Each sample dictionary should contain:
    - 'sample_id': Unique identifier for the sample
    - 'coordinates': numpy array of shape (N, 2) with defect positions

    Args:
        samples: List of dictionaries containing sample data.
        threshold: Distance threshold for edge creation.

    Returns:
        List of dictionaries containing:
        - 'sample_id': The sample identifier
        - 'graph': The constructed NetworkX graph
        - 'node_count': Number of nodes in the graph
        - 'edge_count': Number of edges in the graph
        - 'density': Edge density of the graph

    Raises:
        GraphConstructionError: If any sample fails to construct a graph.
    """
    results = []

    for sample in samples:
        sample_id = sample.get('sample_id', 'unknown')
        coordinates = sample.get('coordinates')

        if coordinates is None:
            logger.warning(f"Skipping sample {sample_id}: no coordinates found")
            continue

        try:
            G = build_graph_from_coordinates(coordinates, threshold, sample_id)

            node_count = G.number_of_nodes()
            edge_count = G.number_of_edges()

            # Calculate density
            if node_count > 1:
                max_edges = node_count * (node_count - 1) / 2
                density = edge_count / max_edges
            else:
                density = 0.0

            results.append({
                'sample_id': sample_id,
                'graph': G,
                'node_count': node_count,
                'edge_count': edge_count,
                'density': density
            })

            logger.info(f"Successfully constructed graph for sample {sample_id}: "
                        f"{node_count} nodes, {edge_count} edges, density={density:.4f}")

        except GraphConstructionError as e:
            logger.error(f"Failed to construct graph for sample {sample_id}: {e}")
            raise

    return results


def export_graph_to_dict(
    G: nx.Graph,
    sample_id: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Export a NetworkX graph to a JSON-compatible dictionary format.

    The output conforms to the graph.schema.yaml specification with:
    - Graph-level metadata (nodes, edges, density)
    - Node list with position attributes
    - Edge list with distance weights

    Args:
        G: The NetworkX graph to export.
        sample_id: Unique identifier for the sample.
        metadata: Optional additional metadata to include.

    Returns:
        A dictionary representing the graph in JSON-compatible format.
    """
    node_count = G.number_of_nodes()
    edge_count = G.number_of_edges()

    # Calculate density
    if node_count > 1:
        max_edges = node_count * (node_count - 1) / 2
        density = edge_count / max_edges
    else:
        density = 0.0

    # Export nodes
    nodes = []
    for node_id, data in G.nodes(data=True):
        nodes.append({
            'id': int(node_id),
            'x': float(data.get('x', 0.0)),
            'y': float(data.get('y', 0.0))
        })

    # Export edges
    edges = []
    for u, v, data in G.edges(data=True):
        edges.append({
            'source': int(u),
            'target': int(v),
            'weight': float(data.get('weight', 0.0))
        })

    # Build the result dictionary
    result = {
        'sample_id': sample_id,
        'metadata': {
            'node_count': node_count,
            'edge_count': edge_count,
            'density': density,
            'is_connected': nx.is_connected(G) if node_count > 0 else False
        },
        'nodes': nodes,
        'edges': edges
    }

    # Add any additional metadata
    if metadata:
        result['metadata'].update(metadata)

    return result
