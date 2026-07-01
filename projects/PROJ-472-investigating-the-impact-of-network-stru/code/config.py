"""
Configuration module for the project.
Handles paths, seeds, and hyperparameters.
"""
import os
from pathlib import Path
from typing import Any, Dict, Final

# Project root is assumed to be the parent of 'code'
PROJECT_ROOT: Final[Path] = Path(__file__).parent.parent

def get_data_root() -> Path:
    """Return the root path for data directory."""
    return PROJECT_ROOT / "data"

def ensure_directories() -> None:
    """Ensure all required data directories exist."""
    data_root = get_data_root()
    (data_root / "raw").mkdir(parents=True, exist_ok=True)
    (data_root / "processed").mkdir(parents=True, exist_ok=True)
    (data_root / "results").mkdir(parents=True, exist_ok=True)
    (data_root / "figures").mkdir(parents=True, exist_ok=True)

# Simulation parameters (Wilson-Cowan defaults)
SIMULATION_PARAMS: Final[Dict[str, Any]] = {
    "connection_strength": 1.2,
    "time_constant": 10.0,
    "external_input": 0.5,
    "noise_level": 0.1,
    "dt": 0.1,
    "duration": 1000.0,
}
