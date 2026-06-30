"""
Versioning utilities for artifact tracking and timestamp updates.
Implements Constitution V requirements for artifact lifecycle management.
"""

import os
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .checksum_utils import load_state_file, save_state_file


def update_artifact_timestamp(artifact_path: str, state_file_path: Optional[str] = None) -> bool:
    """
    Update the 'updated_at' timestamp for a specific artifact in the project state file.

    Args:
        artifact_path: Relative path to the artifact from project root
        state_file_path: Optional path to state file. Defaults to standard location.

    Returns:
        bool: True if update was successful, False otherwise
    """
    if state_file_path is None:
        state_file_path = "state/projects/PROJ-573-https-arxiv-org-abs-2604-27351.yaml"

    state_path = Path(state_file_path)
    if not state_path.exists():
        # Create parent directories and initialize state file
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_data = {
            "project_id": "PROJ-573-https-arxiv-org-abs-2604-27351",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "artifact_hashes": {}
        }
    else:
        state_data = load_state_file(state_file_path)

    # Update timestamp
    state_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Ensure artifact_hashes exists
    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}

    # Compute hash for the artifact if it exists
    artifact_full_path = Path(artifact_path)
    if artifact_full_path.exists():
        from .checksum_utils import compute_file_sha256
        file_hash = compute_file_sha256(artifact_full_path)
        state_data["artifact_hashes"][artifact_path] = {
            "hash": file_hash,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

    return save_state_file(state_file_path, state_data)


def update_timestamp_on_change(artifact_path: str) -> bool:
    """
    Wrapper for update_artifact_timestamp to be called when an artifact changes.
    This function is designed to be integrated into task implementations.

    Args:
        artifact_path: Relative path to the artifact

    Returns:
        bool: True if update was successful
    """
    return update_artifact_timestamp(artifact_path)


def main():
    """Command-line interface for versioning utilities."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Update artifact timestamps and hashes")
    parser.add_argument(
        "artifact_path",
        help="Path to the artifact to update"
    )
    parser.add_argument(
        "--state-file",
        default="state/projects/PROJ-573-https-arxiv-org-abs-2604-27351.yaml",
        help="Path to the state file"
    )

    args = parser.parse_args()

    success = update_artifact_timestamp(args.artifact_path, args.state_file)

    if success:
        print(f"Successfully updated timestamp for: {args.artifact_path}")
        sys.exit(0)
    else:
        print(f"Failed to update timestamp for: {args.artifact_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()