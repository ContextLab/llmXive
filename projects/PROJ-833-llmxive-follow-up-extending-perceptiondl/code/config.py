import os
from pathlib import Path

# Project root is assumed to be the parent of the 'code' directory
# If running as script, we try to infer from __file__, otherwise default to current dir
_project_root = Path(__file__).resolve().parent.parent
if not (_project_root / "code").exists():
    _project_root = Path.cwd()

DATA_DIR = _project_root / "data"
RAW_DIR = DATA_DIR / "raw"
SYNTHETIC_DIR = DATA_DIR / "synthetic"
PROCESSED_DIR = DATA_DIR / "processed"

def get_data_path(subdir: str = "raw") -> Path:
    """
    Get the path to a specific data subdirectory.
    
    Args:
        subdir: Subdirectory name ('raw', 'synthetic', 'processed')
        
    Returns:
        Path object for the requested directory
        
    Raises:
        ValueError: If subdir is not one of the valid options
    """
    valid_subdirs = {"raw": RAW_DIR, "synthetic": SYNTHETIC_DIR, "processed": PROCESSED_DIR}
    if subdir not in valid_subdirs:
        raise ValueError(f"Invalid subdir '{subdir}'. Must be one of {list(valid_subdirs.keys())}")
    return valid_subdirs[subdir]

def ensure_directories():
    """
    Create the required data directory structure if they don't exist.
    
    Creates:
        data/raw/
        data/synthetic/
        data/processed/
        
    Raises:
        OSError: If directories cannot be created
    """
    dirs_to_create = [RAW_DIR, SYNTHETIC_DIR, PROCESSED_DIR]
    
    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)
        
    # Verify creation
    for dir_path in dirs_to_create:
        if not dir_path.exists():
            raise OSError(f"Failed to create directory: {dir_path}")

if __name__ == "__main__":
    # Simple test when run directly
    ensure_directories()
    print(f"Created directories in: {_project_root}")
    print(f"  - {RAW_DIR}")
    print(f"  - {SYNTHETIC_DIR}")
    print(f"  - {PROCESSED_DIR}")