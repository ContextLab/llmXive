import os
import sys
import json
import logging
from pathlib import Path

from config import load_config, get_path

# Import the main logic from the new writer module
from geometry.pose_writer import main as pose_writer_main

def main():
    """
    Runner for T019.
    Executes the pose writer pipeline.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting T019: Write pose estimates and reconstructed boxes.")
        
        # Execute the pose writer logic
        pose_writer_main()
        
        logger.info("T019 execution finished successfully.")
        
    except Exception as e:
        logger.error(f"T019 execution failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()