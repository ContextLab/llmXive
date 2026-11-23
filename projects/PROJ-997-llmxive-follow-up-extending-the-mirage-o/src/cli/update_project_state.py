import hashlib
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

import yaml

# Configure logging for this module
logger = logging.getLogger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"Artifact not found: {file_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to compute hash for {file_path}: {e}")

def find_artifacts(patterns: List[str], base_path: Path) -> List[Path]:
    """Find files matching glob patterns relative to base_path."""
    artifacts = []
    for pattern in patterns:
        for path in base_path.glob(pattern):
            if path.is_file():
                artifacts.append(path)
    return artifacts

def update_project_state(project_root: Path, project_id: str, state_file_name: str = "state.yaml") -> bool:
    """
    Update the project state YAML file with:
    - updated_at: current ISO 8601 timestamp
    - artifact_hashes: SHA-256 checksums of specified artifacts
    """
    # Define artifact patterns relative to project_root
    artifact_patterns = [
        "data/processed/*.parquet",
        "data/models/*.pkl",
        "data/processed/*.json",
        "docs/reports/*.md"
    ]

    # Find all matching artifacts
    artifacts = find_artifacts(artifact_patterns, project_root)

    if not artifacts:
        logger.warning("No artifacts found matching the specified patterns.")
        # Proceed anyway, artifact_hashes will be empty

    # Compute hashes
    artifact_hashes = {}
    for artifact in artifacts:
        rel_path = artifact.relative_to(project_root)
        try:
            hash_val = compute_sha256(artifact)
            artifact_hashes[str(rel_path)] = hash_val
            logger.info(f"Computed hash for {rel_path}: {hash_val[:16]}...")
        except Exception as e:
            logger.error(f"Failed to compute hash for {rel_path}: {e}")
            # Skip this artifact but continue

    # Determine state file path
    state_file_path = project_root / state_file_name
    if not state_file_path.exists():
        # Initialize new state file
        logger.info(f"Creating new state file at {state_file_path}")
        state_data = {
            "project_id": project_id,
            "updated_at": None,
            "artifact_hashes": {}
        }
    else:
        # Load existing state
        logger.info(f"Loading existing state file from {state_file_path}")
        try:
            with open(state_file_path, "r") as f:
                state_data = yaml.safe_load(f) or {}
            # Ensure required keys exist
            state_data.setdefault("project_id", project_id)
            state_data.setdefault("artifact_hashes", {})
        except Exception as e:
            logger.error(f"Failed to load existing state file: {e}")
            raise

    # Update timestamp
    current_time = datetime.now(timezone.utc).isoformat()
    state_data["updated_at"] = current_time

    # Update artifact hashes
    state_data["artifact_hashes"] = artifact_hashes

    # Write updated state
    try:
        with open(state_file_path, "w") as f:
            yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Successfully updated state file: {state_file_path}")
        logger.info(f"Updated timestamp: {current_time}")
        logger.info(f"Number of artifacts hashed: {len(artifact_hashes)}")
        return True
    except Exception as e:
        logger.error(f"Failed to write state file: {e}")
        raise

def main():
    """CLI entry point for updating project state."""
    import argparse

    parser = argparse.ArgumentParser(description="Update project state YAML with artifact hashes.")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path("."),
        help="Path to the project root directory (default: current directory)"
    )
    parser.add_argument(
        "--project-id",
        type=str,
        default="PROJ-997-llmxive-follow-up-extending-the-mirage-o",
        help="Project ID to use in the state file"
    )
    parser.add_argument(
        "--state-file",
        type=str,
        default="state.yaml",
        help="Name of the state file (default: state.yaml)"
    )

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    try:
        success = update_project_state(
            project_root=args.project_root,
            project_id=args.project_id,
            state_file_name=args.state_file
        )
        if success:
            print(f"Project state updated successfully.")
            sys.exit(0)
        else:
            print("Failed to update project state.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
