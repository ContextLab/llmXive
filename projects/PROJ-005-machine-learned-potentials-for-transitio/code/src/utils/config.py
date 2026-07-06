import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, Union

def get_project_root() -> Path:
    """
    Returns the project root directory.
    Assumes the code is executed from the project root or a subdirectory.
    """
    current = Path.cwd()
    # Heuristic: look for a marker file or the specific directory structure
    # defined in T001 (specs/ or data/) to find the root.
    while current != current.parent:
        if (current / "specs").is_dir() and (current / "data").is_dir():
            return current
        current = current.parent
    # Fallback to cwd if structure not found
    return Path.cwd()

def load_yaml_config(config_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Loads a YAML configuration file and returns it as a dictionary.
    
    Args:
        config_path: Path to the YAML file.
        
    Returns:
        Dictionary containing the configuration.
        
    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the file is not valid YAML.
    """
    path = Path(config_path)
    if not path.is_absolute():
        path = get_project_root() / path
        
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
        
    with open(path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        
    return config if config else {}

def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Retrieves an environment variable.
    
    Args:
        key: The environment variable name.
        default: Default value if the variable is not set.
        
    Returns:
        The value of the environment variable or the default.
    """
    return os.getenv(key, default)

def merge_env_overrides(config: Dict[str, Any], prefix: str = "LMXIVE_") -> Dict[str, Any]:
    """
    Merges environment variables into the configuration dictionary.
    Environment variables starting with `prefix` override config values.
    Nested keys in env vars can be represented by underscores (e.g., LMXIVE_MODEL_LR).
    
    Args:
        config: The base configuration dictionary.
        prefix: The prefix for relevant environment variables.
        
    Returns:
        A new dictionary with environment variables merged in.
    """
    merged = config.copy()
    
    for key, value in os.environ.items():
        if key.startswith(prefix):
            # Remove prefix and convert to lowercase for matching
            env_key = key[len(prefix):].lower()
            
            # Split by underscore to handle nested keys
            parts = env_key.split('_')
            
            target = merged
            for i, part in enumerate(parts[:-1]):
                if part not in target:
                    target[part] = {}
                elif not isinstance(target[part], dict):
                    # If the existing value is not a dict, we can't nest further
                    # Convert to dict to allow nesting, or skip. 
                    # Strategy: Replace with dict to allow override
                    target[part] = {}
                target = target[part]
            
            final_key = parts[-1]
            # Try to infer type (int, float, bool) or keep string
            try:
                final_value = int(value)
            except ValueError:
                try:
                    final_value = float(value)
                except ValueError:
                    if value.lower() in ('true', 'false'):
                        final_value = value.lower() == 'true'
                    else:
                        final_value = value
            
            target[final_key] = final_value
            
    return merged

def load_config(config_path: Union[str, Path], prefix: str = "LMXIVE_") -> Dict[str, Any]:
    """
    Loads a YAML config and merges environment variable overrides.
    
    Args:
        config_path: Path to the YAML file.
        prefix: Prefix for environment variables to override config.
        
    Returns:
        Merged configuration dictionary.
    """
    config = load_yaml_config(config_path)
    return merge_env_overrides(config, prefix)

def get_config_value(config: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Safely retrieves a value from a nested configuration dictionary using dot notation.
    
    Args:
        config: The configuration dictionary.
        key: Dot-separated key path (e.g., 'model.learning_rate').
        default: Default value if key is not found.
        
    Returns:
        The value or default.
    """
    parts = key.split('.')
    current = config
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return default
    return current

def save_config(config: Dict[str, Any], config_path: Union[str, Path]) -> None:
    """
    Saves a configuration dictionary to a YAML file.
    
    Args:
        config: The configuration dictionary.
        config_path: Path to save the file.
    """
    path = Path(config_path)
    if not path.is_absolute():
        path = get_project_root() / path
        
    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)