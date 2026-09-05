import os
import sys
from pathlib import Path

def create_directory_structure(base_dir: Path) -> None:
    """
    Creates the standard project directory structure for llmXive science pipeline.
    
    Directories created:
    - code/
    - data/raw/
    - data/processed/
    - data/interim/
    - tests/unit/
    - tests/integration/
    
    Args:
        base_dir: The root directory where the structure will be created.
    """
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/interim",
        "tests/unit",
        "tests/integration",
    ]
    
    created = []
    for dir_path in directories:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        created.append(str(full_path))
        print(f"Created directory: {full_path}")
    
    return created

def main() -> None:
    """Entry point for project structure initialization."""
    # Determine the project root based on the task description
    # The task specifies the project is at: projects/PROJ-424-investigating-the-predictive-power-of-mo/
    # However, since we are running from within the project context, we assume the current 
    # working directory or the parent of this script is the project root.
    
    # Strategy: Look for the project marker or use the script's parent directory
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent if script_path.name == "setup_project.py" else script_path.parent
    
    # If we are in code/setup_project.py, the project root is two levels up
    if "code" in script_path.relative_to(project_root).parts:
        project_root = script_path.parent.parent
    
    print(f"Initializing project structure at: {project_root}")
    
    try:
        created_dirs = create_directory_structure(project_root)
        print(f"Successfully created {len(created_dirs)} directories.")
        
        # Log success
        from utils.logging import get_logger
        logger = get_logger(__name__)
        logger.info("Project structure initialized successfully", extra={
            "event_type": "project_init",
            "directories": created_dirs
        })
        
    except Exception as e:
        print(f"Error creating directory structure: {e}")
        from utils.logging import get_logger
        logger = get_logger(__name__)
        logger.error("Failed to initialize project structure", extra={
            "event_type": "project_init_failed",
            "error": str(e)
        })
        sys.exit(1)

if __name__ == "__main__":
    main()