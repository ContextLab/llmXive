"""
Shape metrics derivation for dark matter haloes.

This module computes axial ratios (b/a, c/a) and triaxiality (T) from
the eigenvalues of the reduced inertia tensor. It also implements
filtering logic for haloes with insufficient particle counts.

Dependencies:
    - numpy
    - pandas (optional, for dataframe handling)
"""

import numpy as np
from typing import Tuple, Optional, Dict, Any, List, Union


def compute_axial_ratios(
    eigenvalues: np.ndarray, sort_descending: bool = True
) -> Tuple[float, float]:
    """
    Compute axial ratios (b/a, c/a) from inertia tensor eigenvalues.

    The eigenvalues of the reduced inertia tensor (lambda_a >= lambda_b >= lambda_c)
    correspond to the squared axis lengths of the ellipsoid.
    Axial ratios are defined as:
        b/a = sqrt(lambda_b / lambda_a)
        c/a = sqrt(lambda_c / lambda_a)

    Args:
        eigenvalues: Array of 3 eigenvalues from the reduced inertia tensor.
        sort_descending: If True, sort eigenvalues from largest to smallest
                         before computing ratios.

    Returns:
        Tuple (b/a, c/a) as floats.
    """
    if len(eigenvalues) != 3:
        raise ValueError(f"Expected 3 eigenvalues, got {len(eigenvalues)}")

    # Ensure non-negative eigenvalues (physical constraint)
    if np.any(eigenvalues < 0):
        raise ValueError("Eigenvalues must be non-negative for physical haloes.")

    # Sort descending: lambda_a >= lambda_b >= lambda_c
    if sort_descending:
        sorted_vals = np.sort(eigenvalues)[::-1]
    else:
        sorted_vals = np.sort(eigenvalues)

    lambda_a, lambda_b, lambda_c = sorted_vals

    # Avoid division by zero
    if lambda_a <= 0:
        return 0.0, 0.0

    b_a = np.sqrt(lambda_b / lambda_a)
    c_a = np.sqrt(lambda_c / lambda_a)

    # Clamp to physical range [0, 1] due to floating point errors
    b_a = np.clip(b_a, 0.0, 1.0)
    c_a = np.clip(c_a, 0.0, 1.0)

    return float(b_a), float(c_a)


def compute_triaxiality(b_a: float, c_a: float) -> float:
    """
    Compute triaxiality parameter T from axial ratios.

    T = (1 - (b/a)^2) / (1 - (c/a)^2)

    Interpretation:
        T ~ 0: Prolate (cigar-shaped)
        T ~ 1: Oblate (pancake-shaped)
        0 < T < 1: Triaxial

    Args:
        b_a: Axial ratio b/a.
        c_a: Axial ratio c/a.

    Returns:
        Triaxiality T (float).
    """
    denom = 1.0 - c_a**2
    if abs(denom) < 1e-12:
        # If c/a is effectively 1, the shape is spherical; T is undefined
        # Convention: return 0.5 or handle as spherical. Here we return 0.5.
        return 0.5

    num = 1.0 - b_a**2
    t = num / denom
    return float(np.clip(t, 0.0, 1.0))


def compute_shape_metrics_from_eigenvalues(
    eigenvalues: np.ndarray
) -> Dict[str, float]:
    """
    Compute all shape metrics (b/a, c/a, T) from eigenvalues.

    Args:
        eigenvalues: Array of 3 eigenvalues.

    Returns:
        Dictionary with keys: 'b_a_ratio', 'c_a_ratio', 'triaxiality'.
    """
    b_a, c_a = compute_axial_ratios(eigenvalues)
    t = compute_triaxiality(b_a, c_a)
    return {
        'b_a_ratio': b_a,
        'c_a_ratio': c_a,
        'triaxiality': t
    }


def filter_halo_by_particle_count(
    particle_count: int,
    min_particles: int = 10000
) -> bool:
    """
    Determine if a halo meets the minimum particle count threshold.

    Args:
        particle_count: Number of particles in the halo.
        min_particles: Minimum required particles (default 10,000).

    Returns:
        True if halo passes the filter, False otherwise.
    """
    return particle_count >= min_particles


def validate_shape_metrics(metrics: Dict[str, float]) -> bool:
    """
    Validate that computed shape metrics are within physical bounds.

    Conditions:
        0 < b/a <= 1
        0 < c/a <= 1
        0 <= T <= 1

    Args:
        metrics: Dictionary containing 'b_a_ratio', 'c_a_ratio', 'triaxiality'.

    Returns:
        True if valid, False otherwise.
    """
    b_a = metrics.get('b_a_ratio', -1.0)
    c_a = metrics.get('c_a_ratio', -1.0)
    t = metrics.get('triaxiality', -1.0)

    if not (0 < b_a <= 1):
        return False
    if not (0 < c_a <= 1):
        return False
    if not (0 <= t <= 1):
        return False

    return True


def process_halo_shape(
    eigenvalues: np.ndarray,
    particle_count: int,
    halo_id: Optional[int] = None,
    min_particles: int = 10000
) -> Optional[Dict[str, Any]]:
    """
    Process a single halo to compute and validate shape metrics.

    This is the main entry point for the shape metrics pipeline for a single halo.
    It computes metrics, validates them, and filters based on particle count.

    Args:
        eigenvalues: Array of 3 eigenvalues from the reduced inertia tensor.
        particle_count: Number of particles in the halo.
        halo_id: Optional ID for the halo.
        min_particles: Minimum particle count threshold.

    Returns:
        Dictionary with shape metrics and halo info if valid, None if filtered out.
    """
    # Filter by particle count
    if not filter_halo_by_particle_count(particle_count, min_particles):
        return None

    # Compute metrics
    metrics = compute_shape_metrics_from_eigenvalues(eigenvalues)

    # Validate metrics
    if not validate_shape_metrics(metrics):
        return None

    result = {
        'halo_id': halo_id,
        'particle_count': particle_count,
        'b_a_ratio': metrics['b_a_ratio'],
        'c_a_ratio': metrics['c_a_ratio'],
        'triaxiality': metrics['triaxiality']
    }

    return result