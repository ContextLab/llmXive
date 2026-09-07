import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime


def compute_file_hash(filepath: str) -> str:
    """Compute SHA-256 hash of a file.

    Args:
        filepath: Path to the file.

    Returns:
        Hex digest of the file.
    """
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def compute_directory_hashes(dirpath: str) -> dict:
    """Compute hashes for all files in a directory.

    Args:
        dirpath: Path to the directory.

    Returns:
        Dictionary mapping filenames to hashes.
    """
    hashes = {}
    path = Path(dirpath)

    if not path.exists():
        return hashes

    for file_path in path.rglob("*"):
        if file_path.is_file():
            rel_path = str(file_path.relative_to(path))
            hashes[rel_path] = compute_file_hash(str(file_path))

    return hashes


def load_state(project_id: str) -> dict:
    """Load the state file for a project.

    Args:
        project_id: Project identifier.

    Returns:
        State dictionary.
    """
    filepath = f"state/projects/{project_id}.yaml"
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            import yaml
            return yaml.safe_load(f)
    return {}


def save_state(project_id: str, state: dict) -> None:
    """Save the state file for a project.

    Args:
        project_id: Project identifier.
        state: State dictionary.
    """
    import yaml
    os.makedirs("state/projects", exist_ok=True)
    filepath = f"state/projects/{project_id}.yaml"
    with open(filepath, "w") as f:
        yaml.dump(state, f, default_flow_style=False)


def update_state_with_artifacts(
    project_id: str, data_dir: str
) -> None:
    """Update state with artifact hashes from data directory.

    Args:
        project_id: Project identifier.
        data_dir: Data directory to hash.
    """
    state = load_state(project_id)
    hashes = compute_directory_hashes(data_dir)

    state["artifact_hashes"] = hashes
    state["updated_at"] = datetime.now().isoformat()

    save_state(project_id, state)
    print(f"Updated state for {project_id}")


def main() -> None:
    """Main entry point for state manager."""
    import argparse

    parser = argparse.ArgumentParser(description="State Manager")
    parser.add_argument("--project", type=str, default="PROJ-866-llmxive-follow-up-extending-foundation-p",
                      help="Project ID")
    parser.add_argument("--data-dir", type=str, default="data", help="Data directory")

    args = parser.parse_args()

    update_state_with_artifacts(args.project, args.data_dir)


if __name__ == "__main__":
    main()
