import numpy as np
import networkx as nx
from scipy import sparse
from scipy.sparse.linalg import spsolve, LinearOperator
from typing import Dict, Any, Tuple, Optional
import logging

from material_db import get_material_conductivity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MIN_RESISTANCE = 1e-12  # Minimum resistance threshold to prevent division by zero
DEFAULT_BULK_CONDUCTIVITY = 1.0  # W/(m·K) fallback if material not found
DEFAULT_DIAMETER_NM = 10.0  # nm
DEFAULT_LENGTH_NM = 100.0  # nm
DEFAULT_LAMBDA_NM = 10.0  # nm (mean free path)
DEFAULT_P = 0.5  # Specularity parameter

def calculate_fuchs_sondheimer_factor(
    diameter_nm: float = DEFAULT_DIAMETER_NM,
    lambda_nm: float = DEFAULT_LAMBDA_NM,
    p: float = DEFAULT_P
) -> float:
    """
    Calculate the Fuchs-Sondheimer size-correction factor.
    
    Formula: f = 1 - (3/8) * (1 - p) * (lambda / d)  [Simplified for d << lambda]
    More accurate for d ~ lambda: Uses the standard approximation.
    
    Args:
        diameter_nm: Wire diameter in nm
        lambda_nm: Electron mean free path in nm
        p: Specularity parameter (0 = diffuse, 1 = specular)
        
    Returns:
        Correction factor (0 < f <= 1)
    """
    if diameter_nm <= 0:
        logger.warning("Diameter must be positive. Using default.")
        diameter_nm = DEFAULT_DIAMETER_NM
    
    ratio = lambda_nm / diameter_nm
    # Simplified Fuchs-Sondheimer approximation for thin wires
    # Effective conductivity = bulk * (1 - 3/8 * (1-p) * (lambda/d))
    # We return the factor that multiplies the bulk conductivity
    factor = 1.0 - (3.0/8.0) * (1.0 - p) * ratio
    
    # Clamp to valid range (0, 1]
    factor = max(0.0, min(1.0, factor))
    
    if factor == 0.0:
        logger.warning("Fuchs-Sondheimer factor clamped to 0.0 due to extreme size effects.")
        
    return factor

def assign_thermal_resistance(
    material: str,
    diameter_nm: float = DEFAULT_DIAMETER_NM,
    length_nm: float = DEFAULT_LENGTH_NM,
    lambda_nm: float = DEFAULT_LAMBDA_NM,
    p: float = DEFAULT_P
) -> float:
    """
    Assign thermal resistance to a nanowire segment based on material and geometry.
    
    R = L / (k_eff * A)
    where k_eff = k_bulk * fuchs_sondheimer_factor
    
    Args:
        material: Material name (e.g., 'Si', 'CNT', 'Ag')
        diameter_nm: Wire diameter in nm
        length_nm: Wire length in nm
        lambda_nm: Mean free path in nm
        p: Specularity parameter
        
    Returns:
        Thermal resistance in K/W (or arbitrary consistent units)
    """
    # Get bulk conductivity
    try:
        k_bulk = get_material_conductivity(material)
    except ValueError as e:
        logger.error(str(e))
        k_bulk = DEFAULT_BULK_CONDUCTIVITY
        logger.warning(f"Using default conductivity {k_bulk} for {material}")
    
    # Calculate size-corrected conductivity
    f_factor = calculate_fuchs_sondheimer_factor(diameter_nm, lambda_nm, p)
    k_eff = k_bulk * f_factor
    
    # Cross-sectional area (circular wire)
    # Area = pi * (d/2)^2
    radius_m = (diameter_nm * 1e-9) / 2.0
    area_m2 = np.pi * (radius_m ** 2)
    
    # Length in meters
    length_m = length_nm * 1e-9
    
    # Resistance R = L / (k * A)
    # Zero-resistance clamping: ensure denominator is not zero
    if area_m2 <= 0:
        logger.error("Invalid wire geometry: area is zero or negative.")
        return MIN_RESISTANCE
        
    if k_eff <= 0:
        logger.warning(f"Effective conductivity is zero or negative ({k_eff}). Clamping resistance.")
        return MIN_RESISTANCE
    
    resistance = length_m / (k_eff * area_m2)
    
    # Apply zero-resistance clamping
    if resistance < MIN_RESISTANCE:
        logger.warning(f"Calculated resistance ({resistance}) below minimum threshold. Clamping to {MIN_RESISTANCE}.")
        resistance = MIN_RESISTANCE
        
    return resistance

def build_edge_resistances(
    G: nx.Graph,
    material: str = 'Si',
    diameter_nm: float = DEFAULT_DIAMETER_NM,
    length_nm: float = DEFAULT_LENGTH_NM,
    lambda_nm: float = DEFAULT_LAMBDA_NM,
    p: float = DEFAULT_P
) -> Dict[Tuple[int, int], float]:
    """
    Build a dictionary of thermal resistances for all edges in the graph.
    
    Args:
        G: NetworkX graph representing the nanowire network
        material: Material name
        diameter_nm: Wire diameter
        length_nm: Wire length (can be overridden per edge if stored in attributes)
        lambda_nm: Mean free path
        p: Specularity parameter
        
    Returns:
        Dictionary mapping (u, v) tuples to resistance values
    """
    edge_resistances = {}
    
    for u, v, data in G.edges(data=True):
        # Allow per-edge geometry override if present
        edge_diameter = data.get('diameter_nm', diameter_nm)
        edge_length = data.get('length_nm', length_nm)
        
        R = assign_thermal_resistance(
            material,
            diameter_nm=edge_diameter,
            length_nm=edge_length,
            lambda_nm=lambda_nm,
            p=p
        )
        edge_resistances[(u, v)] = R
        edge_resistances[(v, u)] = R  # Undirected graph
        
    return edge_resistances

def solve_kirchhoff_heat_flow(
    G: nx.Graph,
    edge_resistances: Dict[Tuple[int, int], float],
    source_nodes: list,
    sink_nodes: list,
    T_source: float = 1.0,
    T_sink: float = 0.0
) -> Tuple[Optional[np.ndarray], bool]:
    """
    Solve the Kirchhoff heat flow equations using sparse linear algebra.
    
    Constructs the conductance matrix G_matrix and solves G_matrix * T = I
    
    Args:
        G: NetworkX graph
        edge_resistances: Dict of resistances
        source_nodes: List of node indices at source temperature
        sink_nodes: List of node indices at sink temperature
        T_source: Source temperature
        T_sink: Sink temperature
        
    Returns:
        Tuple of (temperature_array, is_connected)
        If disconnected, returns (None, False)
    """
    n = G.number_of_nodes()
    if n == 0:
        logger.warning("Empty graph provided.")
        return None, False
        
    # Check connectivity
    if not nx.is_connected(G):
        logger.warning("Graph disconnected; conductivity set to 0.0")
        return None, False
        
    # Build conductance matrix (Laplacian-like)
    # G_ij = sum(1/R_ik) for i=j (diagonal)
    # G_ij = -1/R_ij for i!=j (off-diagonal)
    
    rows = []
    cols = []
    data = []
    
    conductance_sum = np.zeros(n)
    
    for (u, v), R in edge_resistances.items():
        # Apply zero-resistance clamping logic here as well to ensure stability
        if R < MIN_RESISTANCE:
            R = MIN_RESISTANCE
            
        G_ij = 1.0 / R
        
        if u < n and v < n:
            conductance_sum[u] += G_ij
            conductance_sum[v] += G_ij
            
            # Off-diagonal
            rows.extend([u, v])
            cols.extend([v, u])
            data.extend([-G_ij, -G_ij])
    
    # Diagonal
    rows.extend(range(n))
    cols.extend(range(n))
    data.extend(conductance_sum)
    
    L = sparse.csr_matrix((data, (rows, cols)), shape=(n, n))
    
    # Apply Dirichlet boundary conditions
    # Remove rows/cols for fixed temperature nodes and move to RHS
    free_nodes = [i for i in range(n) if i not in source_nodes and i not in sink_nodes]
    
    if not free_nodes:
        # All nodes are fixed temperature
        # Total current is sum of flows between source and sink
        # But for effective conductivity calculation, we need the internal distribution
        # If all are fixed, we can't solve for internal T, but we can calculate direct flow
        # However, typically we have at least one free node or just source/sink
        pass
        
    if len(free_nodes) > 0:
        L_free = L[np.ix_(free_nodes, free_nodes)]
        
        # RHS: I = - sum(G_ij * T_j) for fixed neighbors
        I = np.zeros(len(free_nodes))
        
        for idx, i in enumerate(free_nodes):
            for j in range(n):
                if i != j:
                    G_ij = L[i, j]
                    if j in source_nodes:
                        I[idx] -= G_ij * T_source
                    elif j in sink_nodes:
                        I[idx] -= G_ij * T_sink
        
        try:
            T_free = spsolve(L_free, I)
        except Exception as e:
            logger.error(f"Sparse solver failed: {e}. Graph may be ill-conditioned.")
            return None, False
        
        # Reconstruct full temperature array
        T = np.zeros(n)
        for i, t_val in zip(free_nodes, T_free):
            T[i] = t_val
        for i in source_nodes:
            T[i] = T_source
        for i in sink_nodes:
            T[i] = T_sink
    else:
        # No free nodes, just set fixed temperatures
        T = np.zeros(n)
        for i in source_nodes:
            T[i] = T_source
        for i in sink_nodes:
            T[i] = T_sink
            
    return T, True

def calculate_effective_conductivity(
    G: nx.Graph,
    edge_resistances: Dict[Tuple[int, int], float],
    T_array: np.ndarray,
    source_nodes: list,
    sink_nodes: list,
    T_source: float = 1.0,
    T_sink: float = 0.0,
    total_length: float = 1.0,
    total_cross_section: float = 1.0
) -> float:
    """
    Calculate effective thermal conductivity from the solved temperature field.
    
    k_eff = (Q * L) / (A * Delta_T)
    where Q is total heat flow from source nodes
    
    Args:
        G: NetworkX graph
        edge_resistances: Dict of resistances
        T_array: Temperature at each node
        source_nodes: Source node indices
        sink_nodes: Sink node indices
        T_source: Source temperature
        T_sink: Sink temperature
        total_length: Effective length of the sample
        total_cross_section: Effective cross-sectional area
        
    Returns:
        Effective thermal conductivity (W/(m·K) or consistent units)
    """
    if T_array is None or len(T_array) == 0:
        logger.warning("No temperature array provided. Returning 0.0 conductivity.")
        return 0.0
        
    if not nx.is_connected(G):
        logger.warning("Graph disconnected. Conductivity is 0.0.")
        return 0.0
        
    # Calculate total heat flow Q from source nodes
    Q_total = 0.0
    
    for u in source_nodes:
        for v in G.neighbors(u):
            if (u, v) in edge_resistances:
                R = edge_resistances[(u, v)]
                # Clamp resistance to prevent division by zero
                if R < MIN_RESISTANCE:
                    R = MIN_RESISTONE
                
                # Q = (T_u - T_v) / R
                delta_T = T_array[u] - T_array[v]
                Q = delta_T / R
                Q_total += Q
                
    if Q_total <= 0:
        logger.warning("Non-positive heat flow detected. Returning 0.0 conductivity.")
        return 0.0
        
    delta_T_total = T_source - T_sink
    if delta_T_total <= 0:
        logger.warning("Non-positive temperature difference. Returning 0.0 conductivity.")
        return 0.0
        
    # k_eff = (Q * L) / (A * Delta_T)
    k_eff = (Q_total * total_length) / (total_cross_section * delta_T_total)
    
    # Zero-resistance clamping for final result
    if k_eff < 0:
        logger.warning("Negative conductivity calculated. Returning 0.0.")
        return 0.0
        
    return k_eff

def calculate_effective_conductivity(
    G: nx.Graph,
    material: str = 'Si',
    diameter_nm: float = DEFAULT_DIAMETER_NM,
    length_nm: float = DEFAULT_LENGTH_NM,
    lambda_nm: float = DEFAULT_LAMBDA_NM,
    p: float = DEFAULT_P,
    T_source: float = 1.0,
    T_sink: float = 0.0
) -> Tuple[float, bool]:
    """
    Main entry point to calculate effective thermal conductivity of a network.
    
    1. Build edge resistances
    2. Identify source/sink nodes (e.g., nodes with min/max x-coordinate)
    3. Solve Kirchhoff equations
    4. Calculate effective conductivity
    
    Args:
        G: NetworkX graph
        material: Material name
        diameter_nm: Wire diameter
        length_nm: Wire length
        lambda_nm: Mean free path
        p: Specularity parameter
        T_source: Source temperature
        T_sink: Sink temperature
        
    Returns:
        Tuple of (effective_conductivity, success_flag)
    """
    if G.number_of_nodes() == 0:
        logger.warning("Empty graph. Conductivity = 0.0")
        return 0.0, False
        
    if not nx.is_connected(G):
        logger.warning("Graph disconnected; conductivity set to 0.0")
        return 0.0, False
        
    # Assign resistances
    edge_resistances = build_edge_resistances(
        G, material, diameter_nm, length_nm, lambda_nm, p
    )
    
    # Identify source and sink nodes based on geometry (e.g., x-coordinate)
    # If no positions, use node indices (first half source, second half sink)
    if 'pos' in G.nodes(data=True):
        # Sort by x-coordinate
        nodes_by_x = sorted(G.nodes(data='pos'), key=lambda x: x[1][0] if len(x[1]) > 0 else 0)
        # Split into two groups
        mid = len(nodes_by_x) // 2
        source_nodes = [n[0] for n in nodes_by_x[:mid]]
        sink_nodes = [n[0] for n in nodes_by_x[mid:]]
    else:
        # Fallback: split by index
        nodes = list(G.nodes())
        mid = len(nodes) // 2
        source_nodes = nodes[:mid]
        sink_nodes = nodes[mid:]
        
    if not source_nodes or not sink_nodes:
        logger.error("Could not identify source or sink nodes.")
        return 0.0, False
        
    # Solve
    T_array, is_connected = solve_kirchhoff_heat_flow(
        G, edge_resistances, source_nodes, sink_nodes, T_source, T_sink
    )
    
    if not is_connected or T_array is None:
        return 0.0, False
        
    # Estimate total length and cross-section
    # Simple heuristic: bounding box
    if 'pos' in G.nodes(data=True):
        xs = [d['pos'][0] for n, d in G.nodes(data='pos') if 'pos' in d]
        ys = [d['pos'][1] for n, d in G.nodes(data='pos') if 'pos' in d]
        total_length = max(xs) - min(xs) if xs else 1.0
        total_cross_section = max(ys) - min(ys) if ys else 1.0
    else:
        total_length = 1.0
        total_cross_section = 1.0
        
    k_eff = calculate_effective_conductivity(
        G, edge_resistances, T_array, source_nodes, sink_nodes,
        T_source, T_sink, total_length, total_cross_section
    )
    
    return k_eff, True