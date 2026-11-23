"""
Project Structure Setup Script.

Creates the required directory structure for the llmXive automated science pipeline.
Ensures all necessary folders exist for data management, code organization, and CI/CD.
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

# Define the required directory structure relative to the project root
REQUIRED_DIRS = [
    "src",
    "tests",
    "data/raw",
    "data/processed",
    "data/splits",
    "results",
    "contracts",
    ".github/workflows",
    "data/raw/materials_project",
    "data/raw/nist",
    "data/raw/arxiv",
    "data/processed/intermediate",
    "results/plots",
    "results/models",
    "src/ingest",
    "src/preprocess",
    "src/model",
    "src/evaluate",
    "src/interpret",
    "src/utils",
    "src/cli",
    "src/config",
    "tests/unit",
    "tests/integration",
    "tests/contract",
]

def setup_directories(root_path: Path = None) -> bool:
    """
    Create the project directory structure as per the implementation plan.
    
    Required directories:
    - src/
    - tests/
    - data/raw
    - data/processed
    - data/splits
    - results
    - contracts/
    - .github/workflows/
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    # Define the base project directory (current working directory)
    base_dir = Path.cwd()
    
    # Define all required directories relative to the base directory
    required_dirs = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "data/splits",
        "results",
        "contracts",
        ".github/workflows"
    ]
    
    created_count = 0
    existing_count = 0
    failed_dirs = []
    
    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        try:
            if full_path.exists():
                logger.info(f"Directory already exists: {full_path}")
                existing_count += 1
            else:
                full_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {full_path}")
                created_count += 1
        except OSError as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            failed_dirs.append(str(full_path))
    
    # Summary
    logger.info(f"Directory setup complete. Created: {created_count}, Existing: {existing_count}")
    
    if failed_dirs:
        logger.error(f"Failed to create directories: {', '.join(failed_dirs)}")
        return False
    
    return True

if __name__ == "__main__":
    success = setup_directories()
    sys.exit(0 if success else 1)
