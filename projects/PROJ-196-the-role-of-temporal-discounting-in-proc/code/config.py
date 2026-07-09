"""
Configuration Loader for llmXive Research Pipeline

Provides centralized configuration management including:
- Project root detection
- Configuration file loading (YAML/JSON)
- Environment variable overrides
- Default values for research parameters
- Seed management for reproducibility
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union
import yaml
import numpy as np

# Determine project root (parent of the 'code' directory)
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

# Configuration file paths
CONFIG_PATH = PROJECT_ROOT / "config" / "research_config.yaml"
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "default_config.yaml"

# Default configuration values
DEFAULT_CONFIG = {
    "research": {
        "project_name": "temporal-discounting-procrastination",
        "version": "1.0.0",
        "description": "Analysis of temporal discounting effects on procrastination",
    },
    "data": {
        "raw_dir": "data/raw",
        "processed_dir": "data/processed",
        "figures_dir": "figures",
    },
    "analysis": {
        "random_seed": 42,
        "bootstrap_samples": 1000,
        "reliability_threshold": 0.7,
        "vif_threshold": 5.0,
        "missing_data_threshold": 0.10,
    },
    "paths": {
        "project_root": str(PROJECT_ROOT),
        "code_dir": str(CURRENT_DIR),
    }
}

# Global random state holder
_GLOBAL_RANDOM_STATE: Optional[np.random.Generator] = None

def _load_yaml_config(path: Path) -> Dict[str, Any]:
    """Load configuration from a YAML file."""
    if not path.exists():
        return {}
    
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}

def _load_json_config(path: Path) -> Dict[str, Any]:
    """Load configuration from a JSON file."""
    if not path.exists():
        return {}
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def _merge_configs(defaults: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two configuration dictionaries."""
    result = defaults.copy()
    
    for key, value in overrides.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_configs(result[key], value)
        else:
            result[key] = value
    
    return result

def _apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """Apply environment variable overrides to configuration."""
    # Map environment variables to config keys
    env_overrides = {
        "RESEARCH_RANDOM_SEED": ("analysis", "random_seed"),
        "RESEARCH_BOOTSTRAP_SAMPLES": ("analysis", "bootstrap_samples"),
        "RESEARCH_RELIABILITY_THRESHOLD": ("analysis", "reliability_threshold"),
        "RESEARCH_VIF_THRESHOLD": ("analysis", "vif_threshold"),
    }
    
    for env_var, (section, key) in env_overrides.items():
        if env_var in os.environ:
            value = os.environ[env_var]
            # Try to convert to appropriate type
            try:
                if '.' in value:
                    value = float(value)
                else:
                    value = int(value)
            except ValueError:
                pass  # Keep as string if conversion fails
            
            if section not in config:
                config[section] = {}
            config[section][key] = value
    
    return config

def get_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load and merge all configuration sources.
    
    Priority (lowest to highest):
    1. Default configuration
    2. Default config file (if exists)
    3. Custom config file (if exists)
    4. Environment variables
    
    Args:
        config_path: Optional path to custom configuration file.
                    If None, uses CONFIG_PATH.
    
    Returns:
        Merged configuration dictionary.
    """
    if config_path is None:
        config_path = CONFIG_PATH
    
    # Start with defaults
    config = DEFAULT_CONFIG.copy()
    
    # Load and merge default config file
    if DEFAULT_CONFIG_PATH.exists():
        default_file_config = _load_yaml_config(DEFAULT_CONFIG_PATH)
        config = _merge_configs(config, default_file_config)
    
    # Load and merge custom config file
    if config_path.exists():
        custom_config = _load_yaml_config(config_path)
        config = _merge_configs(config, custom_config)
    
    # Apply environment variable overrides
    config = _apply_env_overrides(config)
    
    # Ensure paths are absolute
    config["paths"]["project_root"] = str(PROJECT_ROOT)
    config["paths"]["code_dir"] = str(CURRENT_DIR)
    
    return config

def get_project_root() -> Path:
    """Get the project root directory."""
    return PROJECT_ROOT

def get_config_value(key: str, default: Any = None) -> Any:
    """
    Get a specific configuration value using dot notation.
    
    Args:
        key: Dot-separated key path (e.g., "analysis.random_seed")
        default: Default value if key not found
    
    Returns:
        Configuration value or default
    """
    config = get_config()
    keys = key.split('.')
    
    current = config
    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        else:
            return default
    
    return current

def get_random_state(seed: Optional[int] = None) -> np.random.Generator:
    """
    Get a reproducible random number generator state.
    
    This function ensures that all stochastic functions in numpy, pandas,
    scipy, and sklearn receive an explicit random state for reproducibility.
    
    Priority for seed selection:
    1. Explicit `seed` argument if provided
    2. `RANDOM_SEED` from environment variable
    3. `analysis.random_seed` from config file
    4. Default value (42)
    
    Args:
        seed: Optional explicit seed integer. If None, falls back to config/env.
    
    Returns:
        A numpy.random.Generator instance initialized with the determined seed.
    
    Example usage:
        # In data generation or modeling functions:
        rng = get_random_state()
        data = rng.normal(0, 1, size=100)
        
        # Passing to sklearn:
        from sklearn.ensemble import RandomForestClassifier
        model = RandomForestClassifier(random_state=get_random_state())
        
        # Passing to scipy:
        from scipy import stats
        sample = stats.norm.rvs(size=100, random_state=get_random_state())
    """
    global _GLOBAL_RANDOM_STATE
    
    # Determine seed value
    if seed is not None:
        final_seed = seed
    else:
        # Check environment variable first
        env_seed = os.environ.get("RESEARCH_RANDOM_SEED")
        if env_seed is not None:
            try:
                final_seed = int(env_seed)
            except ValueError:
                final_seed = DEFAULT_CONFIG["analysis"]["random_seed"]
        else:
            # Check config file
            config_seed = get_config_value("analysis.random_seed")
            if config_seed is not None:
                final_seed = int(config_seed)
            else:
                final_seed = DEFAULT_CONFIG["analysis"]["random_seed"]
    
    # Create and return a new generator instance
    # We create a new instance each time to ensure consistent behavior
    # when passing to functions that might modify the state
    return np.random.default_rng(final_seed)

# Initialize default paths in config
def _initialize_paths(config: Dict[str, Any]) -> None:
    """Ensure all data directories exist."""
    base_path = Path(config["paths"]["project_root"])
    
    data_dirs = [
        base_path / config["data"]["raw_dir"],
        base_path / config["data"]["processed_dir"],
        base_path / config["data"]["figures_dir"],
    ]
    
    for dir_path in data_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)