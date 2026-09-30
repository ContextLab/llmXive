import numpy as np
import networkx as nx
from scipy.integrate import solve_ivp
from typing import List, Dict, Any, Optional, Tuple
from data_models import SynchronizationStatus, SimulationResult
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_disconnected(graph: nx.Graph) -> bool:
    """
    Checks if the graph is disconnected.
    """
    if graph.number_of_nodes() == 0:
        return True
    return not nx.is_connected(graph)

def compute_order_parameter(phases: np.ndarray) -> float:
    """
    Computes the Kuramoto order parameter r.
    """
    if len(phases) == 0:
        return 0.0
    # r = |1/N * sum(exp(i * theta_j))|
    complex_phases = np.exp(1j * phases)
    r = np.abs(np.mean(complex_phases))
    return float(r)

def kuramoto_derivative(t: float, phases: np.ndarray, K: float, omega: np.ndarray, adjacency: np.ndarray) -> np.ndarray:
    """
    Computes the derivative for the Kuramoto model.
    d(theta_i)/dt = omega_i + (K/N) * sum(sin(theta_j - theta_i))
    """
    N = len(phases)
    dphases = np.zeros(N)
    
    # Vectorized computation
    # sin(theta_j - theta_i) = sin(theta_j)cos(theta_i) - cos(theta_j)sin(theta_i)
    sin_phases = np.sin(phases)
    cos_phases = np.cos(phases)
    
    # sum_j A_ij * sin(theta_j - theta_i)
    # = sum_j A_ij * (sin(theta_j)cos(theta_i) - cos(theta_j)sin(theta_i))
    # = cos(theta_i) * sum_j A_ij sin(theta_j) - sin(theta_i) * sum_j A_ij cos(theta_j)
    
    sin_sum = adjacency @ sin_phases
    cos_sum = adjacency @ cos_phases
    
    dphases = omega + (K / N) * (cos_phases * sin_sum - sin_phases * cos_sum)
    
    return dphases

def run_kuramoto_simulation(graph: nx.Graph, K: float, config: Dict[str, Any]) -> SimulationResult:
    """
    Runs the Kuramoto simulation on a given graph with coupling strength K.
    """
    N = graph.number_of_nodes()
    if N == 0:
        return SimulationResult(
            network_id="empty",
            threshold=0.0,
            status=SynchronizationStatus.ERROR,
            metrics={},
            r_parameter=0.0,
            t_parameter=0
        )

    # Natural frequencies (random for now, or from config)
    omega = np.random.RandomState(config.get('random_seed', 42)).randn(N)
    
    # Initial phases
    theta0 = np.random.RandomState(config.get('random_seed', 42)).rand(N) * 2 * np.pi
    
    # Adjacency matrix
    adjacency = nx.to_numpy_array(graph)
    
    # Simulation parameters
    t_span = (0, config.get('t_max', 100))
    t_eval = np.linspace(t_span[0], t_span[1], config.get('n_eval', 1000))
    
    # Solve ODE
    try:
        sol = solve_ivp(
            lambda t, y: kuramoto_derivative(t, y, K, omega, adjacency),
            t_span,
            theta0,
            method='RK45',
            t_eval=t_eval
        )
        
        if not sol.success:
            logger.error(f"Simulation failed: {sol.message}")
            return SimulationResult(
                network_id="failed",
                threshold=K,
                status=SynchronizationStatus.ERROR,
                metrics={},
                r_parameter=0.0,
                t_parameter=0
            )
        
        phases = sol.y
        # Compute order parameter over time
        r_values = [compute_order_parameter(phases[:, i]) for i in range(phases.shape[1])]
        
        # Check for synchronization: r > threshold for t > duration
        r_threshold = config.get('thresholds', {}).get('r', 0.8)
        t_threshold = config.get('thresholds', {}).get('t', 100)
        
        # Find if there's a period where r > r_threshold for at least t_threshold
        # We'll check the last part of the simulation
        # Simplified: check if the last 10% of time steps have r > r_threshold
        last_n = max(1, len(r_values) // 10)
        last_r = r_values[-last_n:]
        avg_r = np.mean(last_r)
        
        status = SynchronizationStatus.SYNCHRONIZED if avg_r > r_threshold else SynchronizationStatus.NOT_SYNCHRONIZED
        
        return SimulationResult(
            network_id="simulation",
            threshold=K,
            status=status,
            metrics={"final_r": float(np.mean(last_r))},
            r_parameter=avg_r,
            t_parameter=int(t_span[1])
        )
    except Exception as e:
        logger.error(f"Simulation error: {e}")
        return SimulationResult(
            network_id="error",
            threshold=K,
            status=SynchronizationStatus.ERROR,
            metrics={},
            r_parameter=0.0,
            t_parameter=0
        )

def find_critical_coupling(graph: nx.Graph, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Finds the critical coupling strength K_c using bisection search.
    """
    # Check for disconnected graph
    if check_disconnected(graph):
        logger.info("Graph is disconnected. Critical coupling is infinity.")
        return {
            "threshold": float('inf'),
            "status": SynchronizationStatus.DISCONNECTED
        }

    K_min = config.get('simulation', {}).get('k_range', [0, 5])[0]
    K_max = config.get('simulation', {}).get('k_range', [0, 5])[1]
    tolerance = config.get('simulation', {}).get('tolerance', 0.001)
    
    # Bisection search
    while K_max - K_min > tolerance:
        K_mid = (K_min + K_max) / 2
        result = run_kuramoto_simulation(graph, K_mid, config)
        
        if result.status == SynchronizationStatus.SYNCHRONIZED:
            K_max = K_mid
        else:
            K_min = K_mid
    
    K_c = (K_min + K_max) / 2
    logger.info(f"Critical coupling K_c found: {K_c:.4f}")
    
    return {
        "threshold": K_c,
        "status": SynchronizationStatus.SYNCHRONIZED
    }

def process_single_network(graph: nx.Graph, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processes a single network: checks connectivity, runs simulation, finds critical coupling.
    """
    if check_disconnected(graph):
        logger.info("Skipping simulation for disconnected graph.")
        return {
            "threshold": float('inf'),
            "status": "disconnected"
        }
    
    result = find_critical_coupling(graph, config)
    return result
