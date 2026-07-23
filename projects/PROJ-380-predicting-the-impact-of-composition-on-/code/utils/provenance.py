"""
Provenance tracking module for llmXive automated science pipeline.

Implements Constitution Principle V: All artifacts must be checksummed
and recorded to a canonical state file to ensure reproducibility and
auditability of the research pipeline.
"""
import hashlib
import os
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from utils.config import get_paths, ensure_directories
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Project identifier derived from the task context
PROJECT_ID = "PROJ-380-predicting-the-impact-of-composition-on-"

def ensure_state_directory() -> Path:
    """
    Ensure the state directory structure exists.
    
    Returns:
        Path: The path to the state directory.
    """
    paths = get_paths()
    state_dir = paths["state"]
    ensure_directories([state_dir])
    return state_dir

def get_provenance_state_file() -> Path:
    """
    Get the path to the canonical provenance state file for this project.
    
    Returns:
        Path: The path to the YAML state file.
    """
    state_dir = ensure_state_directory()
    # Sanitize project ID for filename safety
    safe_project_id = PROJECT_ID.replace("/", "-").replace(" ", "_")
    state_file = state_dir / f"{safe_project_id}.yaml"
    return state_file

def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file using the specified algorithm.
    
    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        str: Hexadecimal checksum string.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If an unsupported algorithm is requested.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot compute checksum: file not found at {file_path}")

    hash_func = hashlib.new(algorithm)
    
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b""):
                hash_func.update(chunk)
    except Exception as e:
        logger.error(f"Error reading file {file_path} for checksum: {e}")
        raise

    return hash_func.hexdigest()

def load_existing_state(state_file: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the existing provenance state from disk, or return an empty state.
    
    Args:
        state_file: Optional override for the state file path.
        
    Returns:
        Dict: The loaded state dictionary.
    """
    if state_file is None:
        state_file = get_provenance_state_file()
        
    if not state_file.exists():
        return {
            "project_id": PROJECT_ID,
            "created_at": datetime.utcnow().isoformat(),
            "artifacts": []
        }
    
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            state = yaml.safe_load(f)
            if state is None:
                return {
                    "project_id": PROJECT_ID,
                    "created_at": datetime.utcnow().isoformat(),
                    "artifacts": []
                }
            return state
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML state file: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error loading state file: {e}")
        raise

def save_state(state: Dict[str, Any], state_file: Optional[Path] = None) -> None:
    """
    Save the provenance state to disk.
    
    Args:
        state: The state dictionary to save.
        state_file: Optional override for the state file path.
    """
    if state_file is None:
        state_file = get_provenance_state_file()
        
    # Ensure parent directory exists
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(state_file, "w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    logger.info(f"Saved provenance state to {state_file}")

def record_artifact(
    artifact_path: Path,
    artifact_type: str,
    description: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    state_file: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Compute checksum for an artifact and record it to the state file.
    
    Args:
        artifact_path: Path to the artifact file.
        artifact_type: Type of artifact (e.g., 'data', 'model', 'config').
        description: Optional human-readable description.
        metadata: Optional additional metadata dictionary.
        state_file: Optional override for the state file path.
        
    Returns:
        Dict: The recorded artifact entry.
    """
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found at {artifact_path}")

    checksum = compute_file_checksum(artifact_path)
    artifact_entry = {
        "path": str(artifact_path.relative_to(Path.cwd())),
        "type": artifact_type,
        "checksum": checksum,
        "algorithm": "sha256",
        "recorded_at": datetime.utcnow().isoformat(),
        "description": description or artifact_path.name,
        "metadata": metadata or {}
    }

    state = load_existing_state(state_file)
    state["artifacts"].append(artifact_entry)
    save_state(state, state_file)
    
    logger.info(f"Recorded artifact: {artifact_path} (checksum: {checksum[:16]}...)")
    return artifact_entry

def verify_artifact(
    artifact_path: Path,
    expected_checksum: str,
    algorithm: str = "sha256"
) -> bool:
    """
    Verify that a file's checksum matches the expected value.
    
    Args:
        artifact_path: Path to the artifact file.
        expected_checksum: The expected checksum string.
        algorithm: Hash algorithm to use.
        
    Returns:
        bool: True if checksums match, False otherwise.
    """
    actual_checksum = compute_file_checksum(artifact_path, algorithm)
    return actual_checksum == expected_checksum

def list_artifacts(
    artifact_type: Optional[str] = None,
    state_file: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    List all recorded artifacts, optionally filtered by type.
    
    Args:
        artifact_type: Optional filter for artifact type.
        state_file: Optional override for the state file path.
        
    Returns:
        List[Dict]: List of artifact entries.
    """
    state = load_existing_state(state_file)
    artifacts = state.get("artifacts", [])
    
    if artifact_type:
        return [a for a in artifacts if a.get("type") == artifact_type]
        
    return artifacts

def main():
    """
    CLI entry point for provenance operations.
    Usage: python -m utils.provenance <command> [args]
    Commands:
      record <path> <type> [description]  -> Record an artifact
      verify <path> <checksum>            -> Verify an artifact
      list [type]                         -> List artifacts
    """
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m utils.provenance <command> [args]")
        print("Commands: record, verify, list")
        sys.exit(1)

    command = sys.argv[1]

    if command == "record":
        if len(sys.argv) < 4:
            print("Usage: record <path> <type> [description]")
            sys.exit(1)
        path = Path(sys.argv[2])
        atype = sys.argv[3]
        desc = sys.argv[4] if len(sys.argv) > 4 else None
        record_artifact(path, atype, description=desc)

    elif command == "verify":
        if len(sys.argv) < 4:
            print("Usage: verify <path> <checksum>")
            sys.exit(1)
        path = Path(sys.argv[2])
        checksum = sys.argv[3]
        if verify_artifact(path, checksum):
            print(f"Verification successful for {path}")
        else:
            print(f"Verification FAILED for {path}")
            sys.exit(1)

    elif command == "list":
        atype = sys.argv[2] if len(sys.argv) > 2 else None
        artifacts = list_artifacts(artifact_type=atype)
        print(f"Found {len(artifacts)} artifacts:")
        for a in artifacts:
            print(f"  - {a['path']} ({a['type']}) [{a['checksum'][:8]}...]")
            
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
