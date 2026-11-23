"""
Dependency Installation Script for PROJ-487
Executes: pip install -r code/requirements.txt
"""
import os
import sys
import subprocess
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def install_dependencies(project_root: Path) -> bool:
    """
    Install dependencies from requirements.txt located in code/
    
    Args:
        project_root: Path to the project root directory
        
    Returns:
        True if installation successful, False otherwise
    """
    requirements_path = project_root / "code" / "requirements.txt"
    
    if not requirements_path.exists():
        logger.error(f"Requirements file not found: {requirements_path}")
        return False
    
    logger.info(f"Installing dependencies from {requirements_path}")
    
    try:
        # Use the current Python interpreter to ensure we install into the correct venv
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            logger.error("Failed to install dependencies:")
            logger.error(result.stderr)
            return False
        
        logger.info("Dependencies installed successfully:")
        logger.info(result.stdout)
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Subprocess error during installation: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during installation: {e}")
        return False

def main():
    """Main entry point for dependency installation"""
    # Determine project root (assume script is in code/ directory)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    logger.info(f"Project root detected at: {project_root}")
    
    success = install_dependencies(project_root)
    
    if success:
        logger.info("T005b: Dependency installation completed successfully")
        sys.exit(0)
    else:
        logger.error("T005b: Dependency installation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()