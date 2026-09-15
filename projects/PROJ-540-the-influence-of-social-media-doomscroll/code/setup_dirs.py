"""
Directory setup module for the llmXive automated science pipeline.
Creates the required project directory structure.
"""
import os
import sys
from pathlib import Path
import logging

# Configure basic logging if not already configured
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_directories(base_path: str = ".") -> None:
    """
    Create the required directory structure for the project.
    
    Args:
        base_path: The root directory where structure will be created.
    """
    base = Path(base_path)
    
    # Define required directories relative to the project root
    required_dirs = [
        "data/raw",
        "data/processed",
        "code",
        "outputs",
        "tests",
        "projects/PROJ-540-the-influence-of-social-media-doomscroll"
    ]
    
    created_count = 0
    
    for dir_path in required_dirs:
        full_path = base / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {full_path}")
    
    # Create __init__.py files in Python package directories
    package_dirs = [
        "code",
        "tests",
        "projects/PROJ-540-the-influence-of-social-media-doomscroll"
    ]
    
    for pkg_dir in package_dirs:
        init_file = base / pkg_dir / "__init__.py"
        if not init_file.exists():
          # Write a minimal docstring to make it a valid package
          with open(init_file, "w", encoding="utf-8") as f:
              f.write(f'"""\nPackage for {pkg_dir}.\n"""\n')
          logger.info(f"Created __init__.py: {init_file}")
          created_count += 1
        else:
            logger.debug(f"__init__.py already exists: {init_file}")
    
    # Create placeholder .gitkeep files in data directories to ensure they persist in git
    data_dirs = [
        "data/raw",
        "data/processed"
    ]
    
    for data_dir in data_dirs:
        keep_file = base / data_dir / ".gitkeep"
        if not keep_file.exists():
            with open(keep_file, "w", encoding="utf-8") as f:
                f.write("# Data directory - keep empty until data is ingested\n")
            logger.info(f"Created .gitkeep: {keep_file}")
            created_count += 1

    logger.info(f"Directory setup complete. Created/verified {created_count} items.")

def main():
    """Entry point for script execution."""
    logger.info("Starting directory setup...")
    create_directories(".")
    logger.info("Directory setup finished successfully.")

if __name__ == "__main__":
    main()
