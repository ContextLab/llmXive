import os
import sys
from pathlib import Path
import logging

# Configure logging for the setup script
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_project_structure():
    """
    Creates the required project directory structure for the llmXive pipeline.
    This implements T001: Create project structure per implementation plan.
    """
    # Define the root directory (project root)
    root = Path(".")
    
    # Define the required directories based on tasks.md
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/metrics",
        "data/results",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "docs"
    ]
    
    created_count = 0
    skipped_count = 0
    
    for dir_path in directories:
        full_path = root / dir_path
        try:
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {full_path}")
                created_count += 1
            else:
                logger.debug(f"Directory already exists: {full_path}")
                skipped_count += 1
        except OSError as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            raise
    
    logger.info(f"Project structure setup complete. Created: {created_count}, Skipped: {skipped_count}")
    return True

def main():
    """
    Entry point for the project setup script.
    """
    logger.info("Starting project structure creation...")
    try:
        create_project_structure()
        logger.info("Project structure created successfully.")
        return 0
    except Exception as e:
        logger.error(f"Project structure creation failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())