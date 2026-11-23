"""
Task T001c: Create specific module directories for the llmXive project.

This script creates the detailed directory structure required for:
- Data management (raw, curated, eval, validation)
- Source modules (generation, filtering, training, evaluation, augmentation, utils)
- Test suites (unit, integration)

Dependency: T001b (base src/, tests/, data/ must exist)
"""
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_t001c_structure(base_path: Path) -> bool:
    """
    Create the specific module directories for Task T001c.
    
    Args:
        base_path: The root directory where the project structure should be created.
                   Expected to be: projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    if not base_path.exists():
        logger.error(f"Base path does not exist: {base_path}")
        return False

    # Define the directory structure relative to base_path
    directories = [
        # Data directories
        "data/raw",
        "data/curated",
        "data/eval",
        "data/validation",
        "data/control",
        "data/baseline",
        "data/prompts",
        
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
    ]
    
    success = True
    created_count = 0
    
    for dir_path in directories:
        full_path = base_path / dir_path
        try:
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {full_path}")
                created_count += 1
            else:
                logger.debug(f"Directory already exists: {full_path}")
            
            # Create __init__.py files in Python package directories
            if dir_path.startswith("src/") or dir_path.startswith("tests/"):
                init_file = full_path / "__init__.py"
                if not init_file.exists():
                    init_file.touch()
                    logger.debug(f"Created __init__.py: {init_file}")
                    
        except OSError as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            success = False
        except Exception as e:
            logger.error(f"Unexpected error creating {full_path}: {e}")
            success = False
    
    logger.info(f"Directory creation complete. Created {created_count} new directories.")
    return success

def main():
    """Main entry point for T001c directory creation."""
    # Determine the base path
    # Expected: projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/
    project_root = Path(__file__).resolve().parent.parent
    base_path = project_root / "projects" / "PROJ-951-llmxive-follow-up-extending-physisforcin" / "code"
    
    logger.info(f"Base path for T001c: {base_path}")
    
    if create_t001c_structure(base_path):
        logger.info("T001c completed successfully.")
        return 0
    else:
        logger.error("T001c failed to create all directories.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
