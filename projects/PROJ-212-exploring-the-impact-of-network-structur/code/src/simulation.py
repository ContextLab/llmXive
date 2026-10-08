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
    Returns True if the graph is disconnected, False otherwise.
    """
    if G.number_of_nodes() == 0:
        return True
    return not nx.is_connected(G)

def compute_order_parameter(phases: np.ndarray) -> float:
    """
    Compute the Kuramoto order parameter r.
    r = | (1/N) * sum(exp(i * theta_j)) |
    """
    if len(phases) == 0:
        return 0.0
    complex_phases = np.exp(1j * phases)
    r = np.abs(np.mean(complex_phases))
    return float(r)

def kuramoto_derivative(t: float, y: np.ndarray, K: float, adj_matrix: np.ndarray, natural_freqs: np.ndarray) -> np.ndarray:
    """
    Compute the derivative for the Kuramoto model:
    d(theta_i)/dt = omega_i + (K/N) * sum_j( A_ij * sin(theta_j - theta_i) )
    """
    N = len(y)
    dtheta = np.zeros(N)
    sin_diff = np.sin(y[:, None] - y[None, :])
    coupling_term = (K / N) * adj_matrix @ sin_diff
    dtheta = natural_freqs + np.sum(coupling_term, axis=1)
    return dtheta

def run_kuramoto_simulation(
    G: nx.Graph,
    K: float,
    t_max: float = 200.0,
    dt: float = 0.1,
    seed: Optional[int] = None
) -> SimulationResult:
    """
    Run the Kuramoto simulation for a given coupling strength K.
    
    Args:
        G: The network graph.
        K: Coupling strength.
        t_max: Maximum simulation time.
        dt: Time step for output.
        seed: Random seed for initial phases.
        
    Returns:
        SimulationResult object.
    """
    if seed is not None:
        np.random.seed(seed)

    N = G.number_of_nodes()
    if N == 0:
        return SimulationResult(
            network_id="empty",
            K=K,
            status=SynchronizationStatus.FAILED,
            threshold=None,
            final_order_parameter=0.0,
            metrics={}
        )

    adj_matrix = nx.to_numpy_array(G)
    natural_freqs = np.random.uniform(-1.0, 1.0, N)
    phases = np.random.uniform(0, 2 * np.pi, N)

    t_eval = np.arange(0, t_max, dt)
    
    try:
        sol = solve_ivp(
            kuramoto_derivative,
            (0, t_max),
            phases,
            args=(K, adj_matrix, natural_freqs),
            method='RK45',
            t_eval=t_eval,
            rtol=1e-6,
            atol=1e-9
        )
        
        if not sol.success:
            logger.error(f"Integration failed: {sol.message}")
            return SimulationResult(
                network_id="error",
                K=K,
                status=SynchronizationStatus.FAILED,
                threshold=None,
                final_order_parameter=0.0,
                metrics={}
            )
        
        final_phases = sol.y[:, -1]
        final_r = compute_order_parameter(final_phases)
        
        # Check for sustained synchronization (r > 0.8 for t > 100)
        # We look at the last 100 time units (or remaining if less)
        last_100_indices = t_eval >= (t_max - 100)
        if np.any(last_100_indices):
            r_last_100 = [compute_order_parameter(sol.y[:, i]) for i, t in enumerate(t_eval) if last_100_indices[i]]
            sustained = all(r > 0.8 for r in r_last_100) if r_last_100 else False
        else:
            sustained = False

        status = SynchronizationStatus.SYNCHRONIZED if sustained else SynchronizationStatus.NOT_SYNCHRONIZED

        return SimulationResult(
            network_id="simulated",
            K=K,
            status=status,
            threshold=None,
            final_order_parameter=final_r,
            metrics={"duration": t_max, "nodes": N}
        )
        
    except Exception as e:
        logger.error(f"Simulation error: {e}")
        return SimulationResult(
            network_id="error",
            K=K,
            status=SynchronizationStatus.FAILED,
            threshold=None,
            final_order_parameter=0.0,
            metrics={}
        )

def find_critical_coupling(
    G: nx.Graph,
    K_min: float = 0.0,
    K_max: float = 5.0,
    tol: float = 0.001,
    max_iter: int = 50,
    seed: Optional[int] = None
) -> Optional[float]:
    """
    Find the critical coupling strength K_c using bisection search.
    K_c is the minimum K where the system sustains synchronization (r > 0.8 for t > 100).
    
    Args:
        G: The network graph.
        K_min: Lower bound for K.
        K_max: Upper bound for K.
        tol: Tolerance for bisection.
        max_iter: Maximum iterations for bisection.
        seed: Random seed.
        
    Returns:
        Critical coupling K_c, or None if not found.
    """
    if check_disconnected(G):
        logger.info("Graph is disconnected. Returning infinity for critical coupling.")
        return float('inf')

    # Check if K_max is sufficient
    res_max = run_kuramoto_simulation(G, K_max, seed=seed)
    if res_max.status != SynchronizationStatus.SYNCHRONIZED:
        logger.warning(f"K_max={K_max} is insufficient for synchronization. Returning None.")
        return None

    # Check if K_min is already synchronized (unlikely but possible)
    res_min = run_kuramoto_simulation(G, K_min, seed=seed)
    if res_min.status == SynchronizationStatus.SYNCHRONIZED:
        return K_min

    low = K_min
    high = K_max
    best_k = None

    for i in range(max_iter):
        mid = (low + high) / 2.0
        res_mid = run_kuramoto_simulation(G, mid, seed=seed)

        if res_mid.status == SynchronizationStatus.SYNCHRONIZED:
            best_k = mid
            high = mid
        else:
            low = mid

        if (high - low) < tol:
            break

    if best_k is None:
        logger.warning("Bisection search did not converge. Falling back to discrete sweep.")
        return discrete_sweep_fallback(G, K_min, K_max, seed=seed)

    return best_k

def discrete_sweep_fallback(
    G: nx.Graph,
    K_min: float = 0.0,
    K_max: float = 5.0,
    step: float = 0.1,
    seed: Optional[int] = None
) -> Optional[float]:
    """
    Fallback method: Discrete sweep of K values to find critical coupling.
    Used if bisection fails to converge.
    """
    K_vals = np.arange(K_min, K_max + step, step)
    best_k = None
    
    for K in K_vals:
        res = run_kuramoto_simulation(G, K, seed=seed)
        if res.status == SynchronizationStatus.SYNCHRONIZED:
            best_k = K
            break
    
    if best_k is None:
        logger.warning(f"Discrete sweep up to {K_max} found no synchronization.")
        return None
    
    return best_k

def process_single_network(
    G: nx.Graph,
    network_id: str,
    K_min: float = 0.0,
    K_max: float = 5.0,
    tol: float = 0.001,
    max_iter: int = 50,
    seed: Optional[int] = None
) -> SimulationResult:
    """
    Process a single network: check connectivity, run simulation, find critical coupling.
    
    Args:
        G: The network graph.
        network_id: Identifier for the network.
        K_min, K_max, tol, max_iter: Parameters for find_critical_coupling.
        seed: Random seed.
        
    Returns:
        SimulationResult object with all fields populated.
    """
    if check_disconnected(G):
        logger.info(f"Network {network_id} is disconnected. Skipping simulation.")
        return SimulationResult(
            network_id=network_id,
            K=float('inf'),
            status=SynchronizationStatus.DISCONNECTED,
            threshold=float('inf'),
            final_order_parameter=0.0,
            metrics={"nodes": G.number_of_nodes(), "edges": G.number_of_edges()}
        )

    threshold = find_critical_coupling(G, K_min, K_max, tol, max_iter, seed)
    
    if threshold is None:
        logger.warning(f"Could not determine threshold for {network_id}.")
        status = SynchronizationStatus.FAILED
        final_r = 0.0
    else:
        # Run one final simulation at the threshold to get the final order parameter
        final_sim = run_kuramoto_simulation(G, threshold, seed=seed)
        status = final_sim.status
        final_r = final_sim.final_order_parameter

    return SimulationResult(
        network_id=network_id,
        K=threshold if threshold is not None else 0.0,
        status=status,
        threshold=threshold,
        final_order_parameter=final_r,
        metrics={"nodes": G.number_of_nodes(), "edges": G.number_of_edges()}
    )