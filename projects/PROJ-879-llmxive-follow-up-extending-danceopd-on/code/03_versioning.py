import argparse
import sys
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

from utils.config import get_config


def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_file_size(file_path: str) -> int:
    """Get file size in bytes."""
    return os.path.getsize(file_path)


def version_artifact(
    file_path: str, state_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate SHA256 hash and file size for an artifact,
    then update the state file in the specified state directory.

    Args:
        file_path: Path to the artifact file to version.
        state_dir: Path to the state directory. If None, uses config.

    Returns:
        Dictionary containing the version record.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Artifact not found: {file_path}")

    # Get config for default state path if not provided
    if state_dir is None:
        config = get_config()
        state_dir = config.get("state_dir", "state")

    state_dir = Path(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)

    state_file = state_dir / "artifacts_state.json"

    # Calculate metadata
    sha256_hash = calculate_sha256(str(file_path))
    file_size = get_file_size(str(file_path))

    # Load existing state or initialize
    if state_file.exists():
        with open(state_file, "r") as f:
            state_data = json.load(f)
    else:
        state_data = {"artifacts": {}, "last_updated": None}

    # Create version record
    version_record = {
        "path": str(file_path),
        "sha256": sha256_hash,
        "size_bytes": file_size,
        "version": 1,  # Increment logic could be added if needed
    }

    # Update state
    file_key = str(file_path)
    if file_key in state_data["artifacts"]:
        # Increment version if file already exists
        version_record["version"] = (
            state_data["artifacts"][file_key].get("version", 0) + 1
        )

    state_data["artifacts"][file_key] = version_record
    state_data["last_updated"] = file_path.stat().st_mtime

    # Write updated state
    with open(state_file, "w") as f:
        json.dump(state_data, f, indent=2)

    return version_record


def main():
    parser = argparse.ArgumentParser(
        description="Calculate SHA256 hashes for artifacts and update state."
    )
    parser.add_argument(
        "file_path",
        type=str,
        help="Path to the artifact file to version.",
    )
    parser.add_argument(
        "--state-dir",
        type=str,
        default=None,
        help="Path to the state directory (default: from config).",
    )

    args = parser.parse_args()

    try:
        version_record = version_artifact(args.file_path, args.state_dir)
        print(f"Artifact versioned successfully:")
        print(json.dumps(version_record, indent=2))
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()