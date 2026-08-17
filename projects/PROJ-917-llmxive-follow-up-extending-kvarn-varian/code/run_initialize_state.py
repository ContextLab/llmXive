"""
Script to initialize the project state file for PROJ-917.
This script creates the necessary directory structure and initializes
the project state YAML file with the required content.
"""
import os
import sys
import yaml
from pathlib import Path
import logging

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from state_manager import initialize_project_state, get_project_root, verify_project_state_exists

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main entry point for initializing the project state."""
    project_id = "PROJ-917-llmxive-follow-up-extending-kvarn-varian"
    
    logger.info(f"Initializing project state for {project_id}")
    
    # Initialize the state file
    try:
        state_file_path = initialize_project_state(project_id)
        logger.info(f"Successfully created state file: {state_file_path}")
        
        # Verify the file was created
        if verify_project_state_exists(project_id):
            logger.info("Verification passed: State file exists")
            
            # Load and display the content
            from state_manager import load_project_state
            state_data = load_project_state(project_id)
            logger.info(f"State content: {state_data}")
            
            return 0
        else:
            logger.error("Verification failed: State file does not exist")
            return 1
            
    except Exception as e:
        logger.error(f"Failed to initialize project state: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())