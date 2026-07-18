"""
Configuration management for llmXive.

Handles:
- Seed pinning for reproducibility
- Path resolution (absolute paths relative to project root)
- Environment variable loading (.env support)
"""

import os
import random
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from dotenv import load_dotenv
except ImportError:
    # Fallback if python-dotenv is not installed (though it should be per requirements)
    def load_dotenv(verbose=False, override=False):
        return False

# --- Constants ---
# Project root is assumed to be the parent of 'src'
# We detect it dynamically to support running from different directories
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"

# Default configuration values
DEFAULT_SEED = 42
DEFAULT_DEVICE = "cpu"
DEFAULT_BATCH_SIZE = 32
DEFAULT_MAX_LENGTH = 512

# --- Global State ---
_config_cache: Dict[str, Any] = {}
_is_initialized = False


def _get_env(name: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Retrieve an environment variable.
    
    Args:
        name: The environment variable name.
        default: Default value if not found.
        required: If True, raise an error if not found.
        
    Returns:
        The value of the environment variable or default.
        
    Raises:
        ValueError: If required is True and the variable is not set.
    """
    value = os.getenv(name, default)
    if required and value is None:
        raise ValueError(f"Required environment variable '{name}' is not set.")
    return value


def _parse_int(value: Optional[str], default: int) -> int:
    """Safely parse an integer from a string."""
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _parse_bool(value: Optional[str], default: bool) -> bool:
    """Safely parse a boolean from a string."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return value.lower() in ("true", "1", "yes", "on")


def initialize(seed: Optional[int] = None) -> Dict[str, Any]:
    """
    Initialize the configuration system.
    
    1. Loads environment variables from .env file if present.
    2. Sets global random seeds (Python, Numpy, PyTorch).
    3. Caches configuration values.
    
    Args:
        seed: Optional seed override. Defaults to DEFAULT_SEED if not provided.
        
    Returns:
        A dictionary of the loaded configuration.
    """
    global _config_cache, _is_initialized
    
    # Load .env
    if _ENV_FILE.exists():
        load_dotenv(dotenv_path=_ENV_FILE)
    
    # Determine seed
    seed_val = seed if seed is not None else _parse_int(_get_env("SEED"), DEFAULT_SEED)
    
    # Set seeds
    random.seed(seed_val)
    try:
        import numpy as np
        np.random.seed(seed_val)
    except ImportError:
        pass
    
    try:
        import torch
        torch.manual_seed(seed_val)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed_val)
            torch.cuda.manual_seed_all(seed_val)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass
    
    # Build config cache
    _config_cache = {
        "seed": seed_val,
        "device": _get_env("DEVICE", DEFAULT_DEVICE),
        "batch_size": _parse_int(_get_env("BATCH_SIZE"), DEFAULT_BATCH_SIZE),
        "max_length": _parse_int(_get_env("MAX_LENGTH"), DEFAULT_MAX_LENGTH),
        "log_level": _get_env("LOG_LEVEL", "INFO"),
        "data_dir": _get_env("DATA_DIR", None), # Allows override, else computed
        "artifacts_dir": _get_env("ARTIFACTS_DIR", None),
        "enable_cache": _parse_bool(_get_env("ENABLE_CACHE", "true"), True),
    }
    
    _is_initialized = True
    return _config_cache


def get_config() -> Dict[str, Any]:
    """
    Get the current configuration dictionary.
    
    Raises:
        RuntimeError: If initialize() has not been called.
    """
    if not _is_initialized:
        initialize()
    return _config_cache.copy()


def get_path(sub_path: str) -> Path:
    """
    Resolve a path relative to the project root or configured directories.
    
    Priority:
    1. If sub_path is absolute, return it.
    2. If 'data_dir' is set in config and sub_path looks like a data path, use it.
    3. Otherwise, resolve relative to PROJECT_ROOT.
    
    Args:
        sub_path: The relative or absolute path string.
        
    Returns:
        An absolute Path object.
    """
    p = Path(sub_path)
    if p.is_absolute():
        return p
    
    # Check for specific directory overrides in config
    cfg = get_config()
    if p.parts[0] == "data" and cfg.get("data_dir"):
        return Path(cfg["data_dir"]) / p.relative_to("data")
    if p.parts[0] == "artifacts" and cfg.get("artifacts_dir"):
        return Path(cfg["artifacts_dir"]) / p.relative_to("artifacts")
        
    return _PROJECT_ROOT / p


def get_project_root() -> Path:
    """Returns the absolute path to the project root."""
    return _PROJECT_ROOT


# Convenience accessors
def get_seed() -> int:
    return get_config()["seed"]

def get_device() -> str:
    return get_config()["device"]

def get_batch_size() -> int:
    return get_config()["batch_size"]

def get_max_length() -> int:
    return get_config()["max_length"]

def get_data_dir() -> Path:
    """Returns the base data directory path."""
    cfg = get_config()
    if cfg.get("data_dir"):
        return Path(cfg["data_dir"])
    return get_path("data")

def get_artifacts_dir() -> Path:
    """Returns the base artifacts directory path."""
    cfg = get_config()
    if cfg.get("artifacts_dir"):
        return Path(cfg["artifacts_dir"])
    return get_path("artifacts")
