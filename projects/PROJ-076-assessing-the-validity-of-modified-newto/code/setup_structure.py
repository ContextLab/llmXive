"""
Project directory structure initialization for llmXive research pipeline.
Implements task T001a: Create project directory structure.
"""
import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_directories():
    """
    Create the required project directory structure.
    Returns a list of created directory paths.
    """
    # Define the base project root (current working directory)
    root = Path.cwd()

    # Define the directory structure to create
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "results",
        "tests",
        "state",
        # Additional subdirectories for code organization
        "code/models",
        "code/utils",
        "code/simulations",
    ]

    created_dirs = []

    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
            created_dirs.append(full_path)
        else:
            logger.info(f"Directory already exists: {full_path}")
            created_dirs.append(full_path)

    # Create placeholder __init__.py files to make directories Python packages
    # where appropriate (code, tests, code/models, code/utils, code/simulations)
    init_dirs = [
        "code",
        "tests",
        "code/models",
        "code/utils",
        "code/simulations",
    ]

    for dir_path in init_dirs:
        full_path = root / dir_path
        init_file = full_path / "__init__.py"
        if not init_file.exists():
            # Create a minimal __init__.py
            init_file.touch()
            logger.info(f"Created placeholder: {init_file}")

    # Create a placeholder README in data directories to indicate purpose
    data_readmes = {
        "data/raw": "Raw downloaded data (e.g., SPARC galaxy data). Do not modify.",
        "data/processed": "Processed and filtered data ready for analysis.",
    }

    for dir_path, description in data_readmes.items():
        full_path = root / dir_path
        readme_file = full_path / "README.md"
        if not readme_file.exists():
            readme_file.write_text(f"# {dir_path}\n\n{description}\n")
            logger.info(f"Created README: {readme_file}")

    return created_dirs

def main():
    """
    Entry point for directory structure creation.
    """
    logger.info("Starting project directory structure creation...")
    created = create_directories()
    logger.info(f"Successfully created/verified {len(created)} directories.")
    logger.info("Project structure is ready for implementation.")

    # Print summary
    print("\nProject Directory Structure:")
    print("-" * 40)
    for d in sorted(created):
        print(f"  {d}")
    print("-" * 40)

if __name__ == "__main__":
    main()
