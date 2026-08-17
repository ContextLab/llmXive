"""
Script to initialize the code/ directory structure for the llmXive project.
Creates the required subdirectories for data generation, model training, simulation, and analysis.
"""
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

def get_project_root() -> Path:
    """
    Determine the project root directory.
    Assumes the script is run from the project root or a subdirectory.
    """
    current_file = Path(__file__).resolve()
    # Traverse up to find the directory containing 'requirements.txt' or 'state/'
    # For simplicity, we assume the script is in code/ and root is parent
    return current_file.parent.parent

def create_directories(root_dir: Path) -> None:
    """
    Create the required directory structure under code/.
    """
    code_dir = root_dir / "code"
    
    # Ensure the root code directory exists
    code_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directory exists: {code_dir}")

    # Define subdirectories
    subdirs = [
        "data_generation",
        "model_training",
        "simulation",
        "analysis"
    ]

    for subdir_name in subdirs:
        subdir_path = code_dir / subdir_name
        subdir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created/verified directory: {subdir_path}")

    # Create __init__.py files to make them Python packages
    for subdir_name in subdirs:
        init_path = code_dir / subdir_name / "__init__.py"
        if not init_path.exists():
            init_path.touch()
            logger.info(f"Created package marker: {init_path}")

def verify_structure(root_dir: Path) -> bool:
    """
    Verify that the required directory structure exists.
    Returns True if all directories are present, False otherwise.
    """
    code_dir = root_dir / "code"
    required_subdirs = [
        "data_generation",
        "model_training",
        "simulation",
        "analysis"
    ]
    
    all_present = True
    for subdir_name in required_subdirs:
        subdir_path = code_dir / subdir_name
        if not subdir_path.is_dir():
            logger.error(f"Missing directory: {subdir_path}")
            all_present = False
        else:
            logger.info(f"Verified directory: {subdir_path}")
    
    return all_present

def main() -> int:
    """
    Main entry point for the script.
    """
    try:
        root = get_project_root()
        logger.info(f"Project root detected at: {root}")
        
        create_directories(root)
        
        if verify_structure(root):
            logger.info("Directory structure initialization successful.")
            return 0
        else:
            logger.error("Directory structure verification failed.")
            return 1
    except Exception as e:
        logger.exception(f"An error occurred during initialization: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())