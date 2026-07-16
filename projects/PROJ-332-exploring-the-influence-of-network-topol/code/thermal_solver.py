import numpy as np
import networkx as nx
from scipy import sparse
from scipy.sparse.linalg import spsolve, LinearOperator
from typing import Dict, Any, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

def calculate_fuchs_sondheimer_factor(d: float, l: float, bulk_k: float) -> float:
    """
    Calculate Fuchs-Sondheimer size-correction factor.
    Formula: f = 1 - (3/8)*(lambda/d)*(1-p)  [Simplified for thin wires]
    Using default lambda=10nm, p=0.5 if not specified in a more complex version.
    Here we assume the factor is applied to the conductivity.
    
    For d < 100nm, apply correction.
    """
    if d >= 100:
        return 1.0
    
    # Default parameters as per spec
    lam = 10.0  # mean free path in nm
    p_spec = 0.5  # specularity parameter
    
    # Simplified FS factor for nanowires
    # k_eff = k_bulk * (1 - 3/8 * (lam/d) * (1-p))
    factor = 1.0 - (3.0/8.0) * (lam / d) * (1.0 - p_spec)
    
    return max(0.0, factor)  # Ensure non-negative

def assign_thermal_resistance(G: nx.Graph, d: float, l: float, bulk_k: float, fs_factor: float) -> None:
    """
    Assign thermal resistance to edges based on geometry and material.
    R = l / (k * A) where A = pi * (d/2)^2
    """
    area = np.pi * (d / 2.0) ** 2
    k_eff = bulk_k * fs_factor
    
    for u, v in G.edges():
        # Assume edge length is normalized to 1 for graph topology, 
        # or use a characteristic length. Here we assume unit length for topology.
        # If physical length is needed, it should be stored in edge attributes.
        R = 1.0 / (k_eff * area)
        G.edges[u, v]['R'] = R

def build_edge_resistances(G: nx.Graph, d: float, l: float, bulk_k: float, fs_factor: float) -> None:
    """Wrapper to assign resistances to the graph."""
    assign_thermal_resistance(G, d, l, bulk_k, fs_factor)

def solve_kirchhoff_heat_flow(G: nx.Graph, N: int, d: float, l: float, bulk_k: float, fs_factor: float) -> float:
    """
    Solve Kirchhoff heat flow to find effective conductivity.
    Returns effective conductivity in W/(m·K).
    """
    if not nx.is_connected(G):
        return 0.0
    
    # Assign resistances
    build_edge_resistances(G, d, l, bulk_k, fs_factor)
    
    # Build conductance matrix (Laplacian)
    # G is undirected, weights are 1/R
    n = G.number_of_nodes()
    L = sparse.lil_matrix((n, n))
    
    for u, v, data in G.edges(data=True):
        R = data.get('R', 1.0)
        if R == 0:
            R = 1e-9  # Zero-resistance clamping to prevent division by zero
        G_val = 1.0 / R
        
        L[u, u] += G_val
        L[v, v] += G_val
        L[u, v] -= G_val
        L[v, u] -= G_val
    
    L = L.tocsr()
    
    # Apply boundary conditions: T[0] = 1, T[N-1] = 0 (or similar)
    # Fix node 0 and node n-1
    fixed_nodes = [0, n-1]
    free_nodes = [i for i in range(n) if i not in fixed_nodes]
    
    if len(free_nodes) == 0:
        # Only 2 nodes
        T = np.zeros(n)
        T[0] = 1.0
        T[n-1] = 0.0
    else:
        # Solve for free nodes
        # L_ff * T_f = - L_fb * T_b
        L_ff = L[np.ix_(free_nodes, free_nodes)]
        L_fb = L[np.ix_(free_nodes, fixed_nodes)]
        T_b = np.zeros(len(fixed_nodes))
        T_b[0] = 1.0  # T[0] = 1
        
        # Solve
        try:
            T_f = spsolve(L_ff, -L_fb @ T_b)
        except Exception as e:
            logger.warning(f"Sparse solve failed: {e}, using pseudo-inverse")
            T_f = np.linalg.lstsq(L_ff.toarray(), -L_fb.toarray() @ T_b, rcond=None)[0]
        
        T = np.zeros(n)
        for i, node in enumerate(free_nodes):
            T[node] = T_f[i]
        T[fixed_nodes[0]] = 1.0
        T[fixed_nodes[1]] = 0.0
    
    # Calculate total current (heat flow) from node 0
    I_total = 0.0
    for v in G.neighbors(0):
        R = G.edges[0, v].get('R', 1.0)
        if R == 0:
            R = 1e-9
        I_total += (T[0] - T[v]) / R
    
    # Effective conductivity: k_eff = I_total * L_total / (A * delta_T)
    # Assume L_total = 1 (normalized), A = pi*(d/2)^2, delta_T = 1
    A = np.pi * (d / 2.0) ** 2
    k_eff = I_total / A
    
    return k_eff

def calculate_effective_conductivity(G: nx.Graph, d: float, l: float, bulk_k: float, fs_factor: float) -> float:
    """Wrapper for solve_kirchhoff_heat_flow."""
    return solve_kirchhoff_heat_flow(G, G.number_of_nodes(), d, l, bulk_k, fs_factor)
