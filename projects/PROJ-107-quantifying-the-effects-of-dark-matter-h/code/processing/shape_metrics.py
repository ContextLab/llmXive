import numpy as np
from typing import Tuple, Optional, Dict, Any, List, Union
import logging
import os

logger = logging.getLogger(__name__)

# Constants for shape binning
PROLATE_THRESHOLD = 0.5
TRIAXIAL_UPPER_THRESHOLD = 0.8
MIN_PARTICLE_COUNT = 10000

def compute_axial_ratios(eigenvalues: np.ndarray) -> Tuple[float, float]:
    """
    Compute axial ratios b/a and c/a from eigenvalues of the inertia tensor.
    
    Args:
        eigenvalues: Array of 3 eigenvalues (sorted descending: lambda_1 >= lambda_2 >= lambda_3)
    
    Returns:
        Tuple of (b/a, c/a) ratios.
        b/a = sqrt(lambda_2 / lambda_1)
        c/a = sqrt(lambda_3 / lambda_1)
    """
    if len(eigenvalues) != 3:
        raise ValueError(f"Expected 3 eigenvalues, got {len(eigenvalues)}")
    
    # Sort descending to ensure lambda_1 is the largest
    sorted_eigs = np.sort(eigenvalues)[::-1]
    lambda_1, lambda_2, lambda_3 = sorted_eigs
    
    # Avoid division by zero
    if lambda_1 <= 0:
        raise ValueError("Largest eigenvalue must be positive")
    
    b_a = np.sqrt(lambda_2 / lambda_1)
    c_a = np.sqrt(lambda_3 / lambda_1)
    
    # Clamp to valid range [0, 1] to handle numerical noise
    b_a = np.clip(b_a, 0.0, 1.0)
    c_a = np.clip(c_a, 0.0, 1.0)
    
    return b_a, c_a

def compute_triaxiality(b_a: float, c_a: float) -> float:
    """
    Compute triaxiality parameter T from axial ratios.
    
    T = (1 - (b/a)^2) / (1 - (c/a)^2)
    T = 0 -> Oblate (spherical disk)
    T = 1 -> Prolate (cigar shape)
    
    Args:
        b_a: b/a axial ratio
        c_a: c/a axial ratio
    
    Returns:
        Triaxiality parameter T in [0, 1]
    """
    if c_a >= 1.0:
        # Spherical case, T is undefined but we return 0
        return 0.0
    
    numerator = 1.0 - (b_a ** 2)
    denominator = 1.0 - (c_a ** 2)
    
    if denominator <= 0:
        # Numerical edge case
        return 0.0
    
    T = numerator / denominator
    
    # Clamp to valid range [0, 1]
    T = np.clip(T, 0.0, 1.0)
    
    return T

def compute_shape_metrics_from_eigenvalues(eigenvalues: np.ndarray) -> Dict[str, float]:
    """
    Compute all shape metrics from eigenvalues.
    
    Args:
        eigenvalues: Array of 3 eigenvalues
    
    Returns:
        Dictionary with keys: 'b_a_ratio', 'c_a_ratio', 'triaxiality'
    """
    b_a, c_a = compute_axial_ratios(eigenvalues)
    T = compute_triaxiality(b_a, c_a)
    
    return {
        'b_a_ratio': float(b_a),
        'c_a_ratio': float(c_a),
        'triaxiality': float(T)
    }

def filter_halo_by_particle_count(particle_count: int, min_count: int = MIN_PARTICLE_COUNT) -> bool:
    """
    Check if a halo meets the minimum particle count requirement.
    
    Args:
        particle_count: Number of particles in the halo
        min_count: Minimum required particle count (default: 10,000)
    
    Returns:
        True if halo should be included, False if it should be excluded
    """
    return particle_count >= min_count

def validate_shape_metrics(metrics: Dict[str, float]) -> Tuple[bool, Optional[str]]:
    """
    Validate that shape metrics are within physically meaningful ranges.
    
    Args:
        metrics: Dictionary with 'b_a_ratio', 'c_a_ratio', 'triaxiality'
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    b_a = metrics.get('b_a_ratio')
    c_a = metrics.get('c_a_ratio')
    T = metrics.get('triaxiality')
    
    if b_a is None or c_a is None or T is None:
        return False, "Missing required shape metrics"
    
    # b/a must be in (0, 1]
    if not (0 < b_a <= 1.0):
        return False, f"b/a ratio {b_a} out of range (0, 1]"
    
    # c/a must be in (0, 1]
    if not (0 < c_a <= 1.0):
        return False, f"c/a ratio {c_a} out of range (0, 1]"
    
    # Triaxiality must be in [0, 1]
    if not (0 <= T <= 1.0):
        return False, f"Triaxiality {T} out of range [0, 1]"
    
    # Additionally, c/a should be <= b/a (by definition of sorting)
    if c_a > b_a:
        logger.warning(f"c/a ({c_a}) > b/a ({b_a}), likely numerical issue")
    
    return True, None

def process_halo_shape(eigenvalues: np.ndarray) -> Dict[str, float]:
    """
    Process a halo's shape from its eigenvalues.
    
    Args:
        eigenvalues: Array of 3 eigenvalues from inertia tensor
    
    Returns:
        Dictionary with shape metrics
    """
    metrics = compute_shape_metrics_from_eigenvalues(eigenvalues)
    is_valid, error = validate_shape_metrics(metrics)
    
    if not is_valid:
        raise ValueError(f"Invalid shape metrics: {error}")
    
    return metrics

def bin_halo_by_shape(c_a_ratio: float) -> str:
    """
    Assign a halo to a shape bin based on c/a ratio.
    
    Bins:
    - 'prolate': c/a < 0.5
    - 'triaxial': 0.5 <= c/a <= 0.8
    - 'spherical': c/a > 0.8
    
    Args:
        c_a_ratio: c/a axial ratio
    
    Returns:
        Shape bin label
    """
    if c_a_ratio < PROLATE_THRESHOLD:
        return 'prolate'
    elif c_a_ratio <= TRIAXIAL_UPPER_THRESHOLD:
        return 'triaxial'
    else:
        return 'spherical'

def compute_shape_metrics_from_halo(halo_data: Dict[str, Any]) -> Optional[Dict[str, float]]:
    """
    Compute shape metrics from a halo dictionary containing eigenvalues.
    
    Args:
        halo_data: Dictionary with 'eigenvalues' key (array of 3 floats)
    
    Returns:
        Dictionary with shape metrics, or None if computation fails
    """
    try:
        eigenvalues = np.array(halo_data['eigenvalues'])
        return process_halo_shape(eigenvalues)
    except Exception as e:
        logger.warning(f"Failed to compute shape metrics: {e}")
        return None

def filter_halo_for_analysis(halo_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Check if a halo should be included in analysis based on particle count.
    
    Args:
        halo_data: Dictionary with 'particle_count' key
    
    Returns:
        Tuple of (include_halo, exclusion_reason)
        - (True, "") if halo should be included
        - (False, reason) if halo should be excluded
    """
    particle_count = halo_data.get('particle_count', 0)
    
    if particle_count < MIN_PARTICLE_COUNT:
        return False, f"particle_count={particle_count} < {MIN_PARTICLE_COUNT}"
    
    return True, ""

def get_exclusion_reason(halo_data: Dict[str, Any]) -> str:
    """
    Get the reason why a halo was excluded from analysis.
    
    Args:
        halo_data: Dictionary with halo information
    
    Returns:
        Exclusion reason string, or empty string if not excluded
    """
    include, reason = filter_halo_for_analysis(halo_data)
    return reason if not include else ""

def validate_and_filter_halo_list(halo_list: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter a list of halos based on particle count and validate shape metrics.
    
    Args:
        halo_list: List of halo dictionaries
    
    Returns:
        Tuple of (valid_halos, excluded_halos_with_reasons)
        - valid_halos: List of halos that passed all filters
        - excluded_halos_with_reasons: List of dicts with 'halo' and 'reason' keys
    """
    valid_halos = []
    excluded_halos = []
    
    for halo in halo_list:
        include, reason = filter_halo_for_analysis(halo)
        
        if not include:
            excluded_halos.append({
                'halo_id': halo.get('halo_id', 'unknown'),
                'reason': reason,
                'particle_count': halo.get('particle_count', 0)
            })
            continue
        
        # Try to compute shape metrics
        try:
            shape_metrics = compute_shape_metrics_from_halo(halo)
            if shape_metrics is not None:
                halo['shape_metrics'] = shape_metrics
                valid_halos.append(halo)
            else:
                excluded_halos.append({
                    'halo_id': halo.get('halo_id', 'unknown'),
                    'reason': 'Failed to compute shape metrics',
                    'particle_count': halo.get('particle_count', 0)
                })
        except Exception as e:
            excluded_halos.append({
                'halo_id': halo.get('halo_id', 'unknown'),
                'reason': f'Exception during shape computation: {str(e)}',
                'particle_count': halo.get('particle_count', 0)
            })
    
    logger.info(f"Filtered halos: {len(valid_halos)} valid, {len(excluded_halos)} excluded")
    return valid_halos, excluded_halos