import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/setup_directories.log')
    ]
)
logger = logging.getLogger(__name__)

def setup_directories():
    """
    Create the required directory structure for the project.
    Creates:
    - data/raw/
    - data/processed/
    - data/models/
    - logs/
    """
    # Define the directories to create relative to the project root
    # We assume this script runs from the project root or code/ directory
    # We use pathlib to handle path resolution robustly
    from pathlib import Path

    # Determine the project root. 
    # If running from code/, go up one level. If running from root, stay.
    # We check if 'data' exists in current dir, if not, check parent.
    current_path = Path.cwd()
    
    # Heuristic: look for 'code' directory to anchor project root
    if (current_path / 'code').exists():
        project_root = current_path
    elif (current_path.parent / 'code').exists():
        project_root = current_path.parent
    else:
        # Fallback: assume current directory is root
        project_root = current_path

    logger.info(f"Project root detected at: {project_root}")

    directories = [
        project_root / 'data' / 'raw',
        project_root / 'data' / 'processed',
        project_root / 'data' / 'models',
        project_root / 'logs',
        # Ensure data exists as a parent if not explicitly listed, though subdirs cover it
        project_root / 'data'
    ]

    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {dir_path}")
                created_count += 1
            except OSError as e:
                logger.error(f"Failed to create directory {dir_path}: {e}")
                raise
        else:
            logger.debug(f"Directory already exists: {dir_path}")

    logger.info(f"Directory setup complete. {created_count} new directories created.")
    return created_count

def main():
    """Entry point for the script."""
    try:
        setup_directories()
        logger.info("T007 Setup directory structure completed successfully.")
    except Exception as e:
        logger.error(f"Task T007 failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()