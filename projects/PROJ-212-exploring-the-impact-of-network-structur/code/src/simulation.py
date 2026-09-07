import numpy as np
import networkx as nx
from scipy.integrate import solve_ivp
from typing import List, Dict, Any, Optional, Tuple
from data_models import SynchronizationStatus, SimulationResult
import logging

logger = logging.getLogger(__name__)

def check_disconnected(G: nx.Graph) -> bool:
    """
    Check if the graph is disconnected.
    
    Returns:
        True if the graph has more than one connected component, False otherwise.
    """
    if G.number_of_nodes() == 0:
        logger.warning("Graph has no nodes.")
        return True
    
    try:
        num_components = nx.number_connected_components(G)
        if num_components > 1:
            logger.info(f"Graph is disconnected with {num_components} components.")
            return True
        return False
    except Exception as e:
        logger.error(f"Error checking connectivity: {e}")
        return True

def kuramoto_derivative(t: float, y: np.ndarray, K: float, adj_matrix: np.ndarray, 
                        omega: np.ndarray) -> np.ndarray:
    """
    Compute the derivative for the Kuramoto model.
    
    d(theta_i)/dt = omega_i + (K/N) * sum_j(adj_ij * sin(theta_j - theta_i))
    
    Args:
        t: Current time (unused, but required by solve_ivp)
        y: Current phase angles (N,)
        K: Coupling strength
        adj_matrix: Adjacency matrix of the network (N, N)
        omega: Natural frequencies (N,)
        
    Returns:
        Derivatives of phase angles (N,)
    """
    N = len(y)
    dydt = np.zeros(N)
    diff = y[:, np.newaxis] - y[np.newaxis, :]
    sin_diff = np.sin(diff)
    coupling_term = (K / N) * np.dot(adj_matrix, sin_diff)
    dydt = omega + coupling_term
    return dydt

def compute_order_parameter(y: np.ndarray, adj_matrix: np.ndarray) -> float:
    """
    Compute the synchronization order parameter r.
    
    r = | (1/N) * sum_j(adj_ij * exp(i * theta_j)) |
    
    For a fully connected graph, this simplifies to the standard definition.
    For sparse graphs, we normalize by the degree or use a weighted average.
    Here, we use the standard definition normalized by N for consistency,
    but weighted by the adjacency matrix to reflect the network structure.
    
    Args:
        y: Current phase angles (N,)
        adj_matrix: Adjacency matrix (N, N)
        
    Returns:
        Order parameter r (float)
    """
    N = len(y)
    if N == 0:
        return 0.0
    
    # Complex representation of phases
    z = np.exp(1j * y)
    
    # Weighted average based on adjacency
    # r = | (1/N) * sum_j (adj_ij * exp(i*theta_j)) | averaged over i?
    # Standard Kuramoto: r = | (1/N) sum exp(i*theta_j) |
    # For network: r = | (1/N) sum_j (k_j / <k>) exp(i*theta_j) | ? 
    # Or simply the magnitude of the mean phasor:
    r = np.abs(np.mean(z))
    
    return float(r)

def run_kuramoto_simulation(G: nx.Graph, K_min: float = 0.0, K_max: float = 5.0, 
                            K_step: float = 0.1, T_final: float = 100.0, 
                            N: int = 200, rtol: float = 1e-6, atol: float = 1e-9,
                            threshold_r: float = 0.8, threshold_t: float = 100.0) -> SimulationResult:
    """
    Run the Kuramoto simulation on a given graph.
    
    Implements early-exit logic for disconnected graphs:
    - If the graph is disconnected, skip the K-sweep and return a result with
      critical coupling strength set to infinity.
    
    Args:
        G: NetworkX graph
        K_min: Minimum coupling strength
        K_max: Maximum coupling strength
        K_step: Step size for K sweep
        T_final: Simulation end time
        N: Number of oscillators (if G has more nodes, a subset is used; if fewer, nodes are duplicated? No, we use G's nodes)
        rtol: Relative tolerance for solver
        atol: Absolute tolerance for solver
        threshold_r: Required order parameter for synchronization
        threshold_t: Duration for which r must stay above threshold_r
        
    Returns:
        SimulationResult object containing critical coupling strength and metrics
    """
    # Check connectivity first
    if check_disconnected(G):
        logger.warning("Graph is disconnected. Skipping K-sweep. Returning infinity for critical coupling.")
        return SimulationResult(
            critical_k=float('inf'),
            is_synchronized=False,
            metrics={"reason": "disconnected_graph", "num_components": nx.number_connected_components(G)},
            status=SynchronizationStatus.INCOMPLETE
        )
    
    # Use the actual graph nodes
    nodes = list(G.nodes())
    actual_N = len(nodes)
    if actual_N == 0:
        logger.warning("Graph has no nodes. Returning infinity.")
        return SimulationResult(
            critical_k=float('inf'),
            is_synchronized=False,
            metrics={"reason": "empty_graph"},
            status=SynchronizationStatus.INCOMPLETE
        )
    
    # Extract adjacency matrix
    adj_matrix = nx.to_numpy_array(G, nodelist=nodes)
    
    # Assign natural frequencies (uniformly distributed in [0, 1])
    np.random.seed(42)  # For reproducibility
    omega = np.random.uniform(0, 1, actual_N)
    
    # Initialize phases randomly
    y0 = np.random.uniform(0, 2 * np.pi, actual_N)
    
    K_values = np.arange(K_min, K_max + K_step, K_step)
    critical_k = float('inf')
    synchronized_at_k = None
    
    logger.info(f"Starting K-sweep from {K_min} to {K_max} with step {K_step}")
    
    for K in K_values:
        # Solve ODE
        sol = solve_ivp(
            lambda t, y: kuramoto_derivative(t, y, K, adj_matrix, omega),
            [0, T_final],
            y0,
            method='RK45',
            rtol=rtol,
            atol=atol
        )
        
        if not sol.success:
            logger.error(f"Integration failed at K={K}: {sol.message}")
            continue
        
        # Compute order parameter over time
        # We'll sample the order parameter at the end of the simulation
        # and check if it stays above threshold for a duration
        t = sol.t
        y = sol.y  # shape (N, len(t))
        
        # Calculate order parameter at each time step
        r_values = []
        for i in range(len(t)):
            r = compute_order_parameter(y[:, i], adj_matrix)
            r_values.append(r)
        
        r_values = np.array(r_values)
        
        # Check if r stays above threshold_r for at least threshold_t duration
        # Find segments where r > threshold_r
        above_threshold = r_values > threshold_r
        if np.any(above_threshold):
            # Find the length of the longest continuous segment above threshold
            # or check if the last segment is long enough
            # Simple approach: check the end of the simulation
            # Count consecutive True values at the end
            consecutive_count = 0
            for val in reversed(above_threshold):
                if val:
                    consecutive_count += 1
                else:
                    break
            
            # Convert count to time
            if len(t) > 1:
                dt = t[1] - t[0]
            else:
                dt = 1.0
                
            duration_above = consecutive_count * dt
            
            if duration_above >= threshold_t:
                critical_k = K
                synchronized_at_k = K
                logger.info(f"Synchronization achieved at K={K} with r={r_values[-1]:.4f}")
                break
        else:
            logger.debug(f"At K={K}, max r={np.max(r_values):.4f}, never sustained above {threshold_r}")
    
    # Determine final status
    if synchronized_at_k is not None:
        status = SynchronizationStatus.SYNCHRONIZED
        is_synchronized = True
    else:
        status = SynchronizationStatus.NOT_SYNCHRONIZED
        is_synchronized = False
        
    return SimulationResult(
        critical_k=critical_k,
        is_synchronized=is_synchronized,
        metrics={
            "K_sweep_range": [K_min, K_max],
            "K_step": K_step,
            "num_nodes": actual_N,
            "synchronized_at_K": synchronized_at_k
        },
        status=status
    )