import os
from pathlib import Path
from typing import Final

# Constants
SEED: Final[int] = 42
DATA_ROOT: Final[str] = "data"
CODE_ROOT: Final[str] = "code"
RESULTS_ROOT: Final[str] = "data/results"


def get_project_root() -> Path:
    """
    Return the project root directory.
    
    Assumes the script is run from the project root or that the code
    directory is inside the project root.
    """
    # Try to find the project root by looking for a known file or directory
    # Common markers: 'requirements.txt', 'pyproject.toml', 'README.md'
    current_path = Path(__file__).resolve()
    
    # Check if we are in code/ directory
    if current_path.name == "config.py" and current_path.parent.name == "code":
        return current_path.parent.parent
    
    # Fallback: traverse up until we find a marker
    for parent in current_path.parents:
        if (parent / "requirements.txt").exists() or \
           (parent / "pyproject.toml").exists() or \
           (parent / "README.md").exists():
            return parent
    
    # If no marker found, assume current working directory
    return Path.cwd()


def ensure_directories(dir_paths: list) -> None:
    """
    Ensure that the given directories exist.
    
    Args:
        dir_paths: List of directory paths (relative or absolute) to create.
    """
    project_root = get_project_root()
    
    for dir_path in dir_paths:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)


def get_data_path(sub_path: str = "") -> Path:
    """
    Get the full path to a data file or directory.
    
    Args:
        sub_path: Optional sub-path relative to the data root.
    
    Returns:
        The full Path object.
    """
    project_root = get_project_root()
    data_root = project_root / DATA_ROOT
    
    if sub_path:
        return data_root / sub_path
    return data_root
