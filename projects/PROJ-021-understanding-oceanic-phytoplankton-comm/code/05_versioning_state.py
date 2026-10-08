import hashlib
import os
import json
import stat
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import yaml

def compute_file_hash(file_path: Union[str, Path]) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_directory_hash(dir_path: Union[str, Path]) -> str:
    """Compute a deterministic hash of all files in a directory."""
    dir_path = Path(dir_path)
    sha256_hash = hashlib.sha256()
    # Sort files for deterministic order
    for file_path in sorted(dir_path.rglob("*")):
        if file_path.is_file():
            rel_path = file_path.relative_to(dir_path)
            sha256_hash.update(str(rel_path).encode('utf-8'))
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_version_state(project_name: str, artifact_path: Union[str, Path], hash_value: str) -> None:
    """Update the project state YAML with a new artifact hash."""
    state_dir = Path("state/projects")
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / f"{project_name}.yaml"

    state_data = {}
    if state_file.exists():
        with open(state_file, "r") as f:
            state_data = yaml.safe_load(f) or {}

    if "artifacts" not in state_data:
        state_data["artifacts"] = {}

    state_data["artifacts"][str(artifact_path)] = {
        "hash": hash_value,
        "updated_at": str(Path(artifact_path).stat().st_mtime)
    }

    with open(state_file, "w") as f:
        yaml.dump(state_data, f, default_flow_style=False)

def verify_artifact_integrity(project_name: str, artifact_path: Union[str, Path], expected_hash: str) -> bool:
    """Verify if an artifact's current hash matches the expected hash."""
    actual_hash = compute_file_hash(artifact_path)
    return actual_hash == expected_hash

def get_state_snapshot(project_name: str) -> Dict[str, Any]:
    """Get the current state snapshot for a project."""
    state_file = Path(f"state/projects/{project_name}.yaml")
    if not state_file.exists():
        return {}
    with open(state_file, "r") as f:
        return yaml.safe_load(f) or {}

def main():
    """CLI entry point for versioning tasks."""
    import argparse
    parser = argparse.ArgumentParser(description="Project versioning and state management")
    parser.add_argument("command", choices=["hash", "update", "verify", "snapshot"])
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--path", help="Path to file or directory")
    parser.add_argument("--expected-hash", help="Expected hash for verification")
    args = parser.parse_args()

    if args.command == "hash":
        if not args.path:
            raise ValueError("--path is required for hash command")
        p = Path(args.path)
        if p.is_dir():
            print(compute_directory_hash(p))
        else:
            print(compute_file_hash(p))
    elif args.command == "update":
        if not args.path:
            raise ValueError("--path is required for update command")
        if not args.expected_hash:
            # Compute current hash if not provided
            p = Path(args.path)
            current_hash = compute_file_hash(p) if p.is_file() else compute_directory_hash(p)
            update_version_state(args.project, args.path, current_hash)
        else:
            update_version_state(args.project, args.path, args.expected_hash)
        print(f"State updated for project {args.project}")
    elif args.command == "verify":
        if not args.path or not args.expected_hash:
            raise ValueError("--path and --expected-hash are required for verify command")
        is_valid = verify_artifact_integrity(args.project, args.path, args.expected_hash)
        print(f"Verification {'PASSED' if is_valid else 'FAILED'}")
        if not is_valid:
            raise SystemExit(1)
    elif args.command == "snapshot":
        snapshot = get_state_snapshot(args.project)
        print(json.dumps(snapshot, indent=2))

if __name__ == "__main__":
    main()