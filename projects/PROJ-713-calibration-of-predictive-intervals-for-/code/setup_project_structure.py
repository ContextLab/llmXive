"""
Project Directory Structure Setup Script.

This script ensures the existence of all required project directories
with idempotency and retry logic using exponential backoff.

Directories created:
- code/
- tests/
- data/raw/
- data/processed/
- results/
"""
import os
import sys
import time
from pathlib import Path
from typing import List, Tuple
from utils.logger import get_logger

# Define the required directory structure relative to the project root
REQUIRED_DIRS = [
    "code",
    "tests",
    "data/raw",
    "data/processed",
    "results"
]

logger = get_logger(__name__)

def ensure_dir_with_backoff(dir_path: Path, max_retries: int = 5, base_delay: float = 0.5) -> Tuple[bool, str]:
    """
    Ensure a directory exists with exponential backoff retry logic.
    
    Args:
        dir_path: The path to the directory to create.
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds between retries.
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    for attempt in range(max_retries):
        try:
            if dir_path.exists():
                if dir_path.is_dir():
                    # Verify writability
                    test_file = dir_path / ".write_test"
                    test_file.touch()
                    test_file.unlink()
                    logger.debug(f"Directory exists and is writable: {dir_path}")
                    return True, f"Directory already exists and is writable: {dir_path}"
                else:
                    return False, f"Path exists but is not a directory: {dir_path}"
            
            dir_path.mkdir(parents=True, exist_ok=True)
            
            # Verify creation and writability
            test_file = dir_path / ".write_test"
            test_file.touch()
            test_file.unlink()
            
            logger.info(f"Successfully created directory: {dir_path}")
            return True, f"Successfully created directory: {dir_path}"
            
        except PermissionError as e:
            delay = base_delay * (2 ** attempt)
            logger.warning(f"Permission denied for {dir_path}, retrying in {delay}s... ({attempt + 1}/{max_retries})")
            time.sleep(delay)
        except OSError as e:
            delay = base_delay * (2 ** attempt)
            logger.warning(f"OS error for {dir_path}: {e}, retrying in {delay}s... ({attempt + 1}/{max_retries})")
            time.sleep(delay)
        except Exception as e:
            logger.error(f"Unexpected error for {dir_path}: {e}")
            return False, f"Unexpected error: {e}"
    
    return False, f"Failed to create/verify directory after {max_retries} attempts: {dir_path}"

def setup_project_structure() -> bool:
    """
    Set up the entire project directory structure.
    
    Returns:
        bool: True if all directories were successfully created/verified, False otherwise.
    """
    project_root = Path(__file__).resolve().parent.parent
    logger.info(f"Setting up project structure in: {project_root}")
    
    all_success = True
    results = []
    
    for dir_name in REQUIRED_DIRS:
        dir_path = project_root / dir_name
        success, message = ensure_dir_with_backoff(dir_path)
        results.append((dir_name, success, message))
        if not success:
            all_success = False
            logger.error(f"Failed to setup: {dir_name}")
        else:
            logger.info(f"Setup complete: {dir_name}")
    
    # Summary log
    logger.info("Project structure setup summary:")
    for dir_name, success, message in results:
        status = "✓" if success else "✗"
        logger.info(f"  {status} {dir_name}: {message}")
    
    return all_success

def main():
    """Main entry point for the script."""
    logger.info("Starting project structure setup...")
    success = setup_project_structure()
    
    if success:
        logger.info("Project structure setup completed successfully.")
        sys.exit(0)
    else:
        logger.error("Project structure setup failed. Check logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()