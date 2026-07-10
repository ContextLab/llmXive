import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

# Project root relative to this script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "env_config.yaml"
MANIFEST_PATH = PROJECT_ROOT / "data" / "manifest.json"

def load_env_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load environment configuration from YAML file.
    
    Args:
        config_path: Path to config file. Defaults to config/env_config.yaml.
        
    Returns:
        Dictionary with configuration values.
        
    Raises:
        FileNotFoundError: If config file does not exist.
        yaml.YAMLError: If config file is malformed.
    """
    if config_path is None:
        config_path = CONFIG_PATH
        
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def validate_manifest_exists() -> bool:
    """Check if data/manifest.json exists (required by T007).
    
    Returns:
        True if manifest exists, False otherwise.
    """
    return MANIFEST_PATH.exists()

def get_encode_api_key(config: Optional[Dict[str, Any]] = None) -> str:
    """Retrieve ENCODE API key from config or environment.
    
    Priority:
    1. config['credentials']['encode_api_key']
    2. ENCODE_API_KEY environment variable
    3. ENCODE_ACCESS_KEY_ID environment variable (fallback)
    
    Args:
        config: Pre-loaded config dict. If None, loads from file.
        
    Returns:
        API key string.
        
    Raises:
        ValueError: If no API key found.
    """
    if config is None:
        config = load_env_config()
        
    # Try config first
    api_key = config.get("credentials", {}).get("encode_api_key")
    if api_key:
        return api_key
        
    # Try environment variables
    env_key = os.environ.get("ENCODE_API_KEY") or os.environ.get("ENCODE_ACCESS_KEY_ID")
    if env_key:
        return env_key
        
    raise ValueError(
        "ENCODE API key not found. Set ENCODE_API_KEY environment variable "
        "or add 'encode_api_key' to config/credentials in env_config.yaml."
    )

def get_data_paths(config: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """Get resolved data directory paths from config.
    
    Args:
        config: Pre-loaded config dict. If None, loads from file.
        
    Returns:
        Dictionary with resolved paths for raw_data, processed_data, models, etc.
    """
    if config is None:
        config = load_env_config()
        
    base_paths = config.get("paths", {})
    project_root = str(PROJECT_ROOT)
    
    resolved = {
        "raw_data": str(PROJECT_ROOT / "data" / "raw"),
        "processed_data": str(PROJECT_ROOT / "data" / "processed"),
        "models": str(PROJECT_ROOT / "data" / "models"),
        "interpretation": str(PROJECT_ROOT / "data" / "interpretation"),
        "figures": str(PROJECT_ROOT / "data" / "figures"),
    }
    
    # Override with config if provided
    for key, value in base_paths.items():
        if key in resolved and value:
            # Handle relative paths
            if not os.path.isabs(value):
                resolved[key] = str(PROJECT_ROOT / value)
            else:
                resolved[key] = value
                
    return resolved

def ensure_directories(config: Optional[Dict[str, Any]] = None) -> None:
    """Create all required data directories if they don't exist.
    
    Args:
        config: Pre-loaded config dict. If None, loads from file.
    """
    paths = get_data_paths(config)
    for path_str in paths.values():
        Path(path_str).mkdir(parents=True, exist_ok=True)

def write_sample_config(output_path: Optional[Path] = None) -> Path:
    """Write a sample configuration file for first-time setup.
    
    Args:
        output_path: Where to write the sample config. Defaults to config/env_config.yaml.
        
    Returns:
        Path to the written file.
    """
    if output_path is None:
        output_path = CONFIG_PATH
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    sample_config = {
        "credentials": {
            "encode_api_key": "YOUR_ENCODE_API_KEY_HERE",
            "encode_secret_key": "YOUR_ENCODE_SECRET_KEY_HERE",
        },
        "paths": {
            "raw_data": "data/raw",
            "processed_data": "data/processed",
            "models": "data/models",
            "interpretation": "data/interpretation",
            "figures": "data/figures",
        },
        "settings": {
            "shannon_entropy_threshold": 0.8,
            "sequence_window_size": 1000,
            "max_workers": 4,
        }
    }
    
    with open(output_path, "w") as f:
        yaml.dump(sample_config, f, default_flow_style=False)
        
    return output_path

def main() -> int:
    """CLI entry point for environment setup and validation.
    
    Returns:
        0 on success, 1 on failure.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Setup and validate environment configuration for CTCF project."
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Generate a sample configuration file if one doesn't exist."
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate that required files (manifest.json) and credentials exist."
    )
    parser.add_argument(
        "--show-paths",
        action="store_true",
        help="Print resolved data paths."
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize config if requested or if it doesn't exist
        if args.init or not CONFIG_PATH.exists():
            if not CONFIG_PATH.exists():
                print(f"Config file not found. Creating sample at {CONFIG_PATH}")
            write_sample_config()
            print(f"Sample configuration written to {CONFIG_PATH}")
            print("Please edit the file to add your ENCODE API credentials.")
            
        # Load config for subsequent operations
        config = load_env_config()
        
        # Validate manifest exists (T007 requirement)
        if args.validate:
            if not validate_manifest_exists():
                print(f"ERROR: Required file not found: {MANIFEST_PATH}")
                print("Run T004/T007 first to generate the data manifest.")
                return 1
                
            try:
                api_key = get_encode_api_key(config)
                print(f"✓ ENCODE API key found (length: {len(api_key)})")
            except ValueError as e:
                print(f"ERROR: {e}")
                return 1
                
            print("✓ Environment validation passed.")
            
        # Show paths
        if args.show_paths or args.validate:
            paths = get_data_paths(config)
            print("\nResolved Data Paths:")
            for key, value in paths.items():
                print(f"  {key}: {value}")
                
        # Ensure directories exist
        ensure_directories(config)
        print("\n✓ All required directories created/verified.")
        
        return 0
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return 1
    except yaml.YAMLError as e:
        print(f"ERROR: Invalid YAML in config file: {e}")
        return 1
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
