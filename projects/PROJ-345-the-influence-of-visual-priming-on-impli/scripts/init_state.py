"""
Initialize the state tracking structure for Project PROJ-345.

Implements Principle V (Versioning) by creating the project-specific
state directory and generating the initial state.yaml file with
the required schema: project_id, created_at, artifact_hashes.
"""
import os
import sys
import logging
from pathlib import Path
from datetime import datetime
import yaml

# Add project root to path to allow imports if needed, though this script is standalone
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.config import Config

def init_state_file(project_id: str, state_root: Path) -> bool:
    """
    Create the state.yaml file for a specific project.
    
    Args:
        project_id: The unique project identifier (e.g., 'PROJ-345-the-influence...')
        state_root: The root directory where state files are stored.
        
    Returns:
        True if successful, False otherwise.
    """
    project_dir = state_root / project_id
    
    # Ensure the project directory exists
    project_dir.mkdir(parents=True, exist_ok=True)
    
    state_file_path = project_dir / "state.yaml"
    
    # Prepare the initial state data structure
    # Per T007 spec: keys must be 'project_id', 'created_at', 'artifact_hashes: {}'
    state_data = {
        "project_id": project_id,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "artifact_hashes": {}
    }
    
    try:
        with open(state_file_path, 'w', encoding='utf-8') as f:
            # Use default_flow_style=False to ensure readable YAML block style
            yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
        
        logging.info(f"State file initialized successfully at: {state_file_path}")
        return True
    except Exception as e:
        logging.error(f"Failed to initialize state file: {e}")
        return False

def main():
    """Main entry point for the state initialization script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Use the Config to determine paths
    # T005 ensures Config.STATE exists and points to 'state/'
    state_root = Path(Config.STATE)
    
    # The task specifies the project ID as PROJ-345
    # However, the directory structure in tasks.md says 'state/projects/PROJ-345/'
    # The full project ID from the prompt is 'PROJ-345-the-influence-of-visual-priming-on-impli'
    # We will use the short ID 'PROJ-345' as per the specific task description path,
    # but ensure the directory matches the task requirement.
    project_id = "PROJ-345"
    
    logging.info(f"Initializing state for project {project_id} at {state_root}")
    
    success = init_state_file(project_id, state_root)
    
    if not success:
        sys.exit(1)
        
    # Verification step
    state_file = state_root / project_id / "state.yaml"
    if state_file.exists():
        logging.info("Verification: state.yaml exists.")
        with open(state_file, 'r') as f:
            content = yaml.safe_load(f)
            required_keys = {"project_id", "created_at", "artifact_hashes"}
            if required_keys.issubset(content.keys()):
                logging.info("Verification: Schema is correct.")
            else:
                logging.error(f"Verification failed: Missing keys. Found: {content.keys()}")
                sys.exit(1)
    else:
        logging.error("Verification failed: state.yaml was not created.")
        sys.exit(1)

if __name__ == "__main__":
    main()
