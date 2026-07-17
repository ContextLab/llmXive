import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import yaml

# Project root is assumed to be the parent of the 'code' directory
# or explicitly passed via argument.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATE_FILE_PATH = PROJECT_ROOT / "state" / "projects" / "PROJ-964-llmxive-follow-up-extending-wan-streamer.yaml"

# Directories to scan for artifacts (relative to project root)
ARTIFACT_DIRS = [
    "data/processed",
    "data/models",
    "data/metrics",
    "figures",
    "state",
    "docs"
]

# Extensions to include in hash calculation
TARGET_EXTENSIONS = {".parquet", ".pt", ".pth", ".json", ".csv", ".yaml", ".yml", ".png", ".pdf", ".txt"}


def compute_file_hash(file_path: Path) -> str:
    """
    Computes SHA-256 hash of a file.
    Reads in chunks to handle large files efficiently.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except (IOError, OSError) as e:
        raise RuntimeError(f"Failed to compute hash for {file_path}: {e}")


def get_file_size_mb(file_path: Path) -> float:
    """Returns file size in megabytes."""
    return file_path.stat().st_size / (1024 * 1024)


def scan_directories(base_dir: Path, relative_dirs: List[str]) -> List[Dict[str, Any]]:
    """
    Scans specified directories relative to base_dir for target files.
    Returns a list of dicts with path, size, and hash.
    """
    artifacts = []
    for rel_dir in relative_dirs:
        current_dir = base_dir / rel_dir
        if not current_dir.exists():
            print(f"Warning: Directory does not exist, skipping: {current_dir}")
            continue

        for file_path in current_dir.rglob("*"):
            if file_path.is_file():
                if file_path.suffix.lower() in TARGET_EXTENSIONS:
                    try:
                        file_hash = compute_file_hash(file_path)
                        file_size = get_file_size_mb(file_path)
                        artifacts.append({
                            "path": str(file_path.relative_to(base_dir)),
                            "size_mb": round(file_size, 4),
                            "hash": file_hash,
                            "modified_time": file_path.stat().st_mtime
                        })
                    except Exception as e:
                        print(f"Error processing {file_path}: {e}")
    return artifacts


def load_state_yaml(state_path: Path) -> Dict[str, Any]:
    """Loads existing state.yaml or returns a default structure if not found."""
    if state_path.exists():
        try:
            with open(state_path, "r") as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise RuntimeError(f"Failed to parse existing state.yaml: {e}")
    else:
        # Ensure parent directory exists
        state_path.parent.mkdir(parents=True, exist_ok=True)
        return {
            "project_id": "PROJ-964-llmxive-follow-up-extending-wan-streamer",
            "last_updated": None,
            "artifacts": {},
            "metadata": {
                "constitution_principle_v": "Artifact hashes registered for reproducibility"
            }
        }


def update_state_with_artifacts(state: Dict[str, Any], artifacts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Updates the state dictionary with new artifact information.
    Groups artifacts by directory for cleaner structure.
    """
    import time
    from datetime import datetime

    state["last_updated"] = datetime.now().isoformat()

    if "artifacts" not in state:
        state["artifacts"] = {}

    # Group by directory
    for artifact in artifacts:
        path_str = artifact["path"]
        parts = path_str.split("/")
        if len(parts) > 1:
            category = parts[0]
        else:
            category = "root"

        if category not in state["artifacts"]:
            state["artifacts"][category] = []

        # Check if file already exists in the list to update or append
        existing = next((a for a in state["artifacts"][category] if a["path"] == path_str), None)
        if existing:
            existing["hash"] = artifact["hash"]
            existing["size_mb"] = artifact["size_mb"]
            existing["modified_time"] = artifact["modified_time"]
        else:
            state["artifacts"][category].append(artifact)

    return state


def save_state_yaml(state: Dict[str, Any], state_path: Path) -> None:
    """Writes the state dictionary to the YAML file."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(state_path, "w") as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False)
        print(f"Successfully updated state file: {state_path}")
    except IOError as e:
        raise RuntimeError(f"Failed to save state.yaml: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Update state.yaml with artifact hashes (Constitution Principle V, FR-020)"
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=str(PROJECT_ROOT),
        help="Path to the project root directory"
    )
    parser.add_argument(
        "--state-file",
        type=str,
        default=str(STATE_FILE_PATH),
        help="Path to the state.yaml file"
    )
    parser.add_argument(
        "--scan-dirs",
        type=str,
        nargs="+",
        default=ARTIFACT_DIRS,
        help="Directories to scan for artifacts (relative to project root)"
    )

    args = parser.parse_args()

    project_root = Path(args.project_root)
    state_file = Path(args.state_file)
    scan_dirs = args.scan_dirs

    if not project_root.exists():
        print(f"Error: Project root does not exist: {project_root}")
        sys.exit(1)

    print(f"Scanning directories in {project_root}...")
    artifacts = scan_directories(project_root, scan_dirs)

    if not artifacts:
        print("No artifacts found to update.")
        # Still update the timestamp even if no new artifacts
    
    state = load_state_yaml(state_file)
    updated_state = update_state_with_artifacts(state, artifacts)
    save_state_yaml(updated_state, state_file)

    print(f"Registered {len(artifacts)} artifacts in state.yaml.")


if __name__ == "__main__":
    main()