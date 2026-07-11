"""
Shape metrics computation and binning logic.
Includes axial ratios, triaxiality, filtering, validation, and shape binning.
"""
import numpy as np
from typing import Tuple, Optional, Dict, Any, List, Union

def compute_axial_ratios(eigenvalues: np.ndarray) -> Tuple[float, float]:
    """
    Compute axial ratios b/a and c/a from eigenvalues of the inertia tensor.
    Eigenvalues are assumed to be sorted in descending order (lambda1 >= lambda2 >= lambda3).
    Axial ratios are calculated as sqrt(lambda2/lambda1) and sqrt(lambda3/lambda1).
    
    Args:
        eigenvalues: Array of 3 eigenvalues sorted descending.
        
    Returns:
        Tuple (b/a, c/a)
    """
    if len(eigenvalues) != 3:
        raise ValueError("Eigenvalues array must contain exactly 3 values.")
    
    lambda1, lambda2, lambda3 = eigenvalues
    
    if lambda1 <= 0:
        raise ValueError("Largest eigenvalue must be positive.")
        
    b_a = np.sqrt(lambda2 / lambda1)
    c_a = np.sqrt(lambda3 / lambda1)
    
    return b_a, c_a

def compute_triaxiality(b_a: float, c_a: float) -> float:
    """
    Compute triaxiality T = (1 - (b/a)^2) / (1 - (c/a)^2).
    T ranges from 0 (prolate) to 1 (oblate).
    
    Args:
        b_a: Axial ratio b/a.
        c_a: Axial ratio c/a.
        
    Returns:
        Triaxiality value T.
    """
    denominator = 1 - c_a**2
    if abs(denominator) < 1e-9:
        # If c/a is very close to 1, the halo is nearly spherical.
        # Triaxiality is undefined or 0.5? 
        # Usually, for spherical, T is not well defined, but we can return 0.5 or handle it.
        # Let's return 0.5 as a neutral value or raise a warning.
        # For now, return 0.5 to avoid division by zero.
        return 0.5
        
    numerator = 1 - b_a**2
    return numerator / denominator

def compute_shape_metrics_from_eigenvalues(eigenvalues: np.ndarray) -> Dict[str, float]:
    """
    Compute all shape metrics from eigenvalues.
    
    Args:
        eigenvalues: Array of 3 eigenvalues.
        
    Returns:
        Dictionary with 'b_a', 'c_a', 'triaxiality'.
    """
    b_a, c_a = compute_axial_ratios(eigenvalues)
    triaxiality = compute_triaxiality(b_a, c_a)
    
    return {
        'b_a': b_a,
        'c_a': c_a,
        'triaxiality': triaxiality
    }

def filter_halo_by_particle_count(halo: Dict[str, Any], min_particles: int = 10000) -> bool:
    """
    Check if a halo has enough particles to be included in the analysis.
    
    Args:
        halo: Dictionary containing halo data, must have 'NumPart' or similar key.
        min_particles: Minimum number of particles required.
        
    Returns:
        True if halo should be included, False otherwise.
    """
    num_particles = halo.get('NumPart', 0)
    return num_particles >= min_particles

def validate_shape_metrics(metrics: Dict[str, float]) -> bool:
    """
    Validate that computed shape metrics are within expected physical ranges.
    0 < b/a <= 1
    0 < c/a <= 1
    0 <= triaxiality <= 1
    
    Args:
        metrics: Dictionary with 'b_a', 'c_a', 'triaxiality'.
        
    Returns:
        True if valid, False otherwise.
    """
    b_a = metrics.get('b_a', -1)
    c_a = metrics.get('c_a', -1)
    triaxiality = metrics.get('triaxiality', -1)
    
    if not (0 < b_a <= 1):
        return False
    if not (0 < c_a <= 1):
        return False
    if not (0 <= triaxiality <= 1):
        return False
        
    return True

def process_halo_shape(eigenvalues: np.ndarray) -> Optional[Dict[str, float]]:
    """
    Process a single halo's eigenvalues to compute and validate shape metrics.
    
    Args:
        eigenvalues: Array of 3 eigenvalues.
        
    Returns:
        Dictionary with shape metrics if valid, None otherwise.
    """
    try:
        metrics = compute_shape_metrics_from_eigenvalues(eigenvalues)
        if validate_shape_metrics(metrics):
            return metrics
        else:
            return None
    except Exception:
        return None

def bin_halo_by_shape(c_a: float) -> str:
    """
    Classify a halo into shape bins based on its c/a ratio.
    
    Bins:
    - 'prolate': c/a < 0.5
    - 'triaxial': 0.5 <= c/a <= 0.8
    - 'spherical': c/a > 0.8
    
    Args:
        c_a: The c/a axial ratio.
        
    Returns:
        String label for the shape bin.
        
    Raises:
        ValueError: If c_a is not in the valid range (0, 1].
    """
    if not (0 < c_a <= 1):
        raise ValueError(f"Invalid c/a ratio: {c_a}. Must be in (0, 1].")
        
    if c_a < 0.5:
        return 'prolate'
    elif c_a <= 0.8:
        return 'triaxial'
    else:
        return 'spherical'

def compute_shape_metrics_from_halo(halo_data: Dict[str, Any]) -> Optional[Dict[str, float]]:
    """
    Compute shape metrics from a full halo data dictionary.
    Assumes halo_data contains 'eigenvalues' key.
    
    Args:
        halo_data: Dictionary containing halo data including eigenvalues.
        
    Returns:
        Dictionary with shape metrics if valid, None otherwise.
    """
    eigenvalues = halo_data.get('eigenvalues')
    if eigenvalues is None:
        return None
        
    return process_halo_shape(np.array(eigenvalues))