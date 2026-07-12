"""
Configuration loader for llmXive project.
Manages paths, constants, and environment-based overrides.
"""
import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union
import yaml

# Configure module logger
logger = logging.getLogger(__name__)

# --- Project Root Detection ---
def _get_project_root() -> Path:
    """
    Determine the project root directory.
    Assumes the project structure is:
    root/
      code/
      data/
      specs/
    """
    current_file = Path(__file__).resolve()
    # Traverse up until we find the 'code' directory or a known marker
    for parent in current_file.parents:
        if (parent / "data").exists() and (parent / "specs").exists():
            return parent
        # Fallback if code is at root
        if parent.name == "code" and (parent.parent / "data").exists():
            return parent.parent
    
    # If all else fails, assume current file's parent is root (for dev)
    logger.warning("Could not auto-detect project root. Using fallback.")
    return current_file.parent

PROJECT_ROOT = _get_project_root()

# --- Default Paths ---
DEFAULT_PATHS = {
    "data_raw": PROJECT_ROOT / "data" / "raw",
    "data_processed": PROJECT_ROOT / "data" / "processed",
    "code_root": PROJECT_ROOT / "code",
    "specs_root": PROJECT_ROOT / "specs",
    "figures_root": PROJECT_ROOT / "figures",
}

# --- Default Constants ---
DEFAULT_CONSTANTS = {
    # Geometry
    "RADIAL_MOTION_THRESHOLD_DEG": 15.0,
    "Z_VELOCITY_THRESHOLD": 0.1,
    "ASPECT_RATIO_TOLERANCE_PCT": 5.0,
    "DEPTH_ERROR_THRESHOLD_PCT": 50.0,
    
    # Memory/Performance
    "MAX_MEMORY_GB": 6.0,
    "CHUNK_SIZE_FRAMES": 100,
    
    # Solver
    "SOLVER_MAX_ITER": 100,
    "SOLVER_EPS": 1e-6,
    
    # Dataset
    "RANDOM_SEED": 42,
}

def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge override into base."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result

def load_config(config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file or environment variables.
    
    Args:
        config_path: Path to a custom config file. Defaults to 'code/config.yaml'.
        
    Returns:
        Merged configuration dictionary.
    """
    # Start with defaults
    config = {
        "paths": DEFAULT_PATHS,
        "constants": DEFAULT_CONSTANTS,
    }
    
    # Determine config file path
    if config_path is None:
        config_path = PROJECT_ROOT / "code" / "config.yaml"
    else:
        config_path = Path(config_path)
    
    # Load file if it exists
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                file_config = yaml.safe_load(f) or {}
            if "paths" in file_config:
                config["paths"] = _deep_merge(config["paths"], file_config["paths"])
            if "constants" in file_config:
                config["constants"] = _deep_merge(config["constants"], file_config["constants"])
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.warning(f"Failed to load config from {config_path}: {e}")
    else:
        logger.info(f"No custom config found at {config_path}, using defaults.")
    
    # Override with environment variables (prefix: LLMXIVE_)
    env_prefix = "LLMXIVE_"
    for key, value in os.environ.items():
        if key.startswith(env_prefix):
            sub_key = key[len(env_prefix):].lower()
            try:
                # Try to parse as number if possible
                if "." in value:
                    value = float(value)
                else:
                    value = int(value)
            except ValueError:
                pass # Keep as string
            
            # Simple override for constants
            if sub_key in config["constants"]:
                config["constants"][sub_key] = value
                logger.debug(f"Overrode constant {sub_key} with env var {key}")
    
    return config

# Global config instance
_config = None

def get_config() -> Dict[str, Any]:
    """Get the singleton configuration object."""
    global _config
    if _config is None:
        _config = load_config()
    return _config

def get_constant(name: str) -> Any:
    """
    Retrieve a specific constant from the configuration.
    
    Args:
        name: The constant name (e.g., 'RADIAL_MOTION_THRESHOLD_DEG').
        
    Returns:
        The constant value.
        
    Raises:
        KeyError: If the constant is not found.
    """
    config = get_config()
    if name not in config["constants"]:
        raise KeyError(f"Constant '{name}' not found in configuration.")
    return config["constants"][name]

def get_path(name: str) -> Path:
    """
    Retrieve a specific path from the configuration.
    
    Args:
        name: The path name (e.g., 'data_raw', 'data_processed').
        
    Returns:
        The Path object.
        
    Raises:
        KeyError: If the path is not found.
    """
    config = get_config()
    if name not in config["paths"]:
        raise KeyError(f"Path '{name}' not found in configuration.")
    return Path(config["paths"][name])

def ensure_paths_exist() -> None:
    """Ensure all configured paths exist on disk."""
    config = get_config()
    for name, path in config["paths"].items():
        path = Path(path)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {path}")

# Convenience function for the main entry point
def main():
    """Main entry point to validate and print configuration."""
    print("llmXive Configuration Loader")
    print("-" * 30)
    config = get_config()
    print(f"Project Root: {PROJECT_ROOT}")
    print("Paths:")
    for k, v in config["paths"].items():
        print(f"  {k}: {v}")
    print("Constants:")
    for k, v in config["constants"].items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    main()
