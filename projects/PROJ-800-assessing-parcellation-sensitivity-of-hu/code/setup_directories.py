import os
import sys
from pathlib import Path
from utils.logger import get_logger, ConfigurationError

logger = get_logger(__name__)

def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory ensured: {path}")
    except OSError as e:
        logger.error(f"Failed to create directory {path}: {e}")
        raise ConfigurationError(f"Failed to create directory {path}: {e}") from e

def main() -> int:
    """
    Create the project directory structure for PROJ-800-assessing-parcellation-sensitivity-of-hu.
    
    Structure:
    projects/PROJ-800-assessing-parcellation-sensitivity-of-hu/
    ├── code/
    ├── tests/
    └── data/
        ├── raw/
        ├── processed/
        └── results/
    
    Returns:
        int: 0 on success, 1 on failure.
    """
    project_root = Path("projects/PROJ-800-assessing-parcellation-sensitivity-of-hu")
    
    # Define the directory structure to create
    directories = [
        project_root,
        project_root / "code",
        project_root / "tests",
        project_root / "data",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "results",
    ]
    
    logger.info(f"Creating project directory structure at: {project_root}")
    
    for directory in directories:
        ensure_directory(directory)
    
    # Verification: List the directory structure
    logger.info("Verifying directory structure...")
    try:
        # Using os.walk to simulate ls -R behavior for verification
        for root, dirs, files in os.walk(project_root):
            level = root.replace(str(project_root), '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            sub_indent = ' ' * 2 * (level + 1)
            for file in files:
                print(f"{sub_indent}{file}")
            # Sort dirs to ensure consistent output
            dirs.sort()
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return 1
    
    logger.info("Directory structure created and verified successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
