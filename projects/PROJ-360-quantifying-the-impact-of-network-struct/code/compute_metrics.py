import os
import json
import pickle
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
import networkx as nx
import numpy as np
from config import get_config

def setup_metrics_logger() -> logging.Logger:
    """Setup and return the metrics logger."""
    logger = logging.getLogger("metrics")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def load_graphs_from_directory(graph_dir: Path) -> List[Dict[str, Any]]:
    """Load all pickle files from the graph directory."""
    graphs = []
    if not graph_dir.exists():
        raise FileNotFoundError(f"Graph directory not found: {graph_dir}")
    
    for pickle_file in graph_dir.glob("*.pkl"):
        with open(pickle_file, 'rb') as f:
            graph_data = pickle.load(f)
            graph_data['source_file'] = pickle_file.name
            graphs.append(graph_data)
    return graphs

def compute_metrics_for_graph(graph: nx.Graph, material_id: str) -> Dict[str, Any]:
    """
    Compute network metrics for a single graph.
    
    Handles disconnected graphs by reporting NaN for average shortest path length.
    Computes network density as a diagnostic only.
    """
    metrics = {
        'material_id': material_id,
        'node_count': graph.number_of_nodes(),
        'edge_count': graph.number_of_edges(),
        'average_degree': np.mean([d for n, d in graph.degree()]) if graph.number_of_nodes() > 0 else 0.0,
    }
    
    # Handle disconnected graphs: report NaN for path length
    if not nx.is_connected(graph):
        metrics['average_shortest_path_length'] = float('nan')
        # Still compute LCC metrics for reference but mark as disconnected
        try:
            lcc = max(nx.connected_components(graph), key=len)
            lcc_graph = graph.subgraph(lcc)
            metrics['lcc_average_shortest_path_length'] = nx.average_shortest_path_length(lcc_graph)
            metrics['lcc_clustering_coefficient'] = nx.average_clustering(lcc_graph)
            metrics['is_connected'] = False
        except nx.NetworkXError:
            metrics['lcc_average_shortest_path_length'] = float('nan')
            metrics['lcc_clustering_coefficient'] = 0.0
            metrics['is_connected'] = False
    else:
        metrics['average_shortest_path_length'] = nx.average_shortest_path_length(graph)
        metrics['lcc_average_shortest_path_length'] = nx.average_shortest_path_length(graph)
        metrics['is_connected'] = True
    
    # Compute global clustering coefficient
    metrics['clustering_coefficient'] = nx.average_clustering(graph)
    
    # Compute network density as a diagnostic only
    if graph.number_of_nodes() > 1:
        metrics['network_density'] = nx.density(graph)
    else:
        metrics['network_density'] = 0.0
    
    return metrics

def extract_physical_descriptors(graph_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Extract physical descriptors from graph metadata.
    
    Returns:
        Dictionary with unit_cell_volume, total_atom_count, mean_atomic_mass
    """
    metadata = graph_data.get('metadata', {})
    structure = graph_data.get('structure', None)
    
    descriptors = {
        'unit_cell_volume': metadata.get('unit_cell_volume', 0.0),
        'total_atom_count': metadata.get('total_atom_count', 0),
        'mean_atomic_mass': metadata.get('mean_atomic_mass', 0.0),
    }
    
    # Fallback calculation if metadata is missing but structure is available
    if structure is not None:
        if descriptors['total_atom_count'] == 0:
            descriptors['total_atom_count'] = len(structure)
        
        if descriptors['unit_cell_volume'] == 0.0 and hasattr(structure, 'cell_volume'):
            descriptors['unit_cell_volume'] = structure.cell_volume
        
        if descriptors['mean_atomic_mass'] == 0.0:
            atomic_masses = [site.species.elements[0].atomic_mass for site in structure]
            if atomic_masses:
                descriptors['mean_atomic_mass'] = np.mean(atomic_masses)
    
    return descriptors

def save_metrics_to_csv(metrics_list: List[Dict[str, Any]], output_path: Path):
    """Save metrics to CSV file with diagnostic header comment."""
    if not metrics_list:
        logging.warning("No metrics to save")
        return
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Define columns order
    primary_columns = [
        'material_id', 'node_count', 'edge_count', 'average_degree',
        'average_shortest_path_length', 'lcc_average_shortest_path_length',
        'clustering_coefficient', 'lcc_clustering_coefficient',
        'network_density', 'is_connected'
    ]
    
    # Add physical descriptors columns
    diagnostic_columns = ['unit_cell_volume', 'total_atom_count', 'mean_atomic_mass']
    
    all_columns = primary_columns + diagnostic_columns
    
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write diagnostic header comment
        writer.writerow(['# DIAGNOSTICS: Physical descriptors excluded from regression features'])
        
        # Write header
        writer.writerow(all_columns)
        
        # Write data rows
        for metrics in metrics_list:
            row = []
            for col in all_columns:
                value = metrics.get(col, '')
                if isinstance(value, float) and np.isnan(value):
                    value = 'NaN'
                row.append(value)
            writer.writerow(row)

def main():
    """Main entry point for computing network metrics."""
    logger = setup_metrics_logger()
    config = get_config()
    
    graph_dir = Path(config.get('data_dir', 'data/processed/networks'))
    output_path = Path(config.get('output_dir', 'data/processed')) / 'metrics.csv'
    
    logger.info(f"Loading graphs from {graph_dir}")
    graphs = load_graphs_from_directory(graph_dir)
    logger.info(f"Loaded {len(graphs)} graphs")
    
    all_metrics = []
    skipped = 0
    
    for graph_data in graphs:
        try:
            material_id = graph_data.get('material_id', graph_data.get('source_file', 'unknown'))
            graph = graph_data['graph']
            
            # Validation: ensure graph has at least 2 nodes and 1 edge
            if graph.number_of_nodes() < 2 or graph.number_of_edges() < 1:
                logger.warning(f"Skipping {material_id}: insufficient nodes or edges")
                skipped += 1
                continue
            
            metrics = compute_metrics_for_graph(graph, material_id)
            
            # Extract physical descriptors
            descriptors = extract_physical_descriptors(graph_data)
            metrics.update(descriptors)
            
            all_metrics.append(metrics)
            logger.info(f"Computed metrics for {material_id}: "
                      f"nodes={metrics['node_count']}, edges={metrics['edge_count']}, "
                      f"avg_degree={metrics['average_degree']:.3f}, "
                      f"clustering={metrics['clustering_coefficient']:.3f}")
            
        except Exception as e:
            logger.error(f"Error processing {graph_data.get('source_file', 'unknown')}: {e}")
            skipped += 1
            continue
    
    logger.info(f"Saved metrics for {len(all_metrics)} graphs, skipped {skipped}")
    save_metrics_to_csv(all_metrics, output_path)
    logger.info(f"Metrics saved to {output_path}")

if __name__ == "__main__":
    main()