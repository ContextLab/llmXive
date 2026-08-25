import os
import sys
from pathlib import Path
import logging
from utils.logging import get_logger

def ensure_tests_directory(base_path: Optional[Path] = None) -> Path:
    """
    Ensure the 'tests' directory exists at the project root.
    
    Creates the directory if it does not exist.
    Verifies existence using pathlib.
    
    Args:
        base_path: Optional base path. Defaults to project root (parent of code/).
        
    Returns:
        Path object pointing to the tests directory.
        
    Raises:
        RuntimeError: If the directory cannot be created or verified.
    """
    if base_path is None:
        # Determine project root: parent of the code directory where this script lives
        # Assuming this script is in code/, project root is one level up
        current_file = Path(__file__).resolve()
        code_dir = current_file.parent
        base_path = code_dir.parent
    
    tests_dir = base_path.joinpath('tests')
    
    logger = get_logger(__name__)
    logger.info(f"Ensuring tests directory exists at: {tests_dir}")
    
    if not tests_dir.exists():
        try:
            tests_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created tests directory: {tests_dir}")
        except OSError as e:
            error_msg = f"Failed to create tests directory at {tests_dir}: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    else:
        logger.debug(f"Tests directory already exists: {tests_dir}")
    
    # Verification step as required by task T001c
    if not tests_dir.is_dir():
        error_msg = f"Verification failed: {tests_dir} exists but is not a directory."
        logger.error(error_msg)
        raise RuntimeError(error_msg)
        
    logger.info(f"Verification passed: tests directory exists at {tests_dir}")
    return tests_dir

def main():
    """Entry point for CLI execution."""
    logging.basicConfig(level=logging.INFO)
    logger = get_logger(__name__)
    
    try:
        tests_path = ensure_tests_directory()
        logger.info(f"Task T001c completed successfully. Directory: {tests_path}")
        return 0
    except RuntimeError as e:
        logger.error(f"Task T001c failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
