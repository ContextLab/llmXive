"""
Inertia Tensor Computation Module.

This module provides functions to compute the reduced inertia tensor of dark matter haloes,
perform eigenvalue decomposition, and derive shape metrics (axial ratios and triaxiality).
It is designed to work with chunked data streams to handle large datasets within memory constraints.
"""

import numpy as np
from typing import Tuple, Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# Constants for numerical stability
EPSILON = 1e-10
MIN_PARTICLE_COUNT = 10000

def compute_reduced_inertia_tensor(
    positions: np.ndarray, 
    masses: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Compute the reduced inertia tensor for a set of particle positions.
    
    The reduced inertia tensor is defined as:
    I_ij = sum_k (m_k * x_k_i * x_k_j) / sum_k (m_k * r_k^2)
    
    where:
    - m_k is the mass of particle k (if provided, otherwise uniform)
    - x_k_i is the i-th coordinate of particle k relative to the center of mass
    - r_k is the distance of particle k from the center of mass
    
    Args:
        positions: Array of shape (N, 3) containing particle positions.
        masses: Optional array of shape (N,) containing particle masses. 
                If None, uniform mass is assumed.
                
    Returns:
        A 3x3 numpy array representing the reduced inertia tensor.
        
    Raises:
        ValueError: If positions array is empty or has incorrect shape.
        ValueError: If masses array length does not match positions.
    """
    if positions.size == 0:
        raise ValueError("Positions array cannot be empty.")
        
    if positions.ndim != 2 or positions.shape[1] != 3:
        raise ValueError(f"Positions must be of shape (N, 3), got {positions.shape}.")
        
    n_particles = positions.shape[0]
    
    if masses is not None:
        if masses.shape[0] != n_particles:
            raise ValueError(f"Masses length ({masses.shape[0]}) must match positions count ({n_particles}).")
        if np.any(masses < 0):
            raise ValueError("Particle masses cannot be negative.")
    else:
        masses = np.ones(n_particles)
        
    # Compute center of mass
    total_mass = np.sum(masses)
    if total_mass == 0:
        raise ValueError("Total mass is zero, cannot compute center of mass.")
        
    com = np.sum(positions * masses[:, np.newaxis], axis=0) / total_mass
    
    # Compute relative positions
    rel_positions = positions - com
    
    # Compute squared distances
    r_squared = np.sum(rel_positions ** 2, axis=1)
    
    # Check for all particles at the center of mass (singular case)
    if np.all(r_squared < EPSILON):
        raise ValueError("All particles are at the center of mass; inertia tensor is singular.")
        
    # Compute the inertia tensor components
    # I_ij = sum(m_k * x_k_i * x_k_j) / sum(m_k * r_k^2)
    numerator = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            numerator[i, j] = np.sum(masses * rel_positions[:, i] * rel_positions[:, j])
            
    denominator = np.sum(masses * r_squared)
    
    inertia_tensor = numerator / denominator
    
    return inertia_tensor

def compute_eigenvalues_and_eigenvectors(
    tensor: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute the eigenvalues and eigenvectors of a symmetric tensor.
    
    The inertia tensor is symmetric, so we use the specialized eig function
    which is more efficient and numerically stable for symmetric matrices.
    
    Args:
        tensor: A 3x3 symmetric numpy array.
        
    Returns:
        Tuple of (eigenvalues, eigenvectors) where:
        - eigenvalues: 1D array of shape (3,) containing eigenvalues in ascending order.
        - eigenvectors: 2D array of shape (3, 3) where columns are the corresponding eigenvectors.
        
    Raises:
        ValueError: If tensor is not a 3x3 matrix.
        LinAlgError: If eigenvalue decomposition fails (should not happen for symmetric tensors).
    """
    if tensor.shape != (3, 3):
        raise ValueError(f"Tensor must be a 3x3 matrix, got {tensor.shape}.")
        
    # Use eigh for symmetric/Hermitian matrices
    eigenvalues, eigenvectors = np.linalg.eigh(tensor)
    
    # Sort eigenvalues in ascending order and reorder eigenvectors accordingly
    sorted_indices = np.argsort(eigenvalues)
    eigenvalues = eigenvalues[sorted_indices]
    eigenvectors = eigenvectors[:, sorted_indices]
    
    # Ensure eigenvalues are non-negative (numerical errors might cause small negatives)
    eigenvalues = np.maximum(eigenvalues, 0.0)
    
    return eigenvalues, eigenvectors

def compute_shape_from_inertia(
    eigenvalues: np.ndarray
) -> Tuple[float, float, float]:
    """
    Compute shape metrics from the eigenvalues of the inertia tensor.
    
    The axial ratios are defined as:
    b/a = sqrt(lambda_2 / lambda_1)
    c/a = sqrt(lambda_3 / lambda_1)
    
    where lambda_1 >= lambda_2 >= lambda_3 are the eigenvalues in descending order.
    
    The triaxiality is defined as:
    T = (lambda_1 - lambda_2) / (lambda_1 - lambda_3)
    
    Args:
        eigenvalues: 1D array of shape (3,) containing eigenvalues.
        
    Returns:
        Tuple of (b/a, c/a, triaxiality) where:
        - b/a: Axis ratio between intermediate and major axes (0 < b/a <= 1).
        - c/a: Axis ratio between minor and major axes (0 < c/a <= 1).
        - triaxiality: Measure of deviation from spherical symmetry (0 <= T <= 1).
        
    Raises:
        ValueError: If eigenvalues array is not of length 3.
        ValueError: If eigenvalues are all zero (spherical symmetry with zero inertia).
    """
    if eigenvalues.shape[0] != 3:
        raise ValueError(f"Eigenvalues must be of length 3, got {eigenvalues.shape[0]}.")
        
    # Sort eigenvalues in descending order (lambda_1 >= lambda_2 >= lambda_3)
    sorted_eigenvalues = np.sort(eigenvalues)[::-1]
    lambda_1, lambda_2, lambda_3 = sorted_eigenvalues
    
    # Check for degenerate cases
    if lambda_1 < EPSILON:
        raise ValueError("Major eigenvalue is near zero; cannot compute shape metrics.")
        
    # Compute axial ratios
    # Add small epsilon to denominator to avoid division by zero for spherical cases
    b_a_ratio = np.sqrt(lambda_2 / (lambda_1 + EPSILON))
    c_a_ratio = np.sqrt(lambda_3 / (lambda_1 + EPSILON))
    
    # Compute triaxiality
    # T = (lambda_1 - lambda_2) / (lambda_1 - lambda_3)
    denominator = lambda_1 - lambda_3
    if abs(denominator) < EPSILON:
        # Perfectly spherical or prolate case
        triaxiality = 0.0
    else:
        triaxiality = (lambda_1 - lambda_2) / denominator
        
    # Ensure triaxiality is within [0, 1]
    triaxiality = np.clip(triaxiality, 0.0, 1.0)
    
    # Ensure axial ratios are within (0, 1]
    b_a_ratio = np.clip(b_a_ratio, 0.0, 1.0)
    c_a_ratio = np.clip(c_a_ratio, 0.0, 1.0)
    
    return b_a_ratio, c_a_ratio, triaxiality

def process_halo_inertia(
    positions: np.ndarray,
    masses: Optional[np.ndarray] = None,
    particle_count: int = 0
) -> Optional[Dict[str, Any]]:
    """
    Process a single halo to compute its shape metrics.
    
    This is a convenience function that chains together the inertia tensor computation,
    eigenvalue decomposition, and shape metric derivation. It includes filtering
    based on particle count to exclude low-resolution haloes.
    
    Args:
        positions: Array of shape (N, 3) containing particle positions.
        masses: Optional array of shape (N,) containing particle masses.
        particle_count: Total number of particles in the halo (for filtering).
        
    Returns:
        A dictionary containing:
        - 'b_a_ratio': float, axial ratio b/a
        - 'c_a_ratio': float, axial ratio c/a
        - 'triaxiality': float, triaxiality measure
        - 'eigenvalues': array of shape (3,), sorted eigenvalues
        - 'eigenvectors': array of shape (3, 3), corresponding eigenvectors
        - 'inertia_tensor': array of shape (3, 3), reduced inertia tensor
        - 'particle_count': int, number of particles used
        
        Returns None if the halo should be excluded (e.g., particle_count < MIN_PARTICLE_COUNT).
        
    Raises:
        ValueError: If positions are invalid or matrix is singular.
    """
    # Filter based on particle count
    if particle_count < MIN_PARTICLE_COUNT:
        logger.debug(f"Excluding halo with {particle_count} particles (< {MIN_PARTICLE_COUNT})")
        return None
        
    try:
        # Compute reduced inertia tensor
        inertia_tensor = compute_reduced_inertia_tensor(positions, masses)
        
        # Compute eigenvalues and eigenvectors
        eigenvalues, eigenvectors = compute_eigenvalues_and_eigenvectors(inertia_tensor)
        
        # Compute shape metrics
        b_a_ratio, c_a_ratio, triaxiality = compute_shape_from_inertia(eigenvalues)
        
        return {
            'b_a_ratio': b_a_ratio,
            'c_a_ratio': c_a_ratio,
            'triaxiality': triaxiality,
            'eigenvalues': eigenvalues,
            'eigenvectors': eigenvectors,
            'inertia_tensor': inertia_tensor,
            'particle_count': particle_count
        }
        
    except ValueError as e:
        logger.warning(f"Failed to compute inertia tensor: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error processing halo inertia: {e}")
        return None