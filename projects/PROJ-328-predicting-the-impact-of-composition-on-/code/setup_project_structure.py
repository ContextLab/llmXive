import os
import sys
import logging
from pathlib import Path
from utils.logging_config import get_logger

# Define the required directory structure relative to the project root
DIRECTORIES = [
    # Data directories
    "data/raw",
    "data/processed",
    "data/outputs",
    "data/config",
    "data/checksums", # implied by checksums.txt location
    
    # Code directories
    "code/ingestion",
    "code/features",
    "code/models",
    "code/evaluation",
    "code/visualization",
    "code/utils",
    
    # Test directories
    "tests/contract",
    "tests/integration",
    "tests/unit", # Added for robustness based on task list
    
    # Misc project structure
    "logs",
    "docs",
    "models"
]

def setup_directories(base_path: Path) -> list:
    """
    Creates the required directory structure if it does not exist.
    Returns a list of created paths.
    """
    created = []
    for dir_path in DIRECTORIES:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path))
        else:
            # Log if it already exists but we are verifying
            pass
    return created

def verify_directory_structure(base_path: Path) -> dict:
    """
    Verifies that all required directories exist.
    Returns a dictionary with 'success' (bool) and 'missing' (list).
    """
    missing = []
    for dir_path in DIRECTORIES:
        full_path = base_path / dir_path
        if not full_path.exists():
            missing.append(dir_path)
    
    return {
        "success": len(missing) == 0,
        "missing": missing,
        "checked_count": len(DIRECTORIES),
        "verified_count": len(DIRECTORIES) - len(missing)
    }

def main():
    logger = get_logger(__name__)
    logger.info("Starting project directory structure setup.")
    
    # Determine project root (assuming script is run from root or code/)
    # We look for the 'data' directory or assume current working directory
    current_dir = Path.cwd()
    
    # Heuristic: if we are in code/, go up one level. If data/ exists, we are likely at root.
    if (current_dir / "data").exists() or (current_dir / "code").exists():
        root_path = current_dir
    else:
        # Fallback: assume current dir is root
        root_path = current_dir
        
    logger.info(f"Using project root: {root_path}")
    
    # Setup
    created = setup_directories(root_path)
    logger.info(f"Created {len(created)} directories.")
    for p in created:
        logger.info(f"  Created: {p}")
        
    # Verify
    verification = verify_directory_structure(root_path)
    
    if verification["success"]:
        logger.info("Directory structure verification PASSED.")
        logger.info(f"Checked {verification['checked_count']} directories.")
        return 0
    else:
        logger.error("Directory structure verification FAILED.")
        logger.error(f"Missing directories: {verification['missing']}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
