import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def setup_data_directories(root_dir: str) -> None:
    """
    Create the required data directory structure:
    - data/raw/
    - data/processed/
    - data/models/
    
    Args:
        root_dir: The project root directory path.
    """
    base_path = Path(root_dir)
    data_path = base_path / "data"
    
    directories = [
        data_path / "raw",
        data_path / "processed",
        data_path / "models"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {directory}")
        
    # Create __init__.py to ensure valid Python package structure if needed
    # (Though data dirs are usually not packages, this aligns with T001)
    init_file = data_path / "__init__.py"
    if not init_file.exists():
        init_file.touch()
        logger.info(f"Created {init_file} to ensure package structure.")

def create_init_files(root_dir: str) -> None:
    """
    Create __init__.py files in the data directories to ensure they are treated as packages.
    """
    base_path = Path(root_dir)
    data_path = base_path / "data"
    
    sub_dirs = ["raw", "processed", "models"]
    
    for sub_dir in sub_dirs:
        dir_path = data_path / sub_dir
        init_path = dir_path / "__init__.py"
        if not init_path.exists():
            init_path.touch()
            logger.info(f"Created {init_path}")

def main() -> None:
    """
    Entry point for the script. Creates data directories relative to the current working directory.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Assume script runs from project root or we target the current working directory
    root_dir = Path.cwd()
    
    logger.info(f"Setting up data directories in: {root_dir}")
    setup_data_directories(root_dir)
    create_init_files(root_dir)
    logger.info("Data directory setup complete.")

if __name__ == "__main__":
    main()
