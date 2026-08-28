import os
import sys
import json
import logging
from pathlib import Path

# Add parent directory to path to allow imports from code/
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from utils.setup_paths import ensure_project_dirs
from utils.hash_utils import calculate_directory_hash, update_project_state

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # The project root is the parent of the code directory
    code_dir = current_dir
    project_root = code_dir.parent
    
    project_name = "PROJ-274-evaluating-the-impact-of-llm-generated-c"
    
    logger.info(f"Project root identified as: {project_root}")
    logger.info(f"Ensuring directory structure for {project_name}...")
    
    created_dirs, actual_root = ensure_project_dirs()
    
    logger.info(f"Created/verified directories:")
    for d in created_dirs:
        logger.info(f"  - {d}")
    
    logger.info("Calculating directory hash...")
    directory_hash = calculate_directory_hash(actual_root)
    
    logger.info(f"Directory Hash (SHA256): {directory_hash}")
    
    logger.info("Updating state file...")
    state_file = update_project_state(actual_root, project_name, directory_hash)
    
    logger.info(f"State file updated: {state_file}")
    logger.info("Project setup complete.")

if __name__ == "__main__":
    main()