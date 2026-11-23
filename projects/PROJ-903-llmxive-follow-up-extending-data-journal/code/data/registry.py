"""
Registry loading utility.
This file was missing and caused the import error in main.py.
"""
import os
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional

def load_registry(registry_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the dataset registry from a YAML file.
    
    Args:
        registry_path: Path to the registry file. Defaults to 'data/dataset_registry.yaml'.
        
    Returns:
        Dictionary containing the registry entries.
        
    Raises:
        FileNotFoundError: If the registry file does not exist.
        yaml.YAMLError: If the file is not valid YAML.
    """
    if registry_path is None:
        registry_path = Path("data/dataset_registry.yaml")
    else:
        registry_path = Path(registry_path)
        
    if not registry_path.exists():
        raise FileNotFoundError(f"Registry file not found at {registry_path}")
        
    with open(registry_path, 'r') as f:
        data = yaml.safe_load(f)
        
    return data
