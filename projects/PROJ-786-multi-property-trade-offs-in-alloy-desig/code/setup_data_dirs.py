"""
Setup script for data directory structure.
Creates raw and processed data directories with .gitkeep files.
"""
import os
from pathlib import Path

def setup_data_directories(project_root: Path = None):
    """
    Creates the required data directory structure.
    
    Args:
        project_root: Path to the project root. If None, uses current working directory.
        
    Returns:
        dict: Dictionary of created directory paths
    """
    if project_root is None:
        project_root = Path.cwd()
    
    # Define data directories relative to project root
    data_raw = project_root / "data" / "raw"
    data_processed = project_root / "data" / "processed"
    
    # Create directories
    data_raw.mkdir(parents=True, exist_ok=True)
    data_processed.mkdir(parents=True, exist_ok=True)
    
    # Create .gitkeep files to ensure directories are tracked by git
    (data_raw / ".gitkeep").touch()
    (data_processed / ".gitkeep").touch()
    
    created_dirs = {
        "data_raw": str(data_raw),
        "data_processed": str(data_processed)
    }
    
    print(f"Created data directory structure:")
    for name, path in created_dirs.items():
        print(f"  {name}: {path}")
    
    return created_dirs

if __name__ == "__main__":
    setup_data_directories()
