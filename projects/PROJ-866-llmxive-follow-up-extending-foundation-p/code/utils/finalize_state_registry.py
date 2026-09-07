import os
import sys
import hashlib
import yaml
from pathlib import Path
from datetime import datetime


def compute_sha256(filepath: str) -> str:
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


def collect_all_artifact_hashes(data_dir: str) -> dict:
    """Collect SHA-256 hashes of all files in the data directory.

    Args:
        data_dir: Root data directory.

    Returns:
        Dictionary mapping relative paths to hashes.
    """
    hashes = {}
    data_path = Path(data_dir)

    if not data_path.exists():
        return hashes

    for file_path in data_path.rglob("*"):
        if file_path.is_file() and file_path.name != ".gitkeep":
            rel_path = str(file_path.relative_to(data_path.parent))
            hashes[rel_path] = compute_sha256(str(file_path))

    return hashes


def update_state_registry(
    project_id: str, artifact_hashes: dict
) -> None:
    """Update the project state registry with artifact hashes.

    Args:
        project_id: Project identifier.
        artifact_hashes: Dictionary of file hashes.
    """
    filepath = f"state/projects/{project_id}.yaml"

    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            state = yaml.safe_load(f)
    else:
        state = {
            "project_id": project_id,
            "created_at": datetime.now().isoformat(),
        }

    state["artifact_hashes"] = artifact_hashes
    state["updated_at"] = datetime.now().isoformat()
    state["status"] = "updated"

    with open(filepath, "w") as f:
        yaml.dump(state, f, default_flow_style=False)

    print(f"Updated state registry: {filepath}")


def main() -> None:
    """Main entry point for state registry finalization."""
    import argparse

    parser = argparse.ArgumentParser(description="Finalize State Registry")
    parser.add_argument("--project", type=str, default="PROJ-866-llmxive-follow-up-extending-foundation-p",
                      help="Project ID")

    args = parser.parse_args()

    hashes = collect_all_artifact_hashes("data")
    update_state_registry(args.project, hashes)
    print(f"Finalized state registry for {args.project}")


if __name__ == "__main__":
    main()
