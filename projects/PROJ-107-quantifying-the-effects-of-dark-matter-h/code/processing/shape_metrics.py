"""
Shape metrics computation for dark matter haloes.

This module provides functions to compute axial ratios, triaxiality,
and bin haloes based on their shape properties.
"""

import numpy as np
from typing import Tuple, Optional, Dict, Any, List, Union
import logging
import os

logger = logging.getLogger(__name__)


def compute_axial_ratios(eigenvalues: np.ndarray) -> Tuple[float, float]:
    """
    Compute axial ratios b/a and c/a from inertia tensor eigenvalues.

    Args:
        eigenvalues: Array of eigenvalues [lambda_a, lambda_b, lambda_c] sorted
                    such that lambda_a >= lambda_b >= lambda_c.

    Returns:
        Tuple of (b/a, c/a) ratios.
    """
    if len(eigenvalues) != 3:
        raise ValueError(f"Expected 3 eigenvalues, got {len(eigenvalues)}")

    # Sort eigenvalues in descending order
    sorted_eigenvalues = np.sort(eigenvalues)[::-1]
    lambda_a, lambda_b, lambda_c = sorted_eigenvalues

    # Avoid division by zero
    if lambda_a <= 0:
        logger.warning("Primary eigenvalue is non-positive, returning NaN ratios")
        return (np.nan, np.nan)

    b_a_ratio = np.sqrt(lambda_b / lambda_a)
    c_a_ratio = np.sqrt(lambda_c / lambda_a)

    return (b_a_ratio, c_a_ratio)


def compute_triaxiality(b_a_ratio: float, c_a_ratio: float) -> float:
    """
    Compute triaxiality parameter T from axial ratios.

    T = (1 - (b/a)^2) / (1 - (c/a)^2)

    Args:
        b_a_ratio: The b/a axial ratio.
        c_a_ratio: The c/a axial ratio.

    Returns:
        Triaxiality parameter T in range [0, 1].
    """
    if c_a_ratio >= 1.0 or c_a_ratio <= 0:
        logger.warning(f"Invalid c/a ratio: {c_a_ratio}, returning NaN triaxiality")
        return np.nan

    numerator = 1 - (b_a_ratio ** 2)
    denominator = 1 - (c_a_ratio ** 2)

    if denominator == 0:
        logger.warning("Denominator is zero, returning NaN triaxiality")
        return np.nan

    T = numerator / denominator

    # Clamp to valid range [0, 1]
    T = max(0.0, min(1.0, T))

    return T


def compute_shape_metrics_from_eigenvalues(eigenvalues: np.ndarray) -> Dict[str, float]:
    """
    Compute all shape metrics from eigenvalues.

    Args:
        eigenvalues: Array of eigenvalues [lambda_a, lambda_b, lambda_c].

    Returns:
        Dictionary with keys: 'b_a_ratio', 'c_a_ratio', 'triaxiality'.
    """
    b_a, c_a = compute_axial_ratios(eigenvalues)
    triaxiality = compute_triaxiality(b_a, c_a)

    return {
        'b_a_ratio': float(b_a),
        'c_a_ratio': float(c_a),
        'triaxiality': float(triaxiality)
    }


def filter_halo_by_particle_count(particle_count: int, min_particles: int = 10000) -> bool:
    """
    Check if a halo meets the minimum particle count threshold.

    Args:
        particle_count: Number of particles in the halo.
        min_particles: Minimum required particles (default: 10000).

    Returns:
        True if halo passes the filter, False otherwise.
    """
    return particle_count >= min_particles


def validate_shape_metrics(
    b_a_ratio: float,
    c_a_ratio: float,
    triaxiality: float
) -> Tuple[bool, Optional[str]]:
    """
    Validate that shape metrics are within physically meaningful bounds.

    Bounds:
        0 < b/a <= 1
        0 < c/a <= 1
        0 <= T <= 1

    Args:
        b_a_ratio: The b/a axial ratio.
        c_a_ratio: The c/a axial ratio.
        triaxiality: The triaxiality parameter.

    Returns:
        Tuple of (is_valid, error_message).
        If valid, error_message is None.
    """
    if not (0 < b_a_ratio <= 1):
        return (False, f"b/a ratio {b_a_ratio} out of bounds (0, 1]")

    if not (0 < c_a_ratio <= 1):
        return (False, f"c/a ratio {c_a_ratio} out of bounds (0, 1]")

    if not (0 <= triaxiality <= 1):
        return (False, f"Triaxiality {triaxiality} out of bounds [0, 1]")

    return (True, None)


def process_halo_shape(
    eigenvalues: np.ndarray,
    particle_count: int,
    min_particles: int = 10000
) -> Optional[Dict[str, float]]:
    """
    Process a single halo's shape metrics.

    Args:
        eigenvalues: Array of eigenvalues.
        particle_count: Number of particles in the halo.
        min_particles: Minimum particle threshold.

    Returns:
        Dictionary of shape metrics if valid, None if halo is excluded.
    """
    # Check particle count
    if not filter_halo_by_particle_count(particle_count, min_particles):
        logger.debug(f"Halo excluded: particle count {particle_count} < {min_particles}")
        return None

    # Compute metrics
    metrics = compute_shape_metrics_from_eigenvalues(eigenvalues)

    # Validate
    is_valid, error = validate_shape_metrics(
        metrics['b_a_ratio'],
        metrics['c_a_ratio'],
        metrics['triaxiality']
    )

    if not is_valid:
        logger.warning(f"Invalid shape metrics: {error}")
        return None

    metrics['particle_count'] = particle_count

    return metrics


def bin_halo_by_shape(c_a_ratio: float) -> str:
    """
    Assign a halo to a shape bin based on c/a ratio.

    Bins (as defined in FR-003/FR-004):
        - 'prolate': c/a < 0.5
        - 'triaxial': 0.5 <= c/a <= 0.8
        - 'spherical': c/a > 0.8

    Args:
        c_a_ratio: The c/a axial ratio.

    Returns:
        String bin label: 'prolate', 'triaxial', or 'spherical'.
    """
    if c_a_ratio < 0.5:
        return 'prolate'
    elif c_a_ratio <= 0.8:
        return 'triaxial'
    else:
        return 'spherical'


def compute_shape_metrics_from_halo(
    positions: np.ndarray,
    masses: Optional[np.ndarray] = None,
    min_particles: int = 10000
) -> Optional[Dict[str, Any]]:
    """
    Compute shape metrics directly from halo particle positions.

    Args:
        positions: Array of particle positions (N, 3).
        masses: Optional array of particle masses. If None, equal masses assumed.
        min_particles: Minimum particle count threshold.

    Returns:
        Dictionary with shape metrics and metadata, or None if excluded.
    """
    particle_count = len(positions)

    if particle_count < min_particles:
        logger.debug(f"Halo excluded: particle count {particle_count} < {min_particles}")
        return None

    # Compute reduced inertia tensor
    from processing.inertia_tensor import compute_reduced_inertia_tensor, compute_eigenvalues_and_eigenvectors

    inertia_tensor = compute_reduced_inertia_tensor(positions, masses)
    eigenvalues, _ = compute_eigenvalues_and_eigenvectors(inertia_tensor)

    # Compute metrics
    metrics = compute_shape_metrics_from_eigenvalues(eigenvalues)
    metrics['particle_count'] = particle_count

    # Assign shape bin
    metrics['shape_bin'] = bin_halo_by_shape(metrics['c_a_ratio'])

    return metrics


def filter_halo_for_analysis(
    halo_data: Dict[str, Any],
    min_particles: int = 10000
) -> bool:
    """
    Filter haloes for analysis based on multiple criteria.

    Args:
        halo_data: Dictionary containing halo information.
        min_particles: Minimum particle count threshold.

    Returns:
        True if halo should be included in analysis, False otherwise.
    """
    particle_count = halo_data.get('num_particles', 0)

    if particle_count < min_particles:
        return False

    # Additional filters can be added here as needed

    return True


def get_exclusion_reason(halo_data: Dict[str, Any]) -> Optional[str]:
    """
    Determine the reason for excluding a halo from analysis.

    Args:
        halo_data: Dictionary containing halo information.

    Returns:
        String describing the exclusion reason, or None if included.
    """
    particle_count = halo_data.get('num_particles', 0)

    if particle_count < 10000:
        return f"insufficient_particles ({particle_count} < 10000)"

    # Check for valid shape metrics if already computed
    b_a = halo_data.get('b_a_ratio')
    c_a = halo_data.get('c_a_ratio')
    triax = halo_data.get('triaxiality')

    if b_a is not None:
        is_valid, error = validate_shape_metrics(b_a, c_a, triax)
        if not is_valid:
            return f"invalid_shape_metrics: {error}"

    return None


def validate_and_filter_halo_list(
    haloes: List[Dict[str, Any]],
    min_particles: int = 10000
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Validate and filter a list of haloes.

    Args:
        haloes: List of halo dictionaries.
        min_particles: Minimum particle count threshold.

    Returns:
        Tuple of (valid_haloes, excluded_haloes_with_reasons).
    """
    valid_haloes = []
    excluded_haloes = []

    for halo in haloes:
        if filter_halo_for_analysis(halo, min_particles):
            valid_haloes.append(halo)
        else:
            reason = get_exclusion_reason(halo)
            excluded_haloes.append({
                'halo_id': halo.get('halo_id', 'unknown'),
                'reason': reason
            })

    return valid_haloes, excluded_haloes