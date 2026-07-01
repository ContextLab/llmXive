"""
Versioning utilities for artifact tracking and timestamp management.

Implements Constitution V requirements for artifact change tracking.
"""
import os
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
import logging
from .logging import get_logger

logger = get_logger(__name__)

# Path to the project state file
PROJECT_STATE_PATH = Path("state/projects/PROJ-573-https-arxiv-org-abs-2604-27351.yaml")


def _ensure_state_file_exists() -> Path:
    """Ensure the project state file exists, creating it with defaults if necessary."""
    if not PROJECT_STATE_PATH.exists():
        logger.info(f"Creating new state file at {PROJECT_STATE_PATH}")
        PROJECT_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        default_state = {
            "project_id": "PROJ-573-https-arxiv-org-abs-2604-27351",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "artifact_hashes": {}
        }
        
        with open(PROJECT_STATE_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(default_state, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Initialized state file with default structure")
    
    return PROJECT_STATE_PATH


def _load_state() -> Dict[str, Any]:
    """Load the current state from the YAML file."""
    path = _ensure_state_file_exists()
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def _save_state(state: Dict[str, Any]) -> None:
    """Save the state back to the YAML file."""
    path = PROJECT_STATE_PATH
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    logger.debug(f"Saved state to {path}")


def update_artifact_timestamp(artifact_path: str) -> None:
    """
    Update the 'updated_at' timestamp in the project state file when an artifact changes.
    
    This function implements Constitution V by ensuring the project state file
    reflects the most recent modification time whenever an artifact is changed.
    
    Args:
        artifact_path: Relative or absolute path to the artifact that was modified.
    
    Returns:
        None
    
    Side Effects:
        Updates the 'updated_at' field in state/projects/PROJ-573-https-arxiv-org-abs-2604-27351.yaml
    """
    try:
        state = _load_state()
        state['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        # Optionally track which artifact was modified
        if 'last_modified_artifacts' not in state:
            state['last_modified_artifacts'] = []
        
        # Normalize path for consistent tracking
        artifact_p = Path(artifact_path)
        if artifact_p.is_absolute():
            try:
                artifact_p = artifact_p.relative_to(Path.cwd())
            except ValueError:
                # If not relative to cwd, keep as absolute
                artifact_p = artifact_p
        
        modified_path = str(artifact_p)
        
        # Avoid duplicates
        if modified_path not in state['last_modified_artifacts']:
            state['last_modified_artifacts'].append(modified_path)
            # Keep list manageable (last 50)
            if len(state['last_modified_artifacts']) > 50:
                state['last_modified_artifacts'] = state['last_modified_artifacts'][-50:]
        
        _save_state(state)
        logger.info(f"Updated timestamp for artifact: {modified_path}")
        
    except Exception as e:
        logger.error(f"Failed to update artifact timestamp for {artifact_path}: {e}")
        raise


def update_timestamp_on_change(artifact_path: str) -> None:
    """
    Helper function to update timestamp on artifact change.
    
    This is an alias for update_artifact_timestamp to support different
    call patterns found in the codebase.
    
    Args:
        artifact_path: Path to the artifact that was modified.
    
    Returns:
        None
    """
    update_artifact_timestamp(artifact_path)


def get_project_state() -> Dict[str, Any]:
    """
    Retrieve the current project state.
    
    Returns:
        Dictionary containing project state information.
    """
    return _load_state()


def main() -> None:
    """
    CLI entry point for versioning utilities.
    
    Demonstrates usage of update_artifact_timestamp.
    """
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m src.utils.versioning <artifact_path>")
        sys.exit(1)
    
    artifact_path = sys.argv[1]
    update_artifact_timestamp(artifact_path)
    print(f"Timestamp updated for: {artifact_path}")


if __name__ == "__main__":
    main()
