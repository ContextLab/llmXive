"""
Script to create and verify the 'results/' directory for the project.

This task (T001e) ensures the 'results/' directory exists and is writable.
It is idempotent: running it multiple times will not fail if the directory
already exists.
"""
import os
import sys
import argparse
import tempfile
from pathlib import Path
from utils.logger import get_logger
from config import PROJECT_ROOT, RESULTS_DIR

logger = get_logger(__name__)


def ensure_dir(directory_path: Path) -> bool:
    """
    Ensure the specified directory exists.
    
    Args:
        directory_path: The Path object representing the directory to create.
        
    Returns:
        bool: True if the directory exists (or was created) and is writable, False otherwise.
    """
    try:
        # Create directory if it doesn't exist (idempotent)
        directory_path.mkdir(parents=True, exist_ok=True)
        
        # Verify writability by attempting to create a temporary file
        test_file = directory_path / ".write_test"
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            # If we can write, remove the test file
            test_file.unlink()
            logger.info(f"Directory '{directory_path}' exists and is writable.")
            return True
        except (IOError, OSError) as e:
            logger.error(f"Directory '{directory_path}' exists but is not writable: {e}")
            return False
        
    except OSError as e:
        logger.error(f"Failed to create directory '{directory_path}': {e}")
        return False


def main(args: Optional[argparse.Namespace] = None) -> int:
    """
    Main entry point for the results directory setup script.
    
    Args:
        args: Optional namespace of command-line arguments. If None, parses from sys.argv.
        
    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    parser = argparse.ArgumentParser(
        description="Create and verify the 'results/' directory for the project."
    )
    parser.add_argument(
        "--path",
        type=str,
        default=str(RESULTS_DIR),
        help=f"Path to the results directory (default: {RESULTS_DIR})"
    )
    
    parsed_args = parser.parse_args() if args is None else args
    
    results_path = Path(parsed_args.path)
    
    # If relative path, resolve relative to PROJECT_ROOT
    if not results_path.is_absolute():
        results_path = PROJECT_ROOT / results_path
    
    logger.info(f"Ensuring results directory exists at: {results_path}")
    
    if ensure_dir(results_path):
        logger.info("Task T001e completed successfully.")
        return 0
    else:
        logger.error("Task T001e failed: Could not ensure results directory is writable.")
        return 1


if __name__ == "__main__":
    sys.exit(main())