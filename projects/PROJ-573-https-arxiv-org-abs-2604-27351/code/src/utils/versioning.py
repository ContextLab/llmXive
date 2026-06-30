import os
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .checksum_utils import load_state_file, save_state_file

PROJECT_ID = "PROJ-573-https-arxiv-org-abs-2604-27351"
STATE_DIR = Path("state")
PROJECTS_STATE_FILE = STATE_DIR / "projects" / f"{PROJECT_ID}.yaml"


def update_artifact_timestamp(artifact_path: str) -> bool:
    """
    Updates the 'updated_at' timestamp in the project state file for a given artifact.
    
    This function loads the project state, ensures the artifact is tracked (adding it if missing),
    and updates the global project 'updated_at' timestamp to the current UTC time.
    
    Args:
        artifact_path: Relative path to the artifact (e.g., 'src/benchmark/config/modalities/timeseries.yaml').
    
    Returns:
        True if the state file was successfully updated, False otherwise.
    """
    current_time = datetime.now(timezone.utc).isoformat()
    
    # Ensure state directory exists
    PROJECTS_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing state or create empty structure
    try:
        state_data = load_state_file(PROJECTS_STATE_FILE)
    except FileNotFoundError:
        state_data = {
            "project_id": PROJECT_ID,
            "created_at": current_time,
            "updated_at": current_time,
            "artifact_hashes": {},
            "artifacts_updated_at": {}
        }
    
    # Normalize path to string key
    path_key = str(Path(artifact_path).as_posix())
    
    # Update artifact-specific timestamp if it exists or initialize it
    if "artifacts_updated_at" not in state_data:
        state_data["artifacts_updated_at"] = {}
    
    state_data["artifacts_updated_at"][path_key] = current_time
    
    # Update global project timestamp
    state_data["updated_at"] = current_time
    state_data["project_id"] = PROJECT_ID
    
    # Save back to file
    try:
        save_state_file(PROJECTS_STATE_FILE, state_data)
        return True
    except Exception as e:
        print(f"Error saving state file: {e}")
        return False


def update_timestamp_on_change(artifact_path: str) -> bool:
    """
    Wrapper function to update timestamps when an artifact changes.
    
    This is the primary entry point for integration with config updates (T040-T042)
    and other artifact modifications. It calls update_artifact_timestamp to perform
    the actual update.
    
    Args:
        artifact_path: Relative path to the modified artifact.
    
    Returns:
        True if update was successful, False otherwise.
    """
    return update_artifact_timestamp(artifact_path)


def main():
    """
    CLI entry point for testing the versioning utility.
    Usage: python -m src.utils.versioning <artifact_path>
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m src.utils.versioning <artifact_path>")
        print("Example: python -m src.utils.versioning src/benchmark/config/modalities/timeseries.yaml")
        sys.exit(1)
    
    artifact = sys.argv[1]
    success = update_timestamp_on_change(artifact)
    
    if success:
        print(f"Successfully updated timestamp for: {artifact}")
        print(f"State file updated: {PROJECTS_STATE_FILE}")
    else:
        print(f"Failed to update timestamp for: {artifact}")
        sys.exit(1)


if __name__ == "__main__":
    main()