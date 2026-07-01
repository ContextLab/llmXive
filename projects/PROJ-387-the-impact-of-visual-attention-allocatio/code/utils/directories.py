import os
from pathlib import Path
from .config import get_project_root, get_data_path, get_output_path
from .logger import get_logger

def ensure_directory(path: Path) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: The directory path to ensure exists.
    """
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        logger = get_logger()
        if logger:
            logger.info(f"Created directory: {path}")

def create_base_directory_structure() -> None:
    """
    Create the base directory structure required for the project.
    
    Creates:
        data/raw/
        data/processed/
        data/eye-tracking/
        data/valence/
        output/plots/
        output/results/
    """
    root = get_project_root()
    
    # Data directories
    data_path = get_data_path()
    ensure_directory(data_path / "raw")
    ensure_directory(data_path / "processed")
    ensure_directory(data_path / "eye-tracking")
    ensure_directory(data_path / "valence")
    
    # Output directories
    output_path = get_output_path()
    ensure_directory(output_path / "plots")
    ensure_directory(output_path / "results")
    
    logger = get_logger()
    if logger:
        logger.info("Base directory structure created successfully.")

def verify_directory_structure() -> bool:
    """
    Verify that all required directories exist.
    
    Returns:
        True if all directories exist, False otherwise.
    """
    required_dirs = [
        get_data_path() / "raw",
        get_data_path() / "processed",
        get_data_path() / "eye-tracking",
        get_data_path() / "valence",
        get_output_path() / "plots",
        get_output_path() / "results",
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if not dir_path.exists():
            all_exist = False
            break
    
    return all_exist
