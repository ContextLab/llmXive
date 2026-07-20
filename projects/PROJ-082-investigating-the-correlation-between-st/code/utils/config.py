import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, Union
import numpy as np
import yaml

# Global configuration state
_config: Dict[str, Any] = {}
_seed: Optional[int] = None

# Paths relative to project root
_CONFIG_DIR = "code/config"
_SCHEMA_FILE = "config_schema.yaml"
_USER_CONFIG_FILE = "config.yaml"

def get_project_root() -> Path:
    """
    Get the project root directory (parent of code/).
    
    Returns:
        Path to project root
    """
    current_file = Path(__file__).resolve()
    return current_file.parent.parent

def set_seed(seed: int = 42):
    """
    Set random seeds for reproducibility across Python, NumPy, and PyTorch (if available).
    
    Args:
        seed: Random seed value
    """
    global _seed
    _seed = seed
    random.seed(seed)
    np.random.seed(seed)
    
    # Attempt to set PyTorch seed if available
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

def get_config_path() -> Path:
    """
    Get the path to the configuration directory.
    
    Returns:
        Path to code/config directory
    """
    return get_project_root() / _CONFIG_DIR

def get_output_path() -> Path:
    """
    Get the path to the processed data directory.
    
    Returns:
        Path to data/processed directory
    """
    return get_project_root() / "data" / "processed"

def get_figure_path() -> Path:
    """
    Get the path to the derived data directory (for figures).
    
    Returns:
        Path to data/derived directory
    """
    return get_project_root() / "data" / "derived"

def _load_schema() -> Dict[str, Any]:
    """
    Load the configuration schema from disk.
    
    Returns:
        Schema dictionary
    """
    schema_path = get_config_path() / _SCHEMA_FILE
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def _validate_config(config: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """
    Validate configuration against schema.
    
    Args:
        config: Configuration dictionary
        schema: Schema dictionary
        
    Raises:
        ValueError: If validation fails
    """
    required_keys = schema.get("required", [])
    properties = schema.get("properties", {})
    
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required configuration key: {key}")
    
    for key, value in config.items():
        if key in properties:
            prop_schema = properties[key]
            expected_type = prop_schema.get("type")
            
            type_map = {
                "int": int,
                "string": str,
                "str": str,
                "number": (int, float),
                "boolean": bool,
                "dict": dict,
                "object": dict,
                "list": list,
                "array": list
            }
            
            if expected_type in type_map:
                expected_python_type = type_map[expected_type]
                if not isinstance(value, expected_python_type):
                    raise ValueError(
                        f"Invalid type for key '{key}': expected {expected_type}, "
                        f"got {type(value).__name__}"
                    )
            
            # Special validation for 'seed' (must be non-negative integer)
            if key == "seed" and "minimum" in prop_schema:
                if value < prop_schema["minimum"]:
                    raise ValueError(
                        f"Value for '{key}' ({value}) is less than minimum "
                        f"allowed ({prop_schema['minimum']})"
                    )
            
            # Special validation for 'paths' (must be dict)
            if key == "paths" and isinstance(value, dict):
                for path_key, path_value in value.items():
                    if not isinstance(path_value, str):
                        raise ValueError(
                            f"Path value for '{path_key}' must be a string, "
                            f"got {type(path_value).__name__}"
                        )
            
            # Special validation for 'limits' (must be dict)
            if key == "limits" and isinstance(value, dict):
                for limit_key, limit_value in value.items():
                    if not isinstance(limit_value, (int, float)):
                        raise ValueError(
                            f"Limit value for '{limit_key}' must be a number, "
                            f"got {type(limit_value).__name__}"
                        )

def load_config() -> Dict[str, Any]:
    """
    Load configuration from code/config/config.yaml if it exists,
    otherwise use defaults. Validates against code/config/config_schema.yaml.
    
    Returns:
        Configuration dictionary
    """
    global _config
    
    # Load schema
    schema = _load_schema()
    
    # Define defaults based on schema
    defaults = {
        "seed": 42,
        "paths": {
            "raw_data": "data/raw",
            "processed_data": "data/processed",
            "derived_data": "data/derived",
            "config": "data/config",
            "logs": "data/logs",
            "figures": "data/derived"
        },
        "limits": {
            "max_studies": 1000,
            "min_studies_for_meta": 10,
            "max_memory_mb": 8000
        }
    }
    
    # Try to load user config
    user_config_path = get_config_path() / _USER_CONFIG_FILE
    if user_config_path.exists():
        with open(user_config_path, 'r') as f:
            user_config = yaml.safe_load(f) or {}
        # Merge user config with defaults
        merged_config = {**defaults, **user_config}
        # Deep merge for nested dicts
        for key in ["paths", "limits"]:
            if key in defaults and key in user_config:
                merged_config[key] = {**defaults[key], **user_config[key]}
    else:
        merged_config = defaults
    
    # Validate against schema
    _validate_config(merged_config, schema)
    
    # Update global config
    _config = merged_config
    return _config

def load_config_from_env(config_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file or environment variables.
    
    Args:
        config_file: Optional path to config file
        
    Returns:
        Configuration dictionary
    """
    global _config
    config = {}
    
    # Try to load from file if provided
    if config_file:
        config_path = Path(config_file)
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
    
    # Override with environment variables
    for key, value in os.environ.items():
        if key.startswith("LLMXIVE_"):
            config[key] = value
    
    # Merge with global config if it exists
    if _config:
        config.update(_config)
    
    _config = config
    return config

def resolve_path(path: Union[str, Path]) -> Path:
    """
    Resolve a path relative to project root if it's not absolute.
    
    Args:
        path: Path to resolve
        
    Returns:
        Absolute Path object
    """
    path_obj = Path(path)
    if path_obj.is_absolute():
        return path_obj
    return get_project_root() / path_obj

def ensure_directory(path: Union[str, Path]):
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Path to ensure exists
    """
    path_obj = resolve_path(path)
    path_obj.mkdir(parents=True, exist_ok=True)

def get_seed() -> Optional[int]:
    """
    Get the currently set random seed.
    
    Returns:
        The seed value or None if not set
    """
    return _seed

def update_config(updates: Dict[str, Any]):
    """
    Update the global configuration with new values.
    
    Args:
        updates: Dictionary of configuration updates
    """
    global _config
    _config.update(updates)

def get_config_value(key: str, default: Any = None) -> Any:
    """
    Get a specific configuration value.
    
    Args:
        key: Configuration key
        default: Default value if key not found
        
    Returns:
        Configuration value or default
    """
    return _config.get(key, default)

def save_config(config: Dict[str, Any], output_path: Optional[Union[str, Path]] = None):
    """
    Save configuration to a YAML file.
    
    Args:
        config: Configuration dictionary to save
        output_path: Optional output path (defaults to code/config/project_config.yaml)
    """
    if output_path is None:
        output_path = get_config_path() / "project_config.yaml"
    
    output_path_obj = resolve_path(output_path)
    ensure_directory(output_path_obj.parent)
    
    with open(output_path_obj, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

def main():
    """
    Command-line interface for configuration management.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Configuration management utility")
    parser.add_argument("--seed", type=int, default=42, help="Random seed to set")
    parser.add_argument("--config", type=str, help="Path to config file to load")
    parser.add_argument("--save", type=str, help="Path to save current config")
    
    args = parser.parse_args()
    
    # Set seed
    set_seed(args.seed)
    print(f"Set random seed to {args.seed}")
    
    # Load config if provided
    if args.config:
        config = load_config_from_env(args.config)
        print(f"Loaded config from {args.config}: {config}")
    
    # Load default config if no custom config provided
    if not args.config:
        config = load_config()
        print(f"Loaded default config: {config}")
    
    # Save config if requested
    if args.save:
        save_config(_config, args.save)
        print(f"Saved config to {args.save}")
    
    # Display current seed
    current_seed = get_seed()
    if current_seed is not None:
        print(f"Current seed: {current_seed}")

if __name__ == "__main__":
    main()
