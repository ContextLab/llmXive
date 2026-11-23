import sys
import logging
from pathlib import Path
from src.config import setup_logging

REQUIRED_DIRS = [
    "src/data",
    "src/models",
    "src/analysis",
    "data/raw",
    "data/processed",
    "data/interim",
    "tests/contract",
    "tests/unit",
    "tests/integration",
    "docs",
]

def verify_structure(root_dir: Path) -> bool:
    """
    Verify that all required project directories exist.
    
    Args:
        root_dir: The root directory of the project.
        
    Returns:
        bool: True if all directories exist, False otherwise.
    """
    logger = logging.getLogger(__name__)
    all_present = True
    
    for dir_name in REQUIRED_DIRS:
        dir_path = root_dir / dir_name
        if dir_path.exists() and dir_path.is_dir():
            logger.info(f"✓ Found: {dir_path}")
        else:
            logger.error(f"✗ Missing: {dir_path}")
            all_present = False
            
    return all_present

def main():
    """Entry point for the verification script."""
    logger = setup_logging()
    root = Path(__file__).resolve().parent.parent.parent
    
    logger.info("Verifying project structure...")
    success = verify_structure(root)
    
    if success:
        logger.info("Project structure verification: PASSED")
        return 0
    else:
        logger.error("Project structure verification: FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
