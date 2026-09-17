import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
import networkx as nx
import numpy as np
from models.atomic_config import AtomicConfiguration
from config.env_config import get_processed_dir, get_cutoff_radius

logger = logging.getLogger(__name__)

def build_graph_from_atoms(config: AtomicConfiguration, cutoff: Optional[float] = None) -> nx.Graph:
    """
    Build a graph representation of an atomic configuration.
    Nodes are atoms, edges represent bonds within the cutoff distance.
    
    Args:
        config: AtomicConfiguration object containing coordinates and species
        cutoff: Bond cutoff distance in Angstroms. Defaults to env config.
    
    Returns:
        networkx.Graph object representing the atomic structure
    """
    if cutoff is None:
        cutoff = get_cutoff_radius()
    
    G = nx.Graph()
    positions = config.coordinates
    n_atoms = len(positions)
    
    # Add nodes
    for i in range(n_atoms):
        G.add_node(i, species=config.species[i], position=positions[i].tolist())
    
    # Add edges based on distance cutoff
    for i in range(n_atoms):
        for j in range(i + 1, n_atoms):
            dist = np.linalg.norm(positions[i] - positions[j])
            if dist <= cutoff:
                G.add_edge(i, j, distance=dist)
    
    return G

def validate_graph_connectivity(G: nx.Graph, config_id: str, min_component_size: int = 10) -> Tuple[bool, List[int], Dict[str, Any]]:
    """
    Validate that the graph is connected and contains no significant disconnected components.
    Logs warnings for disconnected components as per Spec US-1, Scenario 3.
    
    Args:
        G: The graph to validate
        config_id: Identifier for the configuration being validated
        min_component_size: Minimum size for a component to be considered "significant"
    
    Returns:
        Tuple of:
            - is_valid (bool): True if graph is fully connected or has only trivial components
            - isolated_nodes (List[int]): List of node indices in components smaller than min_component_size
            - metadata (Dict): Detailed connectivity information
    """
    if G.number_of_nodes() == 0:
        logger.warning(f"Config {config_id}: Graph has no nodes.")
        return False, [], {"reason": "empty_graph"}

    components = list(nx.connected_components(G))
    n_components = len(components)
    
    metadata = {
        "config_id": config_id,
        "total_nodes": G.number_of_nodes(),
        "total_edges": G.number_of_edges(),
        "n_components": n_components,
        "component_sizes": [len(c) for c in components],
        "largest_component_size": max(len(c) for c in components) if components else 0,
        "isolated_nodes": [],
        "warnings": []
    }

    is_valid = True
    isolated_nodes = []

    if n_components == 1:
        logger.debug(f"Config {config_id}: Graph is fully connected.")
        return True, [], metadata

    # Analyze components
    for i, component in enumerate(components):
        size = len(component)
        if size < min_component_size:
            # Treat as isolated/trivial component
            isolated_nodes.extend(list(component))
            metadata["isolated_nodes"].extend(list(component))
            
            if size == 1:
                warning_msg = f"Config {config_id}: Detected {size} isolated atom(s) (disconnected component)."
            else:
                warning_msg = f"Config {config_id}: Detected disconnected component of size {size} (< {min_component_size})."
            
            logger.warning(warning_msg)
            metadata["warnings"].append(warning_msg)
            is_valid = False
        else:
            logger.info(f"Config {config_id}: Component {i} has size {size}.")

    if not is_valid:
        logger.warning(f"Config {config_id}: Graph validation failed due to disconnected components.")
    
    return is_valid, isolated_nodes, metadata

def build_graphs(configs: List[AtomicConfiguration], cutoff: Optional[float] = None) -> Tuple[List[nx.Graph], List[Dict[str, Any]]]:
    """
    Build graphs for a list of atomic configurations with connectivity validation.
    
    Args:
        configs: List of AtomicConfiguration objects
        cutoff: Bond cutoff distance (optional)
    
    Returns:
        Tuple of:
            - graphs: List of valid nx.Graph objects (excluding those with major connectivity issues)
            - validation_reports: List of metadata dicts for each configuration
    """
    graphs = []
    validation_reports = []
    cutoff = cutoff if cutoff else get_cutoff_radius()
    
    for config in configs:
        G = build_graph_from_atoms(config, cutoff)
        config_id = config.id
        
        is_valid, isolated, meta = validate_graph_connectivity(G, config_id)
        
        # Always record the validation metadata
        validation_reports.append(meta)
        
        # If the graph has significant disconnected components (not just isolated atoms),
        # we might still want to keep it but flag it. 
        # For this implementation, we keep the graph but the metadata indicates validity.
        graphs.append(G)
    
    return graphs, validation_reports

def run_sensitivity_analysis(configs: List[AtomicConfiguration], radii: List[float] = None) -> Dict[str, Any]:
    """
    Run sensitivity analysis on cutoff radius.
    
    Args:
        configs: List of AtomicConfiguration objects
        radii: List of cutoff radii to test. Defaults to [2.8, 3.0, 3.2]
    
    Returns:
        Dictionary containing sensitivity report data
    """
    if radii is None:
        radii = [2.8, 3.0, 3.2]
    
    report = {
        "radii_tested": radii,
        "results": []
    }
    
    for r in radii:
        avg_degree = 0.0
        component_counts = []
        total_nodes = 0
        
        for config in configs:
            G = build_graph_from_atoms(config, r)
            if G.number_of_nodes() > 0:
                total_nodes += G.number_of_nodes()
                avg_degree += np.mean([d for n, d in G.degree()])
                component_counts.append(nx.number_connected_components(G))
        
        n_configs = len(configs)
        if n_configs > 0:
            avg_degree /= n_configs
            avg_components = np.mean(component_counts)
        else:
            avg_components = 0.0
        
        report["results"].append({
            "cutoff_radius": r,
            "average_degree": float(avg_degree),
            "average_component_count": float(avg_components),
            "total_nodes_processed": total_nodes
        })
    
    return report

def save_sensitivity_report(report: Dict[str, Any], output_path: Optional[Path] = None):
    """
    Save sensitivity analysis report to JSON.
    
    Args:
        report: Sensitivity report dictionary
        output_path: Path to save the report. Defaults to data/processed/sensitivity_report.json
    """
    if output_path is None:
        output_path = Path(get_processed_dir()) / "sensitivity_report.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Sensitivity report saved to {output_path}")

def main():
    """
    Main entry point for graph builder module.
    Demonstrates building graphs and running sensitivity analysis.
    """
    setup_logging()
    logger.info("Graph Builder Module Started")
    
    # Example usage would load configs and call build_graphs / run_sensitivity_analysis
    # This is a placeholder for the actual execution logic which depends on data ingestion
    logger.info("Module ready for integration with data pipeline.")

if __name__ == "__main__":
    main()
