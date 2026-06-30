import os
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .checksum_utils import load_state_file, save_state_file


def update_artifact_timestamp(artifact_path: str) -> None:
    """
    Update the updated_at timestamp in the project state file when an artifact changes.

    This implements Constitution V (artifact versioning).

    Args:
        artifact_path: Path to the artifact that was modified.
    """
    # Determine the project state file path based on the artifact location
    # Assuming artifacts are under code/ and state is under code/state/
    project_root = Path(artifact_path).parent.parent.parent
    state_file = project_root / "state" / "projects" / "PROJ-573-https-arxiv-org-abs-2604-27351.yaml"

    if not state_file.exists():
        # If state file doesn't exist, create it
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_data = {
            "project_id": "PROJ-573-https-arxiv-org-abs-2604-27351",
            "updated_at": "",
            "artifact_hashes": {}
        }
    else:
        state_data = load_state_file(str(state_file))

    # Update timestamp
    state_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Ensure artifact_hashes exists even if empty
    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}

    save_state_file(str(state_file), state_data)


def update_timestamp_on_change(artifact_path: str) -> None:
    """
    Helper function to update timestamp when an artifact changes.
    Alias for update_artifact_timestamp for compatibility.

    Args:
        artifact_path: Path to the artifact that was modified.
    """
    update_artifact_timestamp(artifact_path)


def main():
    """
    CLI entry point for versioning utilities.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Versioning utilities for artifact tracking")
    parser.add_argument("--artifact", required=True, help="Path to the artifact file")

    args = parser.parse_args()

    update_artifact_timestamp(args.artifact)
    print(f"Updated timestamp for artifact: {args.artifact}")


if __name__ == "__main__":
    main()