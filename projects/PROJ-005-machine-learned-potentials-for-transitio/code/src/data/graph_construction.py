"""
Graph Construction Module for Transition State Data.

This module implements the conversion of raw geometric data into
TransitionStateGraph objects, including coordination number calculation,
adjacency matrix construction, and outlier filtering.
"""
import json
import math
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from src.utils.logging import get_logger, setup_logger
from src.utils.config import get_project_root

# Initialize logger
logger = setup_logger("graph_construction")

# Constants
COORDINATION_CUTOFF_ANGSTROM = 3.5
OUTLIER_COORDINATION_THRESHOLD = 6
PROJECT_ROOT = get_project_root()

def calculate_coordination_number(atomic_numbers: np.ndarray, coordinates: np.ndarray, cutoff: float = COORDINATION_CUTOFF_ANGSTROM) -> np.ndarray:
    """
    Calculate the coordination number for each atom based on a distance-based cutoff.

    Args:
        atomic_numbers: Array of atomic numbers (Z).
        coordinates: Array of atomic coordinates (N, 3) in Angstroms.
        cutoff: Distance cutoff in Angstroms.

    Returns:
        Array of coordination numbers for each atom.
    """
    n_atoms = len(atomic_numbers)
    if n_atoms == 0:
        return np.array([], dtype=int)

    # Calculate pairwise distances
    # coordinates shape: (N, 3)
    diff = coordinates[:, np.newaxis, :] - coordinates[np.newaxis, :, :]
    distances = np.sqrt(np.sum(diff ** 2, axis=2))

    # Create adjacency mask (exclude self-loops)
    mask = distances < cutoff
    np.fill_diagonal(mask, False)

    # Count neighbors for each atom
    coord_numbers = np.sum(mask, axis=1).astype(int)

    return coord_numbers

def build_adjacency_matrix(atomic_numbers: np.ndarray, coordinates: np.ndarray, cutoff: float = COORDINATION_CUTOFF_ANGSTROM) -> np.ndarray:
    """
    Build an adjacency matrix based on distance cutoff.

    Args:
        atomic_numbers: Array of atomic numbers.
        coordinates: Array of atomic coordinates (N, 3).
        cutoff: Distance cutoff in Angstroms.

    Returns:
        Binary adjacency matrix (N, N).
    """
    n_atoms = len(atomic_numbers)
    if n_atoms == 0:
        return np.zeros((0, 0), dtype=bool)

    diff = coordinates[:, np.newaxis, :] - coordinates[np.newaxis, :, :]
    distances = np.sqrt(np.sum(diff ** 2, axis=2))

    adj = distances < cutoff
    np.fill_diagonal(adj, False)

    return adj

def extract_edge_attributes(
    atomic_numbers: np.ndarray,
    coordinates: np.ndarray,
    cutoff: float = COORDINATION_CUTOFF_ANGSTROM
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Extract edge attributes: source, target, and distance.

    Args:
        atomic_numbers: Array of atomic numbers.
        coordinates: Array of atomic coordinates (N, 3).
        cutoff: Distance cutoff in Angstroms.

    Returns:
        Tuple of (edge_source, edge_target, edge_distances).
    """
    adj = build_adjacency_matrix(atomic_numbers, coordinates, cutoff)
    n_atoms = len(atomic_numbers)

    if n_atoms == 0:
        return np.array([], dtype=int), np.array([], dtype=int), np.array([], dtype=float)

    # Get indices of edges
    edge_source, edge_target = np.where(adj)
    edge_indices = np.stack([edge_source, edge_target], axis=1)

    # Calculate distances for these edges
    diff = coordinates[edge_source] - coordinates[edge_target]
    edge_distances = np.sqrt(np.sum(diff ** 2, axis=1))

    return edge_source, edge_target, edge_distances

def construct_transition_state_graph(
    row: pd.Series,
    cutoff: float = COORDINATION_CUTOFF_ANGSTROM
) -> Dict[str, Any]:
    """
    Construct a TransitionStateGraph dictionary from a single data row.

    Expected row columns:
        - atomic_numbers: list of ints
        - coordinates: list of lists (N, 3)
        - formal_charges: list of ints (optional, default 0)
        - energy_dft: float
        - barrier_height: float
        - reaction_id: str

    Args:
        row: Pandas Series containing reaction data.
        cutoff: Distance cutoff for graph construction.

    Returns:
        Dictionary representing the graph with nodes, edges, and metadata.
    """
    atomic_numbers = np.array(row['atomic_numbers'])
    coordinates = np.array(row['coordinates'])
    formal_charges = row.get('formal_charges', np.zeros(len(atomic_numbers), dtype=int))
    if isinstance(formal_charges, list):
        formal_charges = np.array(formal_charges)

    n_atoms = len(atomic_numbers)

    # Node attributes
    node_features = {
        'atomic_numbers': atomic_numbers.tolist(),
        'formal_charges': formal_charges.tolist()
    }

    # Calculate coordination numbers
    coord_numbers = calculate_coordination_number(atomic_numbers, coordinates, cutoff)
    node_features['coordination_numbers'] = coord_numbers.tolist()

    # Edge attributes
    edge_source, edge_target, edge_distances = extract_edge_attributes(
        atomic_numbers, coordinates, cutoff
    )

    edge_features = {
        'source': edge_source.tolist(),
        'target': edge_target.tolist(),
        'distances': edge_distances.tolist()
    }

    # Graph metadata
    metadata = {
        'reaction_id': row['reaction_id'],
        'n_atoms': n_atoms,
        'energy_dft': float(row['energy_dft']),
        'barrier_height': float(row['barrier_height']),
        'cutoff_used': cutoff,
        'max_coordination': int(np.max(coord_numbers)) if n_atoms > 0 else 0
    }

    # Ligand class classification (simplified heuristic based on transition metal)
    # Assuming Pd, Ni, Cu are the transition metals of interest
    transition_metals = {28, 29, 46}  # Ni, Cu, Pd
    has_transition_metal = any(z in transition_metals for z in atomic_numbers)
    metadata['has_transition_metal'] = has_transition_metal

    return {
        'nodes': node_features,
        'edges': edge_features,
        'metadata': metadata
    }

def filter_outliers(
    graphs: List[Dict[str, Any]],
    threshold: int = OUTLIER_COORDINATION_THRESHOLD
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter graphs based on maximum coordination number.

    Graphs with any atom having coordination number > threshold are flagged
    as outliers. Outliers are separated into a list for exclusion from training
    but retention for testing.

    Args:
        graphs: List of graph dictionaries.
        threshold: Maximum allowed coordination number.

    Returns:
        Tuple of (clean_graphs, outlier_graphs).
    """
    clean_graphs = []
    outlier_graphs = []

    for graph in graphs:
        coord_numbers = graph['nodes']['coordination_numbers']
        max_coord = max(coord_numbers) if coord_numbers else 0

        if max_coord > threshold:
            graph['metadata']['is_outlier'] = True
            outlier_graphs.append(graph)
        else:
            graph['metadata']['is_outlier'] = False
            clean_graphs.append(graph)

    logger.info(f"Filtered {len(outlier_graphs)} outliers (max coordination > {threshold}) "
                f"from {len(graphs)} total graphs. Retaining {len(clean_graphs)} for training.")

    return clean_graphs, outlier_graphs

def save_graphs_to_parquet(
    graphs: List[Dict[str, Any]],
    output_path: Path,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Save a list of graph dictionaries to a Parquet file.

    The graphs are flattened into a tabular format for Parquet storage.
    Complex nested structures are serialized as JSON strings.

    Args:
        graphs: List of graph dictionaries.
        output_path: Path to the output Parquet file.
        metadata: Optional metadata dictionary to include.
    """
    if not graphs:
        logger.warning("No graphs to save.")
        # Create empty file with schema
        output_path.parent.mkdir(parents=True, exist_ok=True)
        empty_df = pd.DataFrame(columns=[
            'reaction_id', 'n_atoms', 'energy_dft', 'barrier_height',
            'nodes_atomic_numbers', 'nodes_formal_charges', 'nodes_coordination_numbers',
            'edges_source', 'edges_target', 'edges_distances', 'is_outlier',
            'has_transition_metal'
        ])
        pq.write_table(pa.Table.from_pandas(empty_df), output_path)
        return

    records = []
    for graph in graphs:
        meta = graph['metadata']
        nodes = graph['nodes']
        edges = graph['edges']

        record = {
            'reaction_id': meta['reaction_id'],
            'n_atoms': meta['n_atoms'],
            'energy_dft': meta['energy_dft'],
            'barrier_height': meta['barrier_height'],
            'nodes_atomic_numbers': json.dumps(nodes['atomic_numbers']),
            'nodes_formal_charges': json.dumps(nodes['formal_charges']),
            'nodes_coordination_numbers': json.dumps(nodes['coordination_numbers']),
            'edges_source': json.dumps(edges['source']),
            'edges_target': json.dumps(edges['target']),
            'edges_distances': json.dumps(edges['distances']),
            'is_outlier': meta.get('is_outlier', False),
            'has_transition_metal': meta.get('has_transition_metal', False)
        }
        records.append(record)

    df = pd.DataFrame(records)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pandas(df), output_path)
    logger.info(f"Saved {len(df)} graphs to {output_path}")

def save_metadata(
    clean_count: int,
    outlier_count: int,
    total_count: int,
    cutoff: float,
    output_path: Path
) -> None:
    """
    Save graph construction metadata to a JSON file.

    Args:
        clean_count: Number of non-outlier graphs.
        outlier_count: Number of outlier graphs.
        total_count: Total number of graphs processed.
        cutoff: Distance cutoff used.
        output_path: Path to the output JSON file.
    """
    metadata = {
        'total_graphs': total_count,
        'clean_graphs': clean_count,
        'outlier_graphs': outlier_count,
        'coordination_cutoff': cutoff,
        'outlier_threshold': OUTLIER_COORDINATION_THRESHOLD
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata to {output_path}")

def run_graph_construction(
    input_path: Path,
    output_graphs_path: Path,
    output_metadata_path: Path,
    cutoff: float = COORDINATION_CUTOFF_ANGSTROM
) -> None:
    """
    Main entry point for graph construction pipeline.

    Reads processed data, constructs graphs, filters outliers, and saves results.

    Args:
        input_path: Path to input processed data (Parquet).
        output_graphs_path: Path to save constructed graphs (Parquet).
        output_metadata_path: Path to save construction metadata (JSON).
        cutoff: Distance cutoff for graph construction.
    """
    logger.info(f"Starting graph construction from {input_path} with cutoff {cutoff} Å")

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Load input data
    df = pq.read_table(input_path).to_pandas()
    logger.info(f"Loaded {len(df)} reactions from {input_path}")

    # Construct graphs
    graphs = []
    for _, row in df.iterrows():
        try:
            graph = construct_transition_state_graph(row, cutoff=cutoff)
            graphs.append(graph)
        except Exception as e:
            logger.error(f"Error constructing graph for {row.get('reaction_id', 'unknown')}: {e}")
            continue

    if not graphs:
        raise RuntimeError("No graphs were successfully constructed.")

    # Filter outliers
    clean_graphs, outlier_graphs = filter_outliers(graphs, threshold=OUTLIER_COORDINATION_THRESHOLD)

    # Combine for saving (all graphs go to file, marked with is_outlier flag)
    all_graphs = clean_graphs + outlier_graphs

    # Save graphs
    save_graphs_to_parquet(all_graphs, output_graphs_path)

    # Save metadata
    save_metadata(
        clean_count=len(clean_graphs),
        outlier_count=len(outlier_graphs),
        total_count=len(all_graphs),
        cutoff=cutoff,
        output_path=output_metadata_path
    )

    logger.info("Graph construction completed successfully.")

def main():
    """CLI entry point for graph construction."""
    import argparse

    parser = argparse.ArgumentParser(description="Construct Transition State Graphs from processed data.")
    parser.add_argument(
        "--input",
        type=str,
        default=str(PROJECT_ROOT / "data" / "processed" / "filtered_reactions.parquet"),
        help="Path to input processed reactions Parquet file."
    )
    parser.add_argument(
        "--output-graphs",
        type=str,
        default=str(PROJECT_ROOT / "data" / "processed" / "graphs.parquet"),
        help="Path to output graphs Parquet file."
    )
    parser.add_argument(
        "--output-metadata",
        type=str,
        default=str(PROJECT_ROOT / "data" / "processed" / "graph_construction_metadata.json"),
        help="Path to output metadata JSON file."
    )
    parser.add_argument(
        "--cutoff",
        type=float,
        default=COORDINATION_CUTOFF_ANGSTROM,
        help=f"Distance cutoff in Angstroms (default: {COORDINATION_CUTOFF_ANGSTROM})"
    )

    args = parser.parse_args()

    run_graph_construction(
        input_path=Path(args.input),
        output_graphs_path=Path(args.output_graphs),
        output_metadata_path=Path(args.output_metadata),
        cutoff=args.cutoff
    )

if __name__ == "__main__":
    main()
