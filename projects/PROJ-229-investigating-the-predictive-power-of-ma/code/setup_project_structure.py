import os
from pathlib import Path
from config import get_config
from code.utils.logger import get_pipeline_logger
from code.utils.error_handling import handle_error, ConfigError

def create_project_structure():
    """
    Creates the required directory structure for the project.
    Specifically handles the creation of code directories:
    - code/data
    - code/models
    - code/utils
    
    Also ensures tests directories exist as per T001c context, 
    though this specific task focuses on code directories.
    """
    config = get_config()
    project_root = Path(config.get('project_root', '.'))
    logger = get_pipeline_logger()
    
    # Define directories to create for T001b
    code_dirs = [
        'code/data',
        'code/models',
        'code/utils'
    ]
    
    # Also include test dirs to ensure full structure if needed by T001c context
    # but primarily focusing on code dirs as per task description
    test_dirs = [
        'tests/unit',
        'tests/integration',
        'tests/contract'
    ]
    
    all_dirs = code_dirs + test_dirs
    
    created_count = 0
    for dir_path in all_dirs:
        full_path = project_root / dir_path
        try:
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {full_path}")
                created_count += 1
            else:
                logger.debug(f"Directory already exists: {full_path}")
        except OSError as e:
            handle_error(ConfigError(f"Failed to create directory {full_path}: {e}"), logger)
            return False
    
    logger.info(f"Project structure setup complete. Created {created_count} directories.")
    return True

def main():
    """Entry point for script execution."""
    logger = get_pipeline_logger()
    logger.info("Starting project structure creation (T001b, T001c)...")
    success = create_project_structure()
    if success:
        logger.info("Project structure creation successful.")
    else:
        logger.error("Project structure creation failed.")
        exit(1)

if __name__ == "__main__":
    main()
