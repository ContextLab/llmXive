"""
Configuration management for llmXive project.

Provides a unified interface to load settings from YAML files and
environment variables, with environment variable overrides.
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

# Default paths relative to project root
DEFAULT_CONFIG_PATH = Path("config.yaml")
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def load_yaml_config(
    config_path: Optional[Path] = None,
    project_root: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the YAML configuration file. If None, defaults 
                     to 'config.yaml' in the project root.
        project_root: Base directory for resolving relative paths. Defaults 
                      to the project root inferred from this module's location.
    
    Returns:
        Dictionary containing the loaded configuration.
    
    Raises:
        FileNotFoundError: If the specified config file does not exist.
        yaml.YAMLError: If the YAML file is malformed.
    """
    if project_root is None:
        project_root = PROJECT_ROOT
    
    if config_path is None:
        config_path = project_root / DEFAULT_CONFIG_PATH
    elif not config_path.is_absolute():
        config_path = project_root / config_path
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    return config if config is not None else {}

def load_env_config() -> Dict[str, Any]:
    """
    Load configuration overrides from environment variables.
    
    Environment variables prefixed with 'LLMXIVE_' are extracted, 
    the prefix is removed, and keys are lowercased and converted to 
    nested dictionaries based on double underscores '__'.
    
    Example:
        LLMXIVE_DATA__RAW_PATH=/data/raw
        LLMXIVE_TRAINING__EPOCHS=50
        LLMXIVE_DEBUG=true
        
        Becomes:
        {
            "data": {"raw_path": "/data/raw"},
            "training": {"epochs": 50},
            "debug": "true"
        }
    
    Returns:
        Dictionary of configuration overrides from environment variables.
    """
    env_vars = {}
    prefix = "LLMXIVE_"
    
    for key, value in os.environ.items():
        if key.startswith(prefix):
            # Remove prefix
            nested_key = key[len(prefix):]
            
            # Split by double underscore for nesting
            parts = nested_key.lower().split("__")
            
            # Build nested dictionary
            current = env_vars
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # Set the final value
            current[parts[-1]] = value
    
    return env_vars

def deep_update(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively update a dictionary with values from another dictionary.
    
    Args:
        base: The base dictionary to update.
        override: The dictionary containing override values.
    
    Returns:
        A new dictionary with merged values.
    """
    result = base.copy()
    
    for key, value in override.items():
        if (
            key in result 
            and isinstance(result[key], dict) 
            and isinstance(value, dict)
        ):
            result[key] = deep_update(result[key], value)
        else:
            result[key] = value
    
    return result

def load_config(
    config_path: Optional[Path] = None,
    project_root: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Load and merge configuration from YAML file and environment variables.
    
    Environment variables take precedence over YAML file values.
    
    Args:
        config_path: Path to the YAML configuration file.
        project_root: Base directory for resolving relative paths.
    
    Returns:
        Merged configuration dictionary.
    """
    # Load base configuration from YAML
    yaml_config = load_yaml_config(config_path, project_root)
    
    # Load overrides from environment variables
    env_config = load_env_config()
    
    # Merge configurations (env overrides yaml)
    return deep_update(yaml_config, env_config)

def get_config_value(
    config: Dict[str, Any],
    key_path: str,
    default: Any = None
) -> Any:
    """
    Retrieve a value from a nested configuration dictionary using a dot-path.
    
    Args:
        config: The configuration dictionary.
        key_path: Dot-separated path to the value (e.g., "data.raw_path").
        default: Default value if the path does not exist.
    
    Returns:
        The value at the specified path, or the default if not found.
    """
    parts = key_path.split(".")
    current = config
    
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return default
    
    return current

# Singleton pattern for global configuration access
_global_config: Optional[Dict[str, Any]] = None

def get_global_config(
    config_path: Optional[Path] = None,
    project_root: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Get or initialize the global configuration singleton.
    
    Args:
        config_path: Path to the YAML configuration file.
        project_root: Base directory for resolving relative paths.
    
    Returns:
        The global configuration dictionary.
    """
    global _global_config
    
    if _global_config is None:
        _global_config = load_config(config_path, project_root)
    
    return _global_config

def reset_global_config() -> None:
    """Reset the global configuration singleton (useful for testing)."""
    global _global_config
    _global_config = None

# Convenience function for common config keys
def get_data_path(config: Optional[Dict[str, Any]] = None) -> Path:
    """
    Get the data directory path from configuration.
    
    Args:
        config: Optional configuration dictionary. If None, uses global config.
    
    Returns:
        Path to the data directory.
    """
    if config is None:
        config = get_global_config()
    
    data_path = get_config_value(config, "data.root", "data")
    return PROJECT_ROOT / data_path

def get_raw_data_path(config: Optional[Dict[str, Any]] = None) -> Path:
    """
    Get the raw data directory path from configuration.
    
    Args:
        config: Optional configuration dictionary. If None, uses global config.
    
    Returns:
        Path to the raw data directory.
    """
    base = get_data_path(config)
    return base / "raw"

def get_processed_data_path(config: Optional[Dict[str, Any]] = None) -> Path:
    """
    Get the processed data directory path from configuration.
    
    Args:
        config: Optional configuration dictionary. If None, uses global config.
    
    Returns:
        Path to the processed data directory.
    """
    base = get_data_path(config)
    return base / "processed"

def get_results_path(config: Optional[Dict[str, Any]] = None) -> Path:
    """
    Get the results directory path from configuration.
    
    Args:
        config: Optional configuration dictionary. If None, uses global config.
    
    Returns:
        Path to the results directory.
    """
    base = get_data_path(config)
    return base / "results"

def get_model_path(config: Optional[Dict[str, Any]] = None) -> Path:
    """
    Get the models directory path from configuration.
    
    Args:
        config: Optional configuration dictionary. If None, uses global config.
    
    Returns:
        Path to the models directory.
    """
    return get_processed_data_path(config) / "models"

def get_device(config: Optional[Dict[str, Any]] = None) -> str:
    """
    Get the device setting (cpu/cuda) from configuration.
    
    Args:
        config: Optional configuration dictionary. If None, uses global config.
    
    Returns:
        Device string (e.g., "cpu" or "cuda").
    """
    if config is None:
        config = get_global_config()
    
    return get_config_value(config, "training.device", "cpu")

def get_batch_size(config: Optional[Dict[str, Any]] = None) -> int:
    """
    Get the batch size from configuration.
    
    Args:
        config: Optional configuration dictionary. If None, uses global config.
    
    Returns:
        Batch size integer.
    """
    if config is None:
        config = get_global_config()
    
    return get_config_value(config, "training.batch_size", 32)

def get_epochs(config: Optional[Dict[str, Any]] = None) -> int:
    """
    Get the number of training epochs from configuration.
    
    Args:
        config: Optional configuration dictionary. If None, uses global config.
    
    Returns:
        Number of epochs.
    """
    if config is None:
        config = get_global_config()
    
    return get_config_value(config, "training.epochs", 30)

def get_learning_rate(config: Optional[Dict[str, Any]] = None) -> float:
    """
    Get the learning rate from configuration.
    
    Args:
        config: Optional configuration dictionary. If None, uses global config.
    
    Returns:
        Learning rate float.
    """
    if config is None:
        config = get_global_config()
    
    return get_config_value(config, "training.learning_rate", 1e-4)

def get_cutoff(config: Optional[Dict[str, Any]] = None) -> float:
    """
    Get the edge cutoff distance from configuration.
    
    Args:
        config: Optional configuration dictionary. If None, uses global config.
    
    Returns:
        Cutoff distance in Angstroms.
    """
    if config is None:
        config = get_global_config()
    
    return get_config_value(config, "data.cutoff", 3.5)

def get_num_folds(config: Optional[Dict[str, Any]] = None) -> int:
    """
    Get the number of cross-validation folds from configuration.
    
    Args:
        config: Optional configuration dictionary. If None, uses global config.
    
    Returns:
        Number of folds.
    """
    if config is None:
        config = get_global_config()
    
    return get_config_value(config, "training.num_folds", 5)

def get_ensemble_size(config: Optional[Dict[str, Any]] = None) -> int:
    """
    Get the ensemble size from configuration.
    
    Args:
        config: Optional configuration dictionary. If None, uses global config.
    
    Returns:
        Number of models in the ensemble.
    """
    if config is None:
        config = get_global_config()
    
    return get_config_value(config, "training.ensemble_size", 5)

def get_min_element_count(config: Optional[Dict[str, Any]] = None) -> int:
    """
    Get the minimum element count threshold from configuration.
    
    Args:
        config: Optional configuration dictionary. If None, uses global config.
    
    Returns:
        Minimum count threshold.
    """
    if config is None:
        config = get_global_config()
    
    return get_config_value(config, "data.min_element_count", 120)

def get_debug_mode(config: Optional[Dict[str, Any]] = None) -> bool:
    """
    Get the debug mode flag from configuration.
    
    Args:
        config: Optional configuration dictionary. If None, uses global config.
    
    Returns:
        Debug mode boolean.
    """
    if config is None:
        config = get_global_config()
    
    debug_val = get_config_value(config, "debug", "false")
    if isinstance(debug_val, bool):
        return debug_val
    return str(debug_val).lower() in ("true", "1", "yes")