"""
Configuration management for the statistical analysis pipeline.

Handles seed pinning for reproducibility and path resolution for data/state directories.
"""
import os
import random
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

# Project root is the parent of the 'src' directory
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent
DATA_DIR: Path = PROJECT_ROOT / "data"
STATE_DIR: PROJECT_ROOT / "state"
RAW_DATA_DIR: Path = DATA_DIR / "raw"
PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
FIGURES_DIR: Path = DATA_DIR / "figures"

# Default configuration
DEFAULT_SEED: int = 42
CONFIG_FILE_NAME: str = "project_config.yaml"


def get_config_path() -> Path:
    """Return the path to the project configuration file."""
    return PROJECT_ROOT / CONFIG_FILE_NAME


def load_config() -> Dict[str, Any]:
    """
    Load configuration from the YAML file.
    
    Returns:
        Dictionary containing configuration settings.
    """
    config_path = get_config_path()
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def save_config(config: Dict[str, Any]) -> None:
    """
    Save configuration to the YAML file.
    
    Args:
        config: Dictionary of configuration settings to save.
    """
    config_path = get_config_path()
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False)


def get_seed() -> int:
    """
    Get the random seed for reproducibility.
    
    Reads the seed from config if available, otherwise uses the default.
    
    Returns:
        Integer seed value.
    """
    config = load_config()
    return config.get("seed", DEFAULT_SEED)


def set_seed(seed: Optional[int] = None) -> int:
    """
    Set the random seed for the entire pipeline.
    
    This function:
    1. Updates the global seed in the configuration file.
    2. Seeds Python's random module.
    3. Seeds numpy (if available).
    4. Seeds PyMC (if available).
    
    Args:
        seed: Optional integer seed. If None, uses DEFAULT_SEED.
    
    Returns:
        The seed value that was set.
    """
    if seed is None:
        seed = DEFAULT_SEED
    
    # Update config
    config = load_config()
    config["seed"] = seed
    save_config(config)
    
    # Seed Python random
    random.seed(seed)
    
    # Seed numpy
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    
    # Seed PyMC
    try:
        import pymc as pm
        pm.set_rng_seed(seed)
    except ImportError:
        pass
    
    return seed


def resolve_data_path(sub_path: str) -> Path:
    """
    Resolve a relative path within the data directory.
    
    Args:
        sub_path: Relative path string (e.g., "raw/polls.csv").
    
    Returns:
        Absolute Path object within the data directory.
    """
    full_path = DATA_DIR / sub_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    return full_path


def resolve_processed_path(sub_path: str) -> Path:
    """
    Resolve a relative path within the processed data directory.
    
    Args:
        sub_path: Relative path string (e.g., "poll_data_cleaned.csv").
    
    Returns:
        Absolute Path object within the processed data directory.
    """
    full_path = PROCESSED_DATA_DIR / sub_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    return full_path


def resolve_state_path(sub_path: str) -> Path:
    """
    Resolve a relative path within the state directory.
    
    Args:
        sub_path: Relative path string (e.g., "projects/PROJ-206.yaml").
    
    Returns:
        Absolute Path object within the state directory.
    """
    full_path = STATE_DIR / sub_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    return full_path


def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
    
    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot compute hash: file not found at {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_project_id() -> str:
    """
    Get the project ID from environment or defaults.
    
    Returns:
        Project ID string.
    """
    return os.getenv("PROJECT_ID", "PROJ-206-statistical-analysis-of-publicly-availab")


def ensure_directories() -> None:
    """Ensure all required directories exist."""
    dirs = [
        DATA_DIR,
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        FIGURES_DIR,
        STATE_DIR,
        STATE_DIR / "projects"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)