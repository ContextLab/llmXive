"""
kinematics.py - Kinematic feature extraction utilities.
"""
import numpy as np
from typing import List, Tuple, Optional, Union, Dict, Any

def compute_velocity(positions: np.ndarray, dt: float = 1.0) -> np.ndarray:
    """
    Compute velocity from a sequence of positions.
    positions: (N, D) array of positions.
    dt: Time step between frames.
    Returns: (N-1, D) array of velocities.
    """
    if len(positions) < 2:
        return np.zeros((0, positions.shape[1]))
    return np.diff(positions, axis=0) / dt

def compute_acceleration(velocities: np.ndarray, dt: float = 1.0) -> np.ndarray:
    """
    Compute acceleration from a sequence of velocities.
    velocities: (N, D) array of velocities.
    dt: Time step between frames.
    Returns: (N-1, D) array of accelerations.
    """
    if len(velocities) < 2:
        return np.zeros((0, velocities.shape[1]))
    return np.diff(velocities, axis=0) / dt

def normalize_joint_angles(angles: np.ndarray, min_angle: float, max_angle: float) -> np.ndarray:
    """
    Normalize joint angles to [0, 1] range.
    angles: (N, D) array of joint angles.
    min_angle: Minimum possible angle (scalar or (D,) array).
    max_angle: Maximum possible angle (scalar or (D,) array).
    Returns: (N, D) normalized angles.
    """
    range_val = max_angle - min_angle
    if np.any(range_val == 0):
        raise ValueError("Range cannot be zero.")
    return (angles - min_angle) / range_val

def extract_kinematic_features(trajectory: np.ndarray, dt: float = 1.0) -> Dict[str, np.ndarray]:
    """
    Extract velocity, acceleration, and joint angles from a trajectory.
    trajectory: (N, D) array of joint positions.
    Returns: Dictionary with keys 'positions', 'velocities', 'accelerations'.
    """
    positions = trajectory
    velocities = compute_velocity(positions, dt)
    accelerations = compute_acceleration(velocities, dt)
    
    return {
        "positions": positions,
        "velocities": velocities,
        "accelerations": accelerations
    }
