import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def create_project_structure():
    """
    Create the required directory structure for the project.
    Creates: code/, data/raw/, data/processed/, tests/, docs/, state/projects/
    """
    base_dir = Path(__file__).resolve().parent.parent
    
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "tests",
        "docs",
        "state/projects"
    ]
    
    created_dirs = []
    for dir_name in directories:
        dir_path = base_dir / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(dir_path))
            logger.info(f"Created directory: {dir_path}")
        else:
            logger.info(f"Directory already exists: {dir_path}")
    
    # Verify structure
    logger.info("Verifying directory structure...")
    for dir_name in directories:
        dir_path = base_dir / dir_name
        if dir_path.exists() and dir_path.is_dir():
            logger.info(f"Verified: {dir_path} exists")
        else:
            logger.error(f"Verification failed: {dir_path} does not exist")
            raise FileNotFoundError(f"Required directory {dir_path} could not be created or verified.")
    
    logger.info("Project structure setup complete.")
    return created_dirs

def main():
    """Main entry point for project structure setup."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    try:
        create_project_structure()
        logger.info("SUCCESS: Project structure created and verified.")
    except Exception as e:
        logger.error(f"FAILED: {e}")
        raise

if __name__ == "__main__":
    main()