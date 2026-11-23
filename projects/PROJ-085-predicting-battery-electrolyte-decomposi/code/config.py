import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
import random
import numpy as np

# Project Root
_PROJECT_ROOT: Optional[Path] = None
_CONFIG: Dict[str, Any] = {}
_SEED: int = 42
_DATASET_URL: str = "https://huggingface.co/datasets/materialsproject/mp-dft-electrolytes"

# Default paths relative to project root
_DATA_DIR = "data"
_RAW_DIR = "data/raw"
_PROCESSED_DIR = "data/processed"
_VALIDATION_DIR = "data/validation"
_OUTPUT_DIR = "data/output"
_FALLBACK_PATH = "data/raw/mock_electrolytes.csv"

def get_project_root() -> Path:
    """Returns the project root directory."""
    global _PROJECT_ROOT
    if _PROJECT_ROOT is None:
        # Try to find project root by looking for a marker file or just using cwd
        # In this pipeline, we assume the script is run from the project root
        _PROJECT_ROOT = Path.cwd()
        # Fallback: if running from code/, go up one level
        if not (_PROJECT_ROOT / ".git").exists() and (_PROJECT_ROOT.parent / ".git").exists():
            _PROJECT_ROOT = _PROJECT_ROOT.parent
    return _PROJECT_ROOT

def get_config() -> Dict[str, Any]:
    """Returns the current configuration dictionary."""
    return _CONFIG.copy()

def get_seed() -> int:
    """Returns the current random seed."""
    return _SEED

def set_seed(seed: int) -> None:
    """Sets the random seed for reproducibility."""
    global _SEED
    _SEED = seed
    random.seed(seed)
    np.random.seed(seed)
    # If using torch, set it there too (optional, but good practice)
    # import torch
    # torch.manual_seed(seed)

def get_dataset_url() -> str:
    """Returns the URL for the dataset source."""
    return _DATASET_URL

def set_dataset_url(url: str) -> None:
    """Sets the dataset URL."""
    global _DATASET_URL
    _DATASET_URL = url

def get_data_dir() -> Path:
    """Returns the path to the data directory."""
    return get_project_root() / _DATA_DIR

def get_raw_dir() -> Path:
    """Returns the path to the raw data directory."""
    return get_project_root() / _RAW_DIR

def get_processed_dir() -> Path:
    """Returns the path to the processed data directory."""
    return get_project_root() / _PROCESSED_DIR

def get_validation_dir() -> Path:
    """Returns the path to the validation data directory."""
    return get_project_root() / _VALIDATION_DIR

def get_output_dir() -> Path:
    """Returns the path to the output directory."""
    return get_project_root() / _OUTPUT_DIR

def get_fallback_path() -> Path:
    """Returns the path to the fallback data file."""
    return get_project_root() / _FALLBACK_PATH

def is_debug_mode() -> bool:
    """Checks if debug mode is enabled via environment variable."""
    return os.getenv("LLMXIVE_DEBUG", "false").lower() in ("true", "1", "yes")

def set_debug_mode(enabled: bool) -> None:
    """Sets the debug mode environment variable."""
    os.environ["LLMXIVE_DEBUG"] = "1" if enabled else "0"

def get_log_level() -> str:
    """Returns the log level based on environment or config."""
    if is_debug_mode():
        return "DEBUG"
    return os.getenv("LLMXIVE_LOG_LEVEL", "INFO")

def save_config_to_env() -> None:
    """Saves current configuration to environment variables for reproducibility."""
    os.environ["LLMXIVE_SEED"] = str(_SEED)
    os.environ["LLMXIVE_DATASET_URL"] = _DATASET_URL
    os.environ["LLMXIVE_DEBUG"] = "1" if is_debug_mode() else "0"
    # Save any custom config items
    for key, value in _CONFIG.items():
        os.environ[f"LLMXIVE_CONFIG_{key.upper()}"] = json.dumps(value)

def load_config_from_env() -> None:
    """Loads configuration from environment variables, overwriting defaults."""
    global _SEED, _DATASET_URL
    if "LLMXIVE_SEED" in os.environ:
        _SEED = int(os.environ["LLMXIVE_SEED"])
    if "LLMXIVE_DATASET_URL" in os.environ:
        _DATASET_URL = os.environ["LLMXIVE_DATASET_URL"]
    if "LLMXIVE_DEBUG" in os.environ:
        set_debug_mode(os.environ["LLMXIVE_DEBUG"] == "1")
    # Load custom config
    for key, value in os.environ.items():
        if key.startswith("LLMXIVE_CONFIG_"):
            config_key = key.replace("LLMXIVE_CONFIG_", "").lower()
            try:
                _CONFIG[config_key] = json.loads(value)
            except json.JSONDecodeError:
                _CONFIG[config_key] = value

def get_config_summary() -> Dict[str, Any]:
    """Returns a summary of the current configuration for logging."""
    return {
        "seed": _SEED,
        "dataset_url": _DATASET_URL,
        "debug_mode": is_debug_mode(),
        "log_level": get_log_level(),
        "paths": {
            "project_root": str(get_project_root()),
            "data_dir": str(get_data_dir()),
            "raw_dir": str(get_raw_dir()),
            "processed_dir": str(get_processed_dir()),
            "validation_dir": str(get_validation_dir()),
        }
    }

# Initialize seed on module load to ensure reproducibility even if set_seed isn't called explicitly
set_seed(_SEED)