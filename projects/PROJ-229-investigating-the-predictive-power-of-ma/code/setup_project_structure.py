import os
from pathlib import Path
from config import get_config
from code.utils.logger import get_pipeline_logger
from code.utils.error_handling import handle_error, ConfigError

def create_project_structure():
    """
    Create the necessary directory structure for the code modules.
    Specifically creates: code/data, code/models, code/utils
    """
    config = get_config()
    logger = get_pipeline_logger()
    
    # Base project root is assumed to be the current working directory or defined in config
    # We construct paths relative to the project root
    project_root = Path.cwd()
    
    # Define the directories to create based on the task requirement
    code_dirs = [
        project_root / "code" / "data",
        project_root / "code" / "models",
        project_root / "code" / "utils"
    ]
    
    created_count = 0
    for dir_path in code_dirs:
        try:
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {dir_path}")
                created_count += 1
            else:
                logger.debug(f"Directory already exists: {dir_path}")
        except Exception as e:
            handle_error(ConfigError, f"Failed to create directory {dir_path}: {str(e)}", logger)
    
    logger.info(f"Project structure setup complete. Created {created_count} new directories.")
    return True

def main():
    """Entry point for script execution."""
    create_project_structure()

if __name__ == "__main__":
    main()