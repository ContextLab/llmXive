import numpy as np
import networkx as nx
from scipy import sparse
from scipy.sparse.linalg import spsolve, LinearOperator
from typing import Dict, Any, Tuple, Optional
import logging
from material_db import get_material_conductivity

logger = logging.getLogger(__name__)

def calculate_fuchs_sondheimer_factor(d: float, lambda_mfp: float = 10.0, p_specular: float = 0.5) -> float:
    """
    Calculate Fuchs-Sondheimer size-correction factor.
    Formula: F = 1 - (3/8) * (lambda/d) * (1 - p_specular)
    """
    if d <= 0:
        return 1.0
    ratio = lambda_mfp / d
    if ratio >= 1.0:
        return 0.1  # Lower bound to prevent zero
    factor = 1.0 - (3.0 / 8.0) * ratio * (1.0 - p_specular)
    return max(factor, 0.01)  # Clamp to prevent zero

def assign_thermal_resistance(graph: nx.Graph, bulk_k: float, d: float, l: float) -> Dict[Tuple[int, int], float]:
    """
    Assign thermal resistance to each edge based on bulk conductivity and geometry.
    R = l / (k * A) where A is cross-sectional area.
    """
    resistances = {}
    area = np.pi * (d / 2) ** 2

    for u, v in graph.edges():
        # Get edge length or use default l
        length = graph.edges[u, v].get('length', l)
        # Apply Fuchs-Sondheimer correction if d < 100nm
        if d < 100.0:
            fs_factor = calculate_fuchs_sondheimer_factor(d)
            effective_k = bulk_k * fs_factor
        else:
            effective_k = bulk_k

        # Zero-resistance clamping (T014)
        if effective_k <= 0:
            effective_k = 1e-10

        resistance = length / (effective_k * area)
        # Clamp minimum resistance to prevent division by zero
        resistance = max(resistance, 1e-10)
        resistances[(u, v)] = resistance
        resistances[(v, u)] = resistance

    return resistances

def build_edge_resistances(graph: nx.Graph, resistances: Dict[Tuple[int, int], float]) -> sparse.csr_matrix:
    """
    Build Laplacian-like matrix for heat flow.
    """
    nodes = list(graph.nodes())
    n = len(nodes)
    node_to_idx = {node: i for i, node in enumerate(nodes)}

    rows = []
    cols = []
    data = []

    for u, v in graph.edges():
        i, j = node_to_idx[u], node_to_idx[v]
        R = resistances.get((u, v), 1.0)
        if R <= 0:
            R = 1e-10
        G = 1.0 / R

        # Off-diagonal
        rows.extend([i, j])
        cols.extend([j, i])
        data.extend([-G, -G])

        # Diagonal (accumulate)
        rows.extend([i, j])
        cols.extend([i, j])
        data.extend([G, G])

    L = sparse.csr_matrix((data, (rows, cols)), shape=(n, n))
    return L

def solve_kirchhoff_heat_flow(graph: nx.Graph, resistances: Dict[Tuple[int, int], float], 
                              temp_source: int, temp_sink: int, T_source: float = 1.0, T_sink: float = 0.0) -> float:
    """
    Solve Kirchhoff heat flow equations.
    Returns total heat flow from source to sink.
    """
    nodes = list(graph.nodes())
    n = len(nodes)
    node_to_idx = {node: i for i, node in enumerate(nodes)}

    if temp_source not in node_to_idx or temp_sink not in node_to_idx:
        logger.warning("Source or sink node not in graph")
        return 0.0

    idx_source = node_to_idx[temp_source]
    idx_sink = node_to_idx[temp_sink]

    L = build_edge_resistances(graph, resistances)

    # Fix source and sink temperatures
    # Remove rows/cols for fixed nodes and adjust RHS
    free_nodes = [i for i in range(n) if i != idx_source and i != idx_sink]
    n_free = len(free_nodes)

    if n_free == 0:
        # Only source and sink
        R = resistances.get((temp_source, temp_sink), 1.0)
        if R <= 0:
            R = 1e-10
        return (T_source - T_sink) / R

    # Build reduced system
    L_free = L[np.ix_(free_nodes, free_nodes)]
    
    # RHS: contribution from fixed nodes
    rhs = np.zeros(n_free)
    for i, node_idx in enumerate(free_nodes):
        # Source contribution
        if L[node_idx, idx_source] != 0:
            rhs[i] -= L[node_idx, idx_source] * T_source
        # Sink contribution
        if L[node_idx, idx_sink] != 0:
            rhs[i] -= L[node_idx, idx_sink] * T_sink

    try:
        # Solve for temperatures at free nodes
        T_free = spsolve(L_free, rhs)
    except Exception as e:
        logger.warning(f"Sparse solve failed: {e}, using fallback")
        T_free = np.zeros(n_free)

    # Calculate total heat flow from source
    total_flow = 0.0
    for v in graph.neighbors(temp_source):
        idx_v = node_to_idx[v]
        R = resistances.get((temp_source, v), 1.0)
        if R <= 0:
            R = 1e-10
        
        if v == temp_sink:
            T_v = T_sink
        elif idx_v in free_nodes:
            T_v = T_free[free_nodes.index(idx_v)]
        else:
            T_v = T_source  # Should not happen

        flow = (T_source - T_v) / R
        total_flow += flow

    return total_flow

def calculate_effective_conductivity(graph: nx.Graph, bulk_k: float, d: float, l: float) -> float:
    """
    Calculate effective thermal conductivity of the network.
    """
    if not graph.number_of_edges():
        return 0.0

    # Assign resistances
    resistances = assign_thermal_resistance(graph, bulk_k, d, l)

    # Select source and sink (farthest nodes or first/last)
    nodes = list(graph.nodes())
    if len(nodes) < 2:
        return 0.0

    # Use first and last nodes as source/sink
    source = nodes[0]
    sink = nodes[-1]

    # Solve
    heat_flow = solve_kirchhoff_heat_flow(graph, resistances, source, sink)

    # Effective conductivity: k_eff = Q * L / (A * delta_T)
    # Assume delta_T = 1, L = characteristic length, A = cross-section
    # For simplicity, use network diameter as L and single wire area as A
    try:
        diameter = nx.diameter(graph)
    except:
        diameter = l

    area = np.pi * (d / 2) ** 2
    k_eff = heat_flow * diameter / area

    return k_eff
