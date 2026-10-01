import os
import sys
from pathlib import Path

# Ensure the script can be imported from the code/ directory
# If running as a script, add the parent directory to sys.path
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.logging_config import get_logger

logger = get_logger(__name__)

def ensure_directory(path: Path) -> bool:
    """
    Ensure a directory exists. Create it if it doesn't.
    
    Args:
        path: Path object representing the directory to create.
        
    Returns:
        bool: True if directory exists or was created successfully, False otherwise.
    """
    try:
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {path}")
        else:
            logger.debug(f"Directory already exists: {path}")
        
        # Verify writability by attempting to create a temporary file
        test_file = path / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
            logger.debug(f"Verified writability for: {path}")
            return True
        except OSError as e:
            logger.error(f"Directory exists but is not writable: {path} - {e}")
            return False
            
    except OSError as e:
        logger.error(f"Failed to create directory: {path} - {e}")
        return False

def main():
    """
    Main entry point for creating data directories.
    
    Creates the following directories relative to the project root:
    - data/raw/
    - data/processed/
    
    Returns:
        int: 0 on success, 1 on failure.
    """
    # Determine project root (assuming this script is in code/)
    project_root = Path(__file__).resolve().parent.parent
    data_root = project_root / "data"
    
    directories = [
        data_root / "raw",
        data_root / "processed"
    ]
    
    success = True
    for dir_path in directories:
        if not ensure_directory(dir_path):
            success = False
    
    if success:
        logger.info("Data directories created and verified successfully.")
        return 0
    else:
        logger.error("Failed to create or verify one or more data directories.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
