import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "state" / "projects"
STATE_FILE_PATH = STATE_DIR / "PROJ-488-evaluating-the-impact-of-code-generation.yaml"

def compute_file_hash(file_path: Union[str, Path]) -> str:
    """Computes SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_directory_hash(dir_path: Union[str, Path]) -> str:
    """Computes a combined hash of all files in a directory."""
    dir_path = Path(dir_path)
    combined_hash = hashlib.sha256()
    
    # Sort files to ensure deterministic order
    for file_path in sorted(dir_path.rglob("*")):
        if file_path.is_file():
            rel_path = file_path.relative_to(dir_path)
            combined_hash.update(str(rel_path).encode('utf-8'))
            combined_hash.update(compute_file_hash(file_path).encode('utf-8'))
    
    return combined_hash.hexdigest()

def load_state_file() -> Dict[str, Any]:
    """Loads the state YAML file, creating it if it doesn't exist."""
    if not STATE_FILE_PATH.exists():
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        return {
            "project_id": "PROJ-488-evaluating-the-impact-of-code-generation",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "artifacts": {},
            "amendment_status": {}
        }
    
    with open(STATE_FILE_PATH, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
        if data is None:
            return {
                "project_id": "PROJ-488-evaluating-the-impact-of-code-generation",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "artifacts": {},
                "amendment_status": {}
            }
        return data

def save_state_file(data: Dict[str, Any]) -> None:
    """Saves the state dictionary to the YAML file."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

def update_state_with_artifact(artifact_path: Union[str, Path], artifact_type: str) -> None:
    """
    Updates the state file with a new artifact hash and metadata.
    
    Args:
        artifact_path: Path to the artifact file or directory.
        artifact_type: Type of artifact (e.g., 'data', 'code', 'figure').
    """
    state = load_state_file()
    artifact_path = Path(artifact_path)
    
    if artifact_path.is_file():
        file_hash = compute_file_hash(artifact_path)
        artifact_key = str(artifact_path.relative_to(PROJECT_ROOT))
        state["artifacts"][artifact_key] = {
            "type": artifact_type,
            "hash": file_hash,
            "updated_at": datetime.now().isoformat()
        }
    elif artifact_path.is_dir():
        dir_hash = compute_directory_hash(artifact_path)
        artifact_key = str(artifact_path.relative_to(PROJECT_ROOT))
        state["artifacts"][artifact_key] = {
            "type": artifact_type,
            "hash": dir_hash,
            "updated_at": datetime.now().isoformat()
        }
    
    state["updated_at"] = datetime.now().isoformat()
    save_state_file(state)

def update_state_timestamp() -> None:
    """Updates the 'updated_at' timestamp in the state file."""
    state = load_state_file()
    state["updated_at"] = datetime.now().isoformat()
    save_state_file(state)

def register_artifact_hash(artifact_path: Union[str, Path], artifact_type: str, custom_hash: Optional[str] = None) -> str:
    """
    Registers an artifact in the state file, computing hash if not provided.
    Returns the computed/registered hash.
    """
    artifact_path = Path(artifact_path)
    if custom_hash:
        file_hash = custom_hash
    elif artifact_path.is_file():
        file_hash = compute_file_hash(artifact_path)
    elif artifact_path.is_dir():
        file_hash = compute_directory_hash(artifact_path)
    else:
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")
    
    update_state_with_artifact(artifact_path, artifact_type)
    return file_hash

def get_artifact_state(artifact_key: str) -> Optional[Dict[str, Any]]:
    """Retrieves the state of a specific artifact by its relative path key."""
    state = load_state_file()
    return state.get("artifacts", {}).get(artifact_key)

def verify_artifact_integrity(artifact_key: str) -> bool:
    """Verifies if an artifact's current hash matches the stored hash."""
    state = load_state_file()
    stored_info = state.get("artifacts", {}).get(artifact_key)
    
    if not stored_info:
        return False
    
    artifact_path = PROJECT_ROOT / artifact_key
    if not artifact_path.exists():
        return False
    
    current_hash = compute_file_hash(artifact_path) if artifact_path.is_file() else compute_directory_hash(artifact_path)
    return current_hash == stored_info.get("hash")

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
    """Main entry point for state tracker operations."""
    print("State Tracker System")
    print(f"State File: {STATE_FILE_PATH}")
    print("Ready to manage project state.")

if __name__ == "__main__":
    main()