import os
import yaml
from pathlib import Path
from typing import Any, Dict

def get_project_root() -> Path:
    """Get the project root directory."""
    # Assuming the script is run from the project root or code/
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    return project_root

def load_config(config_path: str) -> Dict[str, Any]:
    """Load a YAML configuration file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config or {}
