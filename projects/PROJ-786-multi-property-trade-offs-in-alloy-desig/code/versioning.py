"""
Versioning script for llmXive pipeline.
Computes SHA-256 hashes for data/code artifacts and updates a state YAML file.
"""
import os
import hashlib
import yaml
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Default paths relative to project root
DEFAULT_STATE_FILE = "data/processed/version_state.yaml"
DEFAULT_TARGETS = [
    "data/raw",
    "data/processed",
    "code",
]

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_directory_hash(dir_path: Path) -> Dict[str, str]:
    """Compute hashes for all files in a directory recursively."""
    hashes = {}
    for file_path in sorted(dir_path.rglob("*")):
        if file_path.is_file() and not file_path.name.startswith("."):
          # Skip hidden files
          relative_path = file_path.relative_to(dir_path)
          hashes[str(relative_path)] = compute_sha256(file_path)
    return hashes

def load_state(state_file: Path) -> Dict[str, Any]:
    """Load existing state file or return empty structure."""
    if state_file.exists():
        with open(state_file, "r") as f:
            return yaml.safe_load(f) or {}
    return {}

def save_state(state: Dict[str, Any], state_file: Path) -> None:
    """Save state to YAML file."""
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def update_version_state(
    targets: List[str],
    state_file: Optional[Path] = None,
    project_root: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Compute hashes for target paths and update state file.

    Args:
        targets: List of relative paths to hash (files or directories)
        state_file: Path to state YAML file (default: data/processed/version_state.yaml)
        project_root: Project root directory (default: current working directory)

    Returns:
        Updated state dictionary
    """
    if project_root is None:
        project_root = Path.cwd()

    if state_file is None:
        state_file = project_root / DEFAULT_STATE_FILE
    else:
        state_file = Path(state_file)

    # Ensure state_file is relative to project_root if it isn't absolute
    if not state_file.is_absolute():
        state_file = project_root / state_file

    state = load_state(state_file)

    # Initialize or update metadata
    state["last_updated"] = datetime.utcnow().isoformat()
    state["project"] = "PROJ-786-multi-property-trade-offs-in-alloy-desig"
    state["artifacts"] = state.get("artifacts", {})

    for target in targets:
        target_path = project_root / target
        if not target_path.exists():
            print(f"Warning: Target path does not exist: {target_path}")
            continue

        if target_path.is_file():
            # Single file
            relative_name = target_path.name
            artifact_hash = compute_sha256(target_path)
            state["artifacts"][relative_name] = {
                "type": "file",
                "hash": artifact_hash,
                "path": str(target_path.relative_to(project_root))
            }
        elif target_path.is_dir():
            # Directory - hash all contents
            dir_hashes = compute_directory_hash(target_path)
            if dir_hashes:
                # Compute a combined hash for the directory
                combined_content = "\n".join(
                    f"{k}:{v}" for k, v in sorted(dir_hashes.items())
                )
                combined_hash = hashlib.sha256(combined_content.encode()).hexdigest()
                state["artifacts"][target] = {
                    "type": "directory",
                    "hash": combined_hash,
                    "files": dir_hashes,
                    "path": str(target_path.relative_to(project_root))
                }

    save_state(state, state_file)
    return state

def main():
    parser = argparse.ArgumentParser(
        description="Compute SHA-256 hashes for artifacts and update state YAML"
    )
    parser.add_argument(
        "--targets",
        nargs="+",
        default=DEFAULT_TARGETS,
        help="Paths to hash (relative to project root)"
    )
    parser.add_argument(
        "--state-file",
        default=DEFAULT_STATE_FILE,
        help="Path to state YAML file"
    )
    parser.add_argument(
        "--project-root",
        default=None,
        help="Project root directory (default: current directory)"
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Print the updated state to stdout"
    )

    args = parser.parse_args()

    project_root = Path(args.project_root) if args.project_root else Path.cwd()
    state = update_version_state(
        targets=args.targets,
        state_file=args.state_file,
        project_root=project_root
    )

    if args.show:
        print(yaml.dump(state, default_flow_style=False))
    else:
        print(f"State updated successfully at {args.state_file}")
        print(f"Hashed {len(state['artifacts'])} artifact(s)")

if __name__ == "__main__":
    main()