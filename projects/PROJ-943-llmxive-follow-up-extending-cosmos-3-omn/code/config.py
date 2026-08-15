"""
Environment configuration management for llmXive pipeline.

Handles:
- Global random seeds for reproducibility (numpy, torch, random)
- Path resolution for project directories (data, models, logs, etc.)
- Environment variable overrides for paths and settings
"""

import os
import random
from pathlib import Path
from typing import Optional, Dict, Any

# Base project root (assumed to be the directory containing this file's parent 'code')
# Since this file is at code/config.py, the root is code/../..
# However, based on task T001-T006, the project structure puts 'code' at the root of the repo for the scripts.
# Let's assume the repo root is the parent of 'code'.
# If the script is run from within 'code', we adjust.
# Standard convention: PROJECT_ROOT = Path(__file__).resolve().parents[1]
# But tasks T001-T006 imply 'code' is the top level directory for artifacts.
# Let's define the root as the directory containing 'config.py' itself if 'code' is the root,
# or the parent if 'code' is a subdirectory.
# Given T001a creates `code/scripts/`, `code` is the project root for the artifacts.
# We will set PROJECT_ROOT to the directory containing this file.

_SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _SCRIPT_DIR

# Directory Paths
DIR_RAW_DATA = PROJECT_ROOT / "data" / "raw"
DIR_PROCESSED_DATA = PROJECT_ROOT / "data" / "processed"
DIR_SPLITS = PROJECT_ROOT / "data" / "splits"
DIR_MODELS = PROJECT_ROOT / "models"
DIR_LOGS = PROJECT_ROOT / "logs"
DIR_RESULTS = PROJECT_ROOT / "data" / "results"
DIR_FIGURES = PROJECT_ROOT / "figures"
DIR_CONFIGS = PROJECT_ROOT / "configs"

# Ensure directories exist
def _ensure_dirs() -> None:
    """Create all required project directories if they do not exist."""
    dirs = [
        DIR_RAW_DATA,
        DIR_PROCESSED_DATA,
        DIR_SPLITS,
        DIR_MODELS,
        DIR_LOGS,
        DIR_RESULTS,
        DIR_FIGURES,
        DIR_CONFIGS
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# Initialize directories immediately on import
_ensure_dirs()

# Default Configuration
DEFAULT_SEED = 42
DEFAULT_DEVICE = "cpu"
DEFAULT_LOG_LEVEL = "INFO"

# Environment Variable Keys
ENV_SEED = "LLMXIVE_SEED"
ENV_DEVICE = "LLMXIVE_DEVICE"
ENV_LOG_LEVEL = "LLMXIVE_LOG_LEVEL"
ENV_DATA_ROOT = "LLMXIVE_DATA_ROOT"
ENV_MODEL_ROOT = "LLMXIVE_MODEL_ROOT"

def get_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables or defaults.
    Returns a dictionary of configuration values.
    """
    seed = int(os.getenv(ENV_SEED, DEFAULT_SEED))
    device = os.getenv(ENV_DEVICE, DEFAULT_DEVICE)
    log_level = os.getenv(ENV_LOG_LEVEL, DEFAULT_LOG_LEVEL)

    # Allow overriding specific paths via env vars
    data_root = os.getenv(ENV_DATA_ROOT, str(PROJECT_ROOT))
    model_root = os.getenv(ENV_MODEL_ROOT, str(PROJECT_ROOT))

    # Re-evaluate paths if overridden
    base_path = Path(data_root) if not data_root.startswith('/') else Path(data_root)
    # If the env var points to the repo root, we need to adjust relative to code/
    # If the env var points to the code/ directory, we use it directly.
    # For simplicity, we assume env vars override the base PROJECT_ROOT.
    # If ENV_DATA_ROOT is set, we assume it's the new root for data.
    if ENV_DATA_ROOT in os.environ:
        DIR_RAW_DATA = Path(data_root) / "data" / "raw"
        DIR_PROCESSED_DATA = Path(data_root) / "data" / "processed"
        DIR_SPLITS = Path(data_root) / "data" / "splits"
        DIR_RESULTS = Path(data_root) / "data" / "results"
        # Re-ensure dirs if root changed
        for d in [DIR_RAW_DATA, DIR_PROCESSED_DATA, DIR_SPLITS, DIR_RESULTS]:
            d.mkdir(parents=True, exist_ok=True)

    if ENV_MODEL_ROOT in os.environ:
        DIR_MODELS = Path(model_root) / "models"
        DIR_MODELS.mkdir(parents=True, exist_ok=True)

    return {
        "seed": seed,
        "device": device,
        "log_level": log_level,
        "paths": {
            "raw_data": DIR_RAW_DATA,
            "processed_data": DIR_PROCESSED_DATA,
            "splits": DIR_SPLITS,
            "models": DIR_MODELS,
            "logs": DIR_LOGS,
            "results": DIR_RESULTS,
            "figures": DIR_FIGURES,
            "configs": DIR_CONFIGS
        }
    }

def set_seed(seed: Optional[int] = None) -> None:
    """
    Set global random seeds for reproducibility.
    Uses the seed from get_config() if none provided.
    """
    if seed is None:
        config = get_config()
        seed = config["seed"]

    random.seed(seed)
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

def get_path(key: str) -> Path:
    """
    Get a specific path from the configuration.
    Args:
        key: One of 'raw_data', 'processed_data', 'splits', 'models', 'logs', 'results', 'figures', 'configs'
    Returns:
        Path object
    """
    config = get_config()
    return config["paths"][key]

def get_device() -> str:
    """Get the configured device (cpu, cuda, etc)."""
    return get_config()["device"]

# Initialize seed on module load to ensure reproducibility for any immediate calls
# Note: In a real script, set_seed() is usually called explicitly at the start of main()
# but doing it here ensures the environment is prepared.
# We will NOT call set_seed() here to avoid side-effects on import if the user wants to set it later.
# Instead, we provide the function.

# Export public API
__all__ = [
    "get_config",
    "set_seed",
    "get_path",
    "get_device",
    "PROJECT_ROOT",
    "DIR_RAW_DATA",
    "DIR_PROCESSED_DATA",
    "DIR_SPLITS",
    "DIR_MODELS",
    "DIR_LOGS",
    "DIR_RESULTS",
    "DIR_FIGURES",
    "DIR_CONFIGS"
]