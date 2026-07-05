"""
Hashing utilities for the llmXive pipeline.

Implements SHA-256 checksumming for derived datasets and updates
the state tracking YAML files (Constitution Principle V).
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

from code.config import ensure_directories, PROJECT_ROOT
from code.utils.logging_utils import log_pipeline_step


def calculate_sha256(file_path: str) -> str:
    """
    Calculate the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to checksum.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the path is not a file.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()


def update_state_yaml(
    artifact_path: str,
    checksum: str,
    state_file: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Update the state YAML file with the checksum of a derived artifact.
    
    This implements Constitution Principle V: tracking data lineage and integrity.
    
    Args:
        artifact_path: Relative path to the artifact from the project root.
        checksum: The SHA-256 checksum of the artifact.
        state_file: Optional path to the state YAML file. Defaults to 'state/checksums.yaml'.
        metadata: Optional dictionary of additional metadata to store.
    """
    if state_file is None:
        state_file = PROJECT_ROOT / "state" / "checksums.yaml"
    
    state_file = Path(state_file)
    
    # Ensure the state directory exists
    ensure_directories()
    
    # Load existing state or initialize
    if state_file.exists():
        with open(state_file, "r", encoding="utf-8") as f:
            state_data = yaml.safe_load(f) or {}
    else:
        state_data = {
            "pipeline_version": "1.0.0",
            "artifacts": {}
        }
    
    # Ensure artifacts key exists
    if "artifacts" not in state_data:
        state_data["artifacts"] = {}
    
    # Update the entry for this artifact
    entry = {
        "checksum": checksum,
        "last_updated": None,  # Will be set by caller if needed, or left for automation
        "status": "verified"
    }
    
    if metadata:
        entry.update(metadata)
        
    state_data["artifacts"][str(artifact_path)] = entry
    
    # Write back to file
    with open(state_file, "w", encoding="utf-8") as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
    
    log_pipeline_step(
        step_name="hashing_update_state",
        message=f"Updated state for {artifact_path} with checksum {checksum[:16]}...",
        level="INFO"
    )


def verify_artifact(artifact_path: str, expected_checksum: str) -> bool:
    """
    Verify that an artifact's checksum matches the expected value.
    
    Args:
        artifact_path: Path to the artifact.
        expected_checksum: The expected SHA-256 checksum.
        
    Returns:
        True if the checksum matches, False otherwise.
    """
    actual_checksum = calculate_sha256(artifact_path)
    return actual_checksum == expected_checksum


def checksum_derived_datasets() -> Dict[str, str]:
    """
    Find all derived CSVs in data/processed/ and checksum them.
    
    Returns:
        Dictionary mapping relative file paths to their checksums.
    """
    processed_dir = PROJECT_ROOT / "data" / "processed"
    results = {}
    
    if not processed_dir.exists():
        log_pipeline_step(
            step_name="hashing_scan",
            message=f"Processed directory not found: {processed_dir}",
            level="WARNING"
        )
        return results
    
    for csv_file in processed_dir.rglob("*.csv"):
        rel_path = csv_file.relative_to(PROJECT_ROOT)
        checksum = calculate_sha256(csv_file)
        results[str(rel_path)] = checksum
        
        # Update state for each file
        update_state_yaml(
            artifact_path=str(rel_path),
            checksum=checksum,
            metadata={"type": "derived_dataset"}
        )
    
    return results


def main() -> None:
    """
    Main entry point to checksum all derived datasets and update state.
    """
    print("Running hashing integration for derived datasets...")
    
    # Ensure directories exist
    ensure_directories()
    
    # Checksum all derived datasets
    results = checksum_derived_datasets()
    
    if results:
        print(f"Checksummed {len(results)} derived artifacts:")
        for path, checksum in results.items():
            print(f"  {path}: {checksum[:16]}...")
        
        # Verify state file was updated
        state_file = PROJECT_ROOT / "state" / "checksums.yaml"
        if state_file.exists():
            print(f"State file updated: {state_file}")
        else:
            print("ERROR: State file was not created.")
    else:
        print("No derived datasets found to checksum.")


if __name__ == "__main__":
    main()
