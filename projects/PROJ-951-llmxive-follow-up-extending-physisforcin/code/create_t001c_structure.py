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

def create_t001c_structure(base_path: Path) -> None:
    """
    Creates the specific module directories for task T001c.
    
    Directories to create:
    - data/raw, data/curated, data/eval, data/validation
    - src/generation, src/filtering, src/training, src/evaluation, src/augmentation, src/utils
    - tests/unit, tests/integration
    
    Args:
        base_path: The root path where directories should be created (typically projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/)
    """
    # Define the directory structure relative to base_path
    directories = [
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
    
    created_count = 0
    skipped_count = 0
    
    for dir_path in directories:
        full_path = base_path / dir_path
        try:
            if full_path.exists():
                logger.info(f"Directory already exists: {full_path}")
                skipped_count += 1
            else:
                full_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {full_path}")
                created_count += 1
                
                # Create __init__.py files for Python package directories
                if dir_path.startswith("src/") or dir_path.startswith("tests/"):
                    init_file = full_path / "__init__.py"
                    if not init_file.exists():
                        init_file.touch()
                        logger.debug(f"Created __init__.py: {init_file}")
                        
        except Exception as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            raise
    
    logger.info(f"Directory creation complete. Created: {created_count}, Skipped: {skipped_count}")
    
    # Create placeholder .gitkeep files in data directories to ensure they are tracked
    data_dirs = [
        "data/raw", "data/curated", "data/eval", "data/validation",
        "data/control", "data/prompts", "data/baseline", "data/curated_augmented"
    ]
    
    for dir_path in data_dirs:
        full_path = base_path / dir_path
        gitkeep = full_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            logger.debug(f"Created .gitkeep: {gitkeep}")

def main():
    """Main entry point for T001c directory creation."""
    # Determine the base path
    # The project root is expected to be: projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/
    current_dir = Path(__file__).resolve().parent
    base_path = current_dir  # code/ directory is the base for this task
    
    logger.info(f"Creating T001c structure in: {base_path}")
    
    try:
        create_t001c_structure(base_path)
        logger.info("T001c structure creation completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"T001c structure creation failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
