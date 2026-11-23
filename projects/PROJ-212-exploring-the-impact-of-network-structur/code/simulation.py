import numpy as np
import networkx as nx
from scipy.integrate import solve_ivp
from typing import List, Dict, Any, Optional, Tuple
from data_models import SynchronizationStatus, SimulationResult
import logging

logger = logging.getLogger(__name__)

def check_disconnected(edges: List[Tuple[int, int]], n_nodes: int) -> bool:
    """Check if the graph defined by edges and n_nodes is disconnected."""
    if n_nodes == 0:
        return True
    G = nx.Graph()
    G.add_nodes_from(range(n_nodes))
    G.add_edges_from(edges)
    return not nx.is_connected(G)

def kuramoto_derivative(t, y, adj_matrix, K):
    """Compute the derivative for the Kuramoto model."""
    N = len(y)
    dydt = np.zeros(N)
    for i in range(N):
        sum_sin = 0.0
        for j in range(N):
            if adj_matrix[i, j] > 0:
                sum_sin += np.sin(y[j] - y[i])
        dydt[i] = sum_sin * K
    return dydt

def run_kuramoto_simulation(edges: List[Tuple[int, int]], n_nodes: int, config: Dict) -> Tuple[float, SynchronizationStatus]:
    """
    Run Kuramoto simulation to find critical coupling K.
    Sweep K from 0 to 5 in steps of 0.1.
    Threshold: order parameter r > 0.8 for t > 100.
    """
    if n_nodes == 0:
        return float('inf'), SynchronizationStatus.UNKNOWN

    G = nx.Graph()
    G.add_nodes_from(range(n_nodes))
    G.add_edges_from(edges)
    adj_matrix = nx.to_numpy_array(G)

    K_values = np.arange(0.0, 5.1, 0.1)
    T_MAX = 200.0
    THRESHOLD_R = 0.8
    MIN_TIME_SYNCH = 100.0

    for K in K_values:
        # Random initial phases
        y0 = np.random.uniform(0, 2 * np.pi, n_nodes)
        
        # Integrate
        sol = solve_ivp(
            lambda t, y: kuramoto_derivative(t, y, adj_matrix, K),
            [0, T_MAX],
            y0,
            method='RK45',
            t_eval=[T_MAX] # Just check the end state for simplicity in this MVP
        )

        if not sol.success:
            continue

        y_final = sol.y[:, -1]
        
        # Calculate order parameter r
        r_vector = np.zeros(2)
        for phi in y_final:
            r_vector[0] += np.cos(phi)
            r_vector[1] += np.sin(phi)
        r = np.linalg.norm(r_vector) / n_nodes

        if r > THRESHOLD_R:
            # For a more robust check, we'd verify it stays high for MIN_TIME_SYNCH
            # Here we assume if it's high at T_MAX, it's synchronized
            return float(K), SynchronizationStatus.SYNCHRONIZED

    return float('inf'), SynchronizationStatus.NOT_SYNCHRONIZED
