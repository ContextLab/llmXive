"""
Script to create test directory structure for the project.
Creates: tests/unit, tests/integration, tests/contract
"""
import os
import logging
from pathlib import Path
from typing import List

from config import get_config
from code.utils.logger import get_pipeline_logger

logger = get_pipeline_logger()

def create_test_directories() -> List[Path]:
    """
    Create the required test directories if they do not exist.
    
    Returns:
        List[Path]: List of created directory paths.
    """
    base_dir = Path.cwd()
    test_dirs = [
        base_dir / "tests" / "unit",
        base_dir / "tests" / "integration",
        base_dir / "tests" / "contract",
    ]
    
    created = []
    for dir_path in test_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
            created.append(dir_path)
        else:
            logger.debug(f"Directory already exists: {dir_path}")
            
        # Create __init__.py files to make them proper Python packages
        init_file = dir_path / "__init__.py"
        if not init_file.exists():
            init_file.write_text("# Test package\n")
            logger.debug(f"Created __init__.py in: {dir_path}")
            
    return created

def main():
    """Main entry point for creating test directories."""
    logger.info("Starting test directory creation...")
    config = get_config()
    
    if not config:
        logger.warning("Configuration not loaded, proceeding with defaults.")
        
    created_dirs = create_test_directories()
    
    logger.info(f"Successfully created {len(created_dirs)} test directories.")
    for d in created_dirs:
        logger.info(f"  - {d}")
        
    return 0

if __name__ == "__main__":
    exit(main())
