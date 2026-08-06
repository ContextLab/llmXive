import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def create_structure(root_path: Path) -> None:
    """
    Creates the required project directory structure.
    
    Args:
        root_path: The root directory of the project.
    """
    directories = [
        "src",
        "tests",
        "data",
        "data/raw",
        "data/processed",
        "data/results",
        "data/logs",
        "state",
        "specs",
        "contracts",
        "code",
        "code/src",
        "code/tests",
        "code/data",
        "code/scripts",
        "code/utils",
        "code/models",
        "code/analysis",
        "code/results",
        "code/logs",
        "code/state",
    ]
    
    created_count = 0
    for dir_name in directories:
        full_path = root_path / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {full_path}")
    
    logger.info(f"Project structure setup complete. Created {created_count} new directories.")

def main():
    """
    Main entry point for the project structure setup script.
    Determines the project root and creates the directory structure.
    """
    # Determine project root: assume script is in code/ or root, look for 'code' or 'src'
    current_dir = Path.cwd()
    
    # Heuristic: if we are in 'code/', go up one level. If not, assume current is root.
    if current_dir.name == "code" and (current_dir.parent / "src").exists():
        root = current_dir.parent
    elif (current_dir / "src").exists():
        root = current_dir
    elif (current_dir / "code").exists():
        root = current_dir
    else:
        # Fallback: use current directory
        root = current_dir
    
    logger.info(f"Using project root: {root}")
    
    create_structure(root)

if __name__ == "__main__":
    main()