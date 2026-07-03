"""
Artifact versioning utility for managing project state files.

This module provides functionality to update the project state YAML file
after data generation, tracking artifacts and their checksums.
"""
import os
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from config import get_project_id, Paths
from utils.hash_artifacts import calculate_sha256
from utils.logger import get_logger

logger = get_logger(__name__)

def load_state_file(state_path: Path) -> Dict[str, Any]:
    """Load the existing state file or return a default structure if it doesn't exist."""
    if state_path.exists():
        with open(state_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    # Initialize default state structure
    project_id = get_project_id()
    return {
        "project_id": project_id,
        "state": "initializing",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": None,
        "artifacts": {},
        "metadata": {
            "version": "1.0.0",
            "pipeline": "llmXive"
        }
    }

def compute_artifact_checksums(artifact_paths: List[Path]) -> Dict[str, str]:
    """Compute SHA-256 checksums for a list of artifact paths."""
    checksums = {}
    for path in artifact_paths:
        if path.exists():
          checksums[str(path)] = calculate_sha256(path)
        else:
            logger.warning(f"Artifact path does not exist: {path}")
    return checksums

def update_state_file(
    state_path: Path,
    new_artifacts: Optional[List[Path]] = None,
    status: Optional[str] = None,
    metadata_updates: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Update the project state YAML file with new artifact information.
    
    Args:
        state_path: Path to the state YAML file
        new_artifacts: List of new artifact paths to record
        status: Optional new status string (e.g., 'data_generated', 'analysis_complete')
        metadata_updates: Optional dict of additional metadata to merge
    
    Returns:
        The updated state dictionary
    """
    state = load_state_file(state_path)
    
    # Update timestamp
    state["updated_at"] = datetime.utcnow().isoformat() + "Z"
    
    # Update status if provided
    if status:
        state["state"] = status
    
    # Process new artifacts
    if new_artifacts:
        existing_artifacts = state.get("artifacts", {})
        new_checksums = compute_artifact_checksums(new_artifacts)
        
        for path_str, checksum in new_checksums.items():
            existing_artifacts[path_str] = {
                "checksum": checksum,
                "updated_at": datetime.utcnow().isoformat() + "Z"
            }
        
        state["artifacts"] = existing_artifacts
        logger.info(f"Recorded {len(new_checksums)} new artifacts in state file")
    
    # Apply metadata updates
    if metadata_updates:
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"].update(metadata_updates)
    
    # Ensure state directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write updated state
    with open(state_path, 'w', encoding='utf-8') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    logger.info(f"Updated state file: {state_path}")
    return state

def get_state_file_path() -> Path:
    """
    Construct the path to the project state YAML file.
    
    Returns:
        Path to the state file under state/projects/<project_id>.yaml
    """
    project_id = get_project_id()
    # Sanitize project_id for filesystem (remove invalid characters)
    safe_project_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in project_id)
    return Paths.STATE_DIR / "projects" / f"{safe_project_id}.yaml"

def record_data_generation_state(
    generated_files: List[Path],
    status: str = "data_generated"
) -> Dict[str, Any]:
    """
    Convenience function to update state after data generation phase.
    
    Args:
        generated_files: List of paths to files generated in this phase
        status: Status string (defaults to 'data_generated')
    
    Returns:
        The updated state dictionary
    """
    state_path = get_state_file_path()
    return update_state_file(
        state_path=state_path,
        new_artifacts=generated_files,
        status=status,
        metadata_updates={"last_phase": "data_generation"}
    )
