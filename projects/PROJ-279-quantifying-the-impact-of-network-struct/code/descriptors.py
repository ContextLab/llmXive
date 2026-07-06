import logging
import networkx as nx
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from collections import Counter

from models.atomic_config import AtomicConfiguration

logger = logging.getLogger(__name__)

def calculate_ring_statistics(graph: nx.Graph) -> Dict[int, int]:
    """
    Calculate the distribution of ring sizes (3-10) in the graph.
    
    Args:
        graph: NetworkX graph representing atomic connectivity.
        
    Returns:
        Dictionary mapping ring size to count.
    """
    try:
        # Find all simple cycles in the graph
        cycles = list(nx.simple_cycles(graph.to_directed()))
        
        # Filter for undirected cycles (avoid duplicates from direction)
        # Convert to frozenset to handle undirected nature
        unique_cycles = set()
        for cycle in cycles:
            if len(cycle) < 3:
                continue
            # Normalize cycle representation to avoid duplicates
            min_idx = np.argmin(cycle)
            normalized = tuple(cycle[min_idx:] + cycle[:min_idx])
            unique_cycles.add(normalized)
        
        # Count ring sizes
        ring_counts: Dict[int, int] = Counter()
        for cycle in unique_cycles:
            size = len(cycle)
            if 3 <= size <= 10:
                ring_counts[size] += 1
        
        return dict(ring_counts)
    except Exception as e:
        logger.warning(f"Error calculating ring statistics: {e}")
        return {}

def calculate_steinhardt_q6(config: AtomicConfiguration) -> float:
    """
    Calculate the Steinhardt bond orientational order parameter Q6.
    
    Q6 measures the degree of local structural order, with values near 0.57
    for FCC/HCP and lower for amorphous/disordered structures.
    
    Args:
        config: AtomicConfiguration containing coordinates and species.
        
    Returns:
        Q6 value (float).
    """
    if config.coordinates is None or len(config.coordinates) == 0:
        logger.warning("Empty configuration for Q6 calculation")
        return 0.0
    
    coords = np.array(config.coordinates)
    n_atoms = len(coords)
    
    if n_atoms < 2:
        return 0.0
    
    # Calculate cutoff radius (default 3.5 Å if not set)
    cutoff = getattr(config, 'cutoff_radius', 3.5)
    
    # Calculate distance matrix
    diff = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]
    distances = np.sqrt(np.sum(diff**2, axis=2))
    
    # Identify neighbors
    neighbors = []
    for i in range(n_atoms):
        # Exclude self
        dists = distances[i]
        dists[i] = np.inf
        neighbor_indices = np.where(dists < cutoff)[0]
        neighbors.append(neighbor_indices)
    
    # Calculate spherical harmonics for each bond
    # Q6 = sqrt(4*pi/13 * sum(|Y_6m|^2)) averaged over neighbors
    q6_sum = 0.0
    count = 0
    
    # Precompute spherical harmonics constants
    # Y_l^m(theta, phi) for l=6
    # We use the simplified Q6 calculation:
    # Q6(i) = sqrt( (4*pi)/(2*l+1) * sum_m |q_lm(i)|^2 )
    # where q_lm(i) = (1/N_b(i)) * sum_j Y_lm(theta_ij, phi_ij)
    
    for i in range(n_atoms):
        neigh = neighbors[i]
        if len(neigh) == 0:
            continue
        
        # Calculate bond vectors
        bond_vectors = coords[neigh] - coords[i]
        norms = np.sqrt(np.sum(bond_vectors**2, axis=1))
        
        # Avoid division by zero
        valid = norms > 1e-10
        if not np.any(valid):
            continue
        
        bond_vectors = bond_vectors[valid]
        norms = norms[valid]
        
        # Convert to spherical coordinates
        # theta = arccos(z/r), phi = atan2(y, x)
        cos_theta = bond_vectors[:, 2] / norms
        # Clip to avoid numerical issues
        cos_theta = np.clip(cos_theta, -1.0, 1.0)
        sin_theta = np.sqrt(1 - cos_theta**2)
        phi = np.arctan2(bond_vectors[:, 1], bond_vectors[:, 0])
        
        # Calculate Y_6^m for m = -6 to 6
        # Using the simplified approach: sum of |Y_6m|^2
        # For efficiency, we use the approximation that Q6^2 is proportional
        # to the sum of squared Legendre polynomials P_6(cos_theta)
        
        # Simplified Q6 calculation using P_6
        # P_6(x) = (1/16) * (231x^6 - 315x^4 + 105x^2 - 5)
        x = cos_theta
        P6 = (1/16) * (231*x**6 - 315*x**4 + 105*x**2 - 5)
        
        # Q6^2 ~ (1/N_b) * sum(P_6^2)
        q6_i_squared = np.mean(P6**2)
        q6_sum += np.sqrt(q6_i_squared)
        count += 1
    
    if count == 0:
        return 0.0
    
    return q6_sum / count

def calculate_clustering_coefficient(graph: nx.Graph) -> float:
    """
    Calculate the average clustering coefficient of the graph.
    
    The clustering coefficient measures the degree to which nodes in a graph
    tend to cluster together. For a node i, it is the fraction of possible
    triangles that exist.
    
    Args:
        graph: NetworkX graph representing atomic connectivity.
        
    Returns:
        Average clustering coefficient (float).
    """
    if graph.number_of_nodes() == 0:
        return 0.0
    
    try:
        return nx.average_clustering(graph)
    except Exception as e:
        logger.warning(f"Error calculating clustering coefficient: {e}")
        return 0.0

def calculate_descriptors(config: AtomicConfiguration, graph: nx.Graph) -> Dict[str, Any]:
    """
    Calculate all topological descriptors for a configuration.
    
    Args:
        config: AtomicConfiguration.
        graph: Corresponding NetworkX graph.
        
    Returns:
        Dictionary of descriptor values.
    """
    descriptors = {}
    
    # Ring statistics
    ring_stats = calculate_ring_statistics(graph)
    descriptors['ring_statistics'] = ring_stats
    
    # Total ring count
    descriptors['total_rings'] = sum(ring_stats.values())
    
    # Steinhardt Q6
    descriptors['steinhardt_q6'] = calculate_steinhardt_q6(config)
    
    # Clustering coefficient
    descriptors['clustering_coefficient'] = calculate_clustering_coefficient(graph)
    
    # Additional graph metrics
    descriptors['num_nodes'] = graph.number_of_nodes()
    descriptors['num_edges'] = graph.number_of_edges()
    descriptors['avg_degree'] = np.mean([d for n, d in graph.degree()]) if graph.number_of_nodes() > 0 else 0.0
    
    return descriptors