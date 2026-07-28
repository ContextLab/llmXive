"""
Project structure initialization script.
Creates the required directory hierarchy for the llmXive project.
"""
import os
import sys
import logging
from pathlib import Path
from utils.logging import get_logger

def create_directories(base_path: Path) -> None:
    """
    Create the required directory structure for the project.
    
    Args:
        base_path: The root directory where the structure should be created.
    """
    logger = get_logger(__name__)
    
    # Define the directory structure to create
    directories = [
        # Phase 1: Setup - Code structure
        "code",
        "code/data",
        "code/models",
        "code/eval",
        "code/utils",
        
        # Phase 1: Setup - Data structure
        "data",
        "data/raw",
        "data/processed",
        "data/splits",
        "data/schemas",
        
        # Phase 1: Setup - Tests structure
        "tests",
        "tests/contract",
        "tests/unit",
        "tests/integration",
        
        # Phase 1: Setup - Results structure
        "results",
        "results/reports",
        "results/plots"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {full_path}")
    
    logger.info(f"Directory structure setup complete. Created {created_count} new directories.")
    
    # Create __init__.py files in all code and tests directories
    for dir_path in directories:
        if dir_path.startswith("code") or dir_path.startswith("tests"):
            full_path = base_path / dir_path
            init_file = full_path / "__init__.py"
            if not init_file.exists():
                init_file.touch()
                logger.debug(f"Created empty __init__.py: {init_file}")

def main():
    """Main entry point for directory structure creation."""
    logger = get_logger(__name__)
    logger.info("Starting project directory structure creation...")
    
    # Determine the project root (parent of the code directory)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent
    
    logger.info(f"Project root detected at: {project_root}")
    
    create_directories(project_root)
    
    logger.info("Directory structure creation completed successfully.")

if __name__ == "__main__":
    main()
