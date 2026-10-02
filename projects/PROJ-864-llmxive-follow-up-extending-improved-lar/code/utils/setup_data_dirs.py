import os
import sys
from pathlib import Path
from typing import List

from utils.logging import get_logger, info, error

def setup_data_directories() -> bool:
    """
    Create the required directory structure for the project:
    - code/
    - data/
    - tests/
    - state/

    Returns True if all directories exist (created or pre-existing) and are accessible.
    Returns False if any directory creation fails.
    """
    logger = get_logger("setup_data_dirs")
    project_root = Path(__file__).resolve().parent.parent.parent
    
    # The task specifies paths relative to the project root:
    # projects/PROJ-864-llmxive-follow-up-extending-improved-lar/
    # Since this script is at code/utils/setup_data_dirs.py, parent.parent.parent is the project root.
    
    required_dirs = [
        "code",
        "data",
        "tests",
        "state"
    ]
    
    created_dirs: List[Path] = []
    failed_dirs: List[Path] = []
    
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        
        if dir_path.exists():
            if not dir_path.is_dir():
                error(f"Path exists but is not a directory: {dir_path}")
                failed_dirs.append(dir_path)
            else:
                info(f"Directory already exists: {dir_path}")
        else:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                created_dirs.append(dir_path)
                info(f"Created directory: {dir_path}")
            except OSError as e:
                error(f"Failed to create directory {dir_path}: {e}")
                failed_dirs.append(dir_path)
    
    if failed_dirs:
        error(f"Failed to create {len(failed_dirs)} directories.")
        return False
    
    # Verification step: Ensure all directories exist and are writable
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if not os.path.isdir(dir_path):
            error(f"Verification failed: Directory does not exist after attempt: {dir_path}")
            return False
        
        # Check writability
        try:
            test_file = dir_path / ".write_test"
            test_file.touch()
            test_file.unlink()
        except OSError as e:
            error(f"Verification failed: Directory not writable: {dir_path} - {e}")
            return False
    
    info(f"Successfully initialized and verified {len(created_dirs)} directories.")
    return True

def main():
    """Entry point for running the directory setup script directly."""
    success = setup_data_directories()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
