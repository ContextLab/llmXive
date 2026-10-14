"""
persistence_utils.py
Topological Data Analysis utilities for molecular graphs.
Implements shortest-path filtration and persistence image vectorization.
"""

import logging
from typing import List, Tuple, Optional, Dict, Any, Union
import numpy as np
import networkx as nx
import gudhi
import sys

logger = logging.getLogger(__name__)

def build_shortest_path_filtration(graph: nx.Graph) -> np.ndarray:
    """
    Compute the all-pairs shortest-path distance matrix for the graph.
    This matrix serves as the filtration basis for the Rips complex.
    """
    nodes = list(graph.nodes())
    n = len(nodes)
    if n == 0:
        return np.zeros((0, 0))

    dist_matrix = np.zeros((n, n), dtype=np.float64)
    # Compute all-pairs shortest paths
    lengths = nx.all_pairs_dijkstra_path_length(graph)
    
    node_to_idx = {node: i for i, node in enumerate(nodes)}
    for source_node, source_lengths in lengths:
        u = node_to_idx[source_node]
        for target_node, dist in source_lengths.items():
            v = node_to_idx[target_node]
            dist_matrix[u, v] = dist
    
    return dist_matrix

def compute_persistence_diagram(dist_matrix: np.ndarray) -> List[Tuple[float, float]]:
    """
    Compute the persistence diagram using GUDHI.
    Constructs a SimplexTree from the distance matrix.
    """
    n = dist_matrix.shape[0]
    if n == 0:
        return []

    # Create an empty SimplexTree
    st = gudhi.SimplexTree()
    
    # Add 0-simplices (nodes)
    for i in range(n):
        st.insert([i], filtration=0.0)
    
    # Add 1-simplices (edges) based on shortest-path distances
    for i in range(n):
        for j in range(i + 1, n):
            st.insert([i, j], filtration=dist_matrix[i, j])
    
    # Compute persistence
    persistence = st.persistence()
    
    # Return only finite persistence pairs (birth, death)
    # GUDHI returns (dimension, (birth, death))
    diagram = [p[1] for p in persistence if p[1][1] != float('inf')]
    return diagram

def vectorize(diagram: List[Tuple[float, float]], resolution: int = 10, sigma: float = 0.1) -> np.ndarray:
    """
    Vectorize a persistence diagram into a persistence image.
    
    The image is a 2D grid where each point (b, d) in the diagram contributes 
    a Gaussian kernel weighted by its persistence (d - b).
    
    Grid Range: [0, 10] for both birth and death, as molecular graph diameters 
    are typically small.
    """
    if not diagram:
        return np.zeros((resolution, resolution))

    # Define grid
    grid_min, grid_max = 0.0, 10.0
    x = np.linspace(grid_min, grid_max, resolution)
    y = np.linspace(grid_min, grid_max, resolution)
    X, Y = np.meshgrid(x, y)

    image = np.zeros((resolution, resolution))

    for birth, death in diagram:
        # Weight is the persistence
        weight = death - birth
        if weight <= 0:
            continue
        
        # Gaussian kernel: w * exp(-((x-b)^2 + (y-d)^2) / (2 * sigma^2))
        dist_sq = (X - birth)**2 + (Y - death)**2
        image += weight * np.exp(-dist_sq / (2 * sigma**2))

    return image

def handle_empty_diagram(resolution: int = 10) -> np.ndarray:
    """Handle empty persistence diagrams by returning a zero vector."""
    return np.zeros((resolution, resolution))
