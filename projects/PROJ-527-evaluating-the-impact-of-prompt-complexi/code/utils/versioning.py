"""
Artifact versioning utility for tracking project state and generating checksums.

This module provides functions to:
1. Compute SHA-256 checksums for data artifacts
2. Maintain a versioned state file in state/projects/
3. Update the project manifest after data generation
"""
import os
import yaml
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from config import get_project_id, Paths
from utils.logger import get_logger

logger = get_logger(__name__)


def get_state_file_path() -> Path:
    """
    Derive the state file path from the project ID.
    
    Returns:
        Path to the project's YAML state file in state/projects/
    """
    project_id = get_project_id()
    # Ensure the directory exists
    state_dir = Paths.STATE_DIR / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)
    
    # The filename is derived directly from the project ID
    filename = f"{project_id}.yaml"
    return state_dir / filename


def load_state_file() -> Dict[str, Any]:
    """
    Load the existing state file or create a new one if it doesn't exist.
    
    Returns:
        Dictionary containing the project state
    """
    state_path = get_state_file_path()
    
    if state_path.exists():
        with open(state_path, 'r', encoding='utf-8') as f:
            state = yaml.safe_load(f) or {}
    else:
        # Initialize a new state file
        state = {
            "project_id": get_project_id(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": None,
            "artifacts": {},
            "metadata": {}
        }
    
    return state


def compute_artifact_checksums(artifact_paths: List[Path]) -> Dict[str, str]:
    """
    Compute SHA-256 checksums for a list of artifact files.
    
    Args:
        artifact_paths: List of paths to artifacts to checksum
        
    Returns:
        Dictionary mapping relative paths to their SHA-256 hex digest
    """
    checksums = {}
    
    for artifact_path in artifact_paths:
        if not artifact_path.exists():
            logger.warning(f"Artifact not found, skipping checksum: {artifact_path}")
            continue
        
        # Calculate relative path from project root for storage
        try:
            rel_path = str(artifact_path.relative_to(Paths.PROJECT_ROOT))
        except ValueError:
            # If not under project root, use absolute path
            rel_path = str(artifact_path)
        
        # Compute SHA-256
        sha256_hash = hashlib.sha256()
        with open(artifact_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        
        checksums[rel_path] = sha256_hash.hexdigest()
        logger.info(f"Computed checksum for {rel_path}: {checksums[rel_path][:16]}...")
    
    return checksums


def update_state_file(state: Dict[str, Any], new_artifacts: Dict[str, str], 
                     metadata_updates: Optional[Dict[str, Any]] = None) -> None:
    """
    Update the state file with new artifact checksums and metadata.
    
    Args:
        state: Current state dictionary
        new_artifacts: Dictionary of new artifact paths -> checksums
        metadata_updates: Optional dictionary of metadata fields to update
    """
    state["updated_at"] = datetime.utcnow().isoformat()
    
    # Merge new artifacts
    if "artifacts" not in state:
        state["artifacts"] = {}
    state["artifacts"].update(new_artifacts)
    
    # Apply metadata updates
    if metadata_updates:
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"].update(metadata_updates)
    
    # Write back to file
    state_path = get_state_file_path()
    with open(state_path, 'w', encoding='utf-8') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    logger.info(f"Updated state file: {state_path}")


def record_data_generation_state(artifact_paths: List[Path], 
                                 metadata: Optional[Dict[str, Any]] = None) -> None:
    """
    Record the state after data generation by checksumming artifacts and updating the manifest.
    
    This is the primary entry point for T009. It:
    1. Loads the current state file (or creates a new one)
    2. Computes checksums for all provided artifact paths
    3. Updates the state file with the new checksums and metadata
    
    Args:
        artifact_paths: List of paths to data artifacts generated in this run
        metadata: Optional metadata to record (e.g., generation timestamp, config hash)
    """
    logger.info("Recording data generation state...")
    
    # Load current state
    state = load_state_file()
    
    # Compute checksums
    new_checksums = compute_artifact_checksums(artifact_paths)
    
    if not new_checksums:
        logger.warning("No artifacts were checksummed. State file may not be updated with new data.")
    
    # Prepare metadata
    metadata_updates = metadata or {}
    metadata_updates["last_data_generation"] = datetime.utcnow().isoformat()
    metadata_updates["artifact_count"] = len(new_checksums)
    
    # Update and save state
    update_state_file(state, new_checksums, metadata_updates)
    
    logger.info(f"Successfully recorded state for {len(new_checksums)} artifacts.")

def main():
    """
    CLI entry point for the versioning utility.
    
    Usage:
        python -m utils.versioning --artifacts data/processed/prompt_variants.parquet data/results/execution_outcomes.csv
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Record artifact state for versioning")
    parser.add_argument(
        "--artifacts", 
        nargs="+", 
        required=True,
        help="List of artifact paths to checksum and record"
    )
    parser.add_argument(
        "--metadata-json",
        type=str,
        default=None,
        help="Optional JSON string of metadata to record"
    )
    
    args = parser.parse_args()
    
    # Convert string paths to Path objects
    artifact_paths = [Path(p) for p in args.artifacts]
    
    # Parse metadata if provided
    metadata = None
    if args.metadata_json:
        import json
        metadata = json.loads(args.metadata_json)
    
    record_data_generation_state(artifact_paths, metadata)

if __name__ == "__main__":
    main()