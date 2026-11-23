import hashlib
import json
import os
import sys
import argparse
import yaml
from pathlib import Path
from typing import Dict, Any, Union

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

    state_data: Dict[str, Any] = {}
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
    with open(state_file, 'r') as f:
        return yaml.safe_load(f) or {}

def _verify_reanalysis(project_name: str, reanalysis_path: Path) -> None:
    """
    Verify the reanalysis NetCDF file, compute its SHA‑256 hash, and
    update the project's state YAML. If a hash is already recorded
    and differs from the newly computed hash, the function aborts
    with a clear error message (exit code 1) as required by T011a_verify.
    """
    if not reanalysis_path.is_file():
        sys.stderr.write(f"ERROR: Reanalysis file not found at {reanalysis_path}\n")
        sys.exit(1)

    # Compute current hash
    current_hash = compute_file_hash(reanalysis_path)

    # Load existing state (if any) to compare
    state = get_state_snapshot(project_name)
    existing_entry = state.get("artifacts", {}).get(str(reanalysis_path))

    if existing_entry:
        stored_hash = existing_entry.get("hash")
        if stored_hash != current_hash:
            sys.stderr.write("ERROR: Checksum mismatch for reanalysis.nc\n")
            sys.exit(1)

    # Update (or create) the state entry
    update_version_state(project_name, reanalysis_path, current_hash)
    # Successful verification prints the hash for visibility
    print(f"{reanalysis_path}: {current_hash}")

def main() -> None:
    """
    CLI entry point.

    The original script supported commands: hash, update, verify, snapshot.
    For backward compatibility we keep those, but we also add a default
    behaviour (when no arguments are supplied) that performs the
    verification required by task T011a_verify.

    Usage examples:
    - Verify reanalysis (default, no args):
          python code/05_versioning_state.py
    - Explicit command:
          python code/05_versioning_state.py verify-reanalysis --project PROJ-021-understanding-oceanic-phytoplankton-comm
    """
    parser = argparse.ArgumentParser(
        description="Project versioning and state management"
    )
    # If no subcommand is provided we will later default to verify-reanalysis
    parser.add_argument(
        "command",
        nargs="?",
        choices=["hash", "update", "verify", "snapshot", "verify-reanalysis"],
        help="Action to perform"
    )
    parser.add_argument("--project", required=False, help="Project name")
    parser.add_argument("--path", help="Path to file or directory")
    parser.add_argument("--expected-hash", help="Expected hash for verification")
    args = parser.parse_args()

    # Default behaviour: if no command supplied, run verification of reanalysis
    if args.command is None:
        # Determine defaults
        default_project = "PROJ-021-understanding-oceanic-phytoplankton-comm"
        default_path = Path("data/raw/copernicus_global_reanalysis.nc")
        _verify_reanalysis(default_project, default_path)
        return

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
        if not args.project:
            raise ValueError("--project is required for update command")
        if not args.expected_hash:
            # Compute current hash if not provided
            p = Path(args.path)
            current_hash = compute_file_hash(p) if p.is_file() else compute_directory_hash(p)
            update_version_state(args.project, args.path, current_hash)
        else:
            update_version_state(args.project, args.path, args.expected_hash)
        print(f"State updated for project {args.project}")

    elif args.command == "verify":
        if not args.path or not args.expected_hash or not args.project:
            raise ValueError("--path, --expected-hash and --project are required for verify command")
        is_valid = verify_artifact_integrity(args.project, args.path, args.expected_hash)
        print(f"Verification {'PASSED' if is_valid else 'FAILED'}")
        if not is_valid:
            raise SystemExit(1)

    elif args.command == "snapshot":
        if not args.project:
            raise ValueError("--project is required for snapshot command")
        snapshot = get_state_snapshot(args.project)
        print(json.dumps(snapshot, indent=2))

    elif args.command == "verify-reanalysis":
        if not args.project:
            raise ValueError("--project is required for verify-reanalysis command")
        # Use provided path or default location
        reanalysis_path = Path(args.path) if args.path else Path("data/raw/copernicus_global_reanalysis.nc")
        _verify_reanalysis(args.project, reanalysis_path)

if __name__ == "__main__":
    main()
