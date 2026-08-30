import os
import sys
import venv
import subprocess
from pathlib import Path
import logging

# Ensure we can import utils.logging if needed, though we use basic logging here
# to avoid circular dependencies during initial setup.
logger = logging.getLogger(__name__)

logger = get_logger(__name__)

def setup_venv(project_root: str) -> bool:
    """
    Initialize a Python virtual environment in the project root.
    
    Args:
        project_root: Path to the project root directory.
        
    Returns:
        True if successful, False otherwise.
    """
    venv_dir = project_root / "venv"
    
    if venv_dir.exists():
        logger.info(f"Virtual environment already exists at {venv_dir}. Skipping creation.")
        return True
    
    logger.info(f"Creating virtual environment at {venv_dir}...")
    try:
        venv.create(venv_dir, with_pip=True)
        logger.info("Virtual environment created successfully.")
        
        # Verify pip is available in the new environment
        pip_path = venv_dir / "bin" / "pip" if sys.platform != "win32" else venv_dir / "Scripts" / "pip"
        if not pip_path.exists():
            logger.error("Pip not found in the created virtual environment.")
            return False
        
        logger.info(f"Virtual environment ready. Activate with: source {venv_dir}/bin/activate")
        return True
    except Exception as e:
        logger.error(f"Error creating virtual environment: {e}")
        return False

def main():
    """Main entry point for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Determine project root relative to this script's location
    # Script is at: code/setup_venv.py
    # Project root is: parent of code/
    script_path = Path(__file__).resolve()
    code_dir = script_path.parent
    project_root = code_dir.parent
    
    logger.info(f"Project root detected at: {project_root}")
    
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
        logger.info("Task T004 completed successfully.")
        sys.exit(0)
    else:
        logger.error("Task T004 failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()