"""
Versioning utilities for llmXive project.

Implements Constitution V requirements:
- Update state/projects/PROJ-573-https-arxiv-org-abs-2604-27351.yaml updated_at timestamp on artifact changes.
"""
import os
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

# Import existing utilities from sibling module
from .checksum_utils import load_state_file, save_state_file


def update_artifact_timestamp(artifact_path: str, project_id: str = "PROJ-573-https-arxiv-org-abs-2604-27351") -> bool:
    """
    Updates the 'updated_at' timestamp in the project state file when an artifact changes.
    
    Args:
        artifact_path: Path to the artifact that was modified (relative or absolute).
        project_id: The project identifier for the state file.
        
    Returns:
        bool: True if the timestamp was successfully updated, False otherwise.
    """
    # Determine project state file path
    state_dir = Path("state/projects")
    state_dir.mkdir(parents=True, exist_ok=True)
    
    state_file_path = state_dir / f"{project_id}.yaml"
    
    # Load existing state or create new structure
    try:
        if state_file_path.exists():
            state_data = load_state_file(state_file_path)
        else:
            # Initialize new state file structure
            state_data = {
                "project_id": project_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "artifact_hashes": {}
            }
    except Exception as e:
        # Fallback to empty structure if loading fails
        state_data = {
            "project_id": project_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "artifact_hashes": {}
        }
    
    # Update timestamp
    state_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Save updated state
    try:
        save_state_file(state_file_path, state_data)
        return True
    except Exception as e:
        # Log error if saving fails (in a real system, use the logger)
        return False


def update_timestamp_on_change(artifact_path: str, project_id: str = "PROJ-573-https-arxiv-org-abs-2604-27351") -> bool:
    """
    Wrapper for update_artifact_timestamp to be used as a callback or hook.
    Ensures the project state is updated whenever an artifact changes.
    
    Args:
        artifact_path: Path to the artifact that was modified.
        project_id: The project identifier for the state file.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    return update_artifact_timestamp(artifact_path, project_id)


def main():
    """
    CLI entry point for testing the versioning utility.
    Usage: python -m src.utils.versioning <artifact_path>
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m src.utils.versioning <artifact_path>")
        sys.exit(1)
        
    artifact_path = sys.argv[1]
    project_id = "PROJ-573-https-arxiv-org-abs-2604-27351"
    
    success = update_artifact_timestamp(artifact_path, project_id)
    
    if success:
        print(f"Successfully updated timestamp for project {project_id} due to artifact: {artifact_path}")
    else:
        print(f"Failed to update timestamp for project {project_id}")
        sys.exit(1)


if __name__ == "__main__":
    main()
