import os
import random
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.logger import get_logger

logger = get_logger(__name__)

_SEED = 42
_SIMULATED_MODE = False
_MODE_HALIDE = None

def get_path() -> Path:
    """Get project root path."""
    return Path(__file__).parent.parent.parent

def get_data_path() -> Path:
    """Get data directory path."""
    return get_path() / "data"

def get_code_path() -> Path:
    """Get code directory path."""
    return get_path() / "code"

def set_seed(seed: int = 42):
    """Set random seed for reproducibility."""
    global _SEED
    _SEED = seed
    random.seed(seed)
    if 'numpy' in globals():
        import numpy as np
        np.random.seed(seed)
    logger.info(f"Random seed set to {seed}")

def get_solvent_list() -> List[str]:
    """Return list of allowed solvents."""
    return ['acetonitrile', 'chloroform', 'dichloromethane', 'dcm']

def is_simulated_mode() -> bool:
    """Check if pipeline is running in simulated data mode."""
    return _SIMULATED_MODE

def set_simulated_mode(mode: bool, halide: Optional[str] = None):
    """Set simulated mode flag and mode halide."""
    global _SIMULATED_MODE, _MODE_HALIDE
    _SIMULATED_MODE = mode
    _MODE_HALIDE = halide
    logger.info(f"Simulated mode set to {mode}, mode halide: {halide}")

def get_mode_halide() -> Optional[str]:
    """Get the mode halide if in simulated mode."""
    return _MODE_HALIDE
