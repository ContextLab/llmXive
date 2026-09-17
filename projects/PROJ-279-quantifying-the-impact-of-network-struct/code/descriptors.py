import logging
import networkx as nx
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from collections import Counter
from models.atomic_config import AtomicConfiguration

logger = logging.getLogger(__name__)

def calculate_ring_statistics(G: nx.Graph) -> Dict[int, int]:
    """
    Calculate the distribution of ring sizes in the graph.
    Returns a dictionary mapping ring size to count.
    Only considers rings of size 3 to 10.
    """
    if G.number_of_nodes() == 0:
        return {i: 0 for i in range(3, 11)}

    try:
        # NetworkX simple_cycles is for directed graphs.
        # For undirected graphs, we need a different approach.
        # We use the `cycle_basis` which finds a basis of cycles.
        # However, cycle_basis does not guarantee finding ALL rings (specifically smallest rings).
        # For accurate ring statistics in amorphous materials, we often need the "shortest path"
        # based ring identification or specifically the "smallest set of smallest rings" (SSSR).
        # NetworkX's cycle_basis is an approximation for SSSR in undirected graphs.
        
        # To be more robust for a-Si, we will iterate through nodes and find shortest cycles
        # that pass through them, filtering for unique rings.
        # However, for performance on large graphs, SSSR (cycle_basis) is the standard approximation
        # used in many topology analyses unless exact smallest rings are strictly required.
        # Given the constraints, we will use cycle_basis but ensure we count sizes correctly.
        
        cycles = nx.cycle_basis(G)
        
        ring_counts = Counter()
        for cycle in cycles:
            size = len(cycle)
            if 3 <= size <= 10:
                ring_counts[size] += 1
        
        # Ensure all keys 3-10 exist
        result = {i: ring_counts[i] for i in range(3, 11)}
        return result
        
    except Exception as e:
        logger.warning(f"Error calculating ring statistics: {e}")
        return {i: 0 for i in range(3, 11)}

def calculate_steinhardt_q6(config: AtomicConfiguration) -> float:
    """
    Calculate the Steinhardt bond-orientational order parameter Q6.
    Q6 measures the degree of local structural order.
    High Q6 indicates crystalline-like order, low Q6 indicates amorphous/liquid.
    
    Formula: Q_l = [ (4*pi / (2*l + 1)) * sum_{m=-l}^{l} |Q_lm|^2 ]^(1/2)
    where Q_lm = (1/N_b) * sum_{j=1}^{N_b} Y_lm(theta_j, phi_j)
    """
    if config.coordinates is None or config.coordinates.shape[0] < 2:
        return 0.0
    
    positions = config.coordinates
    N = len(positions)
    
    # Determine neighbors based on cutoff if not provided, or use a standard cutoff for Si
    # Assuming a cutoff is available or derived from config. 
    # For this implementation, we assume a standard Si cutoff of ~3.0 Angstroms if not specified.
    # In a real pipeline, this should come from config or environment.
    cutoff = getattr(config, 'cutoff_radius', 3.0) 
    
    # Precompute distance matrix (efficient for moderate N)
    # For very large N, a KDTree should be used.
    diff = positions[:, np.newaxis, :] - positions[np.newaxis, :, :]
    dists = np.sqrt(np.sum(diff**2, axis=2))
    
    # Build adjacency based on cutoff (excluding self)
    neighbor_indices = []
    for i in range(N):
        # Find neighbors within cutoff, excluding self (dist > 0)
        neighbors = np.where((dists[i] < cutoff) & (dists[i] > 1.0))[0]
        neighbor_indices.append(neighbors)
    
    # Spherical harmonics calculation
    # We need to calculate Q6 for the whole system (global Q6)
    # Or average local q6. The task asks for "Steinhardt Parameters (Q6)".
    # Usually, global Q6 is the metric for the whole structure.
    
    # Q_lm = (1/N_b) * sum Y_lm
    # Global Q6 = sqrt( sum |Q_lm|^2 * 4pi / (2l+1) )
    
    # We will compute the average of local q6 vectors to get global Q6?
    # Standard definition: Q_l = sqrt( 4pi / (2l+1) * sum_m |Q_lm|^2 )
    # where Q_lm = (1/N_b) * sum_{j=1}^{N_b} Y_lm(theta_j, phi_j)
    # N_b is total number of bonds.
    
    l = 6
    Q_lm = np.zeros(2 * l + 1, dtype=complex)
    total_bonds = 0
    
    # Precompute spherical harmonics for efficiency? 
    # Or just iterate. For N=1000, O(N^2) is fine.
    
    for i in range(N):
        neighbors = neighbor_indices[i]
        if len(neighbors) == 0:
            continue
        
        for j in neighbors:
            # Vector from i to j
            vec = positions[j] - positions[i]
            dist = np.linalg.norm(vec)
            if dist < 1e-8:
                continue
            
            # Spherical coordinates
            theta = np.arccos(np.clip(vec[2] / dist, -1.0, 1.0))
            phi = np.arctan2(vec[1], vec[0])
            
            # Calculate Y_lm for l=6
            # We can use scipy.special.sph_harm if available, but to avoid heavy deps if not installed:
            # Implementing Y_lm manually or using numpy/scipy.
            # Assuming scipy is available in the environment (common for ASE/SciKit).
            # If not, we can approximate or use a simplified version.
            # Let's assume scipy is present as per typical scientific stack.
            from scipy.special import sph_harm
            
            for m in range(-l, l + 1):
                Y_lm = sph_harm(m, l, phi, theta)
                Q_lm[m + l] += Y_lm
            total_bonds += 1
    
    if total_bonds == 0:
        return 0.0
    
    # Normalize Q_lm
    Q_lm /= total_bonds
    
    # Calculate Q6
    sum_sq = np.sum(np.abs(Q_lm)**2)
    Q6 = np.sqrt((4 * np.pi / (2 * l + 1)) * sum_sq)
    
    return float(Q6)

def calculate_clustering_coefficient(G: nx.Graph) -> float:
    """
    Calculate the average clustering coefficient of the graph.
    This measures the degree to which nodes in a graph tend to cluster together.
    """
    if G.number_of_nodes() == 0:
        return 0.0
    
    try:
        return nx.average_clustering(G)
    except Exception as e:
        logger.warning(f"Error calculating clustering coefficient: {e}")
        return 0.0

def calculate_descriptors(config: AtomicConfiguration, G: nx.Graph) -> Dict[str, Any]:
    """
    Calculate all topological descriptors for a configuration.
    Returns a dictionary with:
      - ring_statistics: Dict[int, int]
      - steinhardt_q6: float
      - clustering_coefficient: float
    """
    ring_stats = calculate_ring_statistics(G)
    q6 = calculate_steinhardt_q6(config)
    cc = calculate_clustering_coefficient(G)
    
    return {
        "ring_statistics": ring_stats,
        "steinhardt_q6": q6,
        "clustering_coefficient": cc
    }

def extract_ring_features(ring_stats: Dict[int, int]) -> List[float]:
    """
    Flatten ring statistics into a feature vector for ML.
    Returns a list of counts for ring sizes 3 to 10.
    """
    return [ring_stats.get(i, 0) for i in range(3, 11)]

def main():
    """
    Main entry point for testing descriptors calculation.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Descriptors module loaded successfully.")
    logger.info("Functions available: calculate_ring_statistics, calculate_steinhardt_q6, calculate_clustering_coefficient")

if __name__ == "__main__":
    main()
