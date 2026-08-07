import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def verify_t001c_structure(base_path: Path) -> bool:
    """
    Verifies that the T001c directory structure has been created correctly.
    
    Required directories:
    - data/raw, data/curated, data/eval, data/validation
    - src/generation, src/filtering, src/training, src/evaluation, src/augmentation, src/utils
    - tests/unit, tests/integration
    
    Args:
        base_path: The root path to verify (typically projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/)
        
    Returns:
        True if all required directories exist, False otherwise
    """
    required_dirs = [
        # Data directories
        "data/raw",
        "data/curated",
        "data/eval",
        "data/validation",
        "data/control",
        "data/prompts",
        "data/baseline",
        "data/curated_augmented",
        
        # Source directories
        "src/generation",
        "src/filtering",
        "src/training",
        "src/evaluation",
        "src/augmentation",
        "src/utils",
        
        # Test directories
        "tests/unit",
        "tests/integration",
        
        # Additional required directories
        "logs",
        "models",
        "figures",
        "state",
        "docs"
    ]
    
    missing_dirs = []
    existing_dirs = []
    
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        if full_path.exists() and full_path.is_dir():
            existing_dirs.append(dir_path)
        else:
            missing_dirs.append(dir_path)
            logger.error(f"Missing directory: {full_path}")
    
    if missing_dirs:
        logger.error(f"Verification failed. Missing {len(missing_dirs)} directories:")
        for dir_path in missing_dirs:
            logger.error(f"  - {dir_path}")
        return False
    else:
        logger.info(f"Verification successful. All {len(existing_dirs)} required directories exist.")
        return True

def print_tree(base_path: Path, max_depth: int = 3):
    """
    Prints a tree view of the directory structure.
    
    Args:
        base_path: The root path to display
        max_depth: Maximum depth to display
    """
    logger.info(f"Directory structure for: {base_path}")
    
    def _print_tree(path: Path, prefix: str = "", depth: int = 0):
        if depth > max_depth:
            return
        
        items = sorted(path.iterdir())
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            connector = "└── " if is_last else "├── "
            logger.info(f"{prefix}{connector}{item.name}")
            
            if item.is_dir():
                extension = "    " if is_last else "│   "
                _print_tree(item, prefix + extension, depth + 1)
    
    _print_tree(base_path)

def main():
    """Main entry point for T001c structure verification."""
    # Determine the base path
    current_dir = Path(__file__).resolve().parent
    base_path = current_dir  # code/ directory is the base for this task
    
    logger.info(f"Verifying T001c structure in: {base_path}")
    
    success = verify_t001c_structure(base_path)
    
    if success:
        logger.info("T001c structure verification passed.")
        print("\nDirectory tree:")
        print_tree(base_path)
        return 0
    else:
        logger.error("T001c structure verification failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())