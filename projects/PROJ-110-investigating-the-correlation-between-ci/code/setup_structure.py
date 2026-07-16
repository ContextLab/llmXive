import os
from pathlib import Path
from utils.logging import get_logger

logger = get_logger(__name__)

def create_directories(base_path: str = ".") -> None:
    """
    Creates the required directory structure for the project.
    
    Creates:
    - data/raw
    - data/processed
    - contracts (for schema definitions)
    
    Args:
        base_path: The root directory where the structure will be created.
    """
    root = Path(base_path)
    
    directories = [
        root / "data" / "raw",
        root / "data" / "processed",
        root / "contracts",
        root / "data" / "figures",
        root / "state" / "projects",
    ]
    
    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {dir_path}")
    
    logger.info(f"Directory structure setup complete. Created {created_count} new directories.")
