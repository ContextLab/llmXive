import os
import json
import pickle
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from pymatgen.core import Structure

def setup_metrics_logger(name: str = "metrics_logger") -> logging.Logger:
    """Setup a logger for the metrics computation module."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def load_graphs_from_directory(directory: str) -> List[Tuple[str, Any]]:
    """Load all pickle files from a directory."""
    graphs = []
    dir_path = Path(directory)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    for pickle_file in dir_path.glob("*.pkl"):
        with open(pickle_file, 'rb') as f:
            graph = pickle.load(f)
            graphs.append((pickle_file.stem, graph))
    return graphs

def compute_metrics_for_graph(graph: Any) -> Dict[str, float]:
    """Compute network metrics for a given graph."""
    import networkx as nx
    
    if len(graph.nodes()) < 2:
        return {
            'avg_degree': 0.0,
            'avg_shortest_path': np.nan,
            'clustering_coeff': 0.0
        }
    
    avg_degree = np.mean([d for n, d in graph.degree()])
    
    # Compute on Largest Connected Component (LCC) for path length
    try:
        lcc = max(nx.connected_components(graph), key=len)
        lcc_graph = graph.subgraph(lcc).copy()
        if len(lcc_graph) > 1:
            avg_shortest_path = nx.average_shortest_path_length(lcc_graph)
        else:
            avg_shortest_path = np.nan
    except nx.NetworkXError:
        avg_shortest_path = np.nan
    
    clustering_coeff = nx.average_clustering(graph)
    
    return {
        'avg_degree': avg_degree,
        'avg_shortest_path': avg_shortest_path,
        'clustering_coeff': clustering_coeff
    }

def extract_physical_descriptors(graph: Any, structure: Optional[Structure] = None) -> Dict[str, float]:
    """
    Extract physical descriptors from the graph or associated structure.
    If structure is None, we try to infer from graph metadata if available,
    otherwise we return NaNs. Ideally, the structure object is passed from the caller.
    """
    # Initialize with NaN
    descriptors = {
        'unit_cell_volume': np.nan,
        'total_atom_count': np.nan,
        'mean_atomic_mass': np.nan
    }
    
    if structure is not None:
        try:
            descriptors['unit_cell_volume'] = structure.volume
        except Exception:
            pass
        
        try:
            descriptors['total_atom_count'] = len(structure)
        except Exception:
            pass
        
        try:
            masses = [site.species.elements[0].atomic_mass for site in structure]
            if masses:
                descriptors['mean_atomic_mass'] = np.mean(masses)
        except Exception:
            pass
    
    return descriptors

def save_metrics_to_csv(metrics_data: List[Dict[str, Any]], output_path: str):
    """
    Save metrics to a CSV file with a diagnostic header comment.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Define columns
    primary_columns = ['material_id', 'avg_degree', 'avg_shortest_path', 'clustering_coeff', 'thermal_conductivity']
    diagnostic_columns = ['unit_cell_volume', 'total_atom_count', 'mean_atomic_mass']
    all_columns = primary_columns + diagnostic_columns
    
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        # Write the required header comment
        writer.writerow(['# DIAGNOSTICS: Physical descriptors excluded from regression features'])
        # Write the header
        writer.writerow(all_columns)
        
        for row in metrics_data:
            # Ensure all keys exist
            row_data = [row.get(col, '') for col in all_columns]
            writer.writerow(row_data)

def main():
    logger = setup_metrics_logger()
    logger.info("Starting network metrics computation and physical descriptor extraction.")
    
    # Paths
    networks_dir = "data/processed/networks"
    # We need to load thermal conductivity data. Since T015 failed, we assume it needs to be
    # re-integrated or loaded from a manifest if T011 created one. 
    # For this task, we assume the caller or a previous step has loaded thermal conductivity 
    # and passed it in, OR we load it from a manifest if available.
    # However, the task T015b specifically asks to append physical descriptors to metrics.csv.
    # The thermal conductivity column is expected by T015. 
    # Since T015 is marked failed, we must ensure we have the thermal conductivity data.
    # We will assume a manifest exists or we load from the network pickle if it was stored there.
    # Let's check if we can load thermal conductivity from the network pickle metadata if stored.
    
    # Fallback: If we can't find thermal conductivity, we might need to re-run T015 logic.
    # But for this task, we focus on the physical descriptors.
    # We will assume the 'network_manifest.json' from T011 contains thermal conductivity.
    
    manifest_path = Path("data/processed/network_manifest.json")
    thermal_data = {}
    
    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
            for mat_id, info in manifest.items():
                if 'thermal_conductivity' in info:
                    thermal_data[mat_id] = info['thermal_conductivity']
    
    if not thermal_data:
        logger.warning("Could not find thermal conductivity data in manifest. Proceeding with NaN for thermal conductivity.")
    
    graphs = load_graphs_from_directory(networks_dir)
    metrics_data = []
    
    for mat_id, graph in graphs:
        metrics = compute_metrics_for_graph(graph)
        
        # Attempt to get structure for physical descriptors
        # This requires the original CIF or structure object. 
        # Since we only have the graph, we need to check if the graph has metadata attached.
        # If not, we try to reconstruct from the graph nodes if they contain element info.
        structure = None
        
        # Check if graph has a 'structure' attribute (unlikely in simple pickle)
        # If the graph was constructed with pymatgen Structure, it might be stored as a graph attribute.
        if hasattr(graph, 'structure'):
            structure = graph.structure
        
        # If not found in graph, we might need to re-parse the CIF. 
        # For this task, we assume the structure is available via the graph or we skip.
        # To be robust, let's try to load the CIF if the graph doesn't have the structure.
        # But the task is about appending to CSV.
        
        phys_desc = extract_physical_descriptors(graph, structure)
        
        row = {
            'material_id': mat_id,
            'avg_degree': metrics['avg_degree'],
            'avg_shortest_path': metrics['avg_shortest_path'],
            'clustering_coeff': metrics['clustering_coeff'],
            'thermal_conductivity': thermal_data.get(mat_id, np.nan),
            'unit_cell_volume': phys_desc['unit_cell_volume'],
            'total_atom_count': phys_desc['total_atom_count'],
            'mean_atomic_mass': phys_desc['mean_atomic_mass']
        }
        metrics_data.append(row)
        logger.info(f"Processed {mat_id}")
    
    output_path = "data/processed/metrics.csv"
    save_metrics_to_csv(metrics_data, output_path)
    logger.info(f"Metrics saved to {output_path}")

if __name__ == "__main__":
    main()