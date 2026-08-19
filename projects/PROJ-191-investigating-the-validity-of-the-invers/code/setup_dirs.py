"""
Setup script to create the full project directory tree for PROJ-191.
This script ensures all required subdirectories exist at the repository root.
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

def main():
    """
    Create the full project directory tree at the repository root.
    
    Target root: projects/PROJ-191-investigating-the-invers/
    Required subdirectories:
    - code/, tests/, data/, docs/
    - code/data/, code/models/, code/inference/, code/robustness/, code/utils/
    - data/raw/, data/processed/, data/results/
    - tests/unit/, tests/contract/, tests/integration/
    """
    # Determine project root (assuming script is in code/ directory)
    script_path = Path(__file__).resolve()
    code_dir = script_path.parent
    project_root = code_dir.parent.parent / "projects" / "PROJ-191-investigating-the-validity-of-the-invers"
    
    # Define all required directories relative to project_root
    directories = [
        # Top-level directories
        "code",
        "tests",
        "data",
        "docs",
        
        # Code subdirectories
        "code/data",
        "code/models",
        "code/inference",
        "code/robustness",
        "code/utils",
        
        # Data subdirectories
        "data/raw",
        "data/processed",
        "data/results",
        
        # Test subdirectories
        "tests/unit",
        "tests/contract",
        "tests/integration",
    ]
    
    # Create directories
    created_count = 0
    existing_count = 0
    failed_count = 0
    
    for dir_path in directories:
        full_path = project_root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            if full_path.exists() and full_path.is_dir():
                if any(full_path.iterdir()):
                    logger.info(f"Directory already exists (non-empty): {full_path}")
                    existing_count += 1
                else:
                    logger.info(f"Created directory: {full_path}")
                    created_count += 1
            else:
                logger.error(f"Failed to create directory: {full_path}")
                failed_count += 1
        except Exception as e:
            logger.error(f"Error creating directory {full_path}: {e}")
            failed_count += 1
    
    # Summary
    logger.info(f"Directory setup complete.")
    logger.info(f"Created: {created_count}, Existing: {existing_count}, Failed: {failed_count}")
    
    if failed_count > 0:
        logger.error("Some directories failed to create. Check logs for details.")
        sys.exit(1)
    else:
        logger.info("All required directories are ready.")
        sys.exit(0)

if __name__ == "__main__":
    main()