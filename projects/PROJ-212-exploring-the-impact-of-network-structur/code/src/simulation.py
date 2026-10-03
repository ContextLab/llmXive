import numpy as np
import networkx as nx
from scipy.integrate import solve_ivp
from typing import List, Dict, Any, Optional, Tuple
from data_models import SynchronizationStatus, SimulationResult
import logging

logger = logging.getLogger(__name__)

def check_disconnected(G: nx.Graph) -> bool:
    """
    Check if the graph G is disconnected.
    Returns True if disconnected, False otherwise.
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

def kuramoto_derivative(t: float, y: np.ndarray, K: float, omega: np.ndarray, adj_matrix: np.ndarray) -> np.ndarray:
    """
    Compute the derivative of the Kuramoto model phases.
    d(theta_i)/dt = omega_i + (K/N) * sum_{j} A_{ij} * sin(theta_j - theta_i)
    """
    N = len(y)
    dtheta = np.zeros(N)
    sin_diff = np.sin(y[:, None] - y[None, :])
    coupling_term = (K / N) * (adj_matrix @ sin_diff).sum(axis=1)
    dtheta = omega + coupling_term
    return dtheta

def run_kuramoto_simulation(
    G: nx.Graph,
    K: float,
    T: float = 100.0,
    dt: float = 0.01,
    seed: Optional[int] = None
) -> Tuple[float, float, SynchronizationStatus]:
    """
    Run a single Kuramoto simulation on graph G with coupling strength K.
    Returns (final_r, mean_r, status).
    """
    if seed is not None:
        np.random.seed(seed)

    N = G.number_of_nodes()
    if N == 0:
        return 0.0, 0.0, SynchronizationStatus.DIVERGED

    omega = np.random.uniform(-0.5, 0.5, N)
    theta_0 = np.random.uniform(0, 2 * np.pi, N)

    adj_matrix = nx.to_numpy_array(G, dtype=np.float64)

    def ode_func(t, y):
        return kuramoto_derivative(t, y, K, omega, adj_matrix)

    t_eval = np.arange(0, T, dt)

    try:
        sol = solve_ivp(
            ode_func,
            (0, T),
            theta_0,
            t_eval=t_eval,
            method='RK45',
            rtol=1e-4,
            atol=1e-6
        )
    except Exception as e:
        logger.warning(f"Integration failed for K={K}: {e}")
        return 0.0, 0.0, SynchronizationStatus.DIVERGED

    if not sol.success:
        logger.warning(f"Integration failed for K={K}: {sol.message}")
        return 0.0, 0.0, SynchronizationStatus.DIVERGED

    phases = sol.y.T
    r_values = [compute_order_parameter(p) for p in phases]

    # Check synchronization criteria: r > 0.8 for last 100 time units
    # Assuming dt=0.01, last 100 units is last 10000 steps
    # If T is small, we check the tail of the simulation
    tail_start_idx = max(0, len(r_values) - int(100 / dt))
    tail_r_values = r_values[tail_start_idx:]

    if len(tail_r_values) == 0:
        return 0.0, 0.0, SynchronizationStatus.UNSTABLE

    mean_r_tail = np.mean(tail_r_values)
    final_r = r_values[-1]

    # Criteria: mean r in tail > 0.8 (approximating "r > 0.8 for t > 100")
    # Spec says: r > 0.8 for t > 100. We interpret as mean(r) in last 100 time units > 0.8
    if mean_r_tail > 0.8:
        status = SynchronizationStatus.SYNCHRONIZED
    elif mean_r_tail > 0.5:
        status = SynchronizationStatus.PARTIAL
    else:
        status = SynchronizationStatus.UNSTABLE

    return final_r, mean_r_tail, status

def find_critical_coupling(
    G: nx.Graph,
    K_min: float = 0.0,
    K_max: float = 5.0,
    tol: float = 0.001,
    max_iter: int = 50
) -> Optional[float]:
    """
    Find the critical coupling strength K_c where synchronization emerges.
    Uses bisection search on K in [K_min, K_max].
    Returns K_c if found, None if not converged or graph is disconnected.
    """
    if check_disconnected(G):
        logger.info("Graph is disconnected. Skipping K-sweep.")
        return float('inf')

    N = G.number_of_nodes()
    if N < 2:
        logger.warning("Graph has fewer than 2 nodes.")
        return float('inf')

    # Bisection search for K_c
    # We look for the smallest K where synchronization status is SYNCHRONIZED
    # Strategy: Binary search for the transition point.
    # However, synchronization is not monotonic in a simple way for all graphs,
    # but generally higher K leads to synchronization.
    # We'll search for the K where status changes from UNSTABLE to SYNCHRONIZED.

    # First, check boundaries
    _, _, status_low = run_kuramoto_simulation(G, K_min)
    if status_low == SynchronizationStatus.SYNCHRONIZED:
        return K_min

    _, _, status_high = run_kuramoto_simulation(G, K_max)
    if status_high != SynchronizationStatus.SYNCHRONIZED:
        logger.warning(f"K_max={K_max} did not achieve synchronization. Returning None.")
        return None

    # Bisection
    K_low, K_high = K_min, K_max
    K_mid = (K_low + K_high) / 2.0
    iterations = 0

    while (K_high - K_low) > tol and iterations < max_iter:
        _, _, status_mid = run_kuramoto_simulation(G, K_mid)

        if status_mid == SynchronizationStatus.SYNCHRONIZED:
            K_high = K_mid
        else:
            K_low = K_mid

        K_mid = (K_low + K_high) / 2.0
        iterations += 1

    if iterations >= max_iter:
        logger.warning(f"Bisection did not converge within {max_iter} iterations.")
        # Fallback to discrete sweep if bisection fails
        logger.info("Attempting discrete sweep fallback.")
        return discrete_sweep_fallback(G, K_min, K_max)

    return K_mid

def discrete_sweep_fallback(
    G: nx.Graph,
    K_min: float,
    K_max: float,
    step: float = 0.1
) -> Optional[float]:
    """
    Fallback to discrete sweep if bisection fails.
    """
    K_values = np.arange(K_min, K_max + step, step)
    for K in K_values:
        _, _, status = run_kuramoto_simulation(G, K)
        if status == SynchronizationStatus.SYNCHRONIZED:
            return K
    return None

def process_single_network(
    G: nx.Graph,
    config: Dict[str, Any]
) -> SimulationResult:
    """
    Process a single network: compute metrics, find critical coupling.
    Returns a SimulationResult object.
    """
    # Pre-check guard clause for disconnected graphs (T015)
    if check_disconnected(G):
        logger.info(f"Graph is disconnected. Returning infinity threshold.")
        return SimulationResult(
            network_id="unknown", # Should be set by caller
            metrics={},
            threshold=float('inf'),
            status=SynchronizationStatus.DISCONNECTED
        )

    # If connected, proceed with normal logic (T014)
    K_c = find_critical_coupling(
        G,
        K_min=config.get('K_min', 0.0),
        K_max=config.get('K_max', 5.0),
        tol=config.get('tol', 0.001)
    )

    if K_c is None:
        K_c = float('inf')

    return SimulationResult(
        network_id="unknown",
        metrics={},
        threshold=K_c,
        status=SynchronizationStatus.SYNCHRONIZED if K_c != float('inf') else SynchronizationStatus.UNSTABLE
    )