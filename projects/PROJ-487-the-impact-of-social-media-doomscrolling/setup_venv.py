import os
import sys
import venv
import subprocess
from pathlib import Path
import logging

def setup_venv(project_root: Path) -> bool:
    """
    Initialize a Python virtual environment in the project root.
    
    Args:
        project_root: Path to the project root directory.
        
    Returns:
        True if successful, False otherwise.
    """
    venv_path = project_root / "venv"
    
    # Check if venv already exists
    if venv_path.exists():
        logging.warning(f"Virtual environment already exists at {venv_path}. Skipping creation.")
        return True
    
    try:
        logging.info(f"Creating virtual environment at {venv_path}...")
        venv.create(venv_path, with_pip=True)
        
        # Verify creation
        if not (venv_path / "bin" / "activate").exists():
            logging.error("Virtual environment created but activate script not found.")
            return False
        
        logging.info(f"Virtual environment successfully created at {venv_path}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to create virtual environment: {e}")
        return False

def main():
    """Main entry point for the script."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Determine project root
    # Assuming script is run from project root or code directory
    current_dir = Path.cwd()
    
    # Check if we are in the project root or a subdirectory
    project_root = current_dir
    if (current_dir / "code").exists() and (current_dir / "data").exists():
        project_root = current_dir
    else:
        # Try to find project root by looking for specific markers
        # or assume current directory is project root
        logging.info(f"Using current directory as project root: {project_root}")
    
    success = setup_venv(project_root)
    
    if success:
        logging.info("Virtual environment setup completed successfully.")
        sys.exit(0)
    else:
        logging.error("Virtual environment setup failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()