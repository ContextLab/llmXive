"""
T006: Setup data directory structure.

Creates the required directory hierarchy for raw, intermediate, processed data,
reference sets, and reports as specified in the project plan.

This script must be executed to ensure all data paths are writable and exist
before data collection or analysis tasks begin.
"""
import os
import sys
from pathlib import Path

# Import from existing project utilities as per API surface
from utils.logger import get_logger
from utils.config import get_project_root

# Define the relative paths to be created under the project root's 'data' and 'reports' directories
# These paths match the requirements in tasks.md for T006 and T001
REQUIRED_DIRS = [
    "data/raw/human_samples",
    "data/raw/llm_samples",
    "data/intermediate",
    "data/processed",
    "data/raw/reference_set",
    "reports",
]

def setup_data_directories():
    """
    Create all required data directories.
    
    Returns:
        bool: True if all directories were created or already exist and are writable,
              False if any directory creation failed or is not writable.
    """
    logger = get_logger(__name__)
    project_root = get_project_root()
    
    if not project_root:
        logger.error("Could not determine project root. Aborting directory setup.")
        return False
    
    base_path = Path(project_root)
    success = True
    
    for dir_name in REQUIRED_DIRS:
        target_dir = base_path / dir_name
        
        try:
            # Create directories if they don't exist, including parents
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Verify writability by attempting to create a temporary marker file
            # This ensures the user has permissions and the path is valid
            marker_file = target_dir / ".write_test_marker"
            try:
                marker_file.touch()
                marker_file.unlink()  # Remove the marker immediately
            except (OSError, PermissionError) as e:
                logger.error(f"Directory {target_dir} exists but is not writable: {e}")
                success = False
                continue
            
            logger.info(f"Verified directory: {target_dir}")
            
        except OSError as e:
            logger.error(f"Failed to create directory {target_dir}: {e}")
            success = False
    
    return success

def main():
    """Entry point for the script."""
    logger = get_logger(__name__)
    logger.info("Starting data directory setup (Task T006)...")
    
    if setup_data_directories():
        logger.info("All data directories created and verified successfully.")
        print("SUCCESS: Data directory structure is ready.")
        sys.exit(0)
    else:
        logger.error("Data directory setup failed. Check logs for details.")
        print("FAILURE: Data directory setup failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
