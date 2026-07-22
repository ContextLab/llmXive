import os
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

def create_directory_structure() -> List[str]:
    """
    Creates the required project directory structure as defined in plan.md.
    Returns a list of created directory paths.
    """
    base_dir = Path(".")
    
    # Define the required directories relative to the project root
    directories = [
        base_dir / "code",
        base_dir / "data",
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "data" / "results",
        base_dir / "tests",
        base_dir / "contracts",
    ]

    created_paths = []
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
            created_paths.append(str(dir_path))
        else:
            logger.debug(f"Directory already exists: {dir_path}")
    
    # Create __init__.py files to ensure Python packages are recognized
    # specifically for the code/ and tests/ roots and subfolders
    package_dirs = [
        base_dir / "code",
        base_dir / "tests",
        base_dir / "data",
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "data" / "results",
        base_dir / "contracts",
    ]
    
    for pkg_dir in package_dirs:
        init_file = pkg_dir / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            logger.info(f"Created package marker: {init_file}")
        
        # Also ensure sub-packages in code/ have init files if they exist
        if pkg_dir == base_dir / "code":
            sub_packages = ["data", "models", "experiments", "analysis"]
            for sub_pkg in sub_packages:
                sub_path = pkg_dir / sub_pkg
                if sub_path.exists():
                    sub_init = sub_path / "__init__.py"
                    if not sub_init.exists():
                        sub_init.touch()
                        logger.info(f"Created package marker: {sub_init}")

    return created_paths

def main():
    """Entry point for directory structure creation."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    logger.info("Starting project directory structure creation...")
    created = create_directory_structure()
    
    if created:
        logger.info(f"Successfully created {len(created)} directories.")
    else:
        logger.info("All required directories already exist.")
    
    logger.info("Directory structure setup complete.")

if __name__ == "__main__":
    main()
