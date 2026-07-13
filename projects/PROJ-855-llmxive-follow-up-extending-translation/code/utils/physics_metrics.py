"""
Physics metrics for stability labeling.
Loads thresholds from config.yaml and calculates tipping/slippage.
"""
import os
import math
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import yaml

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if config_path is None:
        # Default to code/config.yaml relative to this file
        config_path = Path(__file__).parent.parent / "config.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def get_thresholds(config: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
    """Extract physics thresholds from config."""
    if config is None:
        config = load_config()
    
    physics = config.get("physics", {})
    return {
        "tipping_angle_deg": physics.get("tipping_angle_threshold_deg", 15.0),
        "slippage_mm": physics.get("slippage_distance_threshold_mm", 5.0),
        "force_n": physics.get("force_threshold_n", 10.0)
    }

def calculate_tipping_angle(object_pose_quat: Tuple[float, float, float, float], 
                            gravity_vector: Tuple[float, float, float] = (0, 0, -9.81)) -> float:
    """
    Calculate the tipping angle of an object based on its orientation.
    Returns the angle in degrees from the vertical axis.
    """
    qx, qy, qz, qw = object_pose_quat
    
    # Convert quaternion to Euler angles (roll, pitch, yaw)
    # Tipping angle is typically the maximum of roll and pitch deviation from 0
    
    # Calculate pitch (rotation around Y axis)
    sin_pitch = 2 * (qw * qy - qx * qz)
    cos_pitch = 1 - 2 * (qy * qy + qz * qz)
    pitch = math.atan2(sin_pitch, cos_pitch)
    
    # Calculate roll (rotation around X axis)
    sin_roll = 2 * (qw * qx + qy * qz)
    cos_roll = 1 - 2 * (qx * qx + qy * qy)
    roll = math.atan2(sin_roll, cos_roll)
    
    # Convert to degrees
    pitch_deg = math.degrees(pitch)
    roll_deg = math.degrees(roll)
    
    # Return the maximum deviation
    return max(abs(pitch_deg), abs(roll_deg))

def calculate_slippage_distance(initial_pos: Tuple[float, float, float], 
                                final_pos: Tuple[float, float, float]) -> float:
    """
    Calculate the Euclidean distance the object moved (slippage).
    Returns distance in mm.
    """
    dx = final_pos[0] - initial_pos[0]
    dy = final_pos[1] - initial_pos[1]
    dz = final_pos[2] - initial_pos[2]
    
    distance_m = math.sqrt(dx*dx + dy*dy + dz*dz)
    return distance_m * 1000  # Convert to mm

def is_stable(tipping_angle: float, slippage_distance: float, 
              thresholds: Optional[Dict[str, float]] = None) -> bool:
    """
    Determine if an object is stable based on tipping and slippage thresholds.
    Returns True if stable, False otherwise.
    """
    if thresholds is None:
        config = load_config()
        thresholds = get_thresholds(config)
    
    tipping_threshold = thresholds["tipping_angle_deg"]
    slippage_threshold = thresholds["slippage_mm"]
    
    # Stable if both conditions are met
    return (tipping_angle <= tipping_threshold and 
            slippage_distance <= slippage_threshold)

def get_stability_label(tipping_angle: float, slippage_distance: float,
                        config: Optional[Dict[str, Any]] = None) -> int:
    """
    Get binary stability label (1 for stable, 0 for unstable).
    """
    if config is None:
        config = load_config()
    thresholds = get_thresholds(config)
    
    stable = is_stable(tipping_angle, slippage_distance, thresholds)
    return 1 if stable else 0
