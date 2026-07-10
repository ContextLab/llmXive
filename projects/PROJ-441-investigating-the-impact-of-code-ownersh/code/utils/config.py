"""
Configuration management for the llmXive research pipeline.

Provides:
- Environment variable loading from .env files
- Random seed pinning for reproducibility
- Centralized configuration dictionary
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None  # type: ignore


# Default configuration values
DEFAULT_CONFIG: Dict[str, Any] = {
    "seed": 42,
    "max_workers": 2,
    "timeout_seconds": 300,
    "log_level": "INFO",
    "data_dir": "data",
    "code_dir": "code",
    "results_dir": "data/results",
    "processed_dir": "data/processed",
    "raw_dir": "data/raw",
    "figures_dir": "figures",
    "max_snippets_per_repo": 5,
    "max_tokens": 2048,
    "runtime_limit_hours": 6.0,
    "auto_stop_threshold_hours": 5.5,
}


def load_env(env_path: Optional[str] = None) -> bool:
    """
    Load environment variables from a .env file.

    Args:
        env_path: Path to the .env file. If None, looks for .env in the
                  project root or parent directories.

    Returns:
        True if loading was successful (or not required), False otherwise.
    """
    if load_dotenv is None:
        # If python-dotenv is not installed, try to load from standard locations
        # or rely on system environment variables
        project_root = Path(__file__).resolve().parent.parent.parent
        env_candidates = [
            project_root / ".env",
            Path.cwd() / ".env",
            Path.home() / ".env",
        ]
        for candidate in env_candidates:
            if candidate.exists():
                # Manually parse simple KEY=VALUE lines if dotenv is missing
                try:
                    with open(candidate, "r") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#") and "=" in line:
                                key, value = line.split("=", 1)
                                os.environ[key.strip()] = value.strip().strip('"').strip("'")
                    return True
                except Exception:
                    pass
        return False

    # Use python-dotenv if available
    if env_path:
        return load_dotenv(env_path)

    # Default search path
    return load_dotenv()


def set_seed(seed: Optional[int] = None) -> int:
    """
    Set the random seed for reproducibility across all relevant libraries.

    Args:
        seed: The seed value. If None, uses the value from config or defaults to 42.

    Returns:
        The seed value that was set.
    """
    if seed is None:
        seed = int(os.environ.get("RESEARCH_SEED", DEFAULT_CONFIG["seed"]))

    random.seed(seed)

    # Set seeds for common libraries if available
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass

    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass

    try:
        import tensorflow as tf
        tf.random.set_seed(seed)
    except ImportError:
        pass

    return seed


def get_config() -> Dict[str, Any]:
    """
    Load and return the complete configuration dictionary.

    This function:
    1. Loads environment variables from .env if available
    2. Merges with default configuration
    3. Overrides with environment variables (RESEARCH_ prefix)

    Returns:
        A dictionary containing all configuration values.
    """
    # Load environment variables
    load_env()

    # Start with defaults
    config = DEFAULT_CONFIG.copy()

    # Override with environment variables (prefixed with RESEARCH_)
    for key, default_value in DEFAULT_CONFIG.items():
        env_key = f"RESEARCH_{key.upper()}"
        env_value = os.environ.get(env_key)

        if env_value is not None:
            # Type conversion based on default value type
            if isinstance(default_value, bool):
                config[key] = env_value.lower() in ("true", "1", "yes", "on")
            elif isinstance(default_value, int):
                try:
                    config[key] = int(env_value)
                except ValueError:
                    pass
            elif isinstance(default_value, float):
                try:
                    config[key] = float(env_value)
                except ValueError:
                    pass
            elif isinstance(default_value, str):
                config[key] = env_value

    return config


def get_path(key: str, base_dir: Optional[Path] = None) -> Path:
    """
    Get a resolved Path object for a configuration key.

    Args:
        key: The configuration key (e.g., "data_dir", "results_dir")
        base_dir: Base directory to resolve relative paths against.
                 If None, uses the project root.

    Returns:
        A resolved Path object.
    """
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent.parent

    config = get_config()
    path_str = config.get(key, "")

    if not path_str:
        raise ValueError(f"Configuration key '{key}' not found or empty")

    path = Path(path_str)
    if not path.is_absolute():
        path = base_dir / path

    return path


# Initialize configuration on module load
CONFIG = get_config()

# Set seed immediately if specified in environment
if os.environ.get("RESEARCH_SEED") or "seed" in os.environ:
    set_seed()