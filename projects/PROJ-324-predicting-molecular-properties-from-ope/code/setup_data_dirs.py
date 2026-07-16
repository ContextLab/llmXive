import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    """
    Create the required data directory structure for the molecular properties project.
    
    Creates the following directories under the project root:
    - data/raw: For original, unmodified downloaded data
    - data/processed: For cleaned and preprocessed data
    - data/derived: For model outputs, analysis results, and reports
    
    This script is idempotent - it will not fail if directories already exist.
    """
    # Determine project root (assuming this script is in code/ directory)
    project_root = Path(__file__).resolve().parent.parent
    data_root = project_root / "data"
    
    # Define required subdirectories
    required_dirs = [
        data_root / "raw",
        data_root / "processed",
        data_root / "derived"
    ]
    
    # Create directories
    for dir_path in required_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
        else:
            logger.info(f"Directory already exists: {dir_path}")
    
    # Verify all directories exist
    all_created = all(dir_path.exists() and dir_path.is_dir() for dir_path in required_dirs)
    
    if all_created:
        logger.info("Successfully created all required data directories.")
        return 0
    else:
        logger.error("Failed to create one or more required directories.")
        return 1

if __name__ == "__main__":
    exit(main())