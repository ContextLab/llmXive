import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import logging

def get_energy_profile(spin_config: np.ndarray, J: float = 1.0, h: float = 0.0) -> Dict[str, Any]:
    """Calculate the energy profile of a spin configuration.
    
    Args:
        spin_config: 1D numpy array of spins (+1 or -1).
        J: Coupling constant.
        h: External magnetic field.
    
    Returns:
        Dictionary containing energy statistics.
    """
    n_spins = len(spin_config)
    # Simple nearest neighbor energy (1D ring topology assumed for profile calculation 
    # or used as a scalar summary if topology is handled elsewhere)
    # For a general graph, this would need the adjacency matrix. 
    # Here we return the local energy density and total energy assuming a generic interaction
    # if not provided, we return a baseline profile.
    
    total_energy = 0.0
    # Assuming 1D ring for profile if no graph is passed, 
    # but typically this function is called with graph context in dynamics.
    # To be safe and generic:
    if n_spins < 2:
        return {
            "total_energy": 0.0,
            "energy_density": 0.0,
            "magnetization": float(np.sum(spin_config)),
            "magnetization_density": 0.0
        }

    # Placeholder for graph-based energy if adjacency not passed
    # In dynamics.py, we usually pass the graph. Here we calculate local contributions.
    # If called from dynamics with a graph, the graph interaction should be summed there.
    # We return the field contribution and a placeholder for interaction if not provided.
    field_energy = -h * np.sum(spin_config)
    
    # Return basic metrics
    return {
        "total_energy": float(field_energy), # Simplified if J not used or graph not passed
        "energy_density": float(field_energy / n_spins),
        "magnetization": float(np.sum(spin_config)),
        "magnetization_density": float(np.mean(spin_config))
    }

def calculate_spatial_variance(spin_config: np.ndarray, adj_matrix: np.ndarray = None) -> float:
    """Calculate the spatial variance of the spin configuration.
    
    Measures how much the spin values deviate from the mean, weighted by connectivity if provided.
    
    Args:
        spin_config: 1D numpy array of spins.
        adj_matrix: Optional adjacency matrix to weight variance by connectivity.
    
    Returns:
        Spatial variance as a float.
    """
    if len(spin_config) == 0:
        return 0.0
    
    mean_spin = np.mean(spin_config)
    
    if adj_matrix is not None:
        # Weighted variance based on connectivity
        # Variance of (spin_i - mean) * sum_neighbors
        deviations = spin_config - mean_spin
        # Sum of squared deviations weighted by degree (row sum of adj)
        degrees = np.sum(adj_matrix, axis=1)
        if np.sum(degrees) == 0:
            return float(np.var(spin_config))
        
        weighted_sq_dev = np.sum((deviations ** 2) * degrees)
        return float(weighted_sq_dev / np.sum(degrees))
    else:
        return float(np.var(spin_config))

def calculate_diffusion_rate(energy_history: List[float], time_steps: List[int]) -> float:
    """Estimate the diffusion rate from energy history.
    
    Args:
        energy_history: List of energy values over time.
        time_steps: List of corresponding time steps.
    
    Returns:
        Estimated diffusion rate (slope of energy change).
    """
    if len(energy_history) < 2:
        return 0.0
    
    energy_arr = np.array(energy_history)
    time_arr = np.array(time_steps)
    
    # Simple linear regression slope
    if np.std(time_arr) == 0:
        return 0.0
    
    slope, _, _, _, _ = np.polyfit(time_arr, energy_arr, 1, full=False)
    return float(slope)
