import json
import math
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parents[3]

def load_optimal_cutoff() -> float:
    """
    Load the optimal cutoff from the sensitivity analysis results.
    Reads from data/results/cutoff_sensitivity.json.
    """
    project_root = get_project_root()
    cutoff_file = project_root / "data" / "results" / "cutoff_sensitivity.json"
    
    if not cutoff_file.exists():
        raise FileNotFoundError(
            f"Optimal cutoff file not found: {cutoff_file}. "
            "Please run T017-optimal first to generate this file."
        )
    
    with open(cutoff_file, 'r') as f:
        data = json.load(f)
    
    if 'optimal_cutoff' not in data:
        raise ValueError(
            f"Expected 'optimal_cutoff' key in {cutoff_file}, but not found. "
            f"Keys found: {list(data.keys())}"
        )
    
    optimal_cutoff = float(data['optimal_cutoff'])
    logger.info(f"Loaded optimal cutoff: {optimal_cutoff} Å from {cutoff_file}")
    return optimal_cutoff

def calculate_coordination_number(
    atomic_numbers: np.ndarray,
    distances: np.ndarray,
    cutoff: float
) -> np.ndarray:
    """
    Calculate coordination number for each atom based on distance cutoff.
    
    Args:
        atomic_numbers: Array of atomic numbers (N,)
        distances: Distance matrix (N, N)
        cutoff: Distance cutoff in Angstroms
        
    Returns:
        Coordination numbers for each atom (N,)
    """
    n_atoms = len(atomic_numbers)
    coord_numbers = np.zeros(n_atoms, dtype=int)
    
    for i in range(n_atoms):
        for j in range(n_atoms):
            if i != j and distances[i, j] < cutoff:
                coord_numbers[i] += 1
                
    return coord_numbers

def build_adjacency_matrix(
    distances: np.ndarray,
    cutoff: float
) -> np.ndarray:
    """
    Build adjacency matrix based on distance cutoff.
    
    Args:
        distances: Distance matrix (N, N)
        cutoff: Distance cutoff in Angstroms
        
    Returns:
        Adjacency matrix (N, N) with 1 for connected, 0 otherwise
    """
    adjacency = (distances < cutoff).astype(int)
    np.fill_diagonal(adjacency, 0)  # No self-loops
    return adjacency

def extract_edge_attributes(
    distances: np.ndarray,
    adjacency: np.ndarray,
    atomic_numbers: np.ndarray
) -> Tuple[List[Tuple[int, int, float]], List[Dict[str, Any]]]:
    """
    Extract edge attributes for graph construction.
    
    Args:
        distances: Distance matrix (N, N)
        adjacency: Adjacency matrix (N, N)
        atomic_numbers: Array of atomic numbers (N,)
        
    Returns:
        Tuple of (edge_list, edge_attributes)
        edge_list: List of (source, target, distance)
        edge_attributes: List of dicts with edge features
    """
    edge_list = []
    edge_attributes = []
    
    n_atoms = len(atomic_numbers)
    for i in range(n_atoms):
        for j in range(n_atoms):
            if adjacency[i, j] == 1:
                edge_list.append((i, j, distances[i, j]))
                edge_attributes.append({
                    'source': int(i),
                    'target': int(j),
                    'distance': float(distances[i, j]),
                    'source_atomic_number': int(atomic_numbers[i]),
                    'target_atomic_number': int(atomic_numbers[j])
                })
                
    return edge_list, edge_attributes

def construct_transition_state_graph(
    geometry_data: Dict[str, Any],
    cutoff: float
) -> Dict[str, Any]:
    """
    Construct a TransitionStateGraph from geometry data using the specified cutoff.
    
    Args:
        geometry_data: Dictionary containing 'atomic_numbers', 'positions', and metadata
        cutoff: Distance cutoff in Angstroms
        
    Returns:
        Dictionary representing the TransitionStateGraph
    """
    atomic_numbers = np.array(geometry_data['atomic_numbers'])
    positions = np.array(geometry_data['positions'])
    
    n_atoms = len(atomic_numbers)
    
    # Calculate distance matrix
    distances = np.zeros((n_atoms, n_atoms))
    for i in range(n_atoms):
        for j in range(n_atoms):
            diff = positions[i] - positions[j]
            distances[i, j] = np.linalg.norm(diff)
    
    # Build adjacency matrix
    adjacency = build_adjacency_matrix(distances, cutoff)
    
    # Calculate coordination numbers
    coord_numbers = calculate_coordination_number(atomic_numbers, distances, cutoff)
    
    # Extract edge attributes
    edge_list, edge_attributes = extract_edge_attributes(distances, adjacency, atomic_numbers)
    
    # Build node attributes
    node_attributes = []
    for i in range(n_atoms):
        node_attributes.append({
            'atomic_number': int(atomic_numbers[i]),
            'formal_charge': geometry_data.get('formal_charges', [0]*n_atoms)[i],
            'coordination_number': int(coord_numbers[i]),
            'position': positions[i].tolist()
        })
    
    # Build graph
    graph = {
        'nodes': node_attributes,
        'edges': edge_list,
        'edge_attributes': edge_attributes,
        'metadata': {
            'cutoff': cutoff,
            'n_atoms': n_atoms,
            'n_edges': len(edge_list),
            'average_coordination': float(np.mean(coord_numbers)),
            'max_coordination': int(np.max(coord_numbers))
        }
    }
    
    # Add reaction metadata if available
    if 'reaction_id' in geometry_data:
        graph['metadata']['reaction_id'] = geometry_data['reaction_id']
    if 'energy_dft' in geometry_data:
        graph['metadata']['energy_dft'] = float(geometry_data['energy_dft'])
    if 'barrier_height' in geometry_data:
        graph['metadata']['barrier_height'] = float(geometry_data['barrier_height'])
    if 'ligand_class' in geometry_data:
        graph['metadata']['ligand_class'] = geometry_data['ligand_class']
        
    return graph

def filter_outliers(graphs: List[Dict[str, Any]], max_coordination: int = 6) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter graphs with coordination numbers > max_coordination.
    Note: For T016b, we keep all graphs but log warnings.
    
    Args:
        graphs: List of graph dictionaries
        max_coordination: Maximum allowed coordination number
        
    Returns:
        Tuple of (filtered_graphs, outlier_graphs)
    """
    filtered = []
    outliers = []
    
    for graph in graphs:
        max_coord = graph['metadata'].get('max_coordination', 0)
        if max_coord > max_coordination:
            outliers.append(graph)
            logger.warning(
                f"Graph {graph['metadata'].get('reaction_id', 'unknown')} has "
                f"coordination number {max_coord} > {max_coordination}. "
                "Flagged as potential outlier but retained."
            )
        else:
            filtered.append(graph)
            
    return filtered, outliers

def save_graphs_to_parquet(graphs: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save graphs to a Parquet file.
    
    Args:
        graphs: List of graph dictionaries
        output_path: Path to output Parquet file
    """
    # Flatten graphs for Parquet storage
    rows = []
    for graph in graphs:
        row = {
            'reaction_id': graph['metadata'].get('reaction_id', 'unknown'),
            'n_atoms': graph['metadata']['n_atoms'],
            'n_edges': graph['metadata']['n_edges'],
            'average_coordination': graph['metadata']['average_coordination'],
            'max_coordination': graph['metadata']['max_coordination'],
            'cutoff': graph['metadata']['cutoff'],
            'nodes_json': json.dumps(graph['nodes']),
            'edges_json': json.dumps(graph['edges']),
            'edge_attributes_json': json.dumps(graph['edge_attributes'])
        }
        
        # Add optional metadata
        if 'energy_dft' in graph['metadata']:
            row['energy_dft'] = graph['metadata']['energy_dft']
        if 'barrier_height' in graph['metadata']:
            row['barrier_height'] = graph['metadata']['barrier_height']
        if 'ligand_class' in graph['metadata']:
            row['ligand_class'] = graph['metadata']['ligand_class']
            
        rows.append(row)
    
    df = pd.DataFrame(rows)
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved {len(graphs)} graphs to {output_path}")

def save_metadata(graphs: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save metadata about the graphs.
    
    Args:
        graphs: List of graph dictionaries
        output_path: Path to output metadata JSON file
    """
    metadata = {
        'total_graphs': len(graphs),
        'cutoff_used': graphs[0]['metadata']['cutoff'] if graphs else None,
        'average_n_atoms': float(np.mean([g['metadata']['n_atoms'] for g in graphs])) if graphs else 0,
        'average_n_edges': float(np.mean([g['metadata']['n_edges'] for g in graphs])) if graphs else 0,
        'average_coordination': float(np.mean([g['metadata']['average_coordination'] for g in graphs])) if graphs else 0,
        'max_coordination_observed': max([g['metadata']['max_coordination'] for g in graphs]) if graphs else 0
    }
    
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata to {output_path}")

def load_processed_graphs_intermediate(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load intermediate graphs from the parquet file generated by T016a.
    
    Args:
        input_path: Path to the intermediate graphs parquet file
        
    Returns:
        List of graph dictionaries
    """
    df = pd.read_parquet(input_path)
    graphs = []
    
    for _, row in df.iterrows():
        graph = {
            'metadata': {
                'reaction_id': row['reaction_id'],
                'n_atoms': int(row['n_atoms']),
                'n_edges': int(row['n_edges']),
                'average_coordination': float(row['average_coordination']),
                'max_coordination': int(row['max_coordination']),
                'cutoff': float(row['cutoff'])
            },
            'nodes': json.loads(row['nodes_json']),
            'edges': json.loads(row['edges_json']),
            'edge_attributes': json.loads(row['edge_attributes_json'])
        }
        
        if 'energy_dft' in row and not pd.isna(row['energy_dft']):
            graph['metadata']['energy_dft'] = float(row['energy_dft'])
        if 'barrier_height' in row and not pd.isna(row['barrier_height']):
            graph['metadata']['barrier_height'] = float(row['barrier_height'])
        if 'ligand_class' in row and not pd.isna(row['ligand_class']):
            graph['metadata']['ligand_class'] = row['ligand_class']
            
        graphs.append(graph)
        
    return graphs

def run_graph_construction(
    intermediate_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Main function to re-run graph construction with the optimal cutoff.
    
    This function:
    1. Loads the optimal cutoff from data/results/cutoff_sensitivity.json
    2. Reads intermediate graphs from T016a (or reconstructs if needed)
    3. Re-builds graphs using the optimal cutoff
    4. Saves the final graphs to data/processed/graphs.parquet
    
    Args:
        intermediate_path: Path to intermediate graphs (default: data/processed/graphs_intermediate.parquet)
        output_path: Path to output final graphs (default: data/processed/graphs.parquet)
        
    Returns:
        List of final graph dictionaries
    """
    project_root = get_project_root()
    
    # Load optimal cutoff
    optimal_cutoff = load_optimal_cutoff()
    
    # Set default paths
    if intermediate_path is None:
        intermediate_path = project_root / "data" / "processed" / "graphs_intermediate.parquet"
    if output_path is None:
        output_path = project_root / "data" / "processed" / "graphs.parquet"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if intermediate file exists
    if not intermediate_path.exists():
        raise FileNotFoundError(
            f"Intermediate graphs file not found: {intermediate_path}. "
            "Please run T016a first to generate this file."
        )
    
    # Load intermediate graphs
    logger.info(f"Loading intermediate graphs from {intermediate_path}")
    graphs = load_processed_graphs_intermediate(intermediate_path)
    logger.info(f"Loaded {len(graphs)} intermediate graphs")
    
    # Reconstruct graphs with optimal cutoff
    logger.info(f"Reconstructing graphs with optimal cutoff: {optimal_cutoff} Å")
    final_graphs = []
    
    for i, graph in enumerate(graphs):
        # Reconstruct geometry data from intermediate graph
        geometry_data = {
            'atomic_numbers': [node['atomic_number'] for node in graph['nodes']],
            'positions': [node['position'] for node in graph['nodes']],
            'formal_charges': [node.get('formal_charge', 0) for node in graph['nodes']],
            'reaction_id': graph['metadata'].get('reaction_id', f'unknown_{i}'),
            'energy_dft': graph['metadata'].get('energy_dft'),
            'barrier_height': graph['metadata'].get('barrier_height'),
            'ligand_class': graph['metadata'].get('ligand_class')
        }
        
        # Construct new graph with optimal cutoff
        new_graph = construct_transition_state_graph(geometry_data, optimal_cutoff)
        final_graphs.append(new_graph)
        
        if (i + 1) % 100 == 0:
            logger.info(f"Processed {i + 1}/{len(graphs)} graphs")
    
    # Filter outliers (log warnings but keep all for T016b)
    filtered_graphs, outlier_graphs = filter_outliers(final_graphs, max_coordination=6)
    logger.info(f"Outliers flagged: {len(outlier_graphs)}")
    
    # Save final graphs
    logger.info(f"Saving final graphs to {output_path}")
    save_graphs_to_parquet(final_graphs, output_path)
    
    # Save metadata
    metadata_path = output_path.with_suffix('.json')
    save_metadata(final_graphs, metadata_path)
    
    logger.info(f"Graph construction complete. Output: {output_path}")
    return final_graphs

def main():
    """Main entry point for T016b."""
    logger.info("Starting T016b: Re-run graph construction with optimal cutoff")
    
    try:
        graphs = run_graph_construction()
        logger.info(f"Successfully constructed {len(graphs)} graphs with optimal cutoff")
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        raise
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during graph construction: {e}")
        raise

if __name__ == "__main__":
    main()