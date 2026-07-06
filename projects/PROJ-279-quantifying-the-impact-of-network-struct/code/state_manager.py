import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from dotenv import load_dotenv

from logging_config import get_logger
from config.env_config import get_processed_dir, get_data_dir

logger = get_logger(__name__)

# State file location relative to project root
STATE_FILE_NAME = "state.yaml"

def _get_state_path() -> Path:
    """Get the absolute path to the state.yaml file."""
    # The state file lives in the project root 'state/' directory
    # We assume the project root is the parent of the 'code' directory
    code_dir = Path(__file__).parent
    project_root = code_dir.parent
    state_dir = project_root / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / STATE_FILE_NAME

def compute_file_checksum(file_path: Union[str, Path]) -> str:
    """
    Compute SHA-256 checksum of a file.

    Args:
        file_path: Path to the file to checksum.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found for checksum: {path}")

    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def load_state() -> Dict[str, Any]:
    """
    Load the current state from the YAML file.

    Returns:
        Dictionary containing the state data. Returns an empty dict if file doesn't exist.
    """
    state_path = _get_state_path()
    if not state_path.exists():
        logger.debug("State file not found, initializing empty state.")
        return {
            "version": "1.0.0",
            "last_updated": None,
            "artifacts": {},
            "runs": []
        }

    try:
        with open(state_path, "r") as f:
            state = yaml.safe_load(f)
            if state is None:
                return {
                    "version": "1.0.0",
                    "last_updated": None,
                    "artifacts": {},
                    "runs": []
                }
            return state
    except yaml.YAMLError as e:
        logger.error(f"Error parsing state file {state_path}: {e}")
        raise

def save_state(state: Dict[str, Any]) -> None:
    """
    Save the state dictionary to the YAML file.

    Args:
        state: The state dictionary to save.
    """
    state_path = _get_state_path()
    state["last_updated"] = datetime.now().isoformat()

    with open(state_path, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    logger.info(f"State saved to {state_path}")

def register_artifact(
    artifact_path: Union[str, Path],
    artifact_type: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Register a new artifact in the state, computing its checksum and recording metadata.

    Args:
        artifact_path: Path to the artifact file.
        artifact_type: Type of artifact (e.g., 'graph', 'descriptor', 'report').
        metadata: Optional dictionary of additional metadata.

    Returns:
        The artifact record dictionary.

    Raises:
        FileNotFoundError: If the artifact file does not exist.
    """
    path = Path(artifact_path)
    if not path.exists():
        raise FileNotFoundError(f"Artifact not found: {path}")

    state = load_state()
    checksum = compute_file_checksum(path)
    rel_path = str(path) # Store absolute or relative depending on preference, here absolute for clarity in logs

    artifact_record = {
        "path": str(path),
        "type": artifact_type,
        "checksum": checksum,
        "size_bytes": path.stat().st_size,
        "created_at": datetime.now().isoformat(),
        "metadata": metadata or {}
    }

    # Use checksum as key to ensure uniqueness
    key = f"{artifact_type}:{checksum}"
    state["artifacts"][key] = artifact_record

    save_state(state)
    logger.info(f"Registered artifact: {path} (Type: {artifact_type}, Checksum: {checksum[:8]}...)")
    return artifact_record

def verify_artifact(artifact_path: Union[str, Path], artifact_type: Optional[str] = None) -> bool:
    """
    Verify an artifact's checksum against the stored state.

    Args:
        artifact_path: Path to the artifact file.
        artifact_type: Optional type filter.

    Returns:
        True if the checksum matches the stored value, False otherwise.
    """
    path = Path(artifact_path)
    if not path.exists():
        logger.warning(f"Artifact missing during verification: {path}")
        return False

    current_checksum = compute_file_checksum(path)
    state = load_state()

    # Search for matching path and checksum
    found = False
    for key, record in state["artifacts"].items():
        if Path(record["path"]).resolve() == path.resolve():
            if artifact_type and record["type"] != artifact_type:
                continue
            
            if record["checksum"] == current_checksum:
                logger.info(f"Artifact verified: {path}")
                return True
            else:
                logger.error(f"Checksum mismatch for {path}. Expected: {record['checksum']}, Got: {current_checksum}")
                return False
            found = True
            break

    if not found:
        logger.warning(f"Artifact not found in state registry: {path}")
        return False

    return False

def get_artifact_info(artifact_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """
    Retrieve metadata for a specific artifact.

    Args:
        artifact_path: Path to the artifact.

    Returns:
        Artifact record dictionary or None if not found.
    """
    state = load_state()
    path = Path(artifact_path)

    for record in state["artifacts"].values():
        if Path(record["path"]).resolve() == path.resolve():
            return record
    return None

def list_artifacts(artifact_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all registered artifacts, optionally filtered by type.

    Args:
        artifact_type: Optional type filter.

    Returns:
        List of artifact record dictionaries.
    """
    state = load_state()
    artifacts = list(state["artifacts"].values())
    
    if artifact_type:
        return [a for a in artifacts if a["type"] == artifact_type]
    return artifacts

def record_run(
    script_name: str,
    input_artifacts: List[str],
    output_artifacts: List[str],
    status: str = "success",
    duration_seconds: Optional[float] = None
) -> None:
    """
    Record a pipeline run execution in the state.

    Args:
        script_name: Name of the script executed.
        input_artifacts: List of input artifact paths.
        output_artifacts: List of output artifact paths.
        status: Run status (e.g., 'success', 'failed').
        duration_seconds: Execution duration in seconds.
    """
    state = load_state()
    run_record = {
        "timestamp": datetime.now().isoformat(),
        "script": script_name,
        "inputs": input_artifacts,
        "outputs": output_artifacts,
        "status": status,
        "duration_seconds": duration_seconds
    }
    state["runs"].append(run_record)
    save_state(state)
    logger.info(f"Run recorded: {script_name} ({status})")

def get_state_summary() -> Dict[str, Any]:
    """
    Get a summary of the current state.

    Returns:
        Dictionary with counts and latest update time.
    """
    state = load_state()
    return {
        "total_artifacts": len(state["artifacts"]),
        "total_runs": len(state["runs"]),
        "last_updated": state.get("last_updated"),
        "artifact_types": list(set(a["type"] for a in state["artifacts"].values()))
    }

def ensure_state_directory() -> Path:
    """
    Ensure the state directory exists.

    Returns:
        Path to the state directory.
    """
    return _get_state_path().parent
