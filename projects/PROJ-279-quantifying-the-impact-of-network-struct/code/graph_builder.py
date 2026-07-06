import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import networkx as nx
import numpy as np

from models.atomic_config import AtomicConfiguration
from logging_config import get_logger

logger = get_logger(__name__)

def build_graph_from_atoms(config: AtomicConfiguration, cutoff_radius: float = 3.2) -> nx.Graph:
    """
    Construct a networkx graph from an AtomicConfiguration.
    Nodes are atom indices. Edges exist if distance < cutoff_radius.
    """
    G = nx.Graph()
    positions = config.positions
    indices = config.indices if config.indices is not None else range(len(positions))
    
    G.add_nodes_from(indices)
    
    n_atoms = len(positions)
    positions_array = np.array(positions)
    
    # Simple O(N^2) distance calculation for correctness; optimization possible later
    for i in range(n_atoms):
        for j in range(i + 1, n_atoms):
            dist = np.linalg.norm(positions_array[i] - positions_array[j])
            if dist < cutoff_radius:
                G.add_edge(i, j)
                
    return G

def build_graphs(configs: List[AtomicConfiguration], cutoff_radius: float = 3.2) -> Dict[str, nx.Graph]:
    """
    Build graphs for a list of configurations.
    Returns a dict mapping config_id to graph.
    """
    graphs = {}
    for config in configs:
        graph = build_graph_from_atoms(config, cutoff_radius)
        graphs[config.config_id] = graph
    return graphs

def validate_graph_connectivity(graph: nx.Graph, config_id: str) -> bool:
    """
    Validate that the constructed graph is connected.
    Returns True if connected, False otherwise.
    Logs a warning if disconnected.
    """
    if graph.number_of_nodes() == 0:
        logger.warning(f"Config {config_id}: Graph has no nodes.")
        return False
        
    if not nx.is_connected(graph):
        num_components = nx.number_connected_components(graph)
        largest_component_size = len(max(nx.connected_components(graph), key=len))
        total_nodes = graph.number_of_nodes()
        
        logger.warning(
            f"Config {config_id}: Graph is disconnected. "
            f"Total nodes: {total_nodes}, Components: {num_components}, "
            f"Largest component size: {largest_component_size}. "
            f"Proceeding with full graph but flagging for analysis."
        )
        return False
        
    return True

def run_sensitivity_analysis(
    configs: List[AtomicConfiguration], 
    cutoffs: List[float], 
    output_dir: str
) -> Dict[str, Any]:
    """
    Run graph construction with multiple cutoff radii to assess sensitivity.
    Generates a sensitivity report.
    """
    results = []
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for cutoff in cutoffs:
        graphs = build_graphs(configs, cutoff)
        avg_degree = []
        component_counts = []
        
        for config_id, graph in graphs.items():
            if graph.number_of_nodes() > 0:
                # Log connectivity warnings as per T016
                validate_graph_connectivity(graph, config_id)
                
                avg_degree.append(np.mean([d for n, d in graph.degree()]))
                component_counts.append(nx.number_connected_components(graph))
        
        if avg_degree:
            results.append({
                "cutoff_radius": cutoff,
                "average_degree": float(np.mean(avg_degree)),
                "average_components": float(np.mean(component_counts))
            })
    
    report = {
        "cutoffs_tested": cutoffs,
        "results": results
    }
    
    report_path = output_path / "sensitivity_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    logger.info(f"Sensitivity analysis report saved to {report_path}")
    return report