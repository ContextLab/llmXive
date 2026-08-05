"""
Setup script for creating test directory structure with .gitkeep files.

This script creates the necessary directory structure for unit and contract
tests, ensuring proper organization for the project's testing infrastructure.
"""
import os
import sys
from pathlib import Path
from utils.logging import get_logger

def create_test_directories(base_dir: Path) -> bool:
    """
    Create test directory structure with .gitkeep files.
    
    Args:
        base_dir: The base directory where tests/ should be created.
        
    Returns:
        True if all directories were created successfully, False otherwise.
    """
    logger = get_logger(__name__)
    
    test_dirs = [
        base_dir / "tests" / "contract",
        base_dir / "tests" / "unit",
    ]
    
    success = True
    for dir_path in test_dirs:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
            
            # Create .gitkeep file
            gitkeep_path = dir_path / ".gitkeep"
            gitkeep_path.touch()
            logger.info(f"Created .gitkeep file: {gitkeep_path}")
            
        except OSError as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            success = False
    
    return success

def verify_test_directories(base_dir: Path) -> bool:
    """
    Verify that test directories and .gitkeep files exist.
    
    Args:
        base_dir: The base directory to verify.
        
    Returns:
        True if all required directories and files exist, False otherwise.
    """
    logger = get_logger(__name__)
    
    required_paths = [
        base_dir / "tests" / "contract" / ".gitkeep",
        base_dir / "tests" / "unit" / ".gitkeep",
    ]
    
    all_exist = True
    for path in required_paths:
        if path.exists():
            logger.info(f"Verified: {path}")
        else:
            logger.error(f"Missing: {path}")
            all_exist = False
    
    return all_exist

def main() -> int:
    """
    Main entry point for the script.
    
    Returns:
        Exit code: 0 for success, 1 for failure.
    """
    logger = get_logger(__name__)
    logger.info("Starting test directory setup...")
    
    # Determine the project root (assuming script is in code/)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    logger.info(f"Project root: {project_root}")
    
    # Create directories
    if not create_test_directories(project_root):
        logger.error("Failed to create test directories")
        return 1
    
    # Verify creation
    if not verify_test_directories(project_root):
        logger.error("Verification failed")
        return 1
    
    logger.info("Test directory setup completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())