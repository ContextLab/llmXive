"""
Setup script to create the required video output directory structure.
Implements Task T023b: Create data/derived/videos/ directory.
"""
import os
import logging
from pathlib import Path
from utils.config import ensure_directories

logger = logging.getLogger(__name__)

def main():
    """
    Creates the directory structure for storing generated videos.
    Path: projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/data/derived/videos/
    """
    # Determine project root relative to this script location
    # Assuming this script is at code/utils/setup_videos_dir.py
    # Project root is two levels up: code/utils -> code -> project_root
    current_dir = Path(__file__).resolve()
    project_root = current_dir.parent.parent.parent
    
    videos_dir = project_root / "data" / "derived" / "videos"
    
    logger.info(f"Creating video output directory: {videos_dir}")
    
    # ensure_directories from utils.config handles creation
    ensure_directories([videos_dir])
    
    if videos_dir.exists() and videos_dir.is_dir():
        logger.info(f"Successfully created directory: {videos_dir}")
        return True
    else:
        logger.error(f"Failed to create directory: {videos_dir}")
        return False

if __name__ == "__main__":
    # Basic logging setup if not already configured
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    success = main()
    exit(0 if success else 1)