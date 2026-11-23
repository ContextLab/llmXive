import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

def ensure_state_structure() -> None:
    """Ensures that the state directory structure exists."""
    state_dir = Path("state")
    projects_dir = state_dir / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)
    projects_dir.mkdir(parents=True, exist_ok=True)

def compute_file_checksum(filepath: str) -> str:
    """Computes the SHA256 checksum of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()

def compute_directory_checksum(dirpath: str) -> str:
    """Computes the SHA256 checksum of a directory."""
    hasher = hashlib.sha256()
    for root, _, files in os.walk(dirpath):
        for file in sorted(files):
            filepath = os.path.join(root, file)
            with open(filepath, "rb") as f:
                while True:
                    chunk = f.read(4096)
                    if not chunk:
                        break
                    hasher.update(chunk)
    return hasher.hexdigest()

def load_project_state(project_name: str) -> Dict[str, Any]:
    """Loads the project state from a JSON file."""
    state_dir = Path("state")
    project_file = state_dir / "projects" / f"{project_name}.json"
    if not project_file.exists():
        return {}
    with open(project_file, "r") as f:
        return json.load(f)

def save_project_state(project_name: str, state: Dict[str, Any]) -> None:
    """Saves the project state to a JSON file."""
    state_dir = Path("state")
    project_file = state_dir / "projects" / f"{project_name}.json"
    with open(project_file, "w") as f:
        json.dump(state, f, indent=4)

def register_artifact(project_name: str, artifact_path: str, checksum: str) -> None:
    """Registers an artifact in the project state."""
    state = load_project_state(project_name)
    state[artifact_path] = checksum
    save_project_state(project_name, state)

def verify_artifact_integrity(project_name: str, artifact_path: str) -> bool:
    """Verifies the integrity of an artifact."""
    state = load_project_state(project_name)
    if artifact_path not in state:
        return False
    expected_checksum = state[artifact_path]
    actual_checksum = compute_file_checksum(artifact_path)
    return expected_checksum == actual_checksum

def get_artifact_summary(project_name: str) -> Dict[str, str]:
  """Returns a summary of registered artifacts and their checksums."""
  state = load_project_state(project_name)
  return state
def generate_state_report(project_name: str) -> None:
    """Generates a report summarizing the state of the project."""
    state = load_project_state(project_name)
    print(f"Project State Report for {project_name}:")
    print(json.dumps(state, indent=4))
