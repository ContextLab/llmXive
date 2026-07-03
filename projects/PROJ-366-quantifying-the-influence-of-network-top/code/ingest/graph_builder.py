"""
Graph builder module for constructing atomic graphs from XYZ files.

This module handles the conversion of atomic coordinates into graph
representations suitable for GNN analysis, using a bond cutoff distance
to determine edges.
"""
import os
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from collections import Counter

# Try to import ASE, fallback to mock if not available
try:
    from ase import Atoms
    from ase.io import read
    ASE_AVAILABLE = True
except ImportError:
  ASE_AVAILABLE = False
  logging.warning("ASE not available. Using mock implementation for graph_builder.")

logger = logging.getLogger(__name__)

def build_graph_from_xyz(xyz_file: Path, cutoff: float = 3.0) -> Dict[str, Any]:
    """
    Build an atomic graph from an XYZ file using a bond cutoff distance.
    
    Args:
        xyz_file: Path to the XYZ file
        cutoff: Bond cutoff distance in Angstroms (default: 3.0 Å)
        
    Returns:
        Dictionary containing:
        - nodes: List of node attributes (position, element)
        - edges: List of edge indices (i, j)
        - metadata: File info and cutoff used
        
    Raises:
        FileNotFoundError: If the XYZ file doesn't exist
        ValueError: If the file format is invalid
    """
    if not xyz_file.exists():
        logger.error(f"ERR-001: File not found: {xyz_file}")
        raise FileNotFoundError(f"ERR-001: File not found: {xyz_file}")
    
    if not ASE_AVAILABLE:
        # Mock implementation for testing without ASE
        logger.warning("Using mock graph builder (ASE not available)")
        return _mock_build_graph(xyz_file, cutoff)
    
    try:
        # Read the XYZ file
        atoms = read(str(xyz_file))
        
        # Get atomic positions and species
        positions = atoms.get_positions()
        numbers = atoms.get_atomic_numbers()
        
        n_atoms = len(atoms)
        nodes = []
        
        # Create nodes
        for i, (pos, num) in enumerate(zip(positions, numbers)):
            nodes.append({
                "id": i,
                "position": pos.tolist(),
                "atomic_number": int(num)
            })
        
        # Build adjacency based on cutoff
        edges = []
        positions_array = np.array(positions)
        
        # Calculate pairwise distances
        for i in range(n_atoms):
            for j in range(i + 1, n_atoms):
                dist = np.linalg.norm(positions_array[i] - positions_array[j])
                if dist <= cutoff:
                    edges.append([i, j])
        
        graph_data = {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "source_file": str(xyz_file),
                "cutoff": cutoff,
                "n_nodes": n_atoms,
                "n_edges": len(edges),
                "cutoff_unit": "angstrom"
            }
        }
        
        logger.info(f"Built graph from {xyz_file}: {n_atoms} nodes, {len(edges)} edges")
        return graph_data
        
    except Exception as e:
        logger.error(f"ERR-001: Failed to parse XYZ file {xyz_file}: {str(e)}")
        raise ValueError(f"ERR-001: Failed to parse XYZ file: {str(e)}")

def _mock_build_graph(xyz_file: Path, cutoff: float) -> Dict[str, Any]:
    """Mock implementation for testing without ASE."""
    # Generate a simple mock graph
    n_atoms = 64  # Typical small amorphous silicon cell
    np.random.seed(42)
    
    positions = np.random.rand(n_atoms, 3) * 10  # Random positions in 10Å box
    nodes = []
    
    for i in range(n_atoms):
        nodes.append({
            "id": i,
            "position": positions[i].tolist(),
            "atomic_number": 14  # Silicon
        })
    
    # Create mock edges based on cutoff
    edges = []
    for i in range(n_atoms):
        for j in range(i + 1, n_atoms):
            dist = np.linalg.norm(positions[i] - positions[j])
            if dist <= cutoff:
                edges.append([i, j])
    
    return {
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "source_file": str(xyz_file),
            "cutoff": cutoff,
            "n_nodes": n_atoms,
            "n_edges": len(edges),
            "cutoff_unit": "angstrom",
            "mock": True
        }
    }

def calculate_node_degree_stats(graph_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate node degree statistics from a graph.
    
    Args:
        graph_data: Graph dictionary with 'edges' key
        
    Returns:
        Dictionary containing:
        - degree_distribution: Count of each degree
        - mode: Most common degree
        - mean: Average degree
        - std: Standard deviation of degree
        - min_degree: Minimum degree
        - max_degree: Maximum degree
    """
    edges = graph_data.get("edges", [])
    n_nodes = graph_data.get("metadata", {}).get("n_nodes", 0)
    
    if n_nodes == 0:
        logger.warning("No nodes found in graph, returning empty stats")
        return {
            "degree_distribution": {},
            "mode": 0,
            "mean": 0.0,
            "std": 0.0,
            "min_degree": 0,
            "max_degree": 0,
            "n_nodes": 0
        }
    
    # Calculate degrees
    degrees = [0] * n_nodes
    for edge in edges:
        i, j = edge[0], edge[1]
        degrees[i] += 1
        degrees[j] += 1
    
    # Calculate statistics
    degree_counter = Counter(degrees)
    degree_distribution = dict(degree_counter)
    
    mode = degree_counter.most_common(1)[0][0] if degree_counter else 0
    mean = np.mean(degrees)
    std = np.std(degrees)
    min_degree = min(degrees)
    max_degree = max(degrees)
    
    stats = {
        "degree_distribution": degree_distribution,
        "mode": mode,
        "mean": float(mean),
        "std": float(std),
        "min_degree": int(min_degree),
        "max_degree": int(max_degree),
        "n_nodes": n_nodes,
        "n_edges": len(edges)
    }
    
    return stats

def process_directory(
    input_dir: Path,
    output_dir: Path,
    cutoff: float = 3.0,
    stats_output: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Process all XYZ files in a directory and build graphs.
    
    Args:
        input_dir: Directory containing XYZ files
        output_dir: Directory to save graph outputs
        cutoff: Bond cutoff distance (default: 3.0 Å)
        stats_output: Optional path to save aggregated node degree stats
        
    Returns:
        List of graph data dictionaries
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all XYZ files
    xyz_files = list(input_dir.glob("*.xyz"))
    if not xyz_files:
        logger.warning(f"No XYZ files found in {input_dir}")
        return []
    
    logger.info(f"Found {len(xyz_files)} XYZ files to process")
    
    all_graphs = []
    all_stats = []
    
    for xyz_file in xyz_files:
        try:
            graph_data = build_graph_from_xyz(xyz_file, cutoff)
            all_graphs.append(graph_data)
            
            # Calculate stats for this graph
            stats = calculate_node_degree_stats(graph_data)
            stats["source_file"] = str(xyz_file)
            all_stats.append(stats)
            
            # Save individual graph
            output_file = output_dir / f"{xyz_file.stem}.json"
            with open(output_file, 'w') as f:
                json.dump(graph_data, f, indent=2)
                
            logger.info(f"Processed {xyz_file}: {graph_data['metadata']['n_nodes']} nodes")
            
        except Exception as e:
            logger.error(f"Failed to process {xyz_file}: {str(e)}")
            continue
    
    # Save aggregated stats if requested
    if stats_output:
        stats_output = Path(stats_output)
        stats_output.parent.mkdir(parents=True, exist_ok=True)
        
        # Calculate global stats
        all_degrees = []
        for stats in all_stats:
            for degree, count in stats["degree_distribution"].items():
                all_degrees.extend([degree] * count)
        
        if all_degrees:
            global_stats = {
                "total_samples": len(all_stats),
                "global_degree_distribution": dict(Counter(all_degrees)),
                "global_mode": Counter(all_degrees).most_common(1)[0][0],
                "global_mean": float(np.mean(all_degrees)),
                "global_std": float(np.std(all_degrees)),
                "samples": all_stats
            }
            
            with open(stats_output, 'w') as f:
                json.dump(global_stats, f, indent=2)
            logger.info(f"Saved aggregated stats to {stats_output}")
    
    return all_graphs

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Build atomic graphs from XYZ files")
    parser.add_argument("--input", type=Path, required=True, help="Input directory with XYZ files")
    parser.add_argument("--output", type=Path, required=True, help="Output directory for graphs")
    parser.add_argument("--cutoff", type=float, default=3.0, help="Bond cutoff distance (Å)")
    parser.add_argument("--stats", type=Path, help="Output file for aggregated stats")
    
    args = parser.parse_args()
    
    process_directory(args.input, args.output, args.cutoff, args.stats)
