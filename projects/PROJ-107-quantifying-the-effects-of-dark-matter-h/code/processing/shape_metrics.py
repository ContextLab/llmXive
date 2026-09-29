import numpy as np
from typing import Tuple, Optional, Dict, Any, List, Union
import logging

logger = logging.getLogger(__name__)

def compute_axial_ratios(eigenvalues: np.ndarray) -> Tuple[float, float]:
    """
    Compute axial ratios b/a and c/a from eigenvalues of the reduced inertia tensor.
    Eigenvalues should be sorted in descending order (lambda_a >= lambda_b >= lambda_c).
    
    Args:
        eigenvalues: Array of 3 eigenvalues sorted descending.
        
    Returns:
        Tuple (b_a_ratio, c_a_ratio)
    """
    if len(eigenvalues) != 3:
        raise ValueError("Exactly 3 eigenvalues required.")
    
    # Sort descending
    sorted_eigs = np.sort(eigenvalues)[::-1]
    lambda_a, lambda_b, lambda_c = sorted_eigs
    
    # Avoid division by zero
    if lambda_a <= 0:
        raise ValueError("Largest eigenvalue must be positive.")
        
    b_a = np.sqrt(lambda_b / lambda_a)
    c_a = np.sqrt(lambda_c / lambda_a)
    
    return b_a, c_a

def compute_triaxiality(b_a: float, c_a: float) -> float:
    """
    Compute triaxiality T = (1 - (b/a)^2) / (1 - (c/a)^2).
    
    Args:
        b_a: Axial ratio b/a
        c_a: Axial ratio c/a
        
    Returns:
        Triaxiality value T in [0, 1]
    """
    denom = 1.0 - c_a**2
    if np.abs(denom) < 1e-10:
        # Near spherical, T approaches 0
        return 0.0
        
    num = 1.0 - b_a**2
    return num / denom

def compute_shape_metrics_from_eigenvalues(eigenvalues: np.ndarray) -> Dict[str, float]:
    """
    Compute all shape metrics from eigenvalues.
    
    Args:
        eigenvalues: Array of 3 eigenvalues.
        
    Returns:
        Dictionary with keys: 'b_a_ratio', 'c_a_ratio', 'triaxiality'
    """
    b_a, c_a = compute_axial_ratios(eigenvalues)
    T = compute_triaxiality(b_a, c_a)
    
    return {
        'b_a_ratio': b_a,
        'c_a_ratio': c_a,
        'triaxiality': T
    }

def filter_halo_by_particle_count(particle_count: int, min_particles: int = 10000) -> bool:
    """
    Check if halo has enough particles for reliable shape computation.
    
    Args:
        particle_count: Number of particles in the halo.
        min_particles: Minimum required particles (default 10,000).
        
    Returns:
        True if halo passes the filter, False otherwise.
    """
    return particle_count >= min_particles

def validate_shape_metrics(b_a: float, c_a: float, triaxiality: float) -> bool:
    """
    Validate that shape metrics are within physically meaningful ranges.
    
    Args:
        b_a: Axial ratio b/a
        c_a: Axial ratio c/a
        triaxiality: Triaxiality T
        
    Returns:
        True if valid, False otherwise.
    """
    if not (0.0 < b_a <= 1.0):
        return False
    if not (0.0 < c_a <= 1.0):
        return False
    if not (0.0 <= triaxiality <= 1.0):
        return False
    return True

def process_halo_shape(eigenvalues: np.ndarray, particle_count: int, min_particles: int = 10000) -> Optional[Dict[str, Any]]:
    """
    Process a single halo's shape metrics.
    
    Args:
        eigenvalues: Eigenvalues of the reduced inertia tensor.
        particle_count: Number of particles.
        min_particles: Minimum particle threshold.
        
    Returns:
        Dictionary with shape metrics if valid, None if excluded.
    """
    if not filter_halo_by_particle_count(particle_count, min_particles):
        return None
        
    try:
        metrics = compute_shape_metrics_from_eigenvalues(eigenvalues)
        if validate_shape_metrics(metrics['b_a_ratio'], metrics['c_a_ratio'], metrics['triaxiality']):
            return {
                'b_a_ratio': metrics['b_a_ratio'],
                'c_a_ratio': metrics['c_a_ratio'],
                'triaxiality': metrics['triaxiality']
            }
        else:
            logger.warning(f"Shape metrics out of range: {metrics}")
            return None
    except Exception as e:
        logger.warning(f"Failed to compute shape metrics: {e}")
        return None

def bin_halo_by_shape(c_a_ratio: float) -> str:
    """
    Bin a halo into shape categories based on c/a ratio.
    
    Categories:
    - 'prolate': c/a < 0.5
    - 'triaxial': 0.5 <= c/a <= 0.8
    - 'spherical': c/a > 0.8
    
    Args:
        c_a_ratio: The c/a axial ratio.
        
    Returns:
        String label for the shape bin.
    """
    if c_a_ratio < 0.5:
        return 'prolate'
    elif c_a_ratio <= 0.8:
        return 'triaxial'
    else:
        return 'spherical'

def compute_shape_metrics_from_halo(halo_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Compute shape metrics from a halo data dictionary.
    
    Args:
        halo_data: Dictionary containing 'eigenvalues' and 'particle_count'.
        
    Returns:
        Dictionary with shape metrics and bin, or None if excluded.
    """
    eigenvalues = halo_data.get('eigenvalues')
    particle_count = halo_data.get('particle_count', 0)
    
    if eigenvalues is None:
        return None
        
    result = process_halo_shape(eigenvalues, particle_count)
    if result is None:
        return None
        
    result['shape_bin'] = bin_halo_by_shape(result['c_a_ratio'])
    return result

def filter_halo_for_analysis(halo_data: Dict[str, Any]) -> bool:
    """
    Determine if a halo should be included in analysis based on particle count.
    
    Args:
        halo_data: Dictionary containing 'particle_count'.
        
    Returns:
        True if halo should be included, False otherwise.
    """
    particle_count = halo_data.get('particle_count', 0)
    return filter_halo_by_particle_count(particle_count, min_particles=10000)

def get_exclusion_reason(halo_data: Dict[str, Any]) -> str:
    """
    Get the reason why a halo was excluded from analysis.
    
    Args:
        halo_data: Dictionary containing halo information.
        
    Returns:
        String describing the exclusion reason.
    """
    particle_count = halo_data.get('particle_count', 0)
    if particle_count < 10000:
        return f"Insufficient particles: {particle_count} < 10000"
    return "Unknown reason"

def validate_and_filter_halo_list(halo_list: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Validate and filter a list of halos.
    
    Args:
        halo_list: List of halo dictionaries.
        
    Returns:
        Tuple of (valid_halos, excluded_halos)
    """
    valid_halos = []
    excluded_halos = []
    
    for halo in halo_list:
        if filter_halo_for_analysis(halo):
            valid_halos.append(halo)
        else:
            excluded_halos.append({
                'halo_id': halo.get('halo_id', 'unknown'),
                'reason': get_exclusion_reason(halo),
                'particle_count': halo.get('particle_count', 0)
            })
            
    return valid_halos, excluded_halos