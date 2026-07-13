import os
from pathlib import Path

def create_directories(base_path: str = None):
    """
    Create the standard project directory structure.
    
    Args:
        base_path: Optional base path. If None, uses the current working directory.
    
    Returns:
        None
    """
    if base_path is None:
        base_path = Path.cwd()
    else:
        base_path = Path(base_path)
    
    # Define directories to create
    directories = [
        "code",
        "code/data_acquisition",
        "code/feature_extraction",
        "code/analysis",
        "code/utils",
        "data",
        "data/raw",
        "data/processed",
        "tests",
        "docs"
    ]
    
    for dir_name in directories:
        dir_path = base_path / dir_name
        os.makedirs(dir_path, exist_ok=True)
    
    # Create empty checksums.yaml if data directory exists
    checksums_file = base_path / "data" / "checksums.yaml"
    if not checksums_file.exists():
        checksums_file.touch()
    
    # Create empty __init__.py files in code subdirectories
    for dir_name in ["data_acquisition", "feature_extraction", "analysis", "utils"]:
        init_file = base_path / "code" / dir_name / "__init__.py"
        init_file.touch()
