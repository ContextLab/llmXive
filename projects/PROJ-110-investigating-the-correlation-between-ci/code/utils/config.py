"""
Configuration management for the project.

Handles loading environment variables and project paths.
"""
import os
from pathlib import Path
from typing import Dict, Any

def get_project_paths() -> Dict[str, Path]:
    """
    Get standardized project directory paths.
    
    Returns:
        Dictionary mapping path names to Path objects.
    """
    # Assume the project root is the parent of the 'code' directory
    # This works whether running from 'code/' or project root
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent
    
    return {
        "project_root": project_root,
        "code": project_root / "code",
        "data": project_root / "data",
        "data_raw": project_root / "data" / "raw",
        "data_processed": project_root / "data" / "processed",
        "tests": project_root / "tests",
        "docs": project_root / "docs",
        "state": project_root / "state",
    }

def get_config_value(key: str, default: Any = None) -> Any:
    """
    Get a configuration value from environment variables.
    
    Args:
        key: Environment variable name.
        default: Default value if not found.
        
    Returns:
        The configuration value.
    """
    return os.environ.get(key, default)
