"""
Integration tests for simulation module to ensure end-to-end correctness.
"""
import numpy as np
import networkx as nx
from simulation import run_kuramoto_simulation, check_disconnected
from data_models import SynchronizationStatus


def test_ring_graph_analytical_approximation():
    """
    Test against a Ring Graph (N=200) where analytical approximations exist.
    For a ring graph, the critical coupling K_c is related to the eigenvalue spectrum.
    We test that the simulation behaves reasonably (doesn't crash, returns valid r).
    """
    N = 200
    # Create a ring graph
    G = nx.cycle_graph(N)
    
    np.random.seed(42)
    initial_phases = np.random.uniform(0, 2 * np.pi, N)
    
    # Run with a K that is likely below critical for a ring (K_c ~ 1 for simple rings)
    K = 0.5
    dt = 0.1
    duration = 10.0
    
    result = run_kuramoto_simulation(G, initial_phases, K, dt, duration)
    
    assert result['r_final'] >= 0.0
    assert result['r_final'] <= 1.0
    assert np.all(np.isfinite(result['r_series']))
    # For K=0.5 on a ring, we expect partial or no synchronization
    # The exact value depends on initial conditions, but it should be stable.


def test_complete_graph_fast_sync():
    """
    A complete graph should synchronize very quickly.
    """
    N = 50
    G = nx.complete_graph(N)
    
    np.random.seed(42)
    initial_phases = np.random.uniform(0, 2 * np.pi, N)
    
    K = 1.0
    dt = 0.05
    duration = 5.0
    
    result = run_kuramoto_simulation(G, initial_phases, K, dt, duration)
    
    # Complete graphs synchronize almost instantly for K > 0
    assert result['status'] == SynchronizationStatus.SYNCHRONIZED
    assert result['r_final'] > 0.95  # Very high synchronization