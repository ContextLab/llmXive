import os
from pathlib import Path
import random
import numpy as np
import yaml

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directory paths (relative to PROJECT_ROOT)
DIRS = {
    "code": "code",
    "data": "data",
    "tests": "tests",
    "state": "state",
    "data_raw": "data/raw",
    "data_processed": "data/processed",
    "data_logs": "data/logs",
    "reports": "reports",
    "figures": "figures"
}

# Random seed for reproducibility
RANDOM_SEED = 42

# Data Mode Configuration
# Options: 'simulation' | 'real'
# Default: 'simulation'
# If set to 'real', the pipeline will attempt to fetch real data from OSF/HuggingFace
# and will fail loudly if the fetch fails (no synthetic fallback).
DATA_MODE = os.getenv('DATA_MODE', 'simulation')

# Statistical Constants
ALPHA = 0.05
BONFERRONI_CORRECTION_FACTOR = 1  # Will be updated dynamically based on number of tests

# Model Hyperparameters (Simulation Only for now)
GROUND_TRUTH_EFFECT_SIZE = 0.5  # Known effect size for simulation validation

def ensure_directories():
    """Create all required directories if they don't exist."""
    for dir_name in DIRS.values():
        dir_path = PROJECT_ROOT / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)

def init_random_seeds(seed: int = RANDOM_SEED):
    """Initialize random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass  # PyTorch not installed

def validate_data_mode():
    """
    Validates the DATA_MODE configuration.
    Raises ValueError if DATA_MODE is not 'simulation' or 'real'.
    Also enforces the constraint that 'real' mode requires verified sources.
    """
    valid_modes = ['simulation', 'real']
    if DATA_MODE not in valid_modes:
        raise ValueError(f"Invalid DATA_MODE '{DATA_MODE}'. Must be one of {valid_modes}")
    
    if DATA_MODE == 'real':
        # Verify that the real data interface is populated (T050)
        # We attempt to import the constants to ensure the interface exists
        try:
            from data.ingest_real import OSF_API_URL, HF_DATASET_ID, VR_LOG_SCHEMA_COLUMNS
            if not OSF_API_URL or not HF_DATASET_ID:
                raise ValueError("Real data mode enabled but OSF_API_URL or HF_DATASET_ID not defined in ingest_real.py")
        except ImportError as e:
            raise ImportError(
                "DATA_MODE='real' requires the real data interface (T050) to be implemented. "
                f"Failed to import ingest_real constants: {e}"
            )
    
    return True

def get_path(*args, **kwargs) -> Path:
    """
    Resolve a relative path to an absolute path within the project root.
    
    This function is overloaded to support multiple calling conventions found in the codebase:
    
    1. get_path("data/processed/output.csv") -> Returns PROJECT_ROOT / "data/processed/output.csv"
    2. get_path("data", "logs/exclusion.log") -> Returns PROJECT_ROOT / "data" / "logs/exclusion.log"
    3. get_path("", "data/raw/file.csv") -> Returns PROJECT_ROOT / "data/raw/file.csv"
    
    Args:
        *args: Path components. 
               - If 1 arg: treated as a single relative path string.
               - If 2+ args: treated as sequential path segments to join.
        **kwargs: Unused, provided for future extensibility or ignored call sites.
    
    Returns:
        Absolute Path object relative to PROJECT_ROOT.
    
    Raises:
        ValueError: If no arguments are provided.
    """
    if not args:
        raise ValueError("get_path() requires at least one path argument")
    
    # If a single string argument is provided, treat it as the full relative path
    if len(args) == 1 and isinstance(args[0], str):
        relative_path = args[0]
    else:
        # If multiple arguments or non-string types, join them as path segments
        # Convert all args to strings to ensure safe joining
        relative_path = os.path.join(*[str(arg) for arg in args])
    
    # Handle the specific case where the first arg is an empty string (common in some calls)
    # os.path.join("", "path") returns "path", which is correct behavior.
    
    return PROJECT_ROOT / relative_path

def load_yaml_config(file_path: str) -> dict:
    """
    Load a YAML configuration file.
    
    Args:
        file_path: Relative path to the YAML file (e.g., 'data/config/unity_blend_shapes.yaml')
    
    Returns:
        Dictionary containing the configuration
    """
    full_path = get_path(file_path)
    if not full_path.exists():
        raise FileNotFoundError(f"Config file not found: {full_path}")
    
    with open(full_path, 'r') as f:
        return yaml.safe_load(f)