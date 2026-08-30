import os
import sys
import venv
import subprocess
from pathlib import Path
import logging

from utils.logging import get_logger

logger = get_logger(__name__)

def setup_venv(project_root: str) -> bool:
    """
    Create a Python virtual environment in the specified project root.
    The environment is created at <project_root>/venv.
    
    Args:
        project_root: Path to the project root directory.
        
    Returns:
        True if the virtual environment was created successfully, False otherwise.
    """
    venv_path = Path(project_root) / "venv"
    
    if venv_path.exists():
        logger.info(f"Virtual environment already exists at {venv_path}")
        # Verify bin/activate exists
        activate_script = venv_path / "bin" / "activate"
        if activate_script.exists():
            logger.info("Verification: bin/activate exists.")
            return True
        else:
            logger.warning("Virtual environment exists but bin/activate is missing. Recreating.")
            # Remove existing incomplete venv to recreate
            import shutil
            shutil.rmtree(venv_path)
    
    logger.info(f"Creating virtual environment at {venv_path}...")
    
    try:
        venv.create(venv_path, with_pip=True)
        
        # Verify bin/activate exists
        activate_script = venv_path / "bin" / "activate"
        if not activate_script.exists():
            logger.error("Virtual environment created but bin/activate is missing.")
            return False
        
        logger.info("Virtual environment created successfully.")
        logger.info(f"Verification: bin/activate exists at {activate_script}")
        
        # Upgrade pip to ensure latest version
        logger.info("Upgrading pip...")
        subprocess.run(
            [str(venv_path / "bin" / "pip"), "install", "--upgrade", "pip"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        logger.info("Pip upgraded successfully.")
        
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to upgrade pip: {e}")
        return False
    except Exception as e:
        logger.error(f"Error creating virtual environment: {e}")
        return False

def main():
    """Main entry point for the virtual environment setup script."""
    # Determine project root based on the task specification
    # The project root is: projects/PROJ-487-the-impact-of-social-media-doomscrolling/
    # We assume the script is run from the repository root or the project root is passed
    
    project_root = Path.cwd()
    
    # Check if we are inside the specific project directory
    # If the current directory is the project root, use it
    # Otherwise, try to find the project root relative to the script location
    script_dir = Path(__file__).resolve().parent
    parent_dir = script_dir.parent.parent.parent.parent # code -> project root (assuming code/ is at root)
    
    # Adjust path logic: The task specifies the project root is:
    # projects/PROJ-487-the-impact-of-social-media-doomscrolling/
    # If the script is at code/setup_venv.py, the project root is 2 levels up?
    # Let's assume the script is run from the repository root where 'projects' exists.
    
    # Attempt to locate the specific project directory
    if (Path("projects") / "PROJ-487-the-impact-of-social-media-doomscrolling").exists():
        project_root = Path("projects") / "PROJ-487-the-impact-of-social-media-doomscrolling"
    elif script_dir.name == "code" and (script_dir.parent / "projects" / "PROJ-487-the-impact-of-social-media-doomscrolling").exists():
        project_root = script_dir.parent / "projects" / "PROJ-487-the-impact-of-social-media-doomscrolling"
    else:
        # Fallback to current working directory if specific project not found
        logger.warning(f"Specific project directory not found. Using current directory: {project_root}")
    
    logger.info(f"Project root identified as: {project_root}")
    
    if not project_root.exists():
        logger.error(f"Project root does not exist: {project_root}")
        sys.exit(1)
    
    success = setup_venv(str(project_root))
    
    if success:
        logger.info("Task T004 completed successfully: Virtual environment created and verified.")
        sys.exit(0)
    else:
        logger.error("Task T004 failed: Virtual environment creation or verification failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()