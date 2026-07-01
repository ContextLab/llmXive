import os
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from .logging import get_logger

logger = get_logger(__name__)

STATE_FILE_PATH = Path("state/projects/PROJ-573-https-arxiv-org-abs-27351.yaml")

def update_artifact_timestamp(artifact_path: str) -> bool:
    """
    Updates the 'updated_at' timestamp in the project state file whenever
    an artifact changes. This enforces Constitution V (audit trail).

    Args:
        artifact_path: The relative or absolute path of the artifact that changed.

    Returns:
        bool: True if the state file was updated successfully, False otherwise.
    """
    try:
        # Ensure the artifact path is normalized
        artifact_p = Path(artifact_path)
        if not artifact_p.is_absolute():
            artifact_p = Path.cwd() / artifact_p

        # Determine the project state file location
        # Ensure state directory exists
        state_dir = STATE_FILE_PATH.parent
        state_dir.mkdir(parents=True, exist_ok=True)

        # Load existing state or create new structure
        state_data: Dict[str, Any] = {}
        if STATE_FILE_PATH.exists():
            try:
                with open(STATE_FILE_PATH, 'r', encoding='utf-8') as f:
                    state_data = yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                logger.error(f"Failed to parse existing state file: {e}")
                return False

        # Ensure top-level keys exist
        if "projects" not in state_data:
            state_data["projects"] = {}

        project_key = "PROJ-573-https-arxiv-org-abs-2604-27351"
        if project_key not in state_data["projects"]:
            state_data["projects"][project_key] = {}

        # Update timestamp
        now = datetime.now(timezone.utc).isoformat()
        state_data["projects"][project_key]["updated_at"] = now

        # Optionally log the artifact that triggered the update
        if "artifact_hashes" not in state_data["projects"][project_key]:
            state_data["projects"][project_key]["artifact_hashes"] = {}

        logger.info(f"Updated state file for {project_key}. Timestamp: {now}")

        # Write back to file
        with open(STATE_FILE_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)

        return True

    except Exception as e:
        logger.error(f"Failed to update artifact timestamp for {artifact_path}: {e}")
        return False

def update_timestamp_on_change(artifact_path: str) -> bool:
    """
    Wrapper function to update timestamp on artifact change.
    Delegates to update_artifact_timestamp.
    """
    return update_artifact_timestamp(artifact_path)

def main() -> None:
    """CLI entry point for testing/updating timestamps."""
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m src.utils.versioning <artifact_path>")
        sys.exit(1)

    path = sys.argv[1]
    success = update_artifact_timestamp(path)
    if success:
        print(f"Successfully updated timestamp for {path}")
    else:
        print(f"Failed to update timestamp for {path}")
        sys.exit(1)

if __name__ == "__main__":
    main()