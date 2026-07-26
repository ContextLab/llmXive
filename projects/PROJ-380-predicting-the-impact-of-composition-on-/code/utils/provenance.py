import hashlib
import os
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from utils.config import get_paths

# Constants
STATE_DIR_NAME = "state"
PROJECTS_DIR_NAME = "projects"
PROJECT_ID = "PROJ-380-predicting-the-impact-of-composition-on-"
PROVENANCE_FILE_NAME = f"{PROJECT_ID}.yaml"


def ensure_state_directory() -> Path:
    """
    Ensure the state directory and project subdirectory exist.
    Returns the path to the project state directory.
    """
    project_root = get_paths()["project_root"]
    state_dir = project_root / STATE_DIR_NAME
    projects_dir = state_dir / PROJECTS_DIR_NAME
    
    projects_dir.mkdir(parents=True, exist_ok=True)
    return projects_dir


def get_provenance_state_file() -> Path:
    """
    Returns the path to the canonical provenance state file for this project.
    Path: state/projects/PROJ-380-...yaml
    """
    projects_dir = ensure_state_directory()
    return projects_dir / PROVENANCE_FILE_NAME


def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the cryptographic checksum of a file.
    
    Args:
        file_path: Path to the file to hash.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        Hex digest of the file checksum.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot compute checksum: file not found at {file_path}")
    
    if file_path.stat().st_size == 0:
        raise ValueError(f"Cannot compute checksum: file is empty at {file_path}")
    
    hasher = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    
    return hasher.hexdigest()


def load_existing_state(state_file: Path) -> Dict[str, Any]:
    """
    Load the existing state file if it exists, otherwise return an empty structure.
    """
    if not state_file.exists():
        return {
            "project_id": PROJECT_ID,
            "created_at": datetime.utcnow().isoformat(),
            "artifacts": []
        }
    
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data is None:
                return {
                    "project_id": PROJECT_ID,
                    "created_at": datetime.utcnow().isoformat(),
                    "artifacts": []
                }
            return data
    except yaml.YAMLError as e:
        raise RuntimeError(f"Failed to parse existing state file {state_file}: {e}")


def save_state(state_file: Path, state_data: Dict[str, Any]) -> None:
    """
    Save the state dictionary to the YAML file.
    """
    with open(state_file, "w", encoding="utf-8") as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def record_artifact(
    file_path: Path,
    description: str,
    artifact_type: str = "data",
    generated_by: Optional[str] = None,
    dependencies: Optional[List[str]] = None
) -> None:
    """
    Compute the checksum of an artifact and record it to the canonical state file.
    
    This implements Constitution Principle V: All generated artifacts must be
    cryptographically hashed and recorded in the project state.
    
    Args:
        file_path: Absolute or relative path to the artifact file.
        description: Human-readable description of the artifact.
        artifact_type: Category of artifact (e.g., 'data', 'model', 'report').
        generated_by: Name of the script or function that generated this artifact.
        dependencies: List of other artifact paths this one depends on.
    """
    if not isinstance(file_path, Path):
        file_path = Path(file_path)
        
    # Resolve to absolute path for consistency
    if not file_path.is_absolute():
        # Try resolving relative to project root
        project_root = get_paths()["project_root"]
        file_path = (project_root / file_path).resolve()
    else:
        file_path = file_path.resolve()

    if not file_path.exists():
        raise FileNotFoundError(f"Artifact not found at {file_path}, cannot record provenance.")

    checksum = compute_file_checksum(file_path)
    
    state_file = get_provenance_state_file()
    state = load_existing_state(state_file)
    
    artifact_entry = {
        "path": str(file_path),
        "checksum": checksum,
        "algorithm": "sha256",
        "description": description,
        "type": artifact_type,
        "recorded_at": datetime.utcnow().isoformat(),
        "generated_by": generated_by,
        "dependencies": dependencies or []
    }
    
    state["artifacts"].append(artifact_entry)
    save_state(state_file, state)


def verify_artifact(file_path: Path) -> bool:
    """
    Verify that an artifact's current checksum matches the recorded checksum.
    
    Returns:
        True if the checksum matches, False otherwise.
    """
    if not isinstance(file_path, Path):
        file_path = Path(file_path)
        
    if not file_path.is_absolute():
        project_root = get_paths()["project_root"]
        file_path = (project_root / file_path).resolve()
    else:
        file_path = file_path.resolve()

    if not file_path.exists():
        return False

    current_checksum = compute_file_checksum(file_path)
    state_file = get_provenance_state_file()
    
    if not state_file.exists():
        return False
        
    state = load_existing_state(state_file)
    
    # Find the matching entry
    for entry in state.get("artifacts", []):
        if entry["path"] == str(file_path):
            return entry["checksum"] == current_checksum
            
    return False


def list_artifacts() -> List[Dict[str, Any]]:
    """
    List all recorded artifacts in the current project state.
    """
    state_file = get_provenance_state_file()
    if not state_file.exists():
        return []
        
    state = load_existing_state(state_file)
    return state.get("artifacts", [])


def main() -> None:
    """
    CLI entry point for provenance operations.
    Usage:
      python -m utils.provenance record <path> <description> [type]
      python -m utils.provenance verify <path>
      python -m utils.provenance list
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m utils.provenance <command> [args]")
        print("Commands: record, verify, list")
        sys.exit(1)
        
    command = sys.argv[1]
    
    if command == "record":
        if len(sys.argv) < 4:
            print("Usage: python -m utils.provenance record <path> <description> [type]")
            sys.exit(1)
        path = Path(sys.argv[2])
        description = sys.argv[3]
        artifact_type = sys.argv[4] if len(sys.argv) > 4 else "data"
        record_artifact(path, description, artifact_type)
        print(f"Recorded artifact: {path} ({artifact_type})")
        
    elif command == "verify":
        if len(sys.argv) < 3:
            print("Usage: python -m utils.provenance verify <path>")
            sys.exit(1)
        path = Path(sys.argv[2])
        if verify_artifact(path):
            print(f"Verification passed: {path}")
        else:
            print(f"Verification failed: {path}")
            sys.exit(1)
            
    elif command == "list":
        artifacts = list_artifacts()
        if not artifacts:
            print("No artifacts recorded.")
        else:
            for i, entry in enumerate(artifacts, 1):
                print(f"{i}. {entry['path']}")
                print(f"   Checksum: {entry['checksum']}")
                print(f"   Type: {entry['type']}")
                print(f"   Recorded: {entry['recorded_at']}")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
