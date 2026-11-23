import hashlib
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

import yaml

from src.config.logging_config import setup_logger, ensure_log_dir

logger = setup_logger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def find_artifacts(
    project_root: Path,
    patterns: List[str],
) -> List[Path]:
    """Find all artifacts matching the given glob patterns."""
    artifacts = []
    for pattern in patterns:
        artifacts.extend(project_root.glob(pattern))
    return artifacts

def update_project_state(
    project_root: Path,
    state_file_path: Optional[Path] = None,
    artifact_patterns: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Update the project state YAML file with:
    - updated_at: current ISO 8601 timestamp
    - artifact_hashes: SHA-256 checksums of specified artifacts

    Args:
        project_root: Root directory of the project
        state_file_path: Optional path to the state file. Defaults to state/projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o.yaml
        artifact_patterns: Optional list of glob patterns to find artifacts. Defaults to ['data/processed/*.parquet', 'data/models/*.pkl']

    Returns:
        Dict containing the updated state
    """
    if state_file_path is None:
        state_file_path = project_root / "state" / "projects" / "PROJ-997-llmxive-follow-up-extending-the-mirage-o.yaml"

    if artifact_patterns is None:
        artifact_patterns = [
            "data/processed/*.parquet",
            "data/models/*.pkl",
        ]

    ensure_log_dir(project_root / "logs")

    # Ensure state directory exists
    state_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing state or create new
    if state_file_path.exists():
        with open(state_file_path, "r") as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {}

    # Update timestamp
    state["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Find and hash artifacts
    artifact_hashes = {}
    artifacts = find_artifacts(project_root, artifact_patterns)

    for artifact_path in artifacts:
        if artifact_path.is_file():
            relative_path = str(artifact_path.relative_to(project_root))
            checksum = compute_sha256(artifact_path)
            artifact_hashes[relative_path] = checksum
            logger.info(f"Computed checksum for {relative_path}: {checksum}")

    state["artifact_hashes"] = artifact_hashes

    # Write updated state
    with open(state_file_path, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Updated project state file: {state_file_path}")
    logger.info(f"Total artifacts hashed: {len(artifact_hashes)}")

    return state

def main():
    """CLI entry point for updating project state."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Update project state with artifact checksums"
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=".",
        help="Path to project root directory",
    )
    parser.add_argument(
        "--state-file",
        type=str,
        default=None,
        help="Path to state file (optional)",
    )
    parser.add_argument(
        "--artifact-patterns",
        type=str,
        nargs="+",
        default=None,
        help="Glob patterns for artifacts (optional)",
    )

    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()

    state_file_path = (
        Path(args.state_file).resolve() if args.state_file else None
    )

    artifact_patterns = args.artifact_patterns

    try:
        state = update_project_state(
            project_root=project_root,
            state_file_path=state_file_path,
            artifact_patterns=artifact_patterns,
        )
        print(json.dumps(state, indent=2))
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to update project state: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
