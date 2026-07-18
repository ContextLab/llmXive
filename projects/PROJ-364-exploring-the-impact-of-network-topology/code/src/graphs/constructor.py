"""
Graph Construction Module for Network Topology Analysis.

This module implements efficient graph construction from defect coordinate datasets
using scipy.spatial.cKDTree for O(N log N) edge creation within a specified threshold.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

import numpy as np
import networkx as nx
from scipy.spatial import cKDTree

from src.logging_config import get_data_ingestion_logger
from src.config import get_config

logger = get_data_ingestion_logger()


class GraphConstructionError(Exception):
    """Exception raised when graph construction fails."""
    pass


def build_graph_from_coordinates(
    coordinates: np.ndarray,
    threshold: float,
    sample_id: str,
    material: str = "graphene"
) -> nx.Graph:
    """
    Construct a network graph from defect coordinates using cKDTree.

    Nodes represent defects, and edges represent proximity within the given threshold.

    Args:
        coordinates: numpy array of shape (N, 2) containing (x, y) defect coordinates.
        threshold: Distance threshold in nanometers for creating edges.
        sample_id: Unique identifier for the sample being processed.
        material: Material name for logging purposes (default: "graphene").

    Returns:
        networkx.Graph object with nodes as defects and edges as proximity relationships.

    Raises:
        GraphConstructionError: If coordinates are empty or invalid.
    """
    if coordinates is None or len(coordinates) == 0:
        logger.warning(f"[US1] No coordinates provided for sample {sample_id}")
        G = nx.Graph()
        G.graph["sample_id"] = sample_id
        G.graph["material"] = material
        G.graph["node_count"] = 0
        G.graph["edge_count"] = 0
        G.graph["threshold"] = threshold
        G.graph["is_empty"] = True
        return G

    coordinates = np.asarray(coordinates, dtype=np.float64)
    if coordinates.ndim != 2 or coordinates.shape[1] != 2:
        raise GraphConstructionError(
            f"Invalid coordinate shape for sample {sample_id}: "
            f"expected (N, 2), got {coordinates.shape}"
        )

    n_nodes = len(coordinates)
    logger.info(f"[US1] Building graph for sample {sample_id} with {n_nodes} defects "
               f"and threshold {threshold}nm")

    # Build cKDTree for efficient neighbor search
    tree = cKDTree(coordinates)

    # Query all pairs within threshold
    # query_pairs returns a set of frozensets of node indices
    pairs = tree.query_pairs(threshold, output_type='set')

    # Create graph
    G = nx.Graph()
    G.graph["sample_id"] = sample_id
    G.graph["material"] = material
    G.graph["threshold"] = threshold
    G.graph["is_empty"] = False

    # Add nodes with coordinates
    for i, (x, y) in enumerate(coordinates):
        G.add_node(i, x=x, y=y)

    # Add edges
    for i, j in pairs:
        G.add_edge(i, j)

    G.graph["node_count"] = n_nodes
    G.graph["edge_count"] = G.number_of_edges()

    # Calculate edge density
    if n_nodes > 1:
        max_edges = n_nodes * (n_nodes - 1) / 2
        density = G.number_of_edges() / max_edges
    else:
        density = 0.0
    G.graph["density"] = density

    logger.info(f"[US1] Graph {sample_id}: {n_nodes} nodes, {G.number_of_edges()} edges, "
               f"density={density:.4f}")

    return G


def construct_graphs_from_samples(
    samples: List[Dict[str, Any]],
    config: Optional[Dict[str, Any]] = None
) -> List[Tuple[str, nx.Graph]]:
    """
    Construct graphs from a list of sample dictionaries.

    Each sample should contain:
      - 'sample_id': Unique identifier
      - 'coordinates': numpy array or list of (x, y) coordinates
      - 'material': Optional material name

    Args:
        samples: List of sample dictionaries with coordinates and metadata.
        config: Optional configuration dictionary. If None, loads from config.yaml.

    Returns:
        List of tuples (sample_id, networkx.Graph) for each successfully constructed graph.

    Raises:
        GraphConstructionError: If any sample fails to construct a graph.
    """
    if config is None:
        config = get_config()

    threshold = config.get("threshold", 2.0)
    material_default = config.get("default_material", "graphene")

    results = []
    errors = []

    for sample in samples:
        sample_id = sample.get("sample_id")
        if not sample_id:
            error_msg = "Sample missing sample_id"
            logger.error(f"[US1] {error_msg}")
            errors.append(error_msg)
            continue

        coords = sample.get("coordinates")
        if coords is None:
            error_msg = f"[US1] Sample {sample_id} missing coordinates"
            logger.error(error_msg)
            errors.append(error_msg)
            continue

        material = sample.get("material", material_default)

        try:
            graph = build_graph_from_coordinates(
                coordinates=coords,
                threshold=threshold,
                sample_id=sample_id,
                material=material
            )
            results.append((sample_id, graph))
        except GraphConstructionError as e:
            logger.error(f"[US1] Failed to construct graph for {sample_id}: {e}")
            errors.append(str(e))
        except Exception as e:
            logger.error(f"[US1] Unexpected error constructing graph for {sample_id}: {e}")
            errors.append(f"Unexpected error: {e}")

    if errors:
        logger.warning(f"[US1] Constructed {len(results)} graphs with {len(errors)} errors")
        for err in errors[:5]:  # Log first 5 errors
            logger.warning(f"  - {err}")
        if len(errors) > 5:
            logger.warning(f"  ... and {len(errors) - 5} more errors")

    return results


def export_graph_to_dict(graph: nx.Graph) -> Dict[str, Any]:
    """
    Export a NetworkX graph to a dictionary representation suitable for serialization.

    Args:
        graph: NetworkX graph object.

    Returns:
        Dictionary with graph metadata and node/edge information.
    """
    nodes = []
    for node, data in graph.nodes(data=True):
        nodes.append({
            "id": node,
            "x": data.get("x", 0.0),
            "y": data.get("y", 0.0),
            "degree": graph.degree(node)
        })

    edges = []
    for u, v, data in graph.edges(data=True):
        edges.append({
            "source": u,
            "target": v,
            "weight": data.get("weight", 1.0)
        })

    return {
        "sample_id": graph.graph.get("sample_id"),
        "material": graph.graph.get("material"),
        "threshold": graph.graph.get("threshold"),
        "node_count": graph.graph.get("node_count", len(nodes)),
        "edge_count": graph.graph.get("edge_count", len(edges)),
        "density": graph.graph.get("density"),
        "is_empty": graph.graph.get("is_empty", False),
        "nodes": nodes,
        "edges": edges
    }
