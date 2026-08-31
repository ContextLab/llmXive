"""
Project Structure Initialization Script.

This script creates the required directory structure for the llmXive
calibration project with robust error handling, exponential backoff
for filesystem latency, and idempotency checks.
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Tuple

# Import logger from the project's utility module
from utils.logger import get_logger

# Define the required directory structure relative to the project root
# The project root is assumed to be the parent of the 'code' directory
# or we can derive it dynamically.
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent

REQUIRED_DIRS: List[str] = [
    "code",
    "tests",
    "data/raw",
    "data/processed",
    "results"
]

# Configuration for the retry loop
MAX_RETRIES = 5
INITIAL_DELAY = 0.5  # seconds
MAX_DELAY = 5.0      # seconds
DELAY_MULTIPLIER = 2.0

logger = get_logger(__name__)


def ensure_dir_with_backoff(dir_path: Path, max_retries: int = MAX_RETRIES) -> Tuple[bool, str]:
    """
    Ensure a directory exists with exponential backoff retry logic.

    This handles potential filesystem latency issues (e.g., network mounts,
    slow disk I/O) by retrying the creation and verification steps.

    Args:
        dir_path: The absolute path to the directory to create/verify.
        max_retries: Maximum number of retry attempts.

    Returns:
        A tuple (success: bool, message: str).
    """
    current_delay = INITIAL_DELAY

    for attempt in range(1, max_retries + 1):
        try:
            # Create the directory if it doesn't exist (parents=True for nested)
            dir_path.mkdir(parents=True, exist_ok=True)
            
            # Verify existence with a small delay to ensure propagation
            if not dir_path.exists():
                raise FileNotFoundError(f"Directory creation failed: {dir_path} does not exist after mkdir.")
            
            if not dir_path.is_dir():
                raise NotADirectoryError(f"Path exists but is not a directory: {dir_path}")

            # Success
            logger.info(f"Verified directory: {dir_path}")
            return True, f"Successfully created/verified: {dir_path}"

        except (OSError, FileNotFoundError, NotADirectoryError) as e:
            if attempt == max_retries:
                msg = f"Failed to create/verify {dir_path} after {max_retries} attempts: {e}"
                logger.error(msg)
                return False, msg
            
            # Log warning and wait with exponential backoff
            logger.warning(f"Attempt {attempt}/{max_retries} failed for {dir_path}: {e}. Retrying in {current_delay:.2f}s...")
            time.sleep(current_delay)
            
            # Exponential backoff with cap
            current_delay = min(current_delay * DELAY_MULTIPLIER, MAX_DELAY)

    # Should not be reached due to the return in the loop, but safe fallback
    return False, f"Unknown error occurred for {dir_path}"


def setup_project_structure() -> bool:
    """
    Main function to orchestrate the creation of the project directory structure.

    Returns:
        True if all directories were successfully created and verified, False otherwise.
    """
    logger.info(f"Starting project structure setup in: {PROJECT_ROOT}")
    all_success = True
    failures = []

    for dir_name in REQUIRED_DIRS:
        full_path = PROJECT_ROOT / dir_name
        success, message = ensure_dir_with_backoff(full_path)
        
        if success:
            logger.info(f"[OK] {message}")
        else:
            logger.error(f"[FAIL] {message}")
            all_success = False
            failures.append(dir_name)

    if all_success:
        logger.info("Project structure setup completed successfully.")
        # Log the final tree for verification (conceptual, not actual shell command)
        logger.info(f"Created directories: {', '.join(REQUIRED_DIRS)}")
    else:
        logger.error(f"Setup failed. Failed directories: {', '.join(failures)}")

    return all_success


def main():
    """Entry point for the script."""
    # Change to project root to ensure relative paths work if needed elsewhere
    os.chdir(PROJECT_ROOT)
    
    success = setup_project_structure()
    
    if not success:
        sys.exit(1)
    else:
        print("Project structure initialization complete.")
        sys.exit(0)


if __name__ == "__main__":
    main()
