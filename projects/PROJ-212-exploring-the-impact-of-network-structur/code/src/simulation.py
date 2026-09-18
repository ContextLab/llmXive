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
    
    Args:
        G: NetworkX graph to check
        
    Returns:
        True if the graph is disconnected, False otherwise
    """
    if G.number_of_nodes() == 0:
        logger.warning("Graph has no nodes, treating as disconnected")
        return True
        
    if not nx.is_connected(G):
        logger.warning("Graph is disconnected")
        return True
        
    return False

def kuramoto_derivative(t: float, y: np.ndarray, K: float, adj_matrix: np.ndarray) -> np.ndarray:
    """
    Compute the derivative for the Kuramoto model.
    
    Args:
        t: Current time (unused, but required by solve_ivp)
        y: Current phase angles
        K: Coupling strength
        adj_matrix: Adjacency matrix of the network
        
    Returns:
        Array of phase derivatives
    """
    N = len(y)
    dydt = np.zeros(N)
    
    # Compute sin(theta_j - theta_i) for all pairs
    diff = y[:, np.newaxis] - y[np.newaxis, :]
    sin_diff = np.sin(diff)
    
    # Compute sum over neighbors for each node
    for i in range(N):
        dydt[i] = (K / N) * np.sum(adj_matrix[i, :] * sin_diff[i, :])
        
    return dydt

def compute_order_parameter(phases: np.ndarray) -> float:
    """
    Compute the Kuramoto order parameter R.
    
    Args:
        phases: Array of phase angles
        
    Returns:
        Order parameter R (0 <= R <= 1)
    """
    if len(phases) == 0:
        return 0.0
        
    # Compute the complex order parameter
    z = np.mean(np.exp(1j * phases))
    return np.abs(z)

def run_kuramoto_simulation(
    G: nx.Graph,
    k_values: Optional[List[float]] = None,
    t_max: float = 200.0,
    dt: float = 0.01,
    threshold_r: float = 0.8,
    threshold_t: int = 100,
    random_seed: Optional[int] = None
) -> SimulationResult:
    """
    Run Kuramoto synchronization simulation on a network.
    
    Args:
        G: NetworkX graph representing the network
        k_values: List of coupling strengths to test. Defaults to [0, 5] step 0.1
        t_max: Maximum simulation time
        dt: Time step for integration
        threshold_r: Minimum order parameter for synchronization
        threshold_t: Minimum duration of synchronization
        random_seed: Random seed for initial phases
        
    Returns:
        SimulationResult containing the critical coupling strength and metrics
    """
    if k_values is None:
        k_values = list(np.arange(0.0, 5.1, 0.1))
        
    N = G.number_of_nodes()
    
    if N == 0:
        logger.error("Cannot simulate on empty graph")
        return SimulationResult(
            critical_k=float('inf'),
            synchronization_status=SynchronizationStatus.DISCONNECTED,
            metrics={},
            raw_data=None
        )
    
    # Check for disconnected graph - early exit logic
    if check_disconnected(G):
        logger.info("Graph is disconnected, skipping K-sweep, returning infinity")
        return SimulationResult(
            critical_k=float('inf'),
            synchronization_status=SynchronizationStatus.DISCONNECTED,
            metrics={
                'num_nodes': N,
                'num_edges': G.number_of_edges(),
                'is_connected': False,
                'critical_k': float('inf'),
                'status': 'disconnected'
            },
            raw_data=None
        )
    
    # Convert graph to adjacency matrix
    adj_matrix = nx.to_numpy_array(G)
    
    # Set random seed for reproducibility
    if random_seed is not None:
        np.random.seed(random_seed)
        
    # Initialize phases randomly
    initial_phases = np.random.uniform(0, 2 * np.pi, N)
    
    # Track synchronization status for each K
    sync_results = []
    
    for K in k_values:
        # Solve the differential equation
        t_eval = np.arange(0, t_max, dt)
        
        try:
            sol = solve_ivp(
                lambda t, y: kuramoto_derivative(t, y, K, adj_matrix),
                [0, t_max],
                initial_phases,
                method='RK45',
                t_eval=t_eval
            )
            
            if not sol.success:
                logger.warning(f"Integration failed for K={K}: {sol.message}")
                sync_results.append((K, 0.0, False))
                continue
            
            # Compute order parameter over time
            phases = sol.y.T
            order_params = np.array([compute_order_parameter(p) for p in phases])
            
            # Check for sustained synchronization
            # Find the last threshold_t points and check if R > threshold_r
            if len(order_params) >= threshold_t:
                recent_params = order_params[-threshold_t:]
                avg_recent = np.mean(recent_params)
                sustained = np.all(recent_params > threshold_r)
            else:
                avg_recent = np.mean(order_params)
                sustained = avg_recent > threshold_r
                
            sync_results.append((K, avg_recent, sustained))
            
        except Exception as e:
            logger.error(f"Error running simulation for K={K}: {e}")
            sync_results.append((K, 0.0, False))
    
    # Find critical K (first K where sustained synchronization occurs)
    critical_k = float('inf')
    synchronization_status = SynchronizationStatus.NOT_SYNCHRONIZED
    
    for K, avg_r, sustained in sync_results:
        if sustained:
            critical_k = K
            synchronization_status = SynchronizationStatus.SYNCHRONIZED
            break
        
    # If no sustained synchronization found, check if any partial synchronization
    if synchronization_status == SynchronizationStatus.NOT_SYNCHRONIZED:
        max_r = max(avg_r for _, avg_r, _ in sync_results)
        if max_r > threshold_r:
            synchronization_status = SynchronizationStatus.PARTIALLY_SYNCHRONIZED
        
    # Prepare metrics
    metrics = {
        'num_nodes': N,
        'num_edges': G.number_of_edges(),
        'is_connected': True,
        'critical_k': critical_k,
        'status': synchronization_status.value,
        'k_values_tested': len(k_values),
        'max_order_parameter': max(avg_r for _, avg_r, _ in sync_results) if sync_results else 0.0
    }
    
    # Store raw data for analysis
    raw_data = {
        'k_values': [K for K, _, _ in sync_results],
        'order_parameters': [avg_r for _, avg_r, _ in sync_results],
        'sustained': [sustained for _, _, sustained in sync_results]
    }
    
    logger.info(f"Simulation complete for {N} nodes: critical_k = {critical_k}, status = {synchronization_status}")
    
    return SimulationResult(
        critical_k=critical_k,
        synchronization_status=synchronization_status,
        metrics=metrics,
        raw_data=raw_data
    )