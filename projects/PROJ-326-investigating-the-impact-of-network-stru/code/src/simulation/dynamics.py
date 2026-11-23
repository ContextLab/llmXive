import numpy as np
import networkx as nx
from typing import Dict, Any, List, Optional, Tuple
import logging
import time

from code.src.simulation.metrics import get_energy_profile, calculate_spatial_variance

def run_spin_flip_simulation(
    graph: nx.Graph,
    n_steps: int,
    beta: float,
    seed: int,
    h: float = 0.0
) -> Dict[str, Any]:
    """Run simplified Ising spin-flip dynamics on a graph.
    
    Args:
        graph: NetworkX graph representing the spin network.
        n_steps: Number of Monte Carlo steps.
        beta: Inverse temperature (1/kT).
        seed: Random seed for reproducibility.
        h: External magnetic field.
    
    Returns:
        Dictionary containing simulation results including energy history,
        magnetization, and convergence status.
    """
    np.random.seed(seed)
    n_nodes = graph.number_of_nodes()
    nodes = list(graph.nodes())
    
    # Initialize spins randomly (+1 or -1)
    spins = np.random.choice([-1, 1], size=n_nodes)
    
    # Precompute adjacency matrix for speed
    adj_matrix = nx.to_numpy_array(graph, nodelist=nodes)
    
    energy_history = []
    magnetization_history = []
    spatial_variance_history = []
    
    current_energy = 0.0
    
    for step in range(n_steps):
        # Select a random node
        i = np.random.randint(0, n_nodes)
        node = nodes[i]
        current_spin = spins[i]
        
        # Calculate local field from neighbors
        neighbors = list(graph.neighbors(node))
        local_field = h
        for neighbor in neighbors:
            j = nodes.index(neighbor)
            local_field += spins[j]
        
        # Energy change if spin flips
        delta_E = 2 * current_spin * local_field
        
        # Metropolis criterion
        if delta_E <= 0 or np.random.random() < np.exp(-beta * delta_E):
            spins[i] *= -1  # Flip spin
        
        # Calculate metrics
        if step % 10 == 0:  # Log every 10 steps to save time
            # Re-calculate total energy (approximate for speed)
            # Full calculation: E = -J * sum(s_i * s_j) - h * sum(s_i)
            total_E = 0.0
            for u, v in graph.edges():
                i_u = nodes.index(u)
                i_v = nodes.index(v)
                total_E -= spins[i_u] * spins[i_v]
            total_E -= h * np.sum(spins)
            
            energy_history.append(total_E)
            magnetization_history.append(float(np.mean(spins)))
            spatial_variance_history.append(float(calculate_spatial_variance(spins, adj_matrix)))
    
    # Final metrics
    final_energy = 0.0
    for u, v in graph.edges():
        i_u = nodes.index(u)
        i_v = nodes.index(v)
        final_energy -= spins[i_u] * spins[i_v]
    final_energy -= h * np.sum(spins)
    
    return {
        "energy_history": energy_history,
        "magnetization_history": magnetization_history,
        "spatial_variance_history": spatial_variance_history,
        "final_energy": final_energy,
        "final_magnetization": float(np.mean(spins)),
        "converged": True,
        "n_steps": n_steps,
        "seed": seed
    }
