"""
Data directory structure management for the battery electrolyte decomposition project.
Creates and validates the required directory hierarchy for raw, processed, and validation data.
"""
from pathlib import Path
import os
import sys

# Define the required directory structure relative to the project root
# The project root is assumed to be the parent of 'code/'
REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "data/validation",
    "tests/unit",
    "tests/integration",
    "tests/contract",
    "code/models",
    "code/utils",
    "code/visualization",
]

def get_project_root() -> Path:
    """
    Determine the project root directory.
    Assumes the script is run from the root or code/ directory.
    """
    current = Path(__file__).resolve()
    # Navigate up from code/data/structure.py to project root
    # Expected path: <root>/code/data/structure.py
    return current.parent.parent.parent

def create_directory_structure(base_path: Optional[Path] = None) -> dict:
    """
    Creates the required directory structure for the project.
    
    Args:
        base_path: Optional base path. If None, uses the detected project root.
        
    Returns:
        A dictionary mapping directory names to their absolute paths.
    """
    if base_path is None:
        base_path = get_project_root()
    
    created = {}
    for dir_name in REQUIRED_DIRS:
        full_path = base_path / dir_name
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created[dir_name] = str(full_path)
        except OSError as e:
            # Log error but continue creating others
            print(f"Warning: Could not create directory {full_path}: {e}", file=sys.stderr)
    
    return created

def validate_directory_structure(base_path: Optional[Path] = None) -> bool:
    """
    Validates that all required directories exist.
    
    Args:
        base_path: Optional base path. If None, uses the detected project root.
        
    Returns:
        True if all directories exist, False otherwise.
    """
    if base_path is None:
        base_path = get_project_root()
    
    missing = []
    for dir_name in REQUIRED_DIRS:
        full_path = base_path / dir_name
        if not full_path.is_dir():
            missing.append(dir_name)
    
    if missing:
        print(f"Error: Missing required directories: {missing}", file=sys.stderr)
        return False
    
    return True

def get_data_paths(base_path: Optional[Path] = None) -> dict:
    """
    Returns a dictionary of paths to the main data directories.
    
    Args:
        base_path: Optional base path. If None, uses the detected project root.
        
    Returns:
        Dictionary with keys 'raw', 'processed', 'validation' mapping to Path objects.
    """
    if base_path is None:
        base_path = get_project_root()
    
    return {
        "raw": base_path / "data" / "raw",
        "processed": base_path / "data" / "processed",
        "validation": base_path / "data" / "validation",
    }

if __name__ == "__main__":
    print("Initializing data directory structure...")
    root = get_project_root()
    print(f"Project root detected at: {root}")
    
    created = create_directory_structure(root)
    print(f"Created directories: {list(created.keys())}")
    
    if validate_directory_structure(root):
        print("Validation passed: All required directories exist.")
    else:
        print("Validation failed: Some directories are missing.")
        sys.exit(1)
