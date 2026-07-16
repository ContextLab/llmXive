import os
from pathlib import Path
from code.utils.logger import get_logger

def main():
    """
    Create the root directory for the project.
    Task T001: Create `projects/PROJ-446-predicting-molecular-halide-binding-affi/` root directory.
    """
    logger = get_logger(__name__)
    
    # Define the project root path relative to the repository root
    # Assuming the script is run from the repository root or code/
    repo_root = Path(__file__).resolve().parent.parent
    project_root = repo_root / "projects" / "PROJ-446-predicting-molecular-halide-binding-affi"
    
    logger.info(f"Creating project root directory: {project_root}")
    
    try:
        project_root.mkdir(parents=True, exist_ok=True)
        logger.info(f"Successfully created directory: {project_root}")
        
        # Verify existence
        if project_root.exists() and project_root.is_dir():
            logger.info("Verification: Directory exists and is a directory.")
            return True
        else:
            logger.error("Verification failed: Directory does not exist or is not a directory.")
            return False
    except PermissionError:
        logger.error(f"Permission denied while creating directory: {project_root}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error while creating directory: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)