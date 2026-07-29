import os
import logging
from pathlib import Path
from typing import List, Tuple

logger = logging.getLogger(__name__)

def ensure_data_directories(base_path: Path) -> None:
    """
    Create the required directory structure for the project.
    
    Creates:
    - projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech/
      - code/
      - data/
        - raw/
        - processed/
        - results/
      - tests/
      - specs/
    
    Args:
        base_path: The root directory where the project structure will be created.
    """
    project_root = base_path / "projects" / "PROJ-877-llmxive-follow-up-extending-mellum2-tech"
    
    directories = [
        project_root,
        project_root / "code",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "results",
        project_root / "tests",
        project_root / "specs",
        project_root / "figures",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {directory}")

def generate_init_files(base_path: Path) -> None:
    """
    Create __init__.py files in all Python package directories.
    
    Args:
        base_path: The root directory of the project.
    """
    project_root = base_path / "projects" / "PROJ-877-llmxive-follow-up-extending-mellum2-tech"
    python_dirs = [
        project_root / "code",
        project_root / "code" / "analysis",
        project_root / "code" / "data",
        project_root / "code" / "inference",
        project_root / "code" / "utils",
        project_root / "code" / "contracts",
        project_root / "tests",
        project_root / "tests" / "unit",
    ]
    
    for directory in python_dirs:
        init_file = directory / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            logger.info(f"Created __init__.py: {init_file}")

def main():
    """
    Main entry point for directory setup.
    Creates the full project structure and initializes Python packages.
    """
    # Use current working directory as base
    base_path = Path.cwd()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(base_path / "project_init.log"),
            logging.StreamHandler()
        ]
    )
    
    logger.info("Starting project directory initialization...")
    
    ensure_data_directories(base_path)
    generate_init_files(base_path)
    
    # Generate directory listing for verification
    project_root = base_path / "projects" / "PROJ-877-llmxive-follow-up-extending-mellum2-tech"
    log_path = base_path / "project_init.log"
    
    with open(log_path, 'a') as f:
        f.write("\n=== Directory Structure Verification ===\n")
        f.write(f"Project Root: {project_root}\n\n")
        for root, dirs, files in os.walk(project_root):
            level = root.replace(str(project_root), '').count(os.sep)
            indent = ' ' * 2 * level
            f.write(f'{indent}{os.path.basename(root)}/\n')
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                f.write(f'{subindent}{file}\n')
        f.write("\n=== Initialization Complete ===\n")
    
    logger.info(f"Project structure created successfully. Log written to: {log_path}")

if __name__ == "__main__":
    main()
