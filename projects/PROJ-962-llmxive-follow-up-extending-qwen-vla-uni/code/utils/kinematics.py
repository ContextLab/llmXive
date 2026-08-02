"""
Kinematic feature extraction utilities.
"""
import numpy as np
from typing import List, Tuple, Optional

def compute_velocity(
    positions: np.ndarray, 
    dt: float = 1.0
) -> np.ndarray:
    """
    Compute velocity from position data using finite differences.

    Args:
        positions (np.ndarray): Array of shape (T, D) where T is time steps and D is dimensions.
        dt (float): Time step duration.

    Returns:
        np.ndarray: Array of velocity (T-1, D).
    """
    if positions.shape[0] < 2:
        return np.zeros_like(positions)
    
    return np.diff(positions, axis=0) / dt

def compute_acceleration(
    positions: np.ndarray, 
    dt: float = 1.0
) -> np.ndarray:
    """
    Compute acceleration from position data using finite differences.

    Args:
        positions (np.ndarray): Array of shape (T, D).
        dt (float): Time step duration.

    Returns:
        np.ndarray: Array of acceleration (T-2, D).
    """
    if positions.shape[0] < 3:
        return np.zeros_like(positions)
    
    velocities = compute_velocity(positions, dt)
    return compute_velocity(velocities, dt)

def normalize_joint_angles(
    angles: np.ndarray, 
    lower_bounds: np.ndarray, 
    upper_bounds: np.ndarray
) -> np.ndarray:
    """
    Normalize joint angles to [-1, 1] range based on physical limits.

    Args:
        angles (np.ndarray): Array of joint angles (T, D).
        lower_bounds (np.ndarray): Lower physical limits for each joint.
        upper_bounds (np.ndarray): Upper physical limits for each joint.

    Returns:
        np.ndarray: Normalized angles in [-1, 1].
    """
    if angles.shape[-1] != lower_bounds.shape[0]:
        raise ValueError("Dimension mismatch between angles and bounds")
    
    # Avoid division by zero
    ranges = upper_bounds - lower_bounds
    ranges = np.where(ranges == 0, 1.0, ranges)
    
    normalized = 2 * ((angles - lower_bounds) / ranges) - 1
    return np.clip(normalized, -1.0, 1.0)

def extract_kinematic_features(
    trajectory: np.ndarray, 
    dt: float = 0.1
) -> dict:
    """
    Extract all kinematic features from a trajectory.

    Args:
        trajectory (np.ndarray): Array of shape (T, D) representing joint positions over time.
        dt (float): Time step duration.

    Returns:
        dict: Dictionary containing positions, velocities, accelerations.
    """
    features = {
        'positions': trajectory,
        'velocities': compute_velocity(trajectory, dt),
        'accelerations': compute_acceleration(trajectory, dt)
    }
    return features