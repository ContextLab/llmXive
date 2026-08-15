"""
Configuration loader for environment-specific pipeline parameters.

Reads `config/environments.yaml` and exposes the active configuration
based on the `PROJ_ENV` environment variable (default: 'ci').

Provides validation against hard constraints defined in the spec.
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from loguru import logger

# Ensure the code root is in the path if running as a script
if __name__ == "__main__" and str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

def load_environment_config(env_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the environment configuration from config/environments.yaml.
    
    Args:
        env_name: The environment key ('ci' or 'full'). Defaults to 
                  the PROJ_ENV env var or 'ci'.
    
    Returns:
        Dict containing the configuration for the requested environment.
    
    Raises:
        FileNotFoundError: If the config file does not exist.
        KeyError: If the requested environment is not found.
        ValueError: If the config file is malformed.
    """
    if env_name is None:
        env_name = os.getenv("PROJ_ENV", "ci")
    
    config_path = Path(__file__).parent.parent / "config" / "environments.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Environment config not found at {config_path}")
    
    try:
        with open(config_path, "r") as f:
            full_config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Malformed YAML in {config_path}: {e}")
    
    if env_name not in full_config:
        available = ", ".join(full_config.keys())
        raise KeyError(f"Environment '{env_name}' not found. Available: {available}")
    
    config = full_config[env_name]
    
    # Validate critical keys
    required_keys = ["mode", "description", "constraints", "data_sources", "tools", "retention", "logging"]
    missing = [k for k in required_keys if k not in config]
    if missing:
        raise ValueError(f"Environment '{env_name}' missing required keys: {missing}")
    
    logger.info(f"Loaded environment config: {env_name} (mode={config['mode']})")
    return config

def get_constraint(config: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Safely retrieve a constraint value from the loaded config.
    
    Args:
        config: The environment config dictionary.
        key: The constraint key (e.g., 'max_replicates').
        default: Default value if key is missing.
    
    Returns:
        The constraint value or default.
    """
    return config.get("constraints", {}).get(key, default)

def get_tool_param(config: Dict[str, Any], tool: str, param: str, default: Any = None) -> Any:
    """
    Safely retrieve a tool parameter from the loaded config.
    
    Args:
        config: The environment config dictionary.
        tool: The tool name (e.g., 'star', 'suppa').
        param: The parameter name (e.g., 'threads').
        default: Default value if key is missing.
    
    Returns:
        The parameter value or default.
    """
    return config.get("tools", {}).get(tool, {}).get(param, default)

def validate_replicate_count(count: int, config: Dict[str, Any]) -> bool:
    """
    Validate a replicate count against the current environment's constraints.
    
    Args:
        count: The number of replicates.
        config: The environment config dictionary.
    
    Returns:
        True if valid.
    
    Raises:
        ValueError: If the count violates constraints.
    """
    min_rep = get_constraint(config, "min_replicates", 0)
    max_rep = get_constraint(config, "max_replicates", float('inf'))
    
    if count < min_rep:
        raise ValueError(f"Replicate count {count} is below minimum {min_rep} for {config['mode']} mode.")
    if count > max_rep:
        raise ValueError(f"Replicate count {count} exceeds maximum {max_rep} for {config['mode']} mode.")
    
    return True

def main():
    """CLI entry point to dump config for debugging."""
    env = os.getenv("PROJ_ENV", "ci")
    try:
        cfg = load_environment_config(env)
        print(f"Active Environment: {env}")
        print(f"Mode: {cfg['mode']}")
        print(f"Constraints: {cfg['constraints']}")
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
