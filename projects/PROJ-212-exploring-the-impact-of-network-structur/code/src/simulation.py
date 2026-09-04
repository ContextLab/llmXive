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
    
    Returns True if the graph has more than one connected component
    (excluding isolated nodes if they are not part of the main component logic,
    but strictly speaking, nx.number_connected_components > 1 implies disconnected).
    """
    try:
        if G.number_of_nodes() == 0:
            return True
        # Count connected components
        num_components = nx.number_connected_components(G)
        return num_components > 1
    except Exception as e:
        logger.error(f"Error checking graph connectivity: {e}")
        return True  # Assume disconnected on error to be safe

def kuramoto_derivative(t: float, theta: np.ndarray, G: nx.Graph, K: float, omega: np.ndarray) -> np.ndarray:
    """
    Compute the derivative of the phase angles for the Kuramoto model.
    
    d(theta_i)/dt = omega_i + (K/N) * sum(sin(theta_j - theta_i)) for all j in neighbors(i)
    """
    N = len(theta)
    dtheta = np.zeros(N)
    
    # Pre-calculate sin differences might be expensive for large N, but for N=200 it's fine.
    # Vectorized approach:
    # For each i: sum over j in neighbors(i) of sin(theta[j] - theta[i])
    
    # Convert adjacency to a way to iterate efficiently or use matrix mult if dense
    # Given N=200, iterating neighbors is acceptable.
    
    for i in range(N):
        neighbors = list(G.neighbors(i))
        if not neighbors:
            dtheta[i] = omega[i]
            continue
        
        sin_diff_sum = 0.0
        for j in neighbors:
            sin_diff_sum += np.sin(theta[j] - theta[i])
        
        dtheta[i] = omega[i] + (K / N) * sin_diff_sum
        
    return dtheta

def compute_order_parameter(theta: np.ndarray) -> float:
    """
    Compute the Kuramoto order parameter r.
    r = | (1/N) * sum(exp(i * theta_j)) |
    """
    if len(theta) == 0:
        return 0.0
    complex_phases = np.exp(1j * theta)
    r = np.abs(np.mean(complex_phases))
    return float(r)

def run_kuramoto_simulation(
    G: nx.Graph,
    T: float = 1000.0,
    dt: float = 0.1,
    K_values: Optional[List[float]] = None,
    threshold_r: float = 0.8,
    threshold_t: float = 100.0,
    seed: Optional[int] = None
) -> SimulationResult:
    """
    Run Kuramoto simulation on graph G.
    
    If the graph is disconnected, returns a SimulationResult with:
    - critical_k: float('inf')
    - status: SynchronizationStatus.DISCONNECTED
    
    Otherwise, sweeps K values and finds the first K where synchronization
    is maintained (r > threshold_r) for duration > threshold_t.
    """
    if seed is not None:
        np.random.seed(seed)

    # Check for disconnected graph
    if check_disconnected(G):
        logger.warning("Graph is disconnected. Skipping K-sweep. Returning infinity threshold.")
        return SimulationResult(
            critical_k=float('inf'),
            status=SynchronizationStatus.DISCONNECTED,
            metrics={
                "is_disconnected": True,
                "num_components": nx.number_connected_components(G),
                "num_nodes": G.number_of_nodes(),
                "num_edges": G.number_of_edges()
            },
            full_r_history=[]
        )

    N = G.number_of_nodes()
    if N == 0:
        logger.warning("Graph has no nodes. Returning infinity threshold.")
        return SimulationResult(
            critical_k=float('inf'),
            status=SynchronizationStatus.DISCONNECTED,
            metrics={"error": "No nodes"},
            full_r_history=[]
        )

    if K_values is None:
        # Default sweep: K from 0 to 5, step 0.1
        K_values = [round(k, 1) for k in np.arange(0.0, 5.01, 0.1)]

    # Natural frequencies (assume identical for simplicity or random from normal)
    # Standard Kuramoto often uses uniform distribution or identical. 
    # Let's use random frequencies for robustness check.
    omega = np.random.normal(0.0, 1.0, N)
    
    # Initial phases
    theta_0 = np.random.uniform(0, 2 * np.pi, N)

    critical_k = float('inf')
    status = SynchronizationStatus.NOT_SYNCHRONIZED
    found_sync = False
    full_r_history = []

    logger.info(f"Starting simulation for {N} nodes with K sweep: {len(K_values)} values.")

    for K in K_values:
        # Integrate from t=0 to T
        # We need to check r(t) continuously or at steps. 
        # solve_ivp with dense output or specific t_eval points.
        # To check "r > 0.8 for t > 100", we need to ensure that after t=100, 
        # the order parameter stays above 0.8 for the rest of the simulation 
        # (or for a specific duration). 
        # Simplified logic: check if average r in [T_threshold, T] > threshold_r.
        
        t_span = (0.0, T)
        t_eval = np.arange(0.0, T + dt, dt)
        
        try:
            sol = solve_ivp(
                fun=lambda t, y: kuramoto_derivative(t, y, G, K, omega),
                t_span=t_span,
                y0=theta_0,
                method='RK45',
                t_eval=t_eval,
                rtol=1e-4,
                atol=1e-6
            )
            
            if not sol.success:
                logger.warning(f"Integration failed for K={K}: {sol.message}")
                continue
            
            theta_sol = sol.y[0] # phases
            
            # Compute r at each time step
            r_values = []
            for t_idx, t in enumerate(sol.t):
                r_val = compute_order_parameter(theta_sol[:, t_idx])
                r_values.append(r_val)
            
            # Check synchronization condition:
            # "r > threshold_r for t > threshold_t"
            # We check the average r in the window [threshold_t, T]
            start_idx = int(threshold_t / dt)
            if start_idx >= len(r_values):
                start_idx = len(r_values) - 1
                
            window_r = r_values[start_idx:]
            avg_r = np.mean(window_r)
            
            full_r_history.append({
                "K": K,
                "avg_r": float(avg_r),
                "r_at_end": float(r_values[-1]) if r_values else 0.0,
                "max_r": float(np.max(r_values))
            })

            if avg_r > threshold_r:
                critical_k = K
                status = SynchronizationStatus.SYNCHRONIZED
                found_sync = True
                logger.info(f"Found synchronization at K={K} (avg_r={avg_r:.4f})")
                break # Found the critical K (first one in increasing order)
                
        except Exception as e:
            logger.error(f"Error during simulation for K={K}: {e}")
            continue

    if not found_sync:
        logger.info("Synchronization threshold not found in the specified K range.")
        status = SynchronizationStatus.NOT_SYNCHRONIZED
        # Keep critical_k as inf or the last K? 
        # Usually critical_k is the point where it transitions. 
        # If not found, it's effectively > max(K_values).
        # We'll leave it as inf to indicate "not found within range".

    return SimulationResult(
        critical_k=critical_k,
        status=status,
        metrics={
            "num_nodes": N,
            "num_edges": G.number_of_edges(),
            "K_range": [K_values[0], K_values[-1]],
            "threshold_r": threshold_r,
            "threshold_t": threshold_t,
            "found_sync": found_sync
        },
        full_r_history=full_r_history
    )