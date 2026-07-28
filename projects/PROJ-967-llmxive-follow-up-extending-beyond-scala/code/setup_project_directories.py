"""
Task T001a: Create project directories for PROJ-967-llmxive-follow-up-extending-beyond-scala.

Creates the following directories relative to the repository root:
- projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/raw
- projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/processed
- projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/code
- projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests
- projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/results

This script replaces T004 and ensures the project structure exists before
other tasks begin.
"""
import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = "projects/PROJ-967-llmxive-follow-up-extending-beyond-scala"

def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {path}")
    except OSError as e:
        logger.error(f"Failed to create directory {path}: {e}")
        raise

def main() -> None:
    """Create all required project directories."""
    logger.info(f"Starting directory creation for project: {PROJECT_ROOT}")
    
    # Define required directories relative to project root
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "results"
    ]
    
    # Create each directory
    created_count = 0
    for dir_path in directories:
        full_path = Path(PROJECT_ROOT) / dir_path
        ensure_directory(full_path)
        created_count += 1
    
    logger.info(f"Successfully created {created_count} directories for {PROJECT_ROOT}")
    
    # Verify directories exist
    missing = []
    for dir_path in directories:
        full_path = Path(PROJECT_ROOT) / dir_path
        if not full_path.exists():
            missing.append(str(full_path))
    
    if missing:
        logger.error(f"Verification failed: Missing directories: {missing}")
        sys.exit(1)
    else:
        logger.info("Verification successful: All directories exist.")

if __name__ == "__main__":
    main()