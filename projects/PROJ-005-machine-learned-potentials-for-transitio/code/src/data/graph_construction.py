"""
Graph Construction Module for Transition State Graphs.

Converts molecular geometries from QM9-TS into TransitionStateGraph objects
with node attributes (atomic number, formal charge) and edge attributes
(distance-based cutoff). Includes coordination number calculation.
"""

import json
import math
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd

# Import logging utility from existing API surface
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Constants
DEFAULT_CUTOFF_ANGSTROM = 3.5
MAX_COORDINATION_NUMBER = 6
ATOMIC_NUMBERS = {
    'H': 1, 'He': 2, 'Li': 3, 'Be': 4, 'B': 5, 'C': 6, 'N': 7, 'O': 8,
    'F': 9, 'Ne': 10, 'Na': 11, 'Mg': 12, 'Al': 13, 'Si': 14, 'P': 15,
    'S': 16, 'Cl': 17, 'Ar': 18, 'K': 19, 'Ca': 20, 'Sc': 21, 'Ti': 22,
    'V': 23, 'Cr': 24, 'Mn': 25, 'Fe': 26, 'Co': 27, 'Ni': 28, 'Cu': 29,
    'Zn': 30, 'Ga': 31, 'Ge': 32, 'As': 33, 'Se': 34, 'Br': 35, 'Kr': 36,
    'Pd': 46, 'Ag': 47, 'Cd': 48, 'Pt': 78, 'Au': 79
}


def calculate_coordination_number(positions: np.ndarray, atomic_numbers: List[int], cutoff: float = DEFAULT_CUTOFF_ANGSTROM) -> List[int]:
    """
    Calculate coordination numbers for all atoms using a distance-based cutoff.

    FR-002 Logic: Calculate coordination number using a distance-based cutoff of 3.5 Angstroms.

    Args:
        positions: (N, 3) array of atomic positions in Angstroms.
        atomic_numbers: List of atomic numbers for each atom.
        cutoff: Distance cutoff in Angstroms.

    Returns:
        List of coordination numbers for each atom.
    """
    n_atoms = len(positions)
    coordination_numbers = [0] * n_atoms

    for i in range(n_atoms):
        count = 0
        pos_i = positions[i]
        for j in range(n_atoms):
            if i == j:
                continue
            pos_j = positions[j]
            dist = np.linalg.norm(pos_i - pos_j)
            if dist < cutoff:
                count += 1
        coordination_numbers[i] = count

    return coordination_numbers


def build_adjacency_matrix(positions: np.ndarray, cutoff: float = DEFAULT_CUTOFF_ANGSTROM) -> np.ndarray:
    """
    Build an adjacency matrix based on distance cutoff.

    Args:
        positions: (N, 3) array of atomic positions in Angstroms.
        cutoff: Distance cutoff in Angstroms.

    Returns:
        (N, N) boolean adjacency matrix.
    """
    n_atoms = len(positions)
    adj = np.zeros((n_atoms, n_atoms), dtype=bool)

    for i in range(n_atoms):
        for j in range(i + 1, n_atoms):
            dist = np.linalg.norm(positions[i] - positions[j])
            if dist < cutoff:
                adj[i, j] = True
                adj[j, i] = True

    return adj


def extract_edge_attributes(positions: np.ndarray, adj_matrix: np.ndarray) -> List[Dict[str, Any]]:
    """
    Extract edge attributes (distance, indices) for edges present in adjacency matrix.

    Args:
        positions: (N, 3) array of atomic positions.
        adj_matrix: (N, N) boolean adjacency matrix.

    Returns:
        List of dicts with 'source', 'target', 'distance'.
    """
    edges = []
    n_atoms = len(positions)
    for i in range(n_atoms):
        for j in range(i + 1, n_atoms):
            if adj_matrix[i, j]:
                dist = np.linalg.norm(positions[i] - positions[j])
                edges.append({
                    'source': int(i),
                    'target': int(j),
                    'distance': float(dist)
                })
    return edges


def construct_transition_state_graph(
    atom_symbols: List[str],
    positions: np.ndarray,
    formal_charges: Optional[List[int]] = None,
    energy_dft: Optional[float] = None,
    barrier_height: Optional[float] = None,
    ligand_class: Optional[str] = None,
    reaction_id: Optional[str] = None,
    cutoff: float = DEFAULT_CUTOFF_ANGSTROM
) -> Dict[str, Any]:
    """
    Construct a TransitionStateGraph dictionary from molecular data.

    Attributes:
        nodes: List of dicts with 'atomic_number', 'formal_charge'.
        edges: List of dicts with 'source', 'target', 'distance'.
        metadata: Dict with 'energy_dft', 'barrier_height', 'ligand_class', 'reaction_id'.

    Args:
        atom_symbols: List of atomic symbols (e.g., ['C', 'H', 'Pd']).
        positions: (N, 3) array of atomic positions in Angstroms.
        formal_charges: Optional list of formal charges. Defaults to 0.
        energy_dft: DFT energy value.
        barrier_height: Barrier height value.
        ligand_class: Classification of the ligand (e.g., 'Group 13', 'Conventional').
        reaction_id: Unique identifier for the reaction.
        cutoff: Distance cutoff for edge construction.

    Returns:
        Dictionary representing the TransitionStateGraph.
    """
    n_atoms = len(atom_symbols)
    if formal_charges is None:
        formal_charges = [0] * n_atoms

    atomic_numbers = [ATOMIC_NUMBERS.get(sym, 0) for sym in atom_symbols]

    # Calculate coordination numbers (FR-002)
    coordination_numbers = calculate_coordination_number(positions, atomic_numbers, cutoff)

    # Build graph structure
    nodes = []
    for i in range(n_atoms):
        nodes.append({
            'atomic_number': atomic_numbers[i],
            'formal_charge': formal_charges[i],
            'coordination_number': coordination_numbers[i],
            'symbol': atom_symbols[i]
        })

    adj_matrix = build_adjacency_matrix(positions, cutoff)
    edges = extract_edge_attributes(positions, adj_matrix)

    metadata = {
        'energy_dft': energy_dft,
        'barrier_height': barrier_height,
        'ligand_class': ligand_class,
        'reaction_id': reaction_id,
        'cutoff_used': cutoff,
        'n_atoms': n_atoms,
        'n_edges': len(edges)
    }

    graph = {
        'nodes': nodes,
        'edges': edges,
        'metadata': metadata
    }

    return graph


def filter_outliers(
    graphs: List[Dict[str, Any]],
    max_coordination: int = MAX_COORDINATION_NUMBER
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter out graphs with coordination numbers exceeding the threshold.

    Action: Flag samples with >6 coordination for exclusion from training but retention in test.

    Args:
        graphs: List of TransitionStateGraph dictionaries.
        max_coordination: Maximum allowed coordination number.

    Returns:
        Tuple of (valid_graphs, outlier_graphs).
    """
    valid_graphs = []
    outlier_graphs = []

    for graph in graphs:
        is_outlier = False
        for node in graph['nodes']:
            if node['coordination_number'] > max_coordination:
                is_outlier = True
                break

        if is_outlier:
            outlier_graphs.append(graph)
        else:
            valid_graphs.append(graph)

    logger.info(f"Filtered graphs: {len(valid_graphs)} valid, {len(outlier_graphs)} outliers (coord > {max_coordination})")
    return valid_graphs, outlier_graphs


def save_graphs_to_parquet(graphs: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save a list of TransitionStateGraph dictionaries to a Parquet file.

    The data is flattened for storage:
    - nodes are stored as a list of dicts in a 'nodes' column
    - edges are stored as a list of dicts in an 'edges' column
    - metadata is stored as a dict in a 'metadata' column

    Args:
        graphs: List of TransitionStateGraph dictionaries.
        output_path: Path to the output Parquet file.
    """
    if not graphs:
        logger.warning("No graphs to save.")
        # Create empty dataframe with correct schema if needed, or just return
        df = pd.DataFrame(columns=['nodes', 'edges', 'metadata'])
        df.to_parquet(output_path, index=False)
        return

    rows = []
    for i, graph in enumerate(graphs):
        row = {
            'nodes': graph['nodes'],
            'edges': graph['edges'],
            'metadata': graph['metadata']
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved {len(graphs)} graphs to {output_path}")


def save_metadata(outlier_graphs: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save metadata about outliers to a JSON file.

    Args:
        outlier_graphs: List of outlier TransitionStateGraph dictionaries.
        output_path: Path to the output JSON file.
    """
    metadata = {
        'n_outliers': len(outlier_graphs),
        'reason': 'Coordination number > 6'
    }
    if outlier_graphs:
        metadata['sample_reaction_ids'] = [g['metadata'].get('reaction_id') for g in outlier_graphs[:10]]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved outlier metadata to {output_path}")


def main() -> None:
    """
    Main entry point for graph construction pipeline.

    Reads processed data from data/processed/raw_geometries.csv (or similar intermediate),
    constructs graphs, filters outliers, and saves to data/processed/graphs.parquet.
    """
    project_root = Path(__file__).resolve().parents[3]
    input_path = project_root / "data" / "processed" / "filtered_geometries.csv"
    output_path = project_root / "data" / "processed" / "graphs.parquet"
    outlier_meta_path = project_root / "data" / "processed" / "outlier_metadata.json"

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}. Run T015 first.")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Loading geometries from {input_path}")
    df = pd.read_csv(input_path)

    # Expected columns: reaction_id, atoms, positions_json, formal_charges_json, energy_dft, barrier_height, ligand_class
    graphs = []
    for _, row in df.iterrows():
        atoms = row['atoms'].split(',') if isinstance(row['atoms'], str) else row['atoms']
        # Handle positions which might be a string representation of a list or a JSON string
        if isinstance(row['positions'], str):
            try:
                positions = np.array(json.loads(row['positions']))
            except json.JSONDecodeError:
                # Fallback for string format like "[[x,y,z], ...]"
                positions = np.array(eval(row['positions']))
        else:
            positions = np.array(row['positions'])

        formal_charges = row.get('formal_charges')
        if isinstance(formal_charges, str):
            formal_charges = json.loads(formal_charges)
        elif formal_charges is None:
            formal_charges = [0] * len(atoms)

        graph = construct_transition_state_graph(
            atom_symbols=atoms,
            positions=positions,
            formal_charges=formal_charges,
            energy_dft=row.get('energy_dft'),
            barrier_height=row.get('barrier_height'),
            ligand_class=row.get('ligand_class'),
            reaction_id=row.get('reaction_id')
        )
        graphs.append(graph)

    valid_graphs, outlier_graphs = filter_outliers(graphs)

    save_graphs_to_parquet(valid_graphs, output_path)
    save_metadata(outlier_graphs, outlier_meta_path)

    logger.info(f"Graph construction complete. Output: {output_path}")


if __name__ == "__main__":
    main()
