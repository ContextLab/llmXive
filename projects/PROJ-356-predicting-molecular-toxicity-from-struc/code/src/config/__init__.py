"""
Configuration module for the molecular toxicity pipeline.

Provides environment variable management and path resolution.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Project root is the parent of the code directory
_code_dir = Path(__file__).resolve().parent.parent.parent
_project_root = _code_dir.parent

def get_project_paths() -> Dict[str, Path]:
    """
    Get standard project directory paths.
    
    Returns:
        Dictionary mapping logical names to Path objects
    """
    return {
        "root": _project_root,
        "code": _code_dir,
        "src": _code_dir / "src",
        "data": _code_dir / "data",
        "results": _code_dir / "results",
        "models": _code_dir / "models",
        "config": _code_dir / "config",
        "tests": _code_dir / "tests"
    }

def get_env_var(name: str, default: Optional[str] = None) -> str:
    """
    Get an environment variable with a default fallback.
    
    Args:
        name: Environment variable name
        default: Default value if not set
    
    Returns:
        Environment variable value or default
    """
    return os.environ.get(name, default or "")

def validate_paths(paths: Dict[str, Path]) -> bool:
    """
    Validate that required paths exist.
    
    Args:
        paths: Dictionary of paths to validate
    
    Returns:
        True if all paths exist, False otherwise
    """
    all_valid = True
    for name, path in paths.items():
        if not path.exists():
            # Create missing directories
            try:
                path.mkdir(parents=True, exist_ok=True)
                print(f"Created missing directory: {path}")
            except Exception as e:
                print(f"Error creating directory {path}: {e}")
                all_valid = False
    return all_valid

__all__ = ["get_project_paths", "get_env_var", "validate_paths"]