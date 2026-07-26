import os
from pathlib import Path
from config import PROJECT_ROOT
from utils.logger import get_logger

logger = get_logger(__name__)

def setup_data_directories():
    """
    Creates the required data directory structure for the project.
    This includes prompts, models, and specific output directories for base and RL-unified runs.
    Also creates .gitkeep files to ensure directories are tracked in version control.
    """
    base_data_path = Path(PROJECT_ROOT) / "data"
    
    directories = [
        "prompts",
        "models",
        "outputs/base",
        "outputs/rl_unified",
        "raw",
        "processed",
        "logs"
    ]

    created_count = 0
    
    for dir_path in directories:
        full_path = base_data_path / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            logger.debug(f"Directory ensured: {full_path}")
            
            # Create .gitkeep to ensure directory is tracked by git
            gitkeep_path = full_path / ".gitkeep"
            if not gitkeep_path.exists():
                gitkeep_path.touch()
                logger.debug(f"Created .gitkeep in: {full_path}")
                
        except OSError as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            raise

    logger.info(f"Data directory structure setup complete. {created_count} directories ensured.")
    return True

def main():
    logger.info("Starting data directory structure setup...")
    setup_data_directories()
    logger.info("Data directory structure setup finished.")

if __name__ == "__main__":
    main()
