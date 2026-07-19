import os
import math
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import yaml

def load_config(config_path="code/config.yaml"):
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {
            "physics": {
                "tipping_angle_threshold": 0.15,
                "slippage_distance_threshold": 0.02
            }
        }

def get_thresholds(config: Dict[str, Any]) -> Tuple[float, float]:
    """Extract thresholds from config."""
    physics = config.get("physics", {})
    tipping = physics.get("tipping_angle_threshold", 0.15)
    slippage = physics.get("slippage_distance_threshold", 0.02)
    return tipping, slippage

def calculate_tipping_angle(velocity_z: float, velocity_xy: float) -> float:
    """Calculate tipping angle from velocity components."""
    if velocity_xy == 0:
        return 0.0
    return abs(math.atan2(velocity_z, velocity_xy))

def calculate_slippage_distance(translation: Tuple[float, float, float]) -> float:
    """Calculate slippage distance from translation vector."""
    return math.sqrt(translation[0]**2 + translation[1]**2)

def is_stable(tipping_angle: float, slippage_distance: float, thresholds: Tuple[float, float]) -> bool:
    """Determine stability based on thresholds."""
    tipping_thresh, slippage_thresh = thresholds
    if tipping_angle > tipping_thresh:
        return False
    if slippage_distance > slippage_thresh:
        return False
    return True

def get_stability_label(tipping_angle: float, slippage_distance: float, thresholds: Tuple[float, float]) -> int:
    """Get binary stability label (1=stable, 0=unstable)."""
    return 1 if is_stable(tipping_angle, slippage_distance, thresholds) else 0
