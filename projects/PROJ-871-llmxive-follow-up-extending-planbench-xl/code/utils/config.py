import os
from pathlib import Path
from typing import Dict, Any, Optional

# Project root is determined relative to this file's location
# Assuming the structure: projects/PROJ-871-.../code/utils/config.py
# We go up 3 levels to reach the project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Default configuration values
DEFAULT_HYPERPARAMETERS = {
    "llm_batch_size": 1,  # Minimal batch size for CPU memory safety (Task T030a)
    "max_tokens": 512,
    "temperature": 0.7,
    "seed": 42,
    "model_name": "meta-llama/Llama-3-8B-Quantized",
    "cpu_only": True,
}

# Path aliases relative to project root
PATH_ALIASES = {
    "data_raw": "data/raw",
    "data_derived": "data/derived",
    "data_logs": "data/logs",
    "data_results": "data/results",
    "code_agents": "code/agents",
    "code_analysis": "code/analysis",
    "code_dataset": "code/dataset",
    "code_utils": "code/utils",
    "tests": "tests",
}

def get_project_root() -> Path:
    """Return the absolute path to the project root directory."""
    return _PROJECT_ROOT

def get_path(alias: str) -> Path:
    """
    Resolve a path alias to an absolute path within the project.
    
    Args:
        alias: One of the keys in PATH_ALIASES or an absolute path string.
    
    Returns:
        Absolute Path object.
    """
    if alias in PATH_ALIASES:
        return _PROJECT_ROOT / PATH_ALIASES[alias]
    # If it looks like an absolute path or doesn't match, treat as relative to root
    return _PROJECT_ROOT / alias

def get_hyperparameter(name: str, default: Any = None) -> Any:
    """
    Retrieve a hyperparameter value.
    
    Priority:
    1. Environment variable (e.g., LLMXIVE_BATCH_SIZE)
    2. DEFAULT_HYPERPARAMETERS
    3. Provided default
    
    Args:
        name: The hyperparameter name.
        default: Fallback value if not found.
    
    Returns:
        The resolved value.
    """
    env_var_name = f"LLMXIVE_{name.upper()}"
    if env_var_name in os.environ:
        val = os.environ[env_var_name]
        # Attempt type conversion for common types
        if name in ["llm_batch_size", "max_tokens", "seed"]:
            return int(val)
        elif name in ["temperature", "threshold"]:
            return float(val)
        elif val.lower() in ["true", "false"]:
            return val.lower() == "true"
        return val

    if name in DEFAULT_HYPERPARAMETERS:
        return DEFAULT_HYPERPARAMETERS[name]
    
    return default

def ensure_dirs_exist(*paths: str) -> None:
    """
    Ensure that the specified directory paths exist, creating them if necessary.
    
    Args:
        *paths: Directory aliases or relative paths to ensure exist.
    """
    for path_str in paths:
        target = get_path(path_str)
        target.mkdir(parents=True, exist_ok=True)
