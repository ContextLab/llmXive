import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import yaml

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

def load_env_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file or environment variables.
    
    Priority:
    1. Explicit config_path argument
    2. PROJECT_CONFIG environment variable
    3. Default: projects/PROJ-001-mechanistic-interpretability-of-ctcf-bin/config/config.yaml
    
    Args:
        config_path: Optional path to config file.
        
    Returns:
        Dictionary containing configuration values.
    """
    if config_path is None:
        config_path = os.getenv('PROJECT_CONFIG')
    
    if config_path is None:
        # Default relative to project root
        project_root = Path(__file__).resolve().parents[2]
        config_path = str(project_root / 'config' / 'config.yaml')
    
    config_file = Path(config_path)
    
    if not config_file.exists():
        # Try to find relative to current working directory if absolute path failed
        if not config_file.is_absolute():
            config_file = Path.cwd() / config_path
        
        if not config_file.exists():
            # Return minimal default config if file missing, but warn
            logging.warning(f"Config file not found at {config_file}. Using defaults.")
            return _get_default_config()
    
    try:
        with open(config_file, 'r') as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ConfigError(f"Failed to parse config file {config_file}: {e}")

def _get_default_config() -> Dict[str, Any]:
    """Return a default configuration structure."""
    project_root = Path(__file__).resolve().parents[2]
    return {
        "paths": {
            "data_root": str(project_root / "data"),
            "code_root": str(project_root / "code"),
            "processed_data": str(project_root / "data" / "processed"),
            "models": str(project_root / "data" / "models"),
            "interpretation": str(project_root / "data" / "interpretation"),
            "figures": str(project_root / "figures")
        },
        "api": {
            "encode_api_key": None,
            "encode_base_url": "https://www.encodeproject.org"
        },
        "model": {
            "device": "cpu",
            "seed": 42
        }
    }

def validate_manifest_exists(manifest_path: Optional[str] = None) -> bool:
    """
    Validate that the data manifest file exists.
    
    Args:
        manifest_path: Optional path to manifest. Defaults to data/manifest.json.
        
    Returns:
        True if manifest exists, False otherwise.
        
    Raises:
        ConfigError: If manifest is missing and required for operation.
    """
    if manifest_path is None:
        config = load_env_config()
        data_root = Path(config.get("paths", {}).get("data_root", "data"))
        manifest_path = str(data_root / "manifest.json")
    
    manifest_file = Path(manifest_path)
    
    if not manifest_file.exists():
        # Check relative to cwd
        if not manifest_file.is_absolute():
            manifest_file = Path.cwd() / manifest_path
        
        if not manifest_file.exists():
            raise ConfigError(
                f"Data manifest not found at {manifest_file}. "
                "Please run data gap resolution tasks (T003-T007) first."
            )
    
    return True

def get_encode_api_key(config: Optional[Dict[str, Any]] = None) -> str:
    """
    Retrieve the ENCODE API key from environment or config.
    
    Priority:
    1. ENCODE_API_KEY environment variable
    2. api.encode_api_key in config file
    
    Args:
        config: Optional pre-loaded config dict.
        
    Returns:
        The API key string.
        
    Raises:
        ConfigError: If no API key is found.
    """
    # Check environment variable first
    env_key = os.getenv('ENCODE_API_KEY')
    if env_key:
        return env_key
    
    # Check config file
    if config is None:
        config = load_env_config()
    
    api_config = config.get("api", {})
    config_key = api_config.get("encode_api_key")
    
    if config_key:
        return config_key
    
    raise ConfigError(
        "ENCODE API key not found. Set ENCODE_API_KEY environment variable "
        "or add 'encode_api_key' to config/api in config.yaml."
    )

def get_data_paths(config: Optional[Dict[str, Any]] = None) -> Dict[str, Path]:
    """
    Resolve data paths from configuration.
    
    Args:
        config: Optional pre-loaded config dict.
        
    Returns:
        Dictionary mapping path names to Path objects.
    """
    if config is None:
        config = load_env_config()
    
    paths_config = config.get("paths", {})
    
    # Resolve relative to project root if not absolute
    project_root = Path(__file__).resolve().parents[2]
    
    resolved_paths = {}
    for key, value in paths_config.items():
        if value:
            path_obj = Path(value)
            if not path_obj.is_absolute():
                path_obj = project_root / value
            resolved_paths[key] = path_obj
    
    return resolved_paths

def ensure_directories(config: Optional[Dict[str, Any]] = None) -> None:
    """
    Ensure all required directories exist based on configuration.
    
    Args:
        config: Optional pre-loaded config dict.
    """
    paths = get_data_paths(config)
    
    required_dirs = [
        paths.get("data_root"),
        paths.get("processed_data"),
        paths.get("models"),
        paths.get("interpretation"),
        paths.get("figures")
    ]
    
    for dir_path in required_dirs:
        if dir_path:
            dir_path.mkdir(parents=True, exist_ok=True)

def write_sample_config(output_path: Optional[str] = None) -> str:
    """
    Write a sample configuration file to disk.
    
    Args:
        output_path: Optional output path. Defaults to config/config.yaml.
        
    Returns:
        Path to the written file.
    """
    if output_path is None:
        project_root = Path(__file__).resolve().parents[2]
        output_path = str(project_root / "config" / "config.yaml")
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    sample_config = _get_default_config()
    
    # Add comments
    with open(output_file, 'w') as f:
        f.write("# CTCF Binding Site Selection - Configuration File\n")
        f.write("# Copy this file to config.yaml and fill in your API keys and paths.\n\n")
        yaml.dump(sample_config, f, default_flow_style=False, sort_keys=False)
    
    return str(output_file)

def get_config_value(key: str, default: Any = None, config: Optional[Dict[str, Any]] = None) -> Any:
    """
    Get a nested configuration value using dot notation.
    
    Args:
        key: Dot-separated key (e.g., 'api.encode_api_key').
        default: Default value if key not found.
        config: Optional pre-loaded config.
        
    Returns:
        The configuration value or default.
    """
    if config is None:
        config = load_env_config()
    
    keys = key.split('.')
    current = config
    
    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        else:
            return default
    
    return current

def main():
    """CLI entry point for configuration management."""
    import argparse
    import logging
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    parser = argparse.ArgumentParser(description="Manage project configuration")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Validate manifest command
    parser_validate = subparsers.add_parser('validate', help='Validate manifest exists')
    
    # Write sample config command
    parser_sample = subparsers.add_parser('sample', help='Write sample config file')
    parser_sample.add_argument('--output', '-o', help='Output path for sample config')
    
    # Show paths command
    parser_paths = subparsers.add_parser('paths', help='Show resolved data paths')
    
    args = parser.parse_args()
    
    if args.command == 'validate':
        try:
            validate_manifest_exists()
            logger.info("Manifest validation successful.")
        except ConfigError as e:
            logger.error(f"Validation failed: {e}")
            sys.exit(1)
            
    elif args.command == 'sample':
        path = write_sample_config(args.output)
        logger.info(f"Sample config written to: {path}")
        
    elif args.command == 'paths':
        paths = get_data_paths()
        logger.info("Resolved Data Paths:")
        for name, path in paths.items():
            logger.info(f"  {name}: {path}")
            
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
