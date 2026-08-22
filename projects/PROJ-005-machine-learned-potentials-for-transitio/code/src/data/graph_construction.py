"""
Graph Construction Module for Transition State Graphs.

Converts geometric data (atomic positions, species, charges) into
TransitionStateGraph objects suitable for GNN training.

Implements FR-002: Coordination number calculation using a 3.5 Angstrom cutoff.
Implements FR-018: Outlier handling for coordination numbers > 6.
"""

import json
import math
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set

import numpy as np
import pandas as pd

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Constants
DEFAULT_CUTOFF = 3.5  # Angstroms
MAX_COORDINATION_OUTLIER = 6
EPSILON = 1e-8


def calculate_coordination_number(
    positions: np.ndarray,
    atomic_numbers: np.ndarray,
    cutoff: float = DEFAULT_CUTOFF
) -> np.ndarray:
    """
    Calculate the coordination number for each atom in the system.

    Uses a distance-based cutoff to determine neighbors.
    Coordination number = number of atoms within 'cutoff' distance (excluding self).

    Args:
        positions: Array of shape (N, 3) with atomic coordinates in Angstroms.
        atomic_numbers: Array of shape (N,) with atomic numbers (used to filter self).
        cutoff: Distance cutoff in Angstroms.

    Returns:
        Array of shape (N,) with coordination numbers for each atom.
    """
    if len(positions) == 0:
        return np.array([], dtype=int)

    # Calculate pairwise distances
    # Using broadcasting: (N, 1, 3) - (1, N, 3) -> (N, N, 3)
    diff = positions[:, np.newaxis, :] - positions[np.newaxis, :, :]
    distances = np.sqrt(np.sum(diff**2, axis=2))

    # Create adjacency mask (exclude self)
    # distances < cutoff AND distances > 0 (to avoid self-loops)
    adj_mask = (distances < cutoff) & (distances > EPSILON)

    # Sum along axis 1 to get coordination number for each atom
    coord_numbers = np.sum(adj_mask, axis=1).astype(int)

    return coord_numbers


def build_adjacency_matrix(
    positions: np.ndarray,
    cutoff: float = DEFAULT_CUTOFF
) -> np.ndarray:
    """
    Build a binary adjacency matrix based on distance cutoff.

    Args:
        positions: Array of shape (N, 3) with atomic coordinates.
        cutoff: Distance cutoff in Angstroms.

    Returns:
        Binary adjacency matrix of shape (N, N).
    """
    if len(positions) == 0:
        return np.array([[]], dtype=bool)

    diff = positions[:, np.newaxis, :] - positions[np.newaxis, :, :]
    distances = np.sqrt(np.sum(diff**2, axis=2))

    adj_matrix = (distances < cutoff) & (distances > EPSILON)
    return adj_matrix


def extract_edge_attributes(
    positions: np.ndarray,
    adj_matrix: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract edge attributes (distances) and indices from adjacency matrix.

    Args:
        positions: Array of shape (N, 3).
        adj_matrix: Binary adjacency matrix of shape (N, N).

    Returns:
        Tuple of (edge_indices, edge_distances)
        edge_indices: Shape (2, num_edges) containing source and target indices.
        edge_distances: Shape (num_edges,) containing distance for each edge.
    """
    if len(positions) == 0:
        return np.empty((2, 0), dtype=int), np.empty(0)

    # Get indices of edges
    edge_indices = np.argwhere(adj_matrix)
    edge_indices = edge_indices.T  # Shape: (2, num_edges)

    # Calculate distances for these edges
    edge_distances = []
    for src, tgt in edge_indices.T:
        dist = np.linalg.norm(positions[src] - positions[tgt])
        edge_distances.append(dist)

    edge_distances = np.array(edge_distances)

    return edge_indices, edge_distances


def construct_transition_state_graph(
    atomic_numbers: List[int],
    formal_charges: List[int],
    positions: np.ndarray,
    energy_dft: Optional[float] = None,
    barrier_height: Optional[float] = None,
    ligand_class: Optional[str] = None,
    reaction_id: Optional[str] = None,
    cutoff: float = DEFAULT_CUTOFF
) -> Dict[str, Any]:
    """
    Construct a TransitionStateGraph dictionary from geometric data.

    Implements the schema defined in contracts/dataset_graph.schema.yaml:
    - nodes: atomic_number, formal_charge, coordination_number
    - edges: distance, source, target
    - metadata: energy_dft, barrier_height, ligand_class, reaction_id

    Args:
        atomic_numbers: List of atomic numbers for each atom.
        formal_charges: List of formal charges for each atom.
        positions: Array of shape (N, 3) with atomic coordinates.
        energy_dft: DFT computed energy (optional).
        barrier_height: DFT computed barrier height (optional).
        ligand_class: Class label for the ligand (e.g., "Group 13", "Conventional").
        reaction_id: Unique identifier for the reaction.
        cutoff: Distance cutoff for edge construction.

    Returns:
        Dictionary representing the TransitionStateGraph.
    """
    if len(atomic_numbers) != len(formal_charges) or len(atomic_numbers) != len(positions):
        raise ValueError("Lengths of atomic_numbers, formal_charges, and positions must match.")

    atomic_numbers = np.array(atomic_numbers)
    formal_charges = np.array(formal_charges)

    # Calculate coordination numbers
    coord_numbers = calculate_coordination_number(positions, atomic_numbers, cutoff)

    # Build adjacency matrix
    adj_matrix = build_adjacency_matrix(positions, cutoff)

    # Extract edge attributes
    edge_indices, edge_distances = extract_edge_attributes(positions, adj_matrix)

    # Construct node features
    nodes = []
    for i in range(len(atomic_numbers)):
        node = {
            "atomic_number": int(atomic_numbers[i]),
            "formal_charge": int(formal_charges[i]),
            "coordination_number": int(coord_numbers[i]),
            "position": positions[i].tolist()
        }
        nodes.append(node)

    # Construct edge features
    edges = []
    for i in range(len(edge_indices.T)):
        src, tgt = edge_indices[0, i], edge_indices[1, i]
        edge = {
            "source": int(src),
            "target": int(tgt),
            "distance": float(edge_distances[i])
        }
        edges.append(edge)

    # Construct metadata
    metadata = {
        "energy_dft": energy_dft,
        "barrier_height": barrier_height,
        "ligand_class": ligand_class,
        "reaction_id": reaction_id,
        "num_nodes": len(nodes),
        "num_edges": len(edges),
        "cutoff_used": cutoff
    }

    return {
        "nodes": nodes,
        "edges": edges,
        "metadata": metadata
    }


def filter_outliers(
    graphs: List[Dict[str, Any]],
    max_coordination: int = MAX_COORDINATION_OUTLIER
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter graphs based on coordination number outliers.

    Graphs with any node having coordination_number > max_coordination are
    flagged as outliers. These are excluded from training but retained for
    potential test set usage (as per FR-018).

    Args:
        graphs: List of graph dictionaries.
        max_coordination: Maximum allowed coordination number.

    Returns:
        Tuple of (training_graphs, outlier_graphs).
    """
    training_graphs = []
    outlier_graphs = []

    for graph in graphs:
        max_cn = 0
        for node in graph["nodes"]:
            cn = node.get("coordination_number", 0)
            if cn > max_cn:
                max_cn = cn

        if max_cn > max_coordination:
            # Mark as outlier
            graph["metadata"]["is_outlier"] = True
            graph["metadata"]["max_coordination"] = max_cn
            outlier_graphs.append(graph)
            logger.info(
                f"Flagged outlier: {graph['metadata'].get('reaction_id', 'unknown')} "
                f"with max coordination {max_cn}"
            )
        else:
            graph["metadata"]["is_outlier"] = False
            training_graphs.append(graph)

    logger.info(f"Total graphs: {len(graphs)}, Training: {len(training_graphs)}, Outliers: {len(outlier_graphs)}")
    return training_graphs, outlier_graphs


def save_graphs_to_parquet(
    graphs: List[Dict[str, Any]],
    output_path: Path,
    split_label: Optional[str] = None
) -> None:
    """
    Save a list of graphs to a Parquet file.

    The graphs are flattened into a DataFrame where each row represents a graph.
    Node and edge lists are stored as JSON strings to maintain structure.

    Args:
        graphs: List of graph dictionaries.
        output_path: Path to the output Parquet file.
        split_label: Optional label for the split (e.g., 'train', 'test').
    """
    if not graphs:
        logger.warning("No graphs to save.")
        return

    rows = []
    for i, graph in enumerate(graphs):
        row = {
            "graph_id": i,
            "num_nodes": len(graph["nodes"]),
            "num_edges": len(graph["edges"]),
            "nodes_json": json.dumps(graph["nodes"]),
            "edges_json": json.dumps(graph["edges"]),
            "energy_dft": graph["metadata"].get("energy_dft"),
            "barrier_height": graph["metadata"].get("barrier_height"),
            "ligand_class": graph["metadata"].get("ligand_class"),
            "reaction_id": graph["metadata"].get("reaction_id"),
            "is_outlier": graph["metadata"].get("is_outlier", False),
            "max_coordination": graph["metadata"].get("max_coordination", 0)
        }
        if split_label:
            row["split"] = split_label
        rows.append(row)

    df = pd.DataFrame(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved {len(graphs)} graphs to {output_path}")


def save_metadata(
    training_graphs: List[Dict[str, Any]],
    outlier_graphs: List[Dict[str, Any]],
    output_dir: Path
) -> None:
    """
    Save metadata about the constructed graphs.

    Args:
        training_graphs: List of training graphs.
        outlier_graphs: List of outlier graphs.
        output_dir: Directory to save metadata files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "total_graphs": len(training_graphs) + len(outlier_graphs),
        "training_graphs": len(training_graphs),
        "outlier_graphs": len(outlier_graphs),
        "cutoff_used": DEFAULT_CUTOFF,
        "max_coordination_threshold": MAX_COORDINATION_OUTLIER,
        "timestamp": str(pd.Timestamp.now())
    }

    # Save summary JSON
    metadata_path = output_dir / "graph_construction_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata to {metadata_path}")


def main() -> None:
    """
    Main entry point for graph construction pipeline.

    Reads processed data from data/raw/ (or wherever ingest.py puts it),
    constructs graphs, filters outliers, and saves to data/processed/graphs.parquet.
    """
    logger.info("Starting graph construction...")

    # Define paths based on project structure
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    input_path = project_root / "data" / "raw" / "qm9_ts_filtered.json"
    output_dir = project_root / "data" / "processed"

    # Check if input exists (if not, we assume ingest.py hasn't run yet or data is elsewhere)
    # For this task, we assume the data is available in a JSON format from ingest.py
    # If the specific file doesn't exist, we log an error and exit.
    if not input_path.exists():
        # Try alternative common location from T014/T015
        alt_path = project_root / "data" / "raw" / "qm9_ts.json"
        if alt_path.exists():
            input_path = alt_path
        else:
            logger.error(f"Input data not found at {input_path} or {alt_path}. "
                         "Please ensure T014/T015 (ingest) has completed successfully.")
            return

    logger.info(f"Loading data from {input_path}")

    try:
        with open(input_path, "r") as f:
            raw_data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load input data: {e}")
        return

    # Expecting raw_data to be a list of reaction dictionaries
    # Structure assumed from T014/T015:
    # [
    #   {
    #     "reaction_id": "...",
    #     "atomic_numbers": [...],
    #     "formal_charges": [...],
    #     "positions": [[x,y,z], ...],
    #     "energy_dft": ...,
    #     "barrier_height": ...,
    #     "ligand_class": "..."
    #   },
    #   ...
    # ]

    graphs = []
    for reaction in raw_data:
        try:
            graph = construct_transition_state_graph(
                atomic_numbers=reaction["atomic_numbers"],
                formal_charges=reaction["formal_charges"],
                positions=np.array(reaction["positions"]),
                energy_dft=reaction.get("energy_dft"),
                barrier_height=reaction.get("barrier_height"),
                ligand_class=reaction.get("ligand_class"),
                reaction_id=reaction.get("reaction_id")
            )
            graphs.append(graph)
        except Exception as e:
            logger.warning(f"Failed to construct graph for {reaction.get('reaction_id', 'unknown')}: {e}")
            continue

    if not graphs:
        logger.error("No graphs were successfully constructed.")
        return

    # Filter outliers
    training_graphs, outlier_graphs = filter_outliers(graphs)

    # Save training graphs
    training_path = output_dir / "graphs.parquet"
    save_graphs_to_parquet(training_graphs, training_path)

    # Save outlier graphs separately (optional but good practice)
    if outlier_graphs:
        outlier_path = output_dir / "graphs_outliers.parquet"
        save_graphs_to_parquet(outlier_graphs, outlier_path, split_label="outlier")

    # Save metadata
    save_metadata(training_graphs, outlier_graphs, output_dir)

    logger.info("Graph construction completed successfully.")


if __name__ == "__main__":
    main()
