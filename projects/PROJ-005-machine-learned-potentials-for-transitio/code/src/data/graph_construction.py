import json
import math
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd

from src.utils.logging import get_logger, log_metric
from src.utils.config import get_project_root

logger = get_logger(__name__)

def calculate_coordination_number(atomic_numbers: np.ndarray, positions: np.ndarray, cutoff: float = 3.5) -> np.ndarray:
    """
    Calculate coordination number for each atom based on distance-based cutoff.
    
    Args:
        atomic_numbers: Array of atomic numbers (Z)
        positions: Array of atomic positions (N x 3)
        cutoff: Distance cutoff in Angstroms
        
    Returns:
        Array of coordination numbers
    """
    N = len(atomic_numbers)
    coords = np.zeros(N, dtype=int)
    
    if N == 0:
        return coords
        
    positions = np.array(positions)
    
    for i in range(N):
        dists = np.sqrt(np.sum((positions - positions[i])**2, axis=1))
        # Count neighbors within cutoff (excluding self)
        neighbors = np.sum((dists < cutoff) & (dists > 1e-6))
        coords[i] = int(neighbors)
        
    return coords

def build_adjacency_matrix(atomic_numbers: np.ndarray, positions: np.ndarray, cutoff: float = 3.5) -> np.ndarray:
    """
    Build adjacency matrix based on distance cutoff.
    
    Args:
        atomic_numbers: Array of atomic numbers
        positions: Array of atomic positions
        cutoff: Distance cutoff in Angstroms
        
    Returns:
        Adjacency matrix (N x N)
    """
    N = len(atomic_numbers)
    if N == 0:
        return np.zeros((0, 0), dtype=bool)
        
    positions = np.array(positions)
    dists = np.sqrt(np.sum((positions[:, None] - positions[None, :])**2, axis=2))
    adj = (dists < cutoff) & (dists > 1e-6)
    return adj

def extract_edge_attributes(positions: np.ndarray, adj: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract edge attributes (distances) for connected atoms.
    
    Args:
        positions: Array of atomic positions
        adj: Adjacency matrix
        
    Returns:
        Tuple of (edge_index, edge_distances)
    """
    edge_indices = np.argwhere(adj)
    if len(edge_indices) == 0:
        return np.zeros((2, 0), dtype=int), np.zeros(0, dtype=float)
        
    edge_distances = np.sqrt(np.sum((positions[edge_indices[:, 0]] - positions[edge_indices[:, 1]])**2, axis=1))
    return edge_indices.T, edge_distances

def construct_transition_state_graph(data_row: Dict[str, Any], cutoff: float = 3.5) -> Dict[str, Any]:
    """
    Construct a TransitionStateGraph from a data row.
    
    Args:
        data_row: Dictionary containing reaction data
        cutoff: Distance cutoff for graph construction
        
    Returns:
        Dictionary representing the graph with node/edge attributes
    """
    # Extract atomic data
    atomic_numbers = np.array(data_row.get('atomic_numbers', []))
    positions = np.array(data_row.get('positions', []))
    
    if len(atomic_numbers) == 0:
        return None
        
    # Calculate coordination numbers
    coord_nums = calculate_coordination_number(atomic_numbers, positions, cutoff)
    
    # Build adjacency matrix
    adj = build_adjacency_matrix(atomic_numbers, positions, cutoff)
    
    # Extract edge attributes
    edge_index, edge_distances = extract_edge_attributes(positions, adj)
    
    # Construct graph dictionary
    graph = {
        'nodes': {
            'atomic_numbers': atomic_numbers.tolist(),
            'formal_charges': data_row.get('formal_charges', [0]*len(atomic_numbers)),
            'coordination_numbers': coord_nums.tolist()
        },
        'edges': {
            'edge_index': edge_index.tolist(),
            'edge_distances': edge_distances.tolist()
        },
        'metadata': {
            'reaction_id': data_row.get('reaction_id', 'unknown'),
            'energy_dft': data_row.get('energy_dft', None),
            'barrier_height': data_row.get('barrier_height', None),
            'cutoff_used': cutoff,
            'ligand_class': data_row.get('ligand_class', 'unknown')
        }
    }
    
    return graph

def filter_outliers(graphs: List[Dict[str, Any]], max_coordination: int = 6) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Flag samples with coordination number > max_coordination.
    These are excluded from training but retained in test.
    
    Args:
        graphs: List of graph dictionaries
        max_coordination: Maximum allowed coordination number (default 6)
        
    Returns:
        Tuple of (training_graphs, test_graphs)
        - training_graphs: Graphs with all coordination numbers <= max_coordination
        - test_graphs: All graphs (including outliers) for test set retention
    """
    training_graphs = []
    test_graphs = []
    
    outlier_count = 0
    total_count = len(graphs)
    
    for graph in graphs:
        if graph is None:
            continue
            
        coord_nums = graph['nodes']['coordination_numbers']
        max_cn = max(coord_nums) if coord_nums else 0
        
        # All graphs go to test set
        test_graphs.append(graph)
        
        # Only non-outliers go to training set
        if max_cn <= max_coordination:
            training_graphs.append(graph)
        else:
            outlier_count += 1
            logger.warning(f"Outlier detected: {graph['metadata']['reaction_id']} has max coordination {max_cn} > {max_coordination}")
    
    log_metric("outlier_count", outlier_count)
    log_metric("total_samples", total_count)
    log_metric("training_samples", len(training_graphs))
    log_metric("test_samples", len(test_graphs))
    
    logger.info(f"Outlier filtering complete: {outlier_count}/{total_count} samples flagged for exclusion from training")
    
    return training_graphs, test_graphs

def save_graphs_to_parquet(graphs: List[Dict[str, Any]], output_path: Path, split_type: str = "all"):
    """
    Save graphs to parquet format.
    
    Args:
        graphs: List of graph dictionaries
        output_path: Path to output file
        split_type: Type of split (training, test, all)
    """
    if not graphs:
        logger.warning(f"No graphs to save for {split_type}")
        return
        
    # Flatten graphs for parquet
    rows = []
    for graph in graphs:
        row = {
            'reaction_id': graph['metadata']['reaction_id'],
            'energy_dft': graph['metadata']['energy_dft'],
            'barrier_height': graph['metadata']['barrier_height'],
            'ligand_class': graph['metadata']['ligand_class'],
            'num_atoms': len(graph['nodes']['atomic_numbers']),
            'max_coordination': max(graph['nodes']['coordination_numbers']) if graph['nodes']['coordination_numbers'] else 0,
            'num_edges': len(graph['edges']['edge_index'][0]) if graph['edges']['edge_index'] else 0,
            'atomic_numbers': graph['nodes']['atomic_numbers'],
            'coordination_numbers': graph['nodes']['coordination_numbers'],
            'edge_distances': graph['edges']['edge_distances']
        }
        rows.append(row)
    
    df = pd.DataFrame(rows)
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved {len(rows)} graphs to {output_path}")

def save_metadata(training_count: int, test_count: int, outlier_count: int, output_path: Path):
    """
    Save outlier handling metadata.
    
    Args:
        training_count: Number of graphs in training set
        test_count: Number of graphs in test set
        outlier_count: Number of outlier graphs
        output_path: Path to output JSON file
    """
    metadata = {
        "total_samples": training_count + outlier_count,
        "training_samples": training_count,
        "test_samples": test_count,
        "outlier_count": outlier_count,
        "outlier_threshold": 6,
        "outlier_status": "excluded_from_training_retained_in_test"
    }
    
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Saved outlier metadata to {output_path}")

def main():
    """
    Main function to run outlier handling on processed graphs.
    Reads from data/processed/graphs.parquet, applies filtering,
    and saves training/test splits.
    """
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "graphs.parquet"
    training_output = project_root / "data" / "processed" / "graphs_training.parquet"
    test_output = project_root / "data" / "processed" / "graphs_test.parquet"
    metadata_output = project_root / "data" / "processed" / "outlier_metadata.json"
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please run graph_construction.py first to generate graphs.parquet")
        return
        
    # Load graphs
    logger.info(f"Loading graphs from {input_path}")
    df = pd.read_parquet(input_path)
    
    # Reconstruct graph objects (simplified for this task)
    graphs = []
    for _, row in df.iterrows():
        graph = {
            'nodes': {
                'atomic_numbers': row['atomic_numbers'],
                'coordination_numbers': row['coordination_numbers'],
                'formal_charges': [0] * len(row['atomic_numbers'])
            },
            'edges': {
                'edge_index': [[], []],  # Simplified
                'edge_distances': row['edge_distances']
            },
            'metadata': {
                'reaction_id': row['reaction_id'],
                'energy_dft': row['energy_dft'],
                'barrier_height': row['barrier_height'],
                'ligand_class': row['ligand_class'],
                'cutoff_used': 3.5
            }
        }
        graphs.append(graph)
    
    logger.info(f"Loaded {len(graphs)} graphs")
    
    # Filter outliers
    training_graphs, test_graphs = filter_outliers(graphs, max_coordination=6)
    
    # Save results
    save_graphs_to_parquet(training_graphs, training_output, "training")
    save_graphs_to_parquet(test_graphs, test_output, "test")
    save_metadata(len(training_graphs), len(test_graphs), len(test_graphs) - len(training_graphs), metadata_output)
    
    logger.info("Outlier handling complete")

if __name__ == "__main__":
    main()