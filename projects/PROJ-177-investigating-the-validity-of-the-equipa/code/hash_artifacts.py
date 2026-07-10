"""
Hash Artifacts Module.

Generates content hashes (SHA-256) for all files in the `artifacts/` directory
and updates the project state YAML file as per Constitution Principle V.
"""

import hashlib
import os
import sys
import yaml
from pathlib import Path
from datetime import datetime


def calculate_sha256(file_path: Path) -> str:
    """
    Calculate the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Failed to read file {file_path} for hashing: {e}")


def get_artifact_files(artifacts_dir: Path) -> list[Path]:
    """
    Recursively retrieve all files in the artifacts directory.

    Args:
        artifacts_dir: Path to the artifacts directory.

    Returns:
        List of Path objects for files found.
    """
    if not artifacts_dir.exists():
        return []
    
    files = []
    for root, _, filenames in os.walk(artifacts_dir):
        for filename in filenames:
            files.append(Path(root) / filename)
    return sorted(files)


def generate_artifact_hashes(artifacts_dir: Path) -> dict[str, str]:
    """
    Generate hashes for all files in the artifacts directory.

    Args:
        artifacts_dir: Path to the artifacts directory.

    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes.
    """
    hashes = {}
    files = get_artifact_files(artifacts_dir)
    
    for file_path in files:
        try:
            rel_path = str(file_path.relative_to(artifacts_dir))
            hashes[rel_path] = calculate_sha256(file_path)
        except ValueError:
            # Should not happen if relative_to works, but safe fallback
            pass
    
    return hashes


def load_state(state_path: Path) -> dict:
    """
    Load the state YAML file if it exists.

    Args:
        state_path: Path to the state YAML file.

    Returns:
        Dictionary representing the state, or empty dict if not found.
    """
    if not state_path.exists():
        return {}
    
    try:
        with open(state_path, "r") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse state file {state_path}: {e}")


def save_state(state_path: Path, state: dict) -> None:
    """
    Save the state dictionary to the YAML file.

    Args:
        state_path: Path to the state YAML file.
        state: Dictionary to save.
    """
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)


def update_state_with_hashes(state: dict, hashes: dict[str, str]) -> dict:
    """
    Update the state dictionary with new artifact hashes.

    Args:
        state: Current state dictionary.
        hashes: New hashes to record.

    Returns:
        Updated state dictionary.
    """
    if "artifacts" not in state:
        state["artifacts"] = {}
    
    current_artifacts = state["artifacts"]
    if "hashes" not in current_artifacts:
        current_artifacts["hashes"] = {}
    
    # Record timestamp
    current_artifacts["last_updated"] = datetime.utcnow().isoformat() + "Z"
    current_artifacts["hashes"] = hashes
    
    return state


def main() -> int:
    """
    Main entry point for the hash_artifacts script.

    Generates hashes for `artifacts/` and updates `state/project_state.yaml`.
    """
    # Define paths relative to project root (assumed current working directory)
    project_root = Path.cwd()
    artifacts_dir = project_root / "artifacts"
    state_dir = project_root / "state"
    state_file = state_dir / "project_state.yaml"

    # Check if artifacts directory exists
    if not artifacts_dir.exists():
        print(f"Warning: Artifacts directory '{artifacts_dir}' does not exist. Creating empty state update.")
        # Create empty state update to indicate directory was checked but empty
        hashes = {}
    else:
        # Generate hashes
        try:
            hashes = generate_artifact_hashes(artifacts_dir)
            print(f"Generated {len(hashes)} artifact hashes.")
        except Exception as e:
            print(f"Error generating artifact hashes: {e}", file=sys.stderr)
            return 1

    # Load current state
    try:
        state = load_state(state_file)
    except Exception as e:
        print(f"Error loading state file: {e}", file=sys.stderr)
        return 1

    # Update state
    updated_state = update_state_with_hashes(state, hashes)

    # Save state
    try:
        save_state(state_file, updated_state)
        print(f"Updated state file: {state_file}")
    except Exception as e:
        print(f"Error saving state file: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())