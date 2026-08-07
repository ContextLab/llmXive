import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import networkx as nx
import numpy as np

from models.atomic_config import AtomicConfiguration
from config.env_config import get_cutoff_radius, get_processed_dir

logger = logging.getLogger(__name__)

def build_graph_from_atoms(config: AtomicConfiguration, cutoff_radius: Optional[float] = None) -> nx.Graph:
    """
    Build a neighbor graph from an AtomicConfiguration.
    Nodes are atom indices. Edges exist if distance < cutoff_radius.
    """
    if cutoff_radius is None:
        cutoff_radius = get_cutoff_radius()
    
    positions = config.positions
    num_atoms = len(positions)
    
    graph = nx.Graph()
    graph.add_nodes_from(range(num_atoms))
    
    # Simple O(N^2) distance calculation for robustness
    # In production, use ASE neighbor lists for speed
    coords = np.array(positions)
    if coords.shape[0] == 0:
        return graph
        
    # Calculate pairwise distances
    # Using broadcasting: (N, 1, 3) - (1, N, 3) -> (N, N, 3)
    diff = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]
    dists = np.sqrt(np.sum(diff**2, axis=2))
    
    # Mask for upper triangle excluding diagonal
    mask = np.triu(np.ones((num_atoms, num_atoms), dtype=bool), k=1)
    mask &= (dists < cutoff_radius)
    
    # Extract edges
    edges = np.argwhere(mask)
    for i, j in edges:
        graph.add_edge(int(i), int(j))
        
    return graph

def build_graphs(configs: List[AtomicConfiguration], cutoff_radius: Optional[float] = None) -> Dict[str, nx.Graph]:
    """
    Build graphs for a list of configurations.
    Returns a dictionary mapping config_id to graph.
    """
    if cutoff_radius is None:
        cutoff_radius = get_cutoff_radius()
        
    graphs = {}
    for config in configs:
        graph = build_graph_from_atoms(config, cutoff_radius)
        graphs[config.id] = graph
    return graphs

def validate_graph_connectivity(graph: nx.Graph, config_id: str) -> Tuple[bool, List[int]]:
    """
    Check if the graph is connected.
    Returns (is_connected, list_of_disconnected_component_sizes).
    Logs warnings if disconnected components are found (Spec US-1, Scenario 3).
    """
    if graph.number_of_nodes() == 0:
        logger.warning(f"Config {config_id}: Graph has no nodes.")
        return False, []
    
    try:
        components = list(nx.connected_components(graph))
    except nx.NetworkXError as e:
        logger.error(f"Config {config_id}: Error checking connectivity: {e}")
        return False, []
    
    if len(components) == 1:
        return True, []
    
    # Disconnected components found
    component_sizes = [len(c) for c in components]
    largest_size = max(component_sizes)
    num_disconnected = len(components) - 1
    total_nodes = graph.number_of_nodes()
    
    # Log specific warning as per Spec US-1 Scenario 3
    logger.warning(
        f"Config {config_id}: Disconnected components detected. "
        f"Total nodes: {total_nodes}, Largest component: {largest_size}, "
        f"Number of disconnected components: {num_disconnected}. "
        f"Percentage in largest component: {(largest_size/total_nodes)*100:.2f}%. "
        f"This configuration may represent fragmented structures or insufficient cutoff radius."
    )
    
    # Return False and list of sizes of all components except the largest one
    # to allow downstream logic to filter or weight appropriately
    sorted_sizes = sorted(component_sizes, reverse=True)
    disconnected_sizes = sorted_sizes[1:]
    
    return False, disconnected_sizes

def run_sensitivity_analysis(
    configs: List[AtomicConfiguration], 
    radii: List[float]
) -> Dict[str, Any]:
    """
    Run sensitivity analysis for different cutoff radii.
    Calculates average degree and number of connected components for each radius.
    """
    results = []
    for radius in radii:
        graphs = build_graphs(configs, cutoff_radius=radius)
        
        total_degree = 0
        total_nodes = 0
        total_components = 0
        disconnected_count = 0
        
        for cid, graph in graphs.items():
            total_nodes += graph.number_of_nodes()
            total_degree += sum(dict(graph.degree()).values())
            num_comp = nx.number_connected_components(graph)
            total_components += num_comp
            
            if num_comp > 1:
                disconnected_count += 1
        
        avg_degree = total_degree / total_nodes if total_nodes > 0 else 0.0
        avg_components = total_components / len(graphs) if graphs else 0.0
        
        results.append({
            "cutoff_radius": radius,
            "average_degree": avg_degree,
            "average_components": avg_components,
            "configs_with_disconnections": disconnected_count,
            "total_configs": len(graphs)
        })
        
        logger.info(f"Sensitivity Radius {radius} Å: Avg Degree={avg_degree:.2f}, Avg Components={avg_components:.2f}")
    
    return results

def save_sensitivity_report(results: List[Dict[str, Any]], output_path: Optional[Path] = None) -> Path:
    """
    Save sensitivity analysis results to a JSON file.
    """
    if output_path is None:
        output_path = get_processed_dir() / "sensitivity_report.json"
    else:
        output_path = Path(output_path)
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Sensitivity report saved to {output_path}")
    return output_path

def main():
    """
    Main entry point for testing graph builder and sensitivity analysis.
    In a real pipeline, this would be called by main.py after data ingestion.
    """
    setup_logging()
    logger.info("Graph Builder Module loaded.")
    
    # Example usage (would be replaced by actual data loading in main.py)
    # configs = load_configs(...)
    # validate_graph_connectivity(...)
    # run_sensitivity_analysis(...)
    pass

if __name__ == "__main__":
    main()
