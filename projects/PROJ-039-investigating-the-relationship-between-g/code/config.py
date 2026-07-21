import os
import yaml
from pathlib import Path
from typing import Any, Dict

def get_project_root() -> Path:
    """
    Get the project root directory.
    Assumes the script is run from the project root or a subdirectory.
    """
    current = Path(__file__).resolve()
    # Traverse up until we find the directory containing 'data', 'code', 'tests'
    # or until we hit a common project marker
    for parent in current.parents:
        if (parent / "data").exists() and (parent / "code").exists():
            return parent
    # Fallback to current directory if structure not found
    return current.parent

def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load a YAML configuration file.
    
    Args:
        config_path: Path to the YAML file.
        
    Returns:
        Dictionary with configuration data.
    """
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)
