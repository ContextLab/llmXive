import os
import sys
import logging
from pathlib import Path

# Add project root to path to allow imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.utils.logging import get_logger

logger = get_logger("setup_data_structure")

def create_data_directories() -> None:
    """
    Initialize data directories as per task T001b.
    Creates: data/raw/, data/processed/, data/splits/, data/schemas/
    """
    base_path = project_root / "data"
    
    required_dirs = [
        "raw",
        "processed",
        "splits",
        "schemas"
    ]
    
    created_count = 0
    for dir_name in required_dirs:
        dir_path = base_path / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {dir_path}")
    
    logger.info(f"Data directory setup complete. Created {created_count} new directories.")
    return None

def main() -> None:
    """Entry point for script execution."""
    setup_logging()
    logger.info("Starting data directory initialization (T001b)...")
    create_data_directories()
    logger.info("Data directory initialization complete.")

if __name__ == "__main__":
    main()
