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

def verify_t001c_structure(base_path: Path) -> bool:
    """
    Verifies that all required directories for T001c exist.
    
    Required directories:
    - data/raw, data/curated, data/eval, data/validation
    - src/generation, src/filtering, src/training, src/evaluation, src/augmentation, src/utils
    - tests/unit, tests/integration
    
    Args:
        base_path: The base project directory
        
    Returns:
        bool: True if all directories exist, False otherwise
    """
    required_dirs = [
        "data/raw",
        "data/curated",
        "data/eval",
        "data/validation",
        "src/generation",
        "src/filtering",
        "src/training",
        "src/evaluation",
        "src/augmentation",
        "src/utils",
        "tests/unit",
        "tests/integration"
    ]
    
    missing = []
    existing = []
    
    for dir_name in required_dirs:
        dir_path = base_path / dir_name
        if dir_path.exists() and dir_path.is_dir():
            existing.append(dir_name)
        else:
            missing.append(dir_name)
            logger.error(f"Missing directory: {dir_path}")
    
    if missing:
        logger.error(f"Verification FAILED. Missing {len(missing)} directories:")
        for d in missing:
            logger.error(f"  - {d}")
        return False
    else:
        logger.info(f"Verification PASSED. All {len(existing)} required directories exist.")
        return True

def print_tree(base_path: Path, max_depth: int = 2):
    """Prints a simple tree view of the directory structure."""
    def _print_dir(path: Path, prefix: str, depth: int):
        if depth > max_depth:
            return
        
        try:
            entries = sorted(path.iterdir())
        except PermissionError:
            return
        
        for i, entry in enumerate(entries):
            is_last = (i == len(entries) - 1)
            connector = "└── " if is_last else "├── "
            print(f"{prefix}{connector}{entry.name}")
            
            if entry.is_dir():
                new_prefix = prefix + ("    " if is_last else "│   ")
                _print_dir(entry, new_prefix, depth + 1)
    
    print(f"\nDirectory structure for: {base_path}")
    print("=" * 50)
    _print_dir(base_path, "", 0)
    print("=" * 50 + "\n")

def main():
    """Main entry point for T001c verification."""
    if len(sys.argv) > 1:
        base_path = Path(sys.argv[1])
    else:
        base_path = Path.cwd()
        
    logger.info(f"Verifying T001c structure in: {base_path}")
    
    if not base_path.exists():
        logger.error(f"Base path does not exist: {base_path}")
        sys.exit(1)
    
    success = verify_t001c_structure(base_path)
    
    # Optionally print the tree for visual confirmation
    # print_tree(base_path)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()