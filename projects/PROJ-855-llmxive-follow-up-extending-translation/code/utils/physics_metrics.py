"""
Physics metrics calculation utilities for stability labeling.
Implements tipping angle and slippage distance calculations.
"""
import os
import math
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import yaml

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to config.yaml. If None, searches in standard locations.
        
    Returns:
        Dictionary containing configuration values.
    """
    if config_path is None:
        # Search in standard locations
        possible_paths = [
            Path(__file__).parent.parent / "config.yaml",
            Path.cwd() / "config.yaml",
            Path(__file__).parent.parent.parent / "config.yaml",
        ]
        for p in possible_paths:
            if p.exists():
                config_path = str(p)
                break
        else:
            raise FileNotFoundError(
                "config.yaml not found. Expected in code/, project root, or parent directory."
            )
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def get_thresholds(config: Optional[Dict[str, Any]] = None) -> Tuple[float, float]:
    """
    Get stability thresholds from configuration.
    
    Args:
        config: Optional pre-loaded config dict. If None, loads from file.
        
    Returns:
        Tuple of (tipping_angle_threshold_deg, slippage_distance_threshold_m)
    """
    if config is None:
        config = load_config()
    
    physics = config.get('physics', {})
    tipping_threshold = physics.get('tipping_angle_threshold', 15.0)
    slippage_threshold = physics.get('slippage_distance_threshold', 0.02)
    
    return float(tipping_threshold), float(slippage_threshold)

def calculate_tipping_angle(
    initial_quaternion: Tuple[float, float, float, float],
    final_quaternion: Tuple[float, float, float, float]
) -> float:
    """
    Calculate the tipping angle of an object relative to its initial orientation.
    
    The tipping angle is the magnitude of rotation between initial and final states,
    converted to degrees. This measures how much the object has tilted.
    
    Args:
        initial_quaternion: (x, y, z, w) quaternion before manipulation
        final_quaternion: (x, y, z, w) quaternion after manipulation
        
    Returns:
        Tipping angle in degrees (0.0 to 180.0)
    """
    # Convert quaternions to rotation matrices or calculate angle directly
    # Using quaternion difference: q_diff = q_final * q_initial_conjugate
    # Then extract rotation angle from q_diff
    
    x1, y1, z1, w1 = initial_quaternion
    x2, y2, z2, w2 = final_quaternion
    
    # Quaternion conjugate of initial
    x1_conj, y1_conj, z1_conj, w1_conj = -x1, -y1, -z1, w1
    
    # Quaternion multiplication: q_diff = q2 * q1_conj
    w_diff = (w2 * w1_conj - x2 * x1_conj - y2 * y1_conj - z2 * z1_conj)
    x_diff = (w2 * x1_conj + x2 * w1_conj + y2 * z1_conj - z2 * y1_conj)
    y_diff = (w2 * y1_conj - x2 * z1_conj + y2 * w1_conj + z2 * x1_conj)
    z_diff = (w2 * z1_conj + x2 * y1_conj - y2 * x1_conj + z2 * w1_conj)
    
    # Normalize
    norm = math.sqrt(x_diff**2 + y_diff**2 + z_diff**2 + w_diff**2)
    if norm < 1e-10:
        return 0.0
    
    x_diff /= norm
    y_diff /= norm
    z_diff /= norm
    w_diff /= norm
    
    # Extract angle: angle = 2 * acos(|w|)
    # Clamp w_diff to [-1, 1] for numerical stability
    w_diff = max(-1.0, min(1.0, w_diff))
    angle_rad = 2.0 * math.acos(abs(w_diff))
    angle_deg = math.degrees(angle_rad)
    
    return angle_deg

def calculate_slippage_distance(
    initial_position: Tuple[float, float, float],
    final_position: Tuple[float, float, float]
) -> float:
    """
    Calculate the slippage distance (Euclidean displacement) of an object.
    
    Args:
        initial_position: (x, y, z) position before manipulation
        final_position: (x, y, z) position after manipulation
        
    Returns:
        Slippage distance in meters
    """
    dx = final_position[0] - initial_position[0]
    dy = final_position[1] - initial_position[1]
    dz = final_position[2] - initial_position[2]
    
    return math.sqrt(dx**2 + dy**2 + dz**2)

def is_stable(
    tipping_angle_deg: float,
    slippage_distance_m: float,
    tipping_threshold_deg: float,
    slippage_threshold_m: float
) -> bool:
    """
    Determine if an episode is stable based on physics metrics.
    
    An episode is stable if:
    1. Tipping angle is below the threshold
    2. Slippage distance is below the threshold
    
    Args:
        tipping_angle_deg: Calculated tipping angle in degrees
        slippage_distance_m: Calculated slippage distance in meters
        tipping_threshold_deg: Maximum allowed tipping angle
        slippage_threshold_m: Maximum allowed slippage distance
        
    Returns:
        True if stable, False otherwise
    """
    return (tipping_angle_deg < tipping_threshold_deg and 
            slippage_distance_m < slippage_threshold_m)

def get_stability_label(
    initial_quaternion: Tuple[float, float, float, float],
    final_quaternion: Tuple[float, float, float, float],
    initial_position: Tuple[float, float, float],
    final_position: Tuple[float, float, float],
    config: Optional[Dict[str, Any]] = None
) -> int:
    """
    Calculate the binary stability label for an episode.
    
    Args:
        initial_quaternion: Object quaternion at start
        final_quaternion: Object quaternion at end
        initial_position: Object position at start
        final_position: Object position at end
        config: Optional configuration dict. If None, loads from file.
        
    Returns:
        1 if stable, 0 if unstable
    """
    if config is None:
        config = load_config()
    
    tipping_threshold, slippage_threshold = get_thresholds(config)
    
    tipping_angle = calculate_tipping_angle(initial_quaternion, final_quaternion)
    slippage_distance = calculate_slippage_distance(initial_position, final_position)
    
    stable = is_stable(
        tipping_angle,
        slippage_distance,
        tipping_threshold,
        slippage_threshold
    )
    
    return 1 if stable else 0
