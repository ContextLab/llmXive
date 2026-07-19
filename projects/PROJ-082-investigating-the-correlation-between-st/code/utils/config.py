import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, Union
import numpy as np

# Global configuration state
_config: Dict[str, Any] = {}
_seed: Optional[int] = None

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
        Path to data/config directory
    """
    return get_project_root() / "data" / "config"

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
            import yaml
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
        output_path: Optional output path (defaults to data/config/project_config.yaml)
    """
    if output_path is None:
        output_path = get_config_path() / "project_config.yaml"
    
    output_path_obj = resolve_path(output_path)
    ensure_directory(output_path_obj.parent)
    
    import yaml
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