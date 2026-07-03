"""
Inertia Tensor Calculation Module.

Computes the reduced inertia tensor for dark matter haloes and derives
eigenvalues for shape analysis.
"""

import numpy as np
from typing import Tuple, Optional, Dict, Any

def compute_reduced_inertia_tensor(
    positions: np.ndarray,
    masses: Optional[np.ndarray] = None,
    center: Optional[np.ndarray] = None
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Compute the reduced inertia tensor for a set of particle positions.

    The reduced inertia tensor is defined as:
    I_ij = sum_k (m_k * r_k_i * r_k_j) / sum_k (m_k * r_k^2)

    where r_k is the distance of particle k from the center.

    Args:
        positions: Array of shape (N, 3) with particle positions.
        masses: Optional array of shape (N,) with particle masses.
                If None, all particles are assumed to have unit mass.
        center: Optional array of shape (3,) for the center of the halo.
                If None, the center of mass is computed.

    Returns:
        Tuple containing:
            - inertia_tensor: 3x3 numpy array of the inertia tensor.
            - metadata: Dictionary with computation details (center, total_mass, etc.)
    """
    positions = np.asarray(positions, dtype=np.float64)
    
    if positions.shape[1] != 3:
        raise ValueError(f"Positions must have shape (N, 3), got {positions.shape}")
    
    n_particles = positions.shape[0]
    if n_particles == 0:
        raise ValueError("Cannot compute inertia tensor for empty particle set")
    
    # Compute center if not provided
    if center is None:
        if masses is not None:
            masses = np.asarray(masses, dtype=np.float64)
            center = np.average(positions, axis=0, weights=masses)
        else:
            center = np.mean(positions, axis=0)
    
    # Compute relative positions
    relative_positions = positions - center
    
    # Compute distances squared
    r_squared = np.sum(relative_positions ** 2, axis=1)
    
    # Handle edge case where all particles are at the center
    if np.all(r_squared == 0):
        return np.zeros((3, 3)), {
            "center": center,
            "total_mass": 0.0 if masses is None else np.sum(masses),
            "n_particles": n_particles,
            "warning": "All particles at center, returning zero tensor"
        }
    
    # Compute weights
    if masses is not None:
        masses = np.asarray(masses, dtype=np.float64)
        weights = masses * r_squared
        total_weight = np.sum(weights)
    else:
        weights = r_squared
        total_weight = np.sum(weights)
    
    if total_weight == 0:
        return np.zeros((3, 3)), {
            "center": center,
            "total_mass": 0.0 if masses is None else np.sum(masses),
            "n_particles": n_particles,
            "warning": "Total weight is zero, returning zero tensor"
        }
    
    # Compute the inertia tensor components
    # I_ij = sum_k (w_k * r_k_i * r_k_j) / total_weight
    inertia_tensor = np.zeros((3, 3), dtype=np.float64)
    
    for i in range(3):
        for j in range(3):
            inertia_tensor[i, j] = np.sum(weights * relative_positions[:, i] * relative_positions[:, j])
    
    inertia_tensor /= total_weight
    
    metadata = {
        "center": center,
        "total_mass": 0.0 if masses is None else np.sum(masses),
        "n_particles": n_particles,
        "total_weight": total_weight
    }
    
    return inertia_tensor, metadata

def compute_eigenvalues_and_eigenvectors(
    inertia_tensor: np.ndarray,
    sort_descending: bool = True
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Compute eigenvalues and eigenvectors of the inertia tensor.

    Args:
        inertia_tensor: 3x3 symmetric matrix (typically from compute_reduced_inertia_tensor).
        sort_descending: If True, sort eigenvalues in descending order (lambda_1 >= lambda_2 >= lambda_3).

    Returns:
        Tuple containing:
            - eigenvalues: Array of 3 eigenvalues.
            - eigenvectors: 3x3 matrix where columns are eigenvectors.
            - metadata: Dictionary with computation details.
    """
    inertia_tensor = np.asarray(inertia_tensor, dtype=np.float64)
    
    if inertia_tensor.shape != (3, 3):
        raise ValueError(f"Inertia tensor must be 3x3, got {inertia_tensor.shape}")
    
    # Check for symmetry (within floating point tolerance)
    if not np.allclose(inertia_tensor, inertia_tensor.T, atol=1e-10):
        # Symmetrize if slightly asymmetric due to numerical errors
        inertia_tensor = (inertia_tensor + inertia_tensor.T) / 2.0
    
    # Compute eigenvalues and eigenvectors
    eigenvalues, eigenvectors = np.linalg.eigh(inertia_tensor)
    
    # Ensure eigenvalues are sorted
    if sort_descending:
        idx = np.argsort(eigenvalues)[::-1]
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]
    
    # Check for numerical issues
    metadata = {
        "min_eigenvalue": float(np.min(eigenvalues)),
        "max_eigenvalue": float(np.max(eigenvalues)),
        "eigenvalue_range": float(np.max(eigenvalues) - np.min(eigenvalues)),
        "is_positive_semidefinite": bool(np.all(eigenvalues >= -1e-10)),
        "is_singular": bool(np.any(np.abs(eigenvalues) < 1e-10))
    }
    
    return eigenvalues, eigenvectors, metadata

def compute_shape_from_inertia(
    inertia_tensor: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Compute axial ratios and triaxiality from the inertia tensor.

    The axial ratios are computed as:
    - b/a = sqrt(lambda_2 / lambda_1)
    - c/a = sqrt(lambda_3 / lambda_1)

    where lambda_1 >= lambda_2 >= lambda_3 are the eigenvalues.

    Triaxiality is computed as:
    - T = (lambda_1 - lambda_2) / (lambda_1 - lambda_3)

    Args:
        inertia_tensor: 3x3 inertia tensor.

    Returns:
        Tuple containing:
            - eigenvalues: Sorted eigenvalues (descending).
            - shape_metrics: Dictionary with b/a, c/a, and triaxiality.
            - metadata: Computation metadata including validity flags.
    """
    eigenvalues, eigenvectors, eig_meta = compute_eigenvalues_and_eigenvectors(inertia_tensor)
    
    # Check for validity
    if eig_meta["is_singular"] or not eig_meta["is_positive_semidefinite"]:
        return eigenvalues, {
            "b_a_ratio": None,
            "c_a_ratio": None,
            "triaxiality": None,
            "valid": False
        }, eig_meta
    
    lambda_1, lambda_2, lambda_3 = eigenvalues
    
    # Compute axial ratios
    # Add small epsilon to avoid division by zero
    epsilon = 1e-10
    b_a_ratio = np.sqrt(max(0.0, lambda_2 / (lambda_1 + epsilon)))
    c_a_ratio = np.sqrt(max(0.0, lambda_3 / (lambda_1 + epsilon)))
    
    # Compute triaxiality
    # T = (lambda_1 - lambda_2) / (lambda_1 - lambda_3)
    denominator = lambda_1 - lambda_3
    if abs(denominator) < epsilon:
        # If all eigenvalues are nearly equal (spherical), T = 0.5 by convention
        triaxiality = 0.5
    else:
        triaxiality = (lambda_1 - lambda_2) / denominator
    
    # Validate ranges
    b_a_valid = 0.0 < b_a_ratio <= 1.0
    c_a_valid = 0.0 < c_a_ratio <= 1.0
    t_valid = 0.0 <= triaxiality <= 1.0
    
    shape_metrics = {
        "b_a_ratio": float(b_a_ratio),
        "c_a_ratio": float(c_a_ratio),
        "triaxiality": float(triaxiality),
        "valid": b_a_valid and c_a_valid and t_valid
    }
    
    return eigenvalues, shape_metrics, eig_meta

def process_halo_inertia(
    positions: np.ndarray,
    masses: Optional[np.ndarray] = None,
    center: Optional[np.ndarray] = None
) -> Dict[str, Any]:
    """
    Complete pipeline for processing a single halo's inertia tensor.

    Args:
        positions: Array of shape (N, 3) with particle positions.
        masses: Optional array of shape (N,) with particle masses.
        center: Optional array of shape (3,) for the halo center.

    Returns:
        Dictionary containing:
            - inertia_tensor: 3x3 computed tensor.
            - eigenvalues: Sorted eigenvalues.
            - eigenvectors: Corresponding eigenvectors.
            - shape_metrics: Axial ratios and triaxiality.
            - metadata: Computation metadata.
            - valid: Boolean indicating if all computations succeeded.
    """
    try:
        inertia_tensor, tensor_meta = compute_reduced_inertia_tensor(
            positions, masses=masses, center=center
        )
        
        eigenvalues, eigenvectors, eig_meta = compute_eigenvalues_and_eigenvectors(
            inertia_tensor
        )
        
        _, shape_metrics, shape_meta = compute_shape_from_inertia(inertia_tensor)
        
        return {
            "inertia_tensor": inertia_tensor.tolist(),
            "eigenvalues": eigenvalues.tolist(),
            "eigenvectors": eigenvectors.tolist(),
            "shape_metrics": shape_metrics,
            "metadata": {
                **tensor_meta,
                **eig_meta,
                **shape_meta
            },
            "valid": shape_metrics["valid"]
        }
        
    except Exception as e:
        return {
            "inertia_tensor": None,
            "eigenvalues": None,
            "eigenvectors": None,
            "shape_metrics": {
                "b_a_ratio": None,
                "c_a_ratio": None,
                "triaxiality": None,
                "valid": False
            },
            "metadata": {"error": str(e)},
            "valid": False
        }