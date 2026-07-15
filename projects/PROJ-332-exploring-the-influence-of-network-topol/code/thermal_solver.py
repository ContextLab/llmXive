import numpy as np
import networkx as nx
from scipy import sparse
from scipy.sparse.linalg import spsolve, LinearOperator
from typing import Dict, Any, Tuple, Optional
import logging

from material_db import get_material_conductivity

logger = logging.getLogger(__name__)

def calculate_fuchs_sondheimer_factor(d: float, lambda_mfp: float = 10.0, p: float = 0.5) -> float:
    """
    Calculate Fuchs-Sondheimer size-correction factor.
    Formula: F = 1 - (3/8)*(lambda/d)*(1-p) for d < 100nm
    """
    if d >= 100.0:
        return 1.0
    
    factor = 1.0 - (3.0/8.0) * (lambda_mfp / d) * (1.0 - p)
    # Clamp to [0, 1]
    return max(0.0, min(1.0, factor))

def assign_thermal_resistance(graph: nx.Graph, material: str, 
                              d: float, l: float, 
                              lambda_mfp: float = 10.0, p: float = 0.5) -> Dict[tuple, float]:
    """
    Assign thermal resistance to each edge based on material properties and geometry.
    R = l / (k * A) where A = pi*(d/2)^2
    """
    bulk_k = get_material_conductivity(material)
    fs_factor = calculate_fuchs_sondheimer_factor(d, lambda_mfp, p)
    effective_k = bulk_k * fs_factor
    
    # Cross-sectional area
    area = np.pi * (d / 2.0) ** 2
    
    resistance_map = {}
    for u, v in graph.edges():
        # Assume edge length is proportional to node distance (simplified)
        edge_length = l  # Simplified: all wires have length l
        resistance = edge_length / (effective_k * area)
        
        # Clamp to prevent division by zero
        resistance = max(resistance, 1e-10)
        
        resistance_map[(u, v)] = resistance
        resistance_map[(v, u)] = resistance  # Bidirectional
    
    return resistance_map

def build_edge_resistances(graph: nx.Graph, resistance_map: Dict[tuple, float]) -> sparse.csr_matrix:
    """Build conductance matrix from resistance map."""
    n = graph.number_of_nodes()
    node_map = {node: i for i, node in enumerate(graph.nodes())}
    
    # Build sparse conductance matrix
    rows, cols, data = [], [], []
    
    for u, v in graph.edges():
        i, j = node_map[u], node_map[v]
        R = resistance_map.get((u, v), 1e10)
        G = 1.0 / R if R > 0 else 0.0
        
        rows.extend([i, i, j, j])
        cols.extend([i, j, i, j])
        data.extend([G, -G, -G, G])
    
    L = sparse.csr_matrix((data, (rows, cols)), shape=(n, n))
    return L

def solve_kirchhoff_heat_flow(graph: nx.Graph, L: sparse.csr_matrix, 
                              T_hot: float = 300.0, T_cold: float = 290.0) -> float:
    """
    Solve Kirchhoff's heat flow equations.
    Returns effective thermal conductivity.
    """
    n = graph.number_of_nodes()
    
    if n == 0:
        return 0.0
    
    # Check connectivity
    if not nx.is_connected(graph):
        logger.warning("Graph disconnected; conductivity set to 0.0")
        return 0.0
    
    # Identify boundary nodes (simplified: first and last node in sorted order)
    nodes = sorted(graph.nodes())
    hot_node = nodes[0]
    cold_node = nodes[-1]
    
    hot_idx = list(graph.nodes()).index(hot_node)
    cold_idx = list(graph.nodes()).index(cold_node)
    
    # Set boundary conditions
    # Modify L matrix for Dirichlet BCs
    L_modified = L.copy()
    L_modified[hot_idx, :] = 0
    L_modified[hot_idx, hot_idx] = 1
    L_modified[cold_idx, :] = 0
    L_modified[cold_idx, cold_idx] = 1
    
    # RHS: temperatures at boundaries
    b = np.zeros(n)
    b[hot_idx] = T_hot
    b[cold_idx] = T_cold
    
    # Solve
    try:
        T = spsolve(L_modified, b)
    except Exception as e:
        logger.error(f"Sparse solver failed: {e}")
        return 0.0
    
    # Calculate heat flow out of hot node
    Q = 0.0
    for v in graph.neighbors(hot_node):
        v_idx = list(graph.nodes()).index(v)
        R = 1.0 / L[hot_idx, v_idx] if L[hot_idx, v_idx] > 0 else 1e10
        Q += (T[hot_idx] - T[v_idx]) / R
    
    # Effective conductivity (simplified)
    # k_eff = Q * L / (A * delta_T)
    # We return Q as a proxy for conductivity (normalized)
    return Q

def calculate_effective_conductivity(graph: nx.Graph, material: str, 
                                     d: float, l: float) -> float:
    """
    Main function to calculate effective thermal conductivity.
    """
    if graph.number_of_nodes() <= 1:
        logger.warning("Graph has too few nodes; conductivity = 0.0")
        return 0.0
    
    # Assign resistances
    resistance_map = assign_thermal_resistance(graph, material, d, l)
    
    # Build conductance matrix
    L = build_edge_resistances(graph, resistance_map)
    
    # Solve
    conductivity = solve_kirchhoff_heat_flow(graph, L)
    
    return conductivity
