import os
import random
import numpy as np
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

_project_root: Optional[Path] = None
_random_seed: int = 42


def get_project_root() -> Path:
    """
    Returns the project root directory.
    
    Returns:
        Path object pointing to the project root.
    """
    global _project_root
    if _project_root is None:
        # Determine project root from the current file's location
        _project_root = Path(__file__).parent.parent.parent
    return _project_root


def get_data_raw_path() -> Path:
    """
    Returns the path to the raw data directory.
    
    Returns:
        Path object pointing to data/raw.
    """
    return get_project_root() / "data" / "raw"


def get_data_processed_path() -> Path:
    """
    Returns the path to the processed data directory.
    
    Returns:
        Path object pointing to data/processed.
    """
    return get_project_root() / "data" / "processed"


def get_output_path() -> Path:
    """
    Returns the path to the outputs directory.
    
    Returns:
        Path object pointing to outputs.
    """
    return get_project_root() / "outputs"


def get_figures_path() -> Path:
    """
    Returns the path to the figures directory.
    
    Returns:
        Path object pointing to outputs/figures.
    """
    return get_output_path() / "figures"


def get_millennium_path() -> Path:
    """
    Returns the path to the millennium data directory.
    
    Returns:
        Path object pointing to data/raw/millennium.
    """
    return get_data_raw_path() / "millennium"


def get_logs_path() -> Path:
    """
    Returns the path to the logs directory.
    
    Returns:
        Path object pointing to state/logs (or a dedicated logs dir).
    """
    return get_project_root() / "state" / "logs"


def get_state_path() -> Path:
    """
    Returns the path to the state directory.
    
    Returns:
        Path object pointing to state.
    """
    return get_project_root() / "state"


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Loads configuration from a YAML file.
    
    Args:
        config_path: Path to the config file. If None, uses default location.
    
    Returns:
        Dictionary containing configuration.
    """
    if config_path is None:
        config_path = get_project_root() / "config.yaml"
    
    config_path = Path(config_path)
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f) or {}
    else:
        # Return default configuration
        return {
            "random_seed": 42,
            "tng_api_key": "",
            "chunk_size": 1000,
            "mass_tolerance": 0.1,
            "binning_thresholds": {
                "prolate": 0.5,
                "triaxial_upper": 0.8
            }
        }


def set_random_seed(seed: int) -> None:
    """
    Sets the random seed for reproducibility.
    
    Args:
        seed: The random seed value.
    """
    global _random_seed
    _random_seed = seed
    random.seed(seed)
    np.random.seed(seed)


def get_random_seed() -> int:
    """
    Returns the current random seed.
    
    Returns:
        The current random seed value.
    """
    return _random_seed
