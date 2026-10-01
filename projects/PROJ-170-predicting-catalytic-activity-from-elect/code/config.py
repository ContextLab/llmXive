import os
import json
from pathlib import Path
from typing import Any, Dict, Optional, List

def get_project_root() -> Path:
    """Get the project root directory."""
    # Assume project root is two levels up from this file
    return Path(__file__).resolve().parent.parent

def get_data_path() -> Path:
    """Get the data directory path."""
    return get_project_root() / "data"

def get_output_path() -> Path:
    """Get the outputs directory path."""
    return get_project_root() / "outputs"

class Configuration:
    """Base configuration class."""
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        self.config = config_dict or {}
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

def get_config() -> Configuration:
    """Get the global configuration instance."""
    # Load from environment or default
    return Configuration()

def main():
    """Main entry point for config module."""
    print(f"Project root: {get_project_root()}")
    print(f"Data path: {get_data_path()}")
    print(f"Output path: {get_output_path()}")

if __name__ == "__main__":
    main()