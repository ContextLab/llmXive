import os
import sys
from pathlib import Path
import logging

from config import load_config, ensure_directories

logger = logging.getLogger(__name__)

def _log_step(message: str) -> None:
    """Helper to log steps with consistent formatting."""
    logger.info(f"SETUP: {message}")

def create_directories() -> None:
    """Create necessary directory structure."""
    _log_step("Creating directory structure")
    
    # Use the ensure_directories from config
    ensure_directories()
    
    # Additional project-specific directories
    project_dirs = [
        "projects/PROJ-540-the-influence-of-social-media-doomscroll",
        "projects/PROJ-540-the-influence-of-social-media-doomscroll/code",
        "projects/PROJ-540-the-influence-of-social-media-doomscroll/tests",
        "projects/PROJ-540-the-influence-of-social-media-doomscroll/data",
        "projects/PROJ-540-the-influence-of-social-media-doomscroll/data/raw",
        "projects/PROJ-540-the-influence-of-social-media-doomscroll/data/processed",
        "projects/PROJ-540-the-influence-of-social-media-doomscroll/outputs"
    ]
    
    for dir_path in project_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        _log_step(f"Created directory: {dir_path}")

def main() -> None:
    """Main entry point for setup directories script."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        create_directories()
        logger.info("Directory structure created successfully")
    except Exception as e:
        logger.error(f"Directory setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()
