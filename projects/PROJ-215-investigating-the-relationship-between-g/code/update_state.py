import os
import hashlib
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Import from existing project modules
from config import get_output_path
from utils.logging import get_logger

logger = get_logger(__name__)

def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file's contents.
    Returns hex digest string.
    """
    if not file_path.exists():
        logger.warning(f"File not found for hashing: {file_path}")
        return "MISSING"

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error hashing file {file_path}: {e}")
        return "ERROR"

def update_state_file(state_path: Path, project_id: str, artifacts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Update or create the state.yaml file with current timestamp and artifact hashes.
    """
    # Ensure directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing state if present, else initialize
    if state_path.exists():
        try:
            with open(state_path, 'r') as f:
                current_state = yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Could not read existing state file: {e}. Starting fresh.")
            current_state = {}
    else:
        current_state = {}

    # Update timestamp
    current_state['updated_at'] = datetime.utcnow().isoformat() + 'Z'
    current_state['project_id'] = project_id
    current_state['version'] = current_state.get('version', 1) + 1

    # Update artifacts section
    artifacts_section = current_state.get('artifacts', {})
    
    for artifact in artifacts:
        path_str = artifact['path']
        file_path = Path(path_str)
        
        # Compute hash
        file_hash = compute_file_hash(file_path)
        
        # Store in state
        artifacts_section[path_str] = {
            'hash': file_hash,
            'exists': file_path.exists(),
            'size_bytes': file_path.stat().st_size if file_path.exists() else 0,
            'updated_at': datetime.utcnow().isoformat() + 'Z'
        }

    current_state['artifacts'] = artifacts_section

    # Write back to file
    with open(state_path, 'w') as f:
        yaml.dump(current_state, f, default_flow_style=False, sort_keys=False)

    logger.info(f"State file updated: {state_path}")
    return current_state

def run_state_update(project_id: str, artifact_paths: List[str]) -> Dict[str, Any]:
    """
    Main entry point to update the state file for a specific project.
    """
    # Determine state file path based on project ID
    # Assuming structure: state/projects/{project_id}/state.yaml
    state_dir = Path("state/projects") / project_id
    state_file = state_dir / "state.yaml"
    
    logger.info(f"Updating state for project {project_id} at {state_file}")

    # Convert string paths to dicts for the update function
    artifacts_list = [{'path': p} for p in artifact_paths]
    
    return update_state_file(state_file, project_id, artifacts_list)

def main():
    """
    CLI entry point for updating project state.
    Usage: python code/update_state.py <project_id> <path1> <path2> ...
    """
    import sys

    if len(sys.argv) < 3:
        print("Usage: python code/update_state.py <project_id> <artifact_path1> [artifact_path2] ...")
        sys.exit(1)

    project_id = sys.argv[1]
    artifact_paths = sys.argv[2:]

    logger.info(f"Starting state update for {project_id} with {len(artifact_paths)} artifacts")
    
    try:
        result = run_state_update(project_id, artifact_paths)
        print(f"State updated successfully: {result}")
    except Exception as e:
        logger.error(f"Failed to update state: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
