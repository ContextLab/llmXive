"""
Configuration and constants for the project.

Defines paths, random seeds, and mode flags.
"""
from __future__ import annotations

import os
from pathlib import Path
import random
import numpy as np
import yaml

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data Mode Configuration
# Default is 'real'. Set to 'simulation' only if Spec Amendment T090 is APPROVED
# and ENABLE_SIMULATION is True.
DATA_MODE = os.getenv('DATA_MODE', 'real')

# Flag to enable simulation mode (must be True for simulation to run)
ENABLE_SIMULATION = os.getenv('ENABLE_SIMULATION', 'False').lower() == 'true'

# Constants
N_CONFIG = 100  # Default N for MDES fallback

# Formal Deviation Flag
FORMAL_DEVIATION_VR_LOGS = False  # Set to True if T090 is approved

def ensure_directories():
    """Create required directories if they don't exist."""
    dirs = [
        PROJECT_ROOT / "data" / "raw",
        PROJECT_ROOT / "data" / "processed",
        PROJECT_ROOT / "data" / "logs",
        PROJECT_ROOT / "data" / "config",
        PROJECT_ROOT / "state",
        PROJECT_ROOT / "reports",
        PROJECT_ROOT / "figures"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def init_random_seeds(seed: int = 42):
    """Initialize random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)

def validate_data_mode():
    """Validate that DATA_MODE is set correctly."""
    if DATA_MODE not in ['real', 'simulation']:
        raise ValueError(f"Invalid DATA_MODE: {DATA_MODE}. Must be 'real' or 'simulation'.")
    if DATA_MODE == 'simulation' and not ENABLE_SIMULATION:
        raise RuntimeError("Simulation mode requested but ENABLE_SIMULATION is False. "
                           "Check Spec Amendment T090 status.")

def get_path(*parts: str) -> Path:
    """
    Construct a path relative to the project root.
    
    Accepts multiple path segments or a single segment.
    Examples:
      get_path("data", "processed/output.csv") -> PROJECT_ROOT / "data" / "processed" / "output.csv"
      get_path("data/processed/output.csv") -> PROJECT_ROOT / "data" / "processed" / "output.csv"
    """
    if not parts:
        raise ValueError("get_path() requires at least one path argument")
    
    # Handle single argument that might be a full relative path string
    if len(parts) == 1:
        return PROJECT_ROOT / parts[0]
    
    # Handle multiple arguments
    return PROJECT_ROOT / os.path.join(*parts)

def load_yaml_config(file_path: str) -> dict:
    """Load a YAML configuration file."""
    full_path = get_path(file_path)
    if not full_path.exists():
        raise FileNotFoundError(f"Config file not found: {full_path}")
    with open(full_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# Initialize directories on import if needed
ensure_directories()