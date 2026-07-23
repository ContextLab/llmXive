"""
Graph construction and sensitivity analysis for atomic configurations.

Implements graph building from atomic coordinates and sensitivity analysis
across different cutoff radii to study network structure impact.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import networkx as nx
import numpy as np
from models.atomic_config import AtomicConfiguration
from logging_config import get_logger
from config.env_config import get_processed_dir

logger = get_logger(__name__)

def build_graph_from_atoms(config: AtomicConfiguration, cutoff_radius: float) -> nx.Graph:
    """
    Build a networkx graph from an atomic configuration using a distance cutoff.
    
    Args:
        config: AtomicConfiguration object containing coordinates and species
        cutoff_radius: Distance threshold in Angstroms for bond formation
        
    Returns:
        networkx.Graph object representing the atomic network
    """
    G = nx.Graph()
    positions = config.coordinates  # numpy array of shape (N, 3)
    n_atoms = len(positions)
    
    # Add nodes
    for i in range(n_atoms):
        G.add_node(i, species=config.species[i], position=positions[i].tolist())
    
    # Add edges based on distance cutoff
    # Using squared distances to avoid sqrt in comparisons
    cutoff_sq = cutoff_radius ** 2
    
    for i in range(n_atoms):
        for j in range(i + 1, n_atoms):
            dist_sq = np.sum((positions[i] - positions[j]) ** 2)
            if dist_sq < cutoff_sq:
                G.add_edge(i, j, distance=np.sqrt(dist_sq))
                
    return G

def build_graphs(
    configs: List[AtomicConfiguration], 
    cutoff_radius: float
) -> Dict[str, nx.Graph]:
    """
    Build graphs for multiple configurations at a given cutoff radius.
    
    Args:
        configs: List of AtomicConfiguration objects
        cutoff_radius: Distance threshold in Angstroms
        
    Returns:
        Dictionary mapping config_id to networkx.Graph
    """
    graphs = {}
    for config in configs:
        try:
            G = build_graph_from_atoms(config, cutoff_radius)
            graphs[config.config_id] = G
            logger.info(f"Built graph for {config.config_id} with {G.number_of_nodes()} nodes "
                        f"and {G.number_of_edges()} edges at cutoff {cutoff_radius:.2f} Å")
        except Exception as e:
            logger.error(f"Failed to build graph for {config.config_id}: {e}")
            continue
    return graphs

def validate_graph_connectivity(G: nx.Graph, config_id: str) -> Tuple[bool, List[int]]:
    """
    Check if a graph is connected and identify largest component.
    
    Args:
        G: networkx.Graph to validate
        config_id: Identifier for logging
        
    Returns:
        Tuple of (is_connected, list of nodes in largest component)
    """
    if G.number_of_nodes() == 0:
        logger.warning(f"Empty graph for {config_id}")
        return False, []
        
    largest_component = max(nx.connected_components(G), key=len)
    is_connected = len(largest_component) == G.number_of_nodes()
    
    if not is_connected:
        logger.warning(f"Graph for {config_id} has {nx.number_connected_components(G)} "
                       f"components. Largest has {len(largest_component)} nodes.")
        
    return is_connected, list(largest_component)

def run_sensitivity_analysis(
    validated_configs: List[AtomicConfiguration],
    cutoff_radii: List[float] = [2.8, 3.0, 3.2]
) -> Dict[str, Any]:
    """
    Run sensitivity analysis across different cutoff radii.
    
    Computes average degree and number of connected components for each
    cutoff radius to understand how network structure metrics vary.
    
    Args:
        validated_configs: List of AtomicConfiguration objects that passed validation
        cutoff_radii: List of cutoff radii in Angstroms to test
        
    Returns:
        Dictionary containing sensitivity analysis results
    """
    if not validated_configs:
        logger.warning("No validated configurations provided for sensitivity analysis")
        return {"cutoff_radii": cutoff_radii, "results": [], "note": "No data"}
    
    results = []
    
    logger.info(f"Starting sensitivity analysis with {len(validated_configs)} configs "
                f"and cutoffs: {cutoff_radii}")
    
    for cutoff in cutoff_radii:
        logger.info(f"Processing cutoff radius: {cutoff:.2f} Å")
        
        # Build graphs for this cutoff
        graphs = build_graphs(validated_configs, cutoff)
        
        if not graphs:
            logger.warning(f"No graphs built for cutoff {cutoff:.2f} Å")
            continue
        
        # Compute metrics
        total_degree = 0
        total_components = 0
        valid_count = 0
        
        for config_id, G in graphs.items():
            if G.number_of_nodes() == 0:
                continue
                
            avg_degree = np.mean([d for n, d in G.degree()])
            n_components = nx.number_connected_components(G)
            
            total_degree += avg_degree
            total_components += n_components
            valid_count += 1
            
            # Log disconnected components warning
            is_connected, _ = validate_graph_connectivity(G, config_id)
            if not is_connected and n_components > 1:
                logger.debug(f"Config {config_id} at cutoff {cutoff:.2f} Å has {n_components} components")
        
        if valid_count > 0:
            avg_avg_degree = total_degree / valid_count
            avg_components = total_components / valid_count
            
            results.append({
                "cutoff_radius": cutoff,
                "average_degree": float(avg_avg_degree),
                "average_component_count": float(avg_components),
                "configurations_processed": valid_count
            })
            logger.info(f"Cutoff {cutoff:.2f} Å: avg_degree={avg_avg_degree:.4f}, "
                        f"avg_components={avg_components:.4f}")
    
    report = {
        "cutoff_radii": cutoff_radii,
        "results": results,
        "analysis_timestamp": str(Path.cwd()),
        "total_configs_analyzed": len(validated_configs)
    }
    
    return report

def save_sensitivity_report(report: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Save sensitivity analysis report to JSON file.
    
    Args:
        report: Dictionary containing sensitivity analysis results
        output_path: Optional path for output file. If None, uses default location.
        
    Returns:
        Path to the saved file
    """
    if output_path is None:
        processed_dir = get_processed_dir()
        output_path = Path(processed_dir) / "sensitivity_report.json"
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Sensitivity report saved to {output_path}")
    return output_path

def main():
    """
    Main entry point for sensitivity analysis execution.
    
    This function:
    1. Loads validated configurations from data/processed/validation_report.json
    2. Runs sensitivity analysis across cutoff radii {2.8, 3.0, 3.2} Å
    3. Saves results to data/processed/sensitivity_report.json
    """
    setup_logging()
    
    processed_dir = get_processed_dir()
    validation_report_path = Path(processed_dir) / "validation_report.json"
    output_path = Path(processed_dir) / "sensitivity_report.json"
    
    # Load validated configs
    if not validation_report_path.exists():
        logger.error(f"Validation report not found at {validation_report_path}. "
                     "Run T007-exec first to generate validation data.")
        raise FileNotFoundError(f"Validation report not found: {validation_report_path}")
    
    with open(validation_report_path, 'r') as f:
        validation_data = json.load(f)
    
    validated_config_ids = validation_data.get('validated_configs', [])
    
    if not validated_config_ids:
        logger.warning("No validated configurations found in validation report")
        # Create empty report
        report = {"cutoff_radii": [2.8, 3.0, 3.2], "results": [], "note": "No validated configs"}
        save_sensitivity_report(report, output_path)
        return
    
    logger.info(f"Found {len(validated_config_ids)} validated configurations")
    
    # Load atomic configurations from raw data
    # Assuming configs are stored in data/raw/ as individual files or a single file
    # This implementation assumes a standard format where we need to load them
    from download import load_configurations_from_raw  # Import if available, else handle differently
    
    # For now, we'll assume configurations need to be loaded from a processed format
    # In a real scenario, we'd load from the raw trajectory files
    raw_dir = Path(processed_dir).parent / "raw"
    
    # Attempt to load configurations - this assumes a standard loading mechanism
    # that would be implemented in the download module
    try:
        configs = load_configurations_from_raw(raw_dir, validated_config_ids)
    except ImportError:
        # Fallback: try to load from a JSON file if available
        configs_json_path = raw_dir / "configs.json"
        if configs_json_path.exists():
            with open(configs_json_path, 'r') as f:
                all_configs_data = json.load(f)
            
            configs = []
            for config_data in all_configs_data:
                if config_data['config_id'] in validated_config_ids:
                    configs.append(AtomicConfiguration(**config_data))
        else:
            logger.error("No configuration data found. Please ensure raw data is loaded.")
            raise
    
    # Run sensitivity analysis
    cutoff_radii = [2.8, 3.0, 3.2]
    report = run_sensitivity_analysis(configs, cutoff_radii)
    
    # Save report
    save_sensitivity_report(report, output_path)
    
    logger.info(f"Sensitivity analysis complete. Report saved to {output_path}")

if __name__ == "__main__":
    main()
