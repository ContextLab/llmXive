"""
Utility to create the required data directory structure for the project.
Ensures `data/raw/` and `data/processed/` exist before data operations begin.
"""
import os
import sys
from pathlib import Path
import logging

# Add the project root to the path to allow imports from sibling modules if needed
# (Though this script only uses stdlib)
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Import logger if available, otherwise use standard logging
try:
    from utils.logger import get_logger, log_info, log_warning, log_error
    logger = get_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def create_data_directories(base_path: Optional[Path] = None) -> None:
    """
    Create the required directory structure for data storage.
    
    Args:
        base_path: Optional base path. Defaults to the project root.
    """
    if base_path is None:
        base_path = project_root
    
    # Define required directories
    required_dirs = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        # Also ensure other critical data dirs exist for the pipeline
        base_path / "state",
        base_path / "output",
        base_path / "data" / "config",
    ]
    
    created_count = 0
    for dir_path in required_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {dir_path}")
    
    if created_count > 0:
        logger.info(f"Successfully created {created_count} directory(ies).")
    else:
        logger.info("All required directories already exist.")

def main():
    """Entry point for the script."""
    logger.info("Starting directory creation...")
    try:
        create_data_directories()
        logger.info("Directory creation completed successfully.")
    except Exception as e:
        logger.error(f"Failed to create directories: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()