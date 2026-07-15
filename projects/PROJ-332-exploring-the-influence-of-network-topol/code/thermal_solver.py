import numpy as np
import networkx as nx
from scipy import sparse
from scipy.sparse.linalg import spsolve, LinearOperator
from typing import Dict, Any, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

def calculate_fuchs_sondheimer_factor(d: float, lambda_bulk: float, p_specular: float) -> float:
    """
    Calculate the Fuchs-Sondheimer size-correction factor.
    
    Formula: k/k_bulk = 1 - (3/8) * (1-p) * (lambda/d)
    
    Args:
        d: Wire diameter in nm
        lambda_bulk: Bulk mean free path in nm
        p_specular: Specularity parameter (0 = diffuse, 1 = specular)
        
    Returns:
        Correction factor (ratio of size-corrected to bulk conductivity)
    """
    if d <= 0:
        raise ValueError("Diameter must be positive")
    if lambda_bulk <= 0:
        raise ValueError("Mean free path must be positive")
    if not (0 <= p_specular <= 1):
        raise ValueError("Specularity parameter must be between 0 and 1")
    
    # Fuchs-Sondheimer approximation for thin wires
    # Simplified formula for d < 100nm
    if d < 100:
        factor = 1.0 - (3.0/8.0) * (1.0 - p_specular) * (lambda_bulk / d)
        # Clamp to reasonable bounds
        factor = max(0.1, min(1.0, factor))
    else:
        factor = 1.0
    
    logger.debug(f"Fuchs-Sondheimer factor: d={d}, lambda={lambda_bulk}, p={p_specular} -> {factor:.4f}")
    return factor

def assign_thermal_resistance(G: nx.Graph, bulk_k: float, d: float, l: float, fs_factor: float) -> Dict[Tuple[int, int], float]:
    """
    Assign thermal resistance to each edge based on geometry and material.
    
    R = l / (k * A)
    where A = pi * (d/2)^2
    
    Args:
        G: NetworkX graph
        bulk_k: Bulk thermal conductivity (W/mK)
        d: Wire diameter (nm)
        l: Wire length (nm)
        fs_factor: Fuchs-Sondheimer correction factor
        
    Returns:
        Dictionary mapping edges to thermal resistance (K/W)
    """
    resistances = {}
    
    # Convert units: nm -> m
    d_m = d * 1e-9
    l_m = l * 1e-9
    
    # Cross-sectional area
    A = np.pi * (d_m / 2) ** 2
    
    # Effective conductivity
    k_eff = bulk_k * fs_factor
    
    # Calculate resistance for each edge
    for u, v in G.edges():
        # Assume edge length is proportional to l (simplified)
        # In a real model, this would depend on node positions
        R = l_m / (k_eff * A)
        
        # Zero-resistance clamping to prevent division by zero
        R = max(R, 1e-12)
        resistances[(u, v)] = R
        
    return resistances

def build_edge_resistances(G: nx.Graph, resistances: Dict[Tuple[int, int], float]) -> sparse.csr_matrix:
    """
    Build the conductance matrix from edge resistances.
    
    Args:
        G: NetworkX graph
        resistances: Dictionary of edge resistances
        
    Returns:
        Sparse conductance matrix
    """
    n = len(G)
    conductances = {}
    
    for (u, v), R in resistances.items():
        G_val = 1.0 / R
        conductances[(u, v)] = G_val
        conductances[(v, u)] = G_val
    
    # Build sparse matrix
    rows = []
    cols = []
    data = []
    
    for i in range(n):
        rows.append(i)
        cols.append(i)
        data.append(sum(conductances.get((i, j), 0) for j in G.neighbors(i)))
    
    for (u, v), G_val in conductances.items():
        if u != v:
            rows.append(u)
            cols.append(v)
            data.append(-G_val)
    
    K = sparse.csr_matrix((data, (rows, cols)), shape=(n, n))
    return K

def solve_kirchhoff_heat_flow(K: sparse.csr_matrix, T_hot: np.ndarray, T_cold: np.ndarray) -> np.ndarray:
    """
    Solve the Kirchhoff heat flow equations.
    
    K * T = Q
    where T is temperature vector, Q is heat source vector.
    
    Args:
        K: Conductance matrix
        T_hot: Temperatures at hot nodes
        T_cold: Temperatures at cold nodes
        
    Returns:
        Temperature vector
    """
    n = K.shape[0]
    Q = np.zeros(n)
    T = np.zeros(n)
    
    # Apply boundary conditions
    hot_nodes = np.where(T_hot > 0)[0]
    cold_nodes = np.where(T_cold > 0)[0]
    
    # Remove rows/cols for fixed temperatures
    free_nodes = np.setdiff1d(np.arange(n), np.concatenate([hot_nodes, cold_nodes]))
    
    if len(free_nodes) == 0:
        T[hot_nodes] = T_hot[hot_nodes]
        T[cold_nodes] = T_cold[cold_nodes]
        return T
    
    K_free = K[free_nodes][:, free_nodes]
    Q_free = Q[free_nodes]
    
    # Adjust for boundary conditions
    for i, node in enumerate(free_nodes):
        for j in hot_nodes:
            Q_free[i] -= K[node, j] * T_hot[j]
        for j in cold_nodes:
            Q_free[i] -= K[node, j] * T_cold[j]
    
    try:
        T_free = spsolve(K_free, Q_free)
    except Exception as e:
        logger.warning(f"Sparse solver failed: {e}, using pseudo-inverse")
        T_free = np.linalg.lstsq(K_free.toarray(), Q_free, rcond=None)[0]
    
    T[free_nodes] = T_free
    T[hot_nodes] = T_hot[hot_nodes]
    T[cold_nodes] = T_cold[cold_nodes]
    
    return T

def calculate_effective_conductivity(G: nx.Graph, bulk_k: float, d: float, l: float, fs_factor: float) -> float:
    """
    Calculate effective thermal conductivity of the network.
    
    Args:
        G: NetworkX graph
        bulk_k: Bulk thermal conductivity (W/mK)
        d: Wire diameter (nm)
        l: Wire length (nm)
        fs_factor: Fuchs-Sondheimer correction factor
        
    Returns:
        Effective thermal conductivity (W/mK)
    """
    if len(G) < 2:
        logger.warning("Graph too small for conductivity calculation")
        return 0.0
    
    if not nx.is_connected(G):
        logger.warning("Graph disconnected, returning 0 conductivity")
        return 0.0
    
    try:
        # Assign resistances
        resistances = assign_thermal_resistance(G, bulk_k, d, l, fs_factor)
        
        # Build conductance matrix
        K = build_edge_resistances(G, resistances)
        
        # Apply boundary conditions (hot at one end, cold at other)
        # Find two nodes that are furthest apart
        try:
            # Use BFS to find furthest node from node 0
            lengths = nx.single_source_shortest_path_length(G, 0)
            max_node = max(lengths, key=lengths.get)
            hot_node = 0
            cold_node = max_node
        except:
            hot_node = 0
            cold_node = len(G) - 1
        
        T_hot = np.zeros(len(G))
        T_cold = np.zeros(len(G))
        T_hot[hot_node] = 1.0  # 1 K temperature difference
        T_cold[cold_node] = 0.0
        
        # Solve for temperatures
        T = solve_kirchhoff_heat_flow(K, T_hot, T_cold)
        
        # Calculate total heat flow
        Q_total = 0.0
        for neighbor in G.neighbors(hot_node):
            R = resistances.get((hot_node, neighbor), 1e-12)
            Q_total += (T[hot_node] - T[neighbor]) / R
        
        # Effective conductivity: Q = k_eff * A * dT / L
        # k_eff = Q * L / (A * dT)
        d_m = d * 1e-9
        l_m = l * 1e-9
        A = np.pi * (d_m / 2) ** 2
        dT = 1.0  # K
        
        # Estimate network length
        try:
            L_eff = nx.shortest_path_length(G, hot_node, cold_node) * l_m
        except:
            L_eff = l_m
        
        if L_eff <= 0 or A <= 0:
            return 0.0
        
        k_eff = Q_total * L_eff / (A * dT)
        
        # Clamp to reasonable bounds
        k_eff = max(0.0, min(k_eff, 10000.0))
        
        return k_eff
        
    except Exception as e:
        logger.error(f"Conductivity calculation failed: {e}")
        return 0.0