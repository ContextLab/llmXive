import os
from pathlib import Path
from config import get_project_root, get_raw_data_dir, get_processed_data_dir, get_consent_dir, get_specs_dir, get_contracts_dir, get_figures_dir
from logging_config import setup_logging, get_logger

def create_directories():
    """
    Create the project directory hierarchy:
    - code/
    - data/raw/
    - data/processed/
    - data/consent/
    - data/results/ (implied by get_results_dir usage elsewhere, ensuring it exists)
    - figures/
    - tests/
    - specs/ (already exists per task description, but we ensure it)
    - contracts/ (already exists per task description, but we ensure it)
    
    Also creates a .gitkeep in data directories to ensure they are tracked by git.
    """
    logger = get_logger()
    logger.info("Starting directory structure creation...")

    project_root = get_project_root()
    
    # Define directories to create
    # We use the helper functions from config.py to ensure consistency
    # Note: get_project_root returns the root, so we construct sub-paths relative to it
    # if the helpers don't return absolute paths including the root.
    # Based on typical usage, these helpers return Path objects relative to project root or absolute.
    # Let's assume they return absolute paths or paths relative to project_root.
    # To be safe, we will resolve them against project_root if they are relative.
    
    dirs_to_create = [
        get_project_root() / "code",
        get_project_root() / "data" / "raw",
        get_project_root() / "data" / "processed",
        get_project_root() / "data" / "consent",
        get_project_root() / "data" / "results",
        get_project_root() / "figures",
        get_project_root() / "tests",
        get_project_root() / "specs",
        get_project_root() / "contracts",
    ]
    
    # Ensure specific data subdirs exist via config helpers if they exist, 
    # otherwise rely on the list above.
    # The config helpers likely return absolute paths or paths relative to project root.
    # We will just create the explicit list above.
    
    created_count = 0
    for dir_path in dirs_to_create:
        dir_path = Path(dir_path)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {dir_path}")
        
        # Create .gitkeep in data subdirectories
        if dir_path.parent.name == "data" or dir_path.name == "data":
            gitkeep = dir_path / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.touch()
                logger.info(f"Created .gitkeep in: {dir_path}")

    logger.info(f"Directory structure creation complete. {created_count} new directories created.")
    return True

def main():
    setup_logging()
    success = create_directories()
    if success:
        print("Project structure created successfully.")
        return 0
    else:
        print("Failed to create project structure.")
        return 1

if __name__ == "__main__":
    exit(main())
