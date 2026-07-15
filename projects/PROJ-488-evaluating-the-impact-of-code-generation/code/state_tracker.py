import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml

import logging
from logging_config import get_logger

logger = get_logger(__name__)

STATE_FILE_PATH = Path("state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml")

def ensure_state_directory():
    """Ensure the state directory exists."""
    STATE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured state directory exists at {STATE_FILE_PATH.parent}")

def compute_file_hash(file_path: Union[str, Path]) -> str:
    """Compute SHA-256 hash of a file."""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_directory_hash(dir_path: Union[str, Path]) -> str:
    """Compute a combined SHA-256 hash for all files in a directory."""
    dir_path = Path(dir_path)
    if not dir_path.exists() or not dir_path.is_dir():
        raise NotADirectoryError(f"Directory not found: {dir_path}")
    
    combined_hash = hashlib.sha256()
    for file_path in sorted(dir_path.rglob("*")):
        if file_path.is_file():
            file_hash = compute_file_hash(file_path)
            combined_hash.update(file_hash.encode())
    
    return combined_hash.hexdigest()

def load_state_file() -> Dict[str, Any]:
    """Load the state YAML file, creating it if it doesn't exist."""
    ensure_state_directory()
    
    if not STATE_FILE_PATH.exists():
        initial_state = {
            "project_id": "PROJ-488-evaluating-the-impact-of-code-generation",
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "amendment_status": {},
            "artifacts": {},
            "pipeline_stages": {}
        }
        save_state_file(initial_state)
        return initial_state
    
    with open(STATE_FILE_PATH, "r") as f:
        return yaml.safe_load(f)

def save_state_file(state: Dict[str, Any]):
    """Save the state dictionary to the YAML file."""
    ensure_state_directory()
    
    with open(STATE_FILE_PATH, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"State file saved to {STATE_FILE_PATH}")

def update_state_timestamp(state: Dict[str, Any]) -> Dict[str, Any]:
    """Update the updated_at timestamp in the state dictionary."""
    state["updated_at"] = datetime.utcnow().isoformat()
    logger.info(f"Updated state timestamp to {state['updated_at']}")
    return state

def update_state_with_artifact(state: Dict[str, Any], artifact_name: str, artifact_path: Union[str, Path], artifact_type: str = "file") -> Dict[str, Any]:
    """Add or update an artifact entry in the state."""
    artifact_path = Path(artifact_path)
    
    if "artifacts" not in state:
        state["artifacts"] = {}
    
    if artifact_name not in state["artifacts"]:
        state["artifacts"][artifact_name] = {}
    
    artifact_info = {
        "path": str(artifact_path),
        "type": artifact_type,
        "hash": compute_file_hash(artifact_path) if artifact_type == "file" else compute_directory_hash(artifact_path),
        "added_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    state["artifacts"][artifact_name] = artifact_info
    logger.info(f"Updated state with artifact: {artifact_name} ({artifact_type})")
    return state

def register_artifact_hash(state: Dict[str, Any], artifact_name: str, artifact_hash: str):
    """Register a pre-computed hash for an artifact."""
    if "artifacts" not in state:
        state["artifacts"] = {}
    
    if artifact_name in state["artifacts"]:
        state["artifacts"][artifact_name]["hash"] = artifact_hash
        state["artifacts"][artifact_name]["updated_at"] = datetime.utcnow().isoformat()
    else:
        state["artifacts"][artifact_name] = {
            "hash": artifact_hash,
            "registered_at": datetime.utcnow().isoformat()
        }
    
    logger.info(f"Registered artifact hash for: {artifact_name}")
    return state

def get_artifact_state(state: Dict[str, Any], artifact_name: str) -> Optional[Dict[str, Any]]:
    """Retrieve the state of a specific artifact."""
    if "artifacts" not in state:
        return None
    return state["artifacts"].get(artifact_name)

def verify_artifact_integrity(state: Dict[str, Any], artifact_name: str) -> bool:
    """Verify the integrity of an artifact by recomputing its hash."""
    artifact_info = get_artifact_state(state, artifact_name)
    if not artifact_info:
        logger.error(f"Artifact not found in state: {artifact_name}")
        return False
    
    artifact_path = Path(artifact_info["path"])
    if not artifact_path.exists():
        logger.error(f"Artifact file not found: {artifact_path}")
        return False
    
    current_hash = compute_file_hash(artifact_path) if artifact_info["type"] == "file" else compute_directory_hash(artifact_path)
    
    if current_hash != artifact_info["hash"]:
        logger.error(f"Artifact integrity check failed for {artifact_name}. Expected: {artifact_info['hash']}, Got: {current_hash}")
        return False
    
    logger.info(f"Artifact integrity verified for {artifact_name}")
    return True

def update_state_after_pipeline_stage(state: Dict[str, Any], stage_name: str, stage_status: str = "completed", details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Update the state file to record the completion of a pipeline stage.
    This function updates the 'updated_at' timestamp and records stage-specific details.
    """
    if "pipeline_stages" not in state:
        state["pipeline_stages"] = {}
    
    stage_record = {
        "status": stage_status,
        "completed_at": datetime.utcnow().isoformat(),
        "details": details or {}
    }
    
    state["pipeline_stages"][stage_name] = stage_record
    state = update_state_timestamp(state)
    
    logger.info(f"Recorded pipeline stage completion: {stage_name} ({stage_status})")
    return state

def update_state_after_stage(stage_name: str, stage_status: str = "completed", details: Optional[Dict[str, Any]] = None):
    """
    Convenience function to load state, update for a stage, and save.
    Used by scripts to automatically update the state YAML after a stage.
    """
    state = load_state_file()
    state = update_state_after_pipeline_stage(state, stage_name, stage_status, details)
    save_state_file(state)

def main():
    """
    CLI entry point for state tracker operations.
    Usage: python -m code.state_tracker [command] [args]
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="State Tracker CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Command: update-stage
    parser_stage = subparsers.add_parser("update-stage", help="Update state after a pipeline stage")
    parser_stage.add_argument("stage_name", help="Name of the pipeline stage")
    parser_stage.add_argument("--status", default="completed", help="Status of the stage (default: completed)")
    parser_stage.add_argument("--details", type=str, default="{}", help="JSON string of details")
    
    # Command: verify
    parser_verify = subparsers.add_parser("verify", help="Verify artifact integrity")
    parser_verify.add_argument("artifact_name", help="Name of the artifact to verify")
    
    args = parser.parse_args()
    
    if args.command == "update-stage":
        details = json.loads(args.details)
        update_state_after_stage(args.stage_name, args.status, details)
        print(f"State updated for stage: {args.stage_name}")
    
    elif args.command == "verify":
        state = load_state_file()
        success = verify_artifact_integrity(state, args.artifact_name)
        print(f"Verification {'passed' if success else 'failed'} for artifact: {args.artifact_name}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()