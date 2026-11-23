import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
import networkx as nx
import numpy as np

from models.atomic_config import AtomicConfiguration
from config.env_config import get_processed_dir
from logging_config import get_logger

# Define the EXACT discrete set of cutoff radii required by FR-002
# This constant is immutable and enforced by the sensitivity loop logic.
SENSITIVITY_CUTOFFS: Tuple[float, float, float] = (2.8, 3.0, 3.2)
VALID_CUTOFFS = set(SENSITIVITY_CUTOFFS)

logger = get_logger(__name__)


def build_graph_from_atoms(
    config: AtomicConfiguration, cutoff_radius: float
) -> nx.Graph:
    """
    Build a network graph from an atomic configuration using a specific cutoff radius.

    Args:
        config: The atomic configuration object containing coordinates and species.
        cutoff_radius: The distance threshold in Angstroms for bond formation.

    Returns:
        A NetworkX graph where nodes are atoms and edges represent bonds.
    """
    if not isinstance(config, AtomicConfiguration):
        raise TypeError(f"Expected AtomicConfiguration, got {type(config)}")

    if cutoff_radius <= 0:
        raise ValueError(f"Cutoff radius must be positive, got {cutoff_radius}")

    coords = config.coordinates  # Shape: (N, 3)
    N = len(coords)

    G = nx.Graph()
    G.add_nodes_from(range(N))

    # Use a simple O(N^2) distance check. For N ~ 1000-5000, this is acceptable.
    # For very large N, a KDTree approach would be needed.
    # Given the constraint of < 1000 atoms for validation (T007a), N is manageable.
    # However, we use numpy broadcasting for speed.
    dist_matrix = np.linalg.norm(
        coords[:, np.newaxis, :] - coords[np.newaxis, :, :], axis=2
    )

    # Find pairs within cutoff (excluding self, and avoid double counting)
    # We set diagonal to infinity to avoid self-loops
    np.fill_diagonal(dist_matrix, np.inf)

    # Create adjacency matrix boolean mask
    adj_mask = dist_matrix <= cutoff_radius

    # Extract indices of edges (upper triangle to avoid duplicates)
    rows, cols = np.where(adj_mask)
    # Only keep upper triangle indices to avoid double edges
    edges = [(r, c) for r, c in zip(rows, cols) if r < c]

    G.add_edges_from(edges)

    return G


def validate_graph_connectivity(G: nx.Graph) -> Dict[str, Any]:
    """
    Validate the connectivity of the constructed graph.

    Args:
        G: The networkx graph to validate.

    Returns:
        A dictionary with validation results:
        - 'is_connected': bool
        - 'num_components': int
        - 'largest_component_size': int
        - 'warnings': list of strings
    """
    warnings = []
    num_components = nx.number_connected_components(G)
    is_connected = num_components == 1

    if not is_connected:
        sizes = sorted([len(c) for c in nx.connected_components(G)], reverse=True)
        largest_size = sizes[0]
        warnings.append(
            f"Graph is disconnected. Found {num_components} components. "
            f"Largest component size: {largest_size}."
        )
        logger.warning(f"Disconnection detected: {warnings[-1]}")
    else:
        largest_size = G.number_of_nodes()

    return {
        "is_connected": is_connected,
        "num_components": num_components,
        "largest_component_size": largest_size,
        "warnings": warnings,
    }


def build_graphs(
    configs: List[AtomicConfiguration],
    cutoff_radius: float,
    output_dir: Optional[Path] = None,
) -> List[Tuple[str, nx.Graph, Dict[str, Any]]]:
    """
    Build graphs for a list of configurations using a single cutoff radius.

    Args:
        configs: List of atomic configurations.
        cutoff_radius: The cutoff radius to use for all configurations.
        output_dir: Optional directory to save graphs.

    Returns:
        List of tuples: (config_id, graph, validation_info)
    """
    if cutoff_radius not in VALID_CUTOFFS:
        raise ValueError(
            f"Invalid cutoff radius {cutoff_radius}. "
            f"Must be one of {SENSITIVITY_CUTOFFS}. "
            "This is a hard constraint defined in T015a."
        )

    if output_dir is None:
        output_dir = get_processed_dir() / "graphs"
    
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for config in configs:
        try:
            G = build_graph_from_atoms(config, cutoff_radius)
            validation_info = validate_graph_connectivity(G)
            
            # Save graph if requested (T018 requirement)
            # Note: T018 is a separate task, but we prepare the path here.
            # We do not save in this specific function to keep it pure,
            # but the graph is returned for the caller to save.
            
            results.append((config.id, G, validation_info))
            logger.info(f"Built graph for {config.id} with r={cutoff_radius} Å")
        except Exception as e:
            logger.error(f"Failed to build graph for {config.id}: {e}", exc_info=True)
            # Decide whether to skip or fail. For now, skip and log.
            continue

    return results


def run_sensitivity_analysis(
    configs: List[AtomicConfiguration],
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Run the sensitivity analysis loop over the EXACT discrete set of cutoff radii:
    {2.8, 3.0, 3.2} Å.

    This function implements the logic required by T015a and FR-002.

    Args:
        configs: List of validated atomic configurations.
        output_path: Path to save the sensitivity report JSON.

    Returns:
        A dictionary containing the sensitivity report data.
    """
    if output_path is None:
        output_path = get_processed_dir() / "sensitivity_report.json"

    logger.info(f"Starting sensitivity analysis on {len(configs)} configs.")
    logger.info(f"Testing cutoffs: {SENSITIVITY_CUTOFFS}")

    report = {
        "cutoffs_tested": SENSITIVITY_CUTOFFS,
        "num_configs": len(configs),
        "results": []
    }

    for r in SENSITIVITY_CUTOFFS:
        logger.info(f"Processing cutoff radius: {r} Å")
        
        # Build graphs for this specific cutoff
        # We only process the configs passed in (assumed validated by T007-exec)
        graphs_data = build_graphs(configs, r)
        
        # Aggregate statistics
        total_nodes = 0
        total_edges = 0
        total_components = 0
        disconnected_count = 0
        
        for config_id, G, info in graphs_data:
            total_nodes += G.number_of_nodes()
            total_edges += G.number_of_edges()
            total_components += info["num_components"]
            if not info["is_connected"]:
                disconnected_count += 1

        avg_degree = total_edges / total_nodes if total_nodes > 0 else 0.0
        avg_components = total_components / len(graphs_data) if graphs_data else 0.0

        result_entry = {
            "cutoff_radius": r,
            "num_graphs_processed": len(graphs_data),
            "average_degree": avg_degree,
            "average_component_count": avg_components,
            "disconnected_graphs_count": disconnected_count
        }
        
        report["results"].append(result_entry)
        logger.info(
            f"Cutoff {r} Å: Avg Degree={avg_degree:.4f}, "
            f"Avg Components={avg_components:.4f}"
        )

    # Save the report
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Sensitivity report saved to {output_path}")
    return report


def save_sensitivity_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Save the sensitivity analysis report to a JSON file.
    
    Args:
        report: The report dictionary.
        output_path: The file path to save to.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Saved sensitivity report to {output_path}")


def main():
    """
    Entry point for testing the sensitivity loop logic directly.
    This is primarily for development/testing purposes.
    """
    import sys
    from models.atomic_config import AtomicConfiguration
    
    # Create dummy config for testing if no real data is passed
    # In real execution, this would be called by main.py with real configs
    logger.info("Running main for graph_builder sensitivity check.")
    
    # Example usage of the constant
    print(f"Valid cutoffs: {SENSITIVITY_CUTOFFS}")
    
    # Verify the constraint logic
    try:
        # This should work
        build_graphs([], 2.8)
        print("Cutoff 2.8 accepted.")
        
        # This should fail
        build_graphs([], 3.5)
    except ValueError as e:
        print(f"Correctly rejected invalid cutoff: {e}")

if __name__ == "__main__":
    main()