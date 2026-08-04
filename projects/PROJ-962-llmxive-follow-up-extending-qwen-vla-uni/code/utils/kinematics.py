import numpy as np
from typing import List, Tuple, Optional, Union, Dict, Any

def compute_velocity(
    positions: Union[np.ndarray, List[float]], 
    dt: float = 0.02
) -> np.ndarray:
    """
    Compute velocity from a sequence of positions.
    
    Args:
        positions: Array of shape (N, D) where N is time steps and D is dimensions.
        dt: Time step between frames.
        
    Returns:
        Velocity array of shape (N-1, D).
    """
    positions = np.asarray(positions)
    if positions.ndim == 1:
        positions = positions.reshape(-1, 1)
        
    diffs = np.diff(positions, axis=0)
    velocities = diffs / dt
    return velocities

def compute_acceleration(
    velocities: Union[np.ndarray, List[float]], 
    dt: float = 0.02
) -> np.ndarray:
    """
    Compute acceleration from a sequence of velocities.
    
    Args:
        velocities: Array of shape (N, D) where N is time steps and D is dimensions.
        dt: Time step between frames.
        
    Returns:
        Acceleration array of shape (N-1, D).
    """
    velocities = np.asarray(velocities)
    if velocities.ndim == 1:
        velocities = velocities.reshape(-1, 1)
        
    diffs = np.diff(velocities, axis=0)
    accelerations = diffs / dt
    return accelerations

def normalize_joint_angles(
    angles: Union[np.ndarray, List[float]], 
    lower_bounds: Optional[Union[np.ndarray, List[float]]] = None,
    upper_bounds: Optional[Union[np.ndarray, List[float]]] = None
) -> np.ndarray:
    """
    Normalize joint angles to [0, 1] range based on bounds.
    
    Args:
        angles: Array of joint angles.
        lower_bounds: Lower bounds for each joint. If None, uses -pi.
        upper_bounds: Upper bounds for each joint. If None, uses pi.
        
    Returns:
        Normalized angles in [0, 1].
    """
    angles = np.asarray(angles, dtype=float)
    
    if lower_bounds is None:
        lower_bounds = -np.pi * np.ones_like(angles)
    else:
        lower_bounds = np.asarray(lower_bounds, dtype=float)
        
    if upper_bounds is None:
        upper_bounds = np.pi * np.ones_like(angles)
    else:
        upper_bounds = np.asarray(upper_bounds, dtype=float)
        
    range_vals = upper_bounds - lower_bounds
    range_vals[range_vals == 0] = 1.0  # Avoid division by zero
    
    normalized = (angles - lower_bounds) / range_vals
    return np.clip(normalized, 0.0, 1.0)

def extract_kinematic_features(
    trajectory: np.ndarray,
    dt: float = 0.02
) -> Dict[str, np.ndarray]:
    """
    Extract kinematic features (position, velocity, acceleration) from a trajectory.
    
    Args:
        trajectory: Array of shape (T, D) representing T time steps of D-dimensional positions.
        dt: Time step between frames.
        
    Returns:
        Dictionary with keys 'position', 'velocity', 'acceleration'.
    """
    trajectory = np.asarray(trajectory, dtype=float)
    
    features = {
        'position': trajectory,
        'velocity': compute_velocity(trajectory, dt),
        'acceleration': compute_acceleration(compute_velocity(trajectory, dt), dt)
    }
    
    return features
