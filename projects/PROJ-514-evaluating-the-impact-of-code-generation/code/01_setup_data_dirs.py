import os
import sys
from pathlib import Path
from utils.logger import get_logger
from utils.config import get_project_root

def setup_data_directories():
    """
    Creates the required directory structure for the project's data storage.
    
    This implements Task T006: Setup data directory structure.
    Creates:
      - data/raw/human_samples
      - data/raw/llm_samples
      - data/intermediate
      - data/processed
    """
    root = get_project_root()
    logger = get_logger()
    
    # Define the relative paths as per task requirements
    required_dirs = [
        "data/raw/human_samples",
        "data/raw/llm_samples",
        "data/intermediate",
        "data/processed"
    ]
    
    created_count = 0
    for rel_path in required_dirs:
        target_path = root / rel_path
        try:
            target_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {target_path}")
            created_count += 1
        except PermissionError:
            logger.error(f"Permission denied creating directory: {target_path}")
            raise
        except OSError as e:
            logger.error(f"Error creating directory {target_path}: {e}")
            raise
    
    logger.info(f"Successfully created {created_count} data directories.")
    return created_count

def main():
    """Entry point for the script."""
    try:
        count = setup_data_directories()
        print(f"Setup complete. {count} directories created.")
        sys.exit(0)
    except Exception as e:
        print(f"Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()