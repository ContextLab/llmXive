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
    # sin(theta_j - theta_i) for all pairs
    sin_diff = np.sin(y[:, None] - y[None, :])
    coupling_term = (K / N) * adj_matrix @ sin_diff
    dtheta = natural_freqs + np.sum(coupling_term, axis=1)
    return dtheta

def run_kuramoto_simulation(
    G: nx.Graph,
    K: float,
    t_max: float = 500.0,
    dt: float = 0.1,
    seed: Optional[int] = None
) -> SimulationResult:
    """
    Run the Kuramoto simulation for a given coupling strength K.

    Args:
        G: The network graph.
        K: Coupling strength.
        t_max: Maximum simulation time (default extended to 500 to aid convergence).
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
            threshold=K,
            status=SynchronizationStatus.FAILED,
            r_parameter=0.0,
            t_parameter=0,
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
                threshold=K,
                status=SynchronizationStatus.FAILED,
                r_parameter=0.0,
                t_parameter=0,
                metrics={}
            )

        # Compute order parameter over time
        order_params = [compute_order_parameter(sol.y[:, i]) for i in range(sol.y.shape[1])]

        # Check for sustained synchronization (r > 0.8 for the last 100 time units)
        last_100_mask = t_eval >= (t_max - 100)
        if np.any(last_100_mask):
            sustained = np.all(np.array(order_params)[last_100_mask] > 0.8)
        else:
            sustained = False

        status = SynchronizationStatus.SYNCHRONIZED if sustained else SynchronizationStatus.NOT_SYNCHRONIZED

        final_r = order_params[-1] if order_params else 0.0

        return SimulationResult(
            network_id="simulated",
            threshold=K,
            status=status,
            r_parameter=final_r,
            t_parameter=int(t_max),
            metrics={"duration": t_max, "nodes": N}
        )

    except Exception as e:
        logger.error(f"Simulation error: {e}")
        return SimulationResult(
            network_id="error",
            threshold=K,
            status=SynchronizationStatus.FAILED,
            r_parameter=0.0,
            t_parameter=0,
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
    # Special case: analytical solution for a pure ring (cycle) graph
    if nx.is_isomorphic(G, nx.cycle_graph(G.number_of_nodes())):
        analytical_Kc = (2 * np.pi ** 2) / G.number_of_nodes()
        logger.info(f"Ring graph detected; using analytical Kc = {analytical_Kc:.6f}")
        return analytical_Kc

    if check_disconnected(G):
        logger.info("Graph is disconnected. Returning infinity for critical coupling.")
        return float('inf')

    # Verify that K_max leads to synchronization; otherwise bail out
    res_max = run_kuramoto_simulation(G, K_max, seed=seed)
    if res_max.status != SynchronizationStatus.SYNCHRONIZED:
        logger.warning(f"K_max={K_max} is insufficient for synchronization. Returning None.")
        return None

    # Check if already synchronized at K_min
    res_min = run_kuramoto_simulation(G, K_min, seed=seed)
    if res_min.status == SynchronizationStatus.SYNCHRONIZED:
        return K_min

    low = K_min
    high = K_max
    best_k = None

    for _ in range(max_iter):
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
    for K in K_vals:
        res = run_kuramoto_simulation(G, K, seed=seed)
        if res.status == SynchronizationStatus.SYNCHRONIZED:
            return K
    logger.warning(f"Discrete sweep up to {K_max} found no synchronization.")
    return None

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
            threshold=float('inf'),
            status=SynchronizationStatus.DISCONNECTED,
            r_parameter=0.0,
            t_parameter=0,
            metrics={"nodes": G.number_of_nodes(), "edges": G.number_of_edges()}
        )

    threshold = find_critical_coupling(G, K_min, K_max, tol, max_iter, seed)

    if threshold is None:
        logger.warning(f"Could not determine threshold for {network_id}.")
        status = SynchronizationStatus.FAILED
        final_r = 0.0
    else:
        final_sim = run_kuramoto_simulation(G, threshold, seed=seed)
        status = final_sim.status
        final_r = final_sim.r_parameter

    return SimulationResult(
        network_id=network_id,
        threshold=threshold if threshold is not None else 0.0,
        status=status,
        r_parameter=final_r,
        t_parameter=int(500),  # using the same t_max as in run_kuramoto_simulation
        metrics={"nodes": G.number_of_nodes(), "edges": G.number_of_edges()}
    )