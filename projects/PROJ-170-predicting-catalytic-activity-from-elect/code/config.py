import os
import json
from pathlib import Path
from typing import Any, Dict, Optional, List

def get_project_root() -> Path:
    """Returns the root directory of the project."""
    return Path(__file__).resolve().parent.parent

def get_data_path() -> Path:
    """Returns the path to the data directory."""
    return get_project_root() / "data"

def get_output_path() -> Path:
    """Returns the path to the outputs directory."""
    return get_project_root() / "outputs"

class Configuration:
    """Configuration holder for the project."""
    def __init__(self):
        self.project_root = get_project_root()
        self.data_path = get_data_path()
        self.output_path = get_output_path()

def get_config() -> Configuration:
    """Returns a Configuration instance."""
    return Configuration()

def main():
    """Entry point for config module."""
    config = get_config()
    print(f"Project Root: {config.project_root}")
    print(f"Data Path: {config.data_path}")
    print(f"Output Path: {config.output_path}")

if __name__ == "__main__":
    main()