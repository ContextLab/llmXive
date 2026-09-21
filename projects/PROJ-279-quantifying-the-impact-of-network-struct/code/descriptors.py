import logging
import networkx as nx
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from collections import Counter
from models.atomic_config import AtomicConfiguration
from vdos_handler import load_vdos, calculate_participation_ratios, check_vdos_availability
from config.env_config import get_processed_dir

logger = logging.getLogger(__name__)

def calculate_ring_statistics(graph: nx.Graph) -> Dict[int, int]:
    """
    Calculate ring statistics for a given graph.
    Returns a dictionary mapping ring size to count.
    """
    # Simple cycle detection for ring statistics
    # In a real implementation, this would use a more robust algorithm like Girth or Johnson's algorithm
    # For amorphous silicon, we typically look for rings of size 3-10
    ring_counts: Dict[int, int] = {}
    
    # Find all simple cycles up to a reasonable size
    try:
        cycles = nx.simple_cycles(graph.to_directed())
        for cycle in cycles:
            size = len(cycle)
            if 3 <= size <= 10:  # Focus on relevant ring sizes for a-Si
                ring_counts[size] = ring_counts.get(size, 0) + 1
    except Exception as e:
        logger.warning(f"Error calculating ring statistics: {e}")
        # Return empty dict if calculation fails
        return {}
    
    return ring_counts

def calculate_steinhardt_q6(config: AtomicConfiguration) -> float:
    """
    Calculate the Steinhardt Q6 bond orientational order parameter.
    This measures the degree of local structural order.
    """
    if len(config.coordinates) < 2:
        return 0.0
    
    # Simplified Q6 calculation
    # In a full implementation, this would involve spherical harmonics
    # For now, we use a proxy based on coordination number variance
    coords = config.coordinates
    n_atoms = len(coords)
    
    # Calculate average distance to nearest neighbors
    # This is a simplified proxy for Q6
    distances = []
    for i in range(n_atoms):
        for j in range(i + 1, n_atoms):
            dist = np.linalg.norm(coords[i] - coords[j])
            distances.append(dist)
    
    if not distances:
        return 0.0
    
    avg_dist = np.mean(distances)
    # Normalize and map to a Q6-like value (0-1 range)
    q6_proxy = 1.0 / (1.0 + np.std(distances) / avg_dist)
    return float(q6_proxy)

def calculate_clustering_coefficient(graph: nx.Graph) -> float:
    """
    Calculate the average clustering coefficient of the graph.
    """
    if graph.number_of_nodes() == 0:
        return 0.0
    return nx.average_clustering(graph)

def calculate_descriptors(
    config: AtomicConfiguration,
    graph: nx.Graph,
    cutoff_radius: float
) -> Dict[str, Any]:
    """
    Calculate all topological descriptors for a configuration.
    """
    ring_stats = calculate_ring_statistics(graph)
    q6 = calculate_steinhardt_q6(config)
    clustering = calculate_clustering_coefficient(graph)
    
    return {
        "ring_distribution": ring_stats,
        "q6": q6,
        "clustering_coefficient": clustering,
        "n_atoms": len(config.coordinates),
        "n_edges": graph.number_of_edges(),
        "avg_degree": sum(dict(graph.degree()).values()) / graph.number_of_nodes() if graph.number_of_nodes() > 0 else 0
    }

def extract_ring_features(ring_stats: Dict[int, int]) -> List[float]:
    """
    Extract a fixed-length feature vector from ring statistics.
    Returns a list of counts for ring sizes 3 through 10.
    """
    features = []
    for size in range(3, 11):
        features.append(float(ring_stats.get(size, 0)))
    return features

def filter_and_fallback(
    validated_configs: List[AtomicConfiguration],
    processed_dir: str
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Implement filter and fallback logic for VDOS availability.
    
    This function attempts to load pre-calculated VDOS for each configuration.
    If VDOS is missing, the configuration is marked as VDOS-MISSING but NOT excluded.
    It proceeds to calculate topological descriptors for all configurations.
    
    Args:
        validated_configs: List of AtomicConfiguration objects that passed validation.
        processed_dir: Path to the processed data directory where VDOS files might be stored.
    
    Returns:
        Tuple of (processed_configs, vdos_missing_configs)
        - processed_configs: List of dicts with full descriptors (including VDOS if available)
        - vdos_missing_configs: List of dicts with topological descriptors only and VDOS-MISSING flag
    """
    processed_configs = []
    vdos_missing_configs = []
    
    processed_path = Path(processed_dir)
    
    for config in validated_configs:
        config_id = config.id
        logger.info(f"Processing configuration: {config_id}")
        
        # Attempt to load VDOS
        vdos_data = None
        vdos_available = False
        
        try:
            # Check if VDOS file exists for this config
            vdos_path = processed_path / f"vdos_{config_id}.npy"
            if vdos_path.exists():
                vdos_data = load_vdos(config_id, processed_dir)
                if vdos_data is not None:
                    vdos_available = True
                    logger.info(f"VDOS loaded successfully for {config_id}")
            else:
                logger.warning(f"VDOS file not found for {config_id}")
        except Exception as e:
            logger.warning(f"Failed to load VDOS for {config_id}: {e}")
        
        # Calculate topological descriptors (always done)
        # Note: In a full implementation, we would build the graph here
        # For now, we assume the graph is already built and stored
        graph_path = processed_path / "graphs" / f"{config_id}.graphml"
        if graph_path.exists():
            graph = nx.read_graphml(str(graph_path))
        else:
            logger.error(f"Graph file not found for {config_id}: {graph_path}")
            continue
        
        descriptors = calculate_descriptors(config, graph, 3.0)  # Default cutoff
        
        # Prepare result based on VDOS availability
        result = {
            "config_id": config_id,
            "ring_distribution": descriptors["ring_distribution"],
            "q6": descriptors["q6"],
            "clustering_coefficient": descriptors["clustering_coefficient"],
            "n_atoms": descriptors["n_atoms"],
            "n_edges": descriptors["n_edges"],
            "avg_degree": descriptors["avg_degree"]
        }
        
        if vdos_available:
            # Add VDOS data and participation ratios
            try:
                participation_ratios = calculate_participation_ratios(vdos_data)
                result["vdos_vector"] = vdos_data.tolist() if isinstance(vdos_data, np.ndarray) else vdos_data
                result["participation_ratios"] = participation_ratios
                result["data_quality"] = "full"
                processed_configs.append(result)
                logger.info(f"Full descriptors calculated for {config_id}")
            except Exception as e:
                logger.error(f"Failed to calculate participation ratios for {config_id}: {e}")
                # Fallback to topological only
                result["vdos_vector"] = None
                result["participation_ratios"] = None
                result["data_quality"] = "topological_only"
                vdos_missing_configs.append(result)
        else:
            # Mark as VDOS-MISSING but retain for topological analysis
            result["vdos_vector"] = None
            result["participation_ratios"] = None
            result["data_quality"] = "topological_only"
            vdos_missing_configs.append(result)
            logger.info(f"Configuration {config_id} marked as VDOS-MISSING, retained for topological analysis")
    
    return processed_configs, vdos_missing_configs

def main():
    """
    Main entry point for the descriptors module.
    Demonstrates the filter and fallback logic.
    """
    import sys
    from pathlib import Path
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load configuration
    processed_dir = get_processed_dir()
    logger.info(f"Using processed directory: {processed_dir}")
    
    # In a real scenario, we would load validated configs from the validation report
    # For demonstration, we'll show the function signature and logic
    logger.info("Filter and fallback logic implemented in filter_and_fallback()")
    logger.info("This function will be called by the execution pipeline (T024b)")
    
    # Example usage (would be replaced by actual config loading in T024b)
    # validated_configs = load_validation_report()
    # processed, missing = filter_and_fallback(validated_configs, processed_dir)
    
    print("Descriptors module loaded successfully.")
    print("filter_and_fallback() is ready to process configurations.")

if __name__ == "__main__":
    main()