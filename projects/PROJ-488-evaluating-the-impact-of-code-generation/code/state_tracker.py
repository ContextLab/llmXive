import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml

STATE_DIR = Path("state")
PROJECT_STATE_FILE = STATE_DIR / "projects" / "PROJ-488-evaluating-the-impact-of-code-generation.yaml"

def compute_file_hash(file_path: Union[str, Path]) -> str:
    """
    Compute SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file
    
    Returns:
        Hex string of the SHA-256 hash
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_directory_hash(dir_path: Union[str, Path]) -> str:
    """
    Compute a combined hash for all files in a directory.
    
    Args:
        dir_path: Path to the directory
    
    Returns:
        Hex string of the combined SHA-256 hash
    """
    dir_path = Path(dir_path)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    
    combined_hash = hashlib.sha256()
    
    # Sort files for deterministic ordering
    files = sorted(dir_path.rglob("*"))
    for file_path in files:
        if file_path.is_file():
          # Include relative path in hash
          rel_path = file_path.relative_to(dir_path)
          combined_hash.update(str(rel_path).encode('utf-8'))
          # Include file content hash
          file_hash = compute_file_hash(file_path)
          combined_hash.update(file_hash.encode('utf-8'))
    
    return combined_hash.hexdigest()

def load_state_file(state_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Load state from YAML file.
    
    Args:
        state_path: Optional path to state file. Defaults to project state file.
    
    Returns:
        Dictionary containing state data
    """
    if state_path is None:
        state_path = PROJECT_STATE_FILE
    else:
        state_path = Path(state_path)
    
    if not state_path.exists():
        return {
            "project_id": "PROJ-488-evaluating-the-impact-of-code-generation",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "artifacts": {},
            "figures": {},
            "metrics": {},
            "statistics": {},
            "amendment_status": {}
        }
    
    with open(state_path, 'r') as f:
        return yaml.safe_load(f)

def save_state_file(state_path: Union[str, Path], state: Dict[str, Any]) -> None:
    """
    Save state to YAML file.
    
    Args:
        state_path: Path to state file
        state: State dictionary to save
    """
    state_path = Path(state_path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def update_state_with_artifact(
    state: Dict[str, Any],
    artifact_type: str,
    artifact_name: str,
    artifact_path: Union[str, Path],
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Update state with a new artifact entry.
    
    Args:
        state: Current state dictionary
        artifact_type: Type of artifact (e.g., 'metric', 'figure', 'dataset')
        artifact_name: Name/identifier for the artifact
        artifact_path: Path to the artifact file
        metadata: Optional additional metadata
    
    Returns:
        Updated state dictionary
    """
    artifact_path = Path(artifact_path)
    
    if artifact_type not in state:
        state[artifact_type] = {}
    
    try:
        file_hash = compute_file_hash(artifact_path)
    except FileNotFoundError:
        file_hash = None
    
    entry = {
        "path": str(artifact_path),
        "hash": file_hash,
        "updated_at": datetime.now().isoformat()
    }
    
    if metadata:
        entry.update(metadata)
    
    state[artifact_type][artifact_name] = entry
    state["updated_at"] = datetime.now().isoformat()
    
    return state

def update_state_timestamp(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update the timestamp in the state.
    
    Args:
        state: Current state dictionary
    
    Returns:
        Updated state dictionary
    """
    state["updated_at"] = datetime.now().isoformat()
    return state

def register_artifact_hash(
    state: Dict[str, Any],
    artifact_type: str,
    artifact_name: str,
    artifact_hash: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Register an artifact hash in state without computing it.
    
    Args:
        state: Current state dictionary
        artifact_type: Type of artifact
        artifact_name: Name/identifier for the artifact
        artifact_hash: Pre-computed hash
        metadata: Optional additional metadata
    
    Returns:
        Updated state dictionary
    """
    if artifact_type not in state:
        state[artifact_type] = {}
    
    entry = {
        "hash": artifact_hash,
        "updated_at": datetime.now().isoformat()
    }
    
    if metadata:
        entry.update(metadata)
    
    state[artifact_type][artifact_name] = entry
    state["updated_at"] = datetime.now().isoformat()
    
    return state

def get_artifact_state(state: Dict[str, Any], artifact_type: str, artifact_name: str) -> Optional[Dict[str, Any]]:
    """
    Get state information for a specific artifact.
    
    Args:
        state: Current state dictionary
        artifact_type: Type of artifact
        artifact_name: Name/identifier for the artifact
    
    Returns:
        Artifact state dictionary or None if not found
    """
    if artifact_type in state and artifact_name in state[artifact_type]:
        return state[artifact_type][artifact_name]
    return None

def verify_artifact_integrity(state: Dict[str, Any], artifact_type: str, artifact_name: str) -> bool:
    """
    Verify the integrity of an artifact by comparing stored hash with current hash.
    
    Args:
        state: Current state dictionary
        artifact_type: Type of artifact
        artifact_name: Name/identifier for the artifact
    
    Returns:
        True if integrity verified, False otherwise
    """
    artifact_info = get_artifact_state(state, artifact_type, artifact_name)
    if not artifact_info or "path" not in artifact_info or "hash" not in artifact_info:
        return False
    
    try:
        current_hash = compute_file_hash(artifact_info["path"])
        return current_hash == artifact_info["hash"]
    except FileNotFoundError:
        return False

def update_state_after_pipeline_stage(stage_name: str, artifacts: Dict[str, List[Dict[str, str]]]) -> None:
    """
    Update state after a pipeline stage completes.
    
    Args:
        stage_name: Name of the pipeline stage
        artifacts: Dictionary mapping artifact types to lists of artifact info
    """
    state = load_state_file()
    
    if "pipeline_stages" not in state:
        state["pipeline_stages"] = {}
    
    stage_info = {
        "completed_at": datetime.now().isoformat(),
        "artifacts": artifacts
    }
    
    state["pipeline_stages"][stage_name] = stage_info
    
    # Update individual artifacts
    for artifact_type, artifact_list in artifacts.items():
        for artifact in artifact_list:
            if "name" in artifact and "path" in artifact:
                update_state_with_artifact(state, artifact_type, artifact["name"], artifact["path"])
    
    state["updated_at"] = datetime.now().isoformat()
    save_state_file(PROJECT_STATE_FILE, state)

def update_state_after_stage(stage_name: str, stage_artifact_path: Optional[Union[str, Path]] = None) -> None:
    """
    Updates the state YAML with an 'updated_at' timestamp after a pipeline stage.
    If an artifact path is provided, it also registers the artifact hash.
    
    Args:
        stage_name: Name of the pipeline stage (e.g., 'ingestion', 'metrics', 'analysis').
        stage_artifact_path: Optional path to the main output artifact of this stage.
    """
    state = load_state_file()
    
    # Update the global timestamp
    state["updated_at"] = datetime.now().isoformat()
    
    # Log stage completion in the artifacts section if path provided
    if stage_artifact_path:
        artifact_path = Path(stage_artifact_path)
        if artifact_path.exists():
            if artifact_path.is_file():
                file_hash = compute_file_hash(artifact_path)
                artifact_key = str(artifact_path.relative_to(PROJECT_ROOT))
            else:
                file_hash = compute_directory_hash(artifact_path)
                artifact_key = str(artifact_path.relative_to(PROJECT_ROOT))
            
            state["artifacts"][artifact_key] = {
                "type": "stage_output",
                "stage": stage_name,
                "hash": file_hash,
                "updated_at": state["updated_at"]
            }
        else:
            # Log that the stage completed but artifact not found yet
            state["stages"] = state.get("stages", {})
            state["stages"][stage_name] = {
                "status": "completed",
                "updated_at": state["updated_at"],
                "artifact_found": False
            }
    else:
        # Just timestamp update for stages without a single main artifact
        state["stages"] = state.get("stages", {})
        state["stages"][stage_name] = {
            "status": "completed",
            "updated_at": state["updated_at"]
        }
    
    save_state_file(state)

def main():
    """Main entry point for state tracker module."""
    print("State Tracker Module")
    print(f"Project State File: {PROJECT_STATE_FILE}")
    
    # Load and display current state
    state = load_state_file()
    print(json.dumps(state, indent=2))

if __name__ == "__main__":
    main()