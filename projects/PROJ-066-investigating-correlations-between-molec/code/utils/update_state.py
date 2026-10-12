"""
State management utilities for the llmXive pipeline.

Records artifact hashes for the project in a PROJECT-OWNED location
(data/processed/artifact_hashes.yaml). The platform owns the top-level
``state/`` directory and derives artifact hashes itself at verification
time, so this module must NOT create or write any ``state/`` paths.
"""
import hashlib
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

import yaml

# Project root: this file lives at <project>/code/utils/update_state.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Project-owned artifact hash registry (NOT the platform-owned state/ dir).
ARTIFACT_REGISTRY_PATH = PROJECT_ROOT / "data" / "processed" / "artifact_hashes.yaml"

DEFAULT_PROJECT_ID = "PROJ-066-investigating-correlations-between-molec"


def compute_file_hash(file_path: Path) -> str:
    """
    Computes the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        RuntimeError: If an error occurs during hashing.
    """
    file_path = Path(file_path)
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found for hashing: {file_path}")
    except Exception as e:
        raise RuntimeError(f"Error computing hash for {file_path}: {e}")


def get_artifact_hash(file_path: Path) -> str:
    """Alias for compute_file_hash."""
    return compute_file_hash(file_path)


def _resolve_registry_path() -> Path:
    """Return the project-owned artifact registry path, creating dirs."""
    ARTIFACT_REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    return ARTIFACT_REGISTRY_PATH


def load_state_file(project_id: str) -> Dict[str, Any]:
    """
    Loads the project's artifact-hash registry (project-owned file).

    Creates the registry file and directories if they don't exist.

    Args:
        project_id: The unique identifier for the project.

    Returns:
        Dictionary containing the project's recorded artifact state.
    """
    registry = _resolve_registry_path()
    if registry.exists():
        with open(registry, "r") as f:
            content = yaml.safe_load(f)
            if isinstance(content, dict) and content.get("project_id") == project_id:
                return content
            if content:
                return content
    return {
        "project_id": project_id,
        "last_updated": None,
        "artifacts": [],
    }


def save_state_file(project_id: str, state: Dict[str, Any]) -> None:
    """
    Saves the state dictionary to the project-owned registry file.

    Args:
        project_id: The unique identifier for the project.
        state: The dictionary containing the project state to save.
    """
    registry = _resolve_registry_path()
    with open(registry, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)


def verify_artifact_integrity(project_id: str, artifact_path: str, expected_hash: str) -> bool:
    """
    Verifies the integrity of an artifact by recomputing its hash and comparing.

    Args:
        project_id: The project identifier (kept for API compatibility).
        artifact_path: Path to the artifact file (absolute, or relative to
            the project root).
        expected_hash: The expected SHA-256 hash string.

    Returns:
        True if the artifact hash matches the expected hash, False otherwise.
    """
    full_path = Path(artifact_path)
    if not full_path.is_absolute():
        full_path = PROJECT_ROOT / artifact_path

    if not full_path.exists():
        return False

    try:
        return compute_file_hash(full_path) == expected_hash
    except Exception:
        return False


def update_state(project_id: str, artifacts: List[Dict[str, Any]]) -> None:
    """
    Updates the project's artifact-hash registry with new artifact information.

    This function ensures the registry exists, updates the timestamp, and
    appends or updates the provided artifacts list. All output goes to the
    project-owned registry under data/processed/ — never to state/.

    Args:
        project_id: The unique identifier for the project.
        artifacts: A list of dictionaries, each containing:
            - artifact_path: Relative path to the artifact (required).
            - hash: The SHA-256 hash of the artifact (computed if absent).
            - source: Optional source description.
            - version: Optional version string.
    """
    state = load_state_file(project_id)
    state.setdefault("project_id", project_id)
    state["last_updated"] = datetime.now().isoformat()
    state.setdefault("artifacts", [])

    existing = {a.get("artifact_path"): a for a in state["artifacts"]}

    for artifact in artifacts:
        path = artifact.get("artifact_path")
        if not path:
            raise ValueError("Each artifact must have an 'artifact_path' key.")

        entry = dict(artifact)
        if not entry.get("hash"):
            full_path = Path(path)
            if not full_path.is_absolute():
                full_path = PROJECT_ROOT / path
            entry["hash"] = compute_file_hash(full_path)
        entry["last_updated"] = datetime.now().isoformat()

        if path in existing:
            existing[path].update(entry)
        else:
            state["artifacts"].append(entry)
            existing[path] = entry

    save_state_file(project_id, state)


def main() -> None:
    """CLI entry point: record hashes for artifact paths given as arguments."""
    import sys

    artifacts = [
        {"artifact_path": p, "source": "cli"}
        for p in sys.argv[1:]
    ]
    if not artifacts:
        print("Usage: python utils/update_state.py <artifact_path> [...]")
        sys.exit(1)
    update_state(DEFAULT_PROJECT_ID, artifacts)
    print(f"Recorded {len(artifacts)} artifact hash(es) in {ARTIFACT_REGISTRY_PATH}")


if __name__ == "__main__":
    main()
