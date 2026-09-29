"""
Inertia Tensor Computation Module for Dark Matter Halo Shape Analysis.

This module implements the calculation of reduced inertia tensors for dark matter
haloes, including eigenvalue decomposition and shape derivation. It provides
robust handling for singular matrices and edge cases as required by the
scientific pipeline.

Functions:
    compute_reduced_inertia_tensor: Calculate the reduced inertia tensor from particle data.
    compute_eigenvalues_and_eigenvectors: Perform eigendecomposition on the inertia tensor.
    compute_shape_from_inertia: Derive axial ratios and triaxiality from eigenvalues.
    process_halo_inertia: End-to-end processing of a single halo.
"""

import numpy as np
from typing import Tuple, Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


def compute_reduced_inertia_tensor(
    positions: np.ndarray,
    weights: Optional[np.ndarray] = None,
    center: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Compute the reduced inertia tensor for a set of particle positions.

    The reduced inertia tensor is defined as:
        I_ij = sum_k (w_k * x_ki * x_kj) / sum_k (w_k * r_k^2)

    where x_ki is the i-th coordinate of particle k relative to the center,
    and r_k is the distance from the center.

    Args:
        positions: Array of shape (N, 3) containing particle positions.
        weights: Optional array of shape (N,) containing particle weights.
                If None, uniform weights are used.
        center: Optional array of shape (3,) containing the center of the halo.
               If None, the center of mass is computed.

    Returns:
        A 3x3 numpy array representing the reduced inertia tensor.

    Raises:
        ValueError: If positions array is empty or has wrong shape.
        ValueError: If weights are provided but have wrong length.
    """
    if positions is None or len(positions) == 0:
        raise ValueError("Positions array cannot be empty.")

    positions = np.asarray(positions, dtype=np.float64)
    if positions.shape[1] != 3:
        raise ValueError(f"Positions must have shape (N, 3), got {positions.shape}")

    n_particles = positions.shape[0]

    if weights is None:
        weights = np.ones(n_particles)
    else:
        weights = np.asarray(weights, dtype=np.float64)
        if len(weights) != n_particles:
            raise ValueError(f"Weights length ({len(weights)}) must match number of particles ({n_particles})")

    # Compute center if not provided
    if center is None:
        center = np.average(positions, axis=0, weights=weights)

    # Compute relative positions
    rel_positions = positions - center

    # Compute squared distances
    r_squared = np.sum(rel_positions**2, axis=1)

    # Check for singular case (all particles at center)
    if np.sum(r_squared) < 1e-15:
        raise ValueError("All particles are at the center; cannot compute reduced inertia tensor.")

    # Compute the reduced inertia tensor
    # I_ij = sum_k (w_k * x_ki * x_kj) / sum_k (w_k * r_k^2)
    numerator = np.zeros((3, 3), dtype=np.float64)
    for i in range(3):
        for j in range(3):
            numerator[i, j] = np.sum(weights * rel_positions[:, i] * rel_positions[:, j])

    denominator = np.sum(weights * r_squared)

    inertia_tensor = numerator / denominator

    # Ensure symmetry (numerical precision)
    inertia_tensor = (inertia_tensor + inertia_tensor.T) / 2.0

    return inertia_tensor


def compute_eigenvalues_and_eigenvectors(
    inertia_tensor: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute eigenvalues and eigenvectors of the inertia tensor.

    Args:
        inertia_tensor: A 3x3 symmetric numpy array.

    Returns:
        Tuple of (eigenvalues, eigenvectors) where:
            - eigenvalues: Array of shape (3,) sorted in descending order
            - eigenvectors: Array of shape (3, 3) where columns are eigenvectors

    Raises:
        ValueError: If input is not a 3x3 matrix.
        RuntimeError: If eigenvalue decomposition fails.
    """
    if inertia_tensor.shape != (3, 3):
        raise ValueError(f"Inertia tensor must be 3x3, got {inertia_tensor.shape}")

    try:
        eigenvalues, eigenvectors = np.linalg.eigh(inertia_tensor)
    except np.linalg.LinAlgError as e:
        logger.error(f"Eigenvalue decomposition failed: {e}")
        raise RuntimeError(f"Failed to compute eigenvalues: {e}")

    # Sort eigenvalues in descending order (a >= b >= c)
    sort_indices = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[sort_indices]
    eigenvectors = eigenvectors[:, sort_indices]

    # Check for singular matrix (zero eigenvalue)
    if eigenvalues[-1] < 1e-15:
        raise ValueError("Inertia tensor is singular (zero eigenvalue).")

    return eigenvalues, eigenvectors


def compute_shape_from_inertia(
    eigenvalues: np.ndarray
) -> Dict[str, float]:
    """
    Compute shape metrics from inertia tensor eigenvalues.

    The eigenvalues (lambda_a, lambda_b, lambda_c) correspond to the squared
    axial ratios of the ellipsoid. We compute:
        - b/a = sqrt(lambda_b / lambda_a)
        - c/a = sqrt(lambda_c / lambda_a)
        - triaxiality = (lambda_a - lambda_b) / (lambda_a - lambda_c)

    Args:
        eigenvalues: Array of shape (3,) sorted in descending order.

    Returns:
        Dictionary containing:
            - 'b_a_ratio': float, ratio of intermediate to major axis (0 < b/a <= 1)
            - 'c_a_ratio': float, ratio of minor to major axis (0 < c/a <= 1)
            - 'triaxiality': float, measure of triaxiality (0 <= T <= 1)
            - 'eigenvalues': tuple of the three eigenvalues

    Raises:
        ValueError: If eigenvalues are not sorted descending or contain invalid values.
    """
    if len(eigenvalues) != 3:
        raise ValueError(f"Expected 3 eigenvalues, got {len(eigenvalues)}")

    # Ensure eigenvalues are positive
    if np.any(eigenvalues <= 0):
        raise ValueError(f"Eigenvalues must be positive, got {eigenvalues}")

    lambda_a, lambda_b, lambda_c = eigenvalues

    # Compute axial ratios
    # Using a small epsilon to avoid division by zero
    epsilon = 1e-15
    b_a_ratio = np.sqrt(lambda_b / (lambda_a + epsilon))
    c_a_ratio = np.sqrt(lambda_c / (lambda_a + epsilon))

    # Clamp ratios to valid range [0, 1]
    b_a_ratio = np.clip(b_a_ratio, 0.0, 1.0)
    c_a_ratio = np.clip(c_a_ratio, 0.0, 1.0)

    # Compute triaxiality
    # T = (a^2 - b^2) / (a^2 - c^2) = (lambda_a - lambda_b) / (lambda_a - lambda_c)
    denom = (lambda_a - lambda_c) + epsilon
    triaxiality = (lambda_a - lambda_b) / denom
    triaxiality = np.clip(triaxiality, 0.0, 1.0)

    return {
        'b_a_ratio': float(b_a_ratio),
        'c_a_ratio': float(c_a_ratio),
        'triaxiality': float(triaxiality),
        'eigenvalues': (float(lambda_a), float(lambda_b), float(lambda_c))
    }


def process_halo_inertia(
    positions: np.ndarray,
    particle_count: int,
    halo_id: int,
    weights: Optional[np.ndarray] = None,
    center: Optional[np.ndarray] = None,
    min_particles: int = 10000
) -> Optional[Dict[str, Any]]:
    """
    Process a single halo to compute its shape metrics.

    This is the main entry point for halo shape computation. It handles:
        1. Particle count validation
        2. Inertia tensor computation
        3. Eigenvalue decomposition
        4. Shape metric derivation

    Args:
        positions: Array of shape (N, 3) containing particle positions.
        particle_count: Total number of particles in the halo.
        halo_id: Unique identifier for the halo.
        weights: Optional array of particle weights.
        center: Optional center position for the halo.
        min_particles: Minimum number of particles required (default 10000).

    Returns:
        Dictionary containing shape metrics if successful, None if halo is excluded.
        Structure:
            {
                'halo_id': int,
                'particle_count': int,
                'b_a_ratio': float,
                'c_a_ratio': float,
                'triaxiality': float,
                'eigenvalues': tuple,
                'status': 'success'
            }

    Raises:
        ValueError: If particle count is below threshold or computation fails.
    """
    # Validate particle count
    if particle_count < min_particles:
        logger.debug(f"Halo {halo_id} has {particle_count} particles, below threshold {min_particles}")
        return None

    if positions is None or len(positions) == 0:
        logger.warning(f"Halo {halo_id} has no position data")
        return None

    try:
        # Compute reduced inertia tensor
        inertia_tensor = compute_reduced_inertia_tensor(
            positions=positions,
            weights=weights,
            center=center
        )

        # Compute eigenvalues and eigenvectors
        eigenvalues, eigenvectors = compute_eigenvalues_and_eigenvectors(inertia_tensor)

        # Compute shape metrics
        shape_metrics = compute_shape_from_inertia(eigenvalues)

        # Validate shape metrics
        if not (0 < shape_metrics['b_a_ratio'] <= 1):
            logger.warning(f"Halo {halo_id}: Invalid b/a ratio {shape_metrics['b_a_ratio']}")
            return None
        if not (0 < shape_metrics['c_a_ratio'] <= 1):
            logger.warning(f"Halo {halo_id}: Invalid c/a ratio {shape_metrics['c_a_ratio']}")
            return None
        if not (0 <= shape_metrics['triaxiality'] <= 1):
            logger.warning(f"Halo {halo_id}: Invalid triaxiality {shape_metrics['triaxiality']}")
            return None

        result = {
            'halo_id': halo_id,
            'particle_count': particle_count,
            'b_a_ratio': shape_metrics['b_a_ratio'],
            'c_a_ratio': shape_metrics['c_a_ratio'],
            'triaxiality': shape_metrics['triaxiality'],
            'eigenvalues': shape_metrics['eigenvalues'],
            'status': 'success'
        }

        return result

    except ValueError as e:
        logger.warning(f"Halo {halo_id}: Inertia computation failed - {e}")
        return None
    except RuntimeError as e:
        logger.error(f"Halo {halo_id}: Critical error in inertia computation - {e}")
        return None