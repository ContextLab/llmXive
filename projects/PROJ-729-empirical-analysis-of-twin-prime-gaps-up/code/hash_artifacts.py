"""
Artifact Hashing and State Management.

Computes SHA-256 hashes for project artifacts and updates the state YAML file.
Implements Constitution Principle V: Traceability and Integrity.
"""
import os
import sys
import hashlib
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional

from config import get_config, get_state_path, get_schema_path
from utils import setup_logging, exit_with_error

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_artifacts_to_hash(config: Dict[str, Any]) -> List[Path]:
    """Get list of artifacts to hash based on configuration."""
    artifacts = []
    
    # Data artifacts
    data_raw = Path(config['data_raw'])
    if data_raw.exists():
        for file in data_raw.glob("*.csv"):
            artifacts.append(file)
    
    # Results artifacts
    data_results = Path(config['data_results'])
    if data_results.exists():
        for file in data_results.glob("*.json"):
            artifacts.append(file)
    
    # Figures
    data_figures = Path(config['data_figures'])
    if data_figures.exists():
        for file in data_figures.glob("*.png"):
            artifacts.append(file)
    
    # Schema
    schema_path = get_schema_path(config)
    if schema_path and schema_path.exists():
        artifacts.append(schema_path)
    
    return artifacts

def update_state_file(config: Dict[str, Any], artifacts_hashes: Dict[str, str], 
                     execution_metrics: Optional[Dict[str, Any]] = None) -> None:
    """Update the project state YAML file with new artifact hashes."""
    state_path = get_state_path(config)
    
    # Load existing state or create new
    if state_path.exists():
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {
            "project_id": config.get('project_id', 'unknown'),
            "artifacts": {},
            "last_updated": None,
            "execution_metrics": {}
        }
    
    # Update artifact hashes
    state["artifacts"] = artifacts_hashes
    
    # Update execution metrics if provided
    if execution_metrics:
        state["execution_metrics"] = execution_metrics
    
    # Update timestamp
    import datetime
    state["last_updated"] = datetime.datetime.now().isoformat()
    
    # Write state back to file
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def main():
    """Main entry point for hashing artifacts."""
    logger = setup_logging("hash_artifacts")
    
    config = get_config()
    logger.info("Starting artifact hashing process.")
    
    # Get artifacts to hash
    artifacts = get_artifacts_to_hash(config)
    
    if not artifacts:
        logger.warning("No artifacts found to hash.")
        return
    
    # Compute hashes
    artifacts_hashes = {}
    for artifact in artifacts:
        try:
            file_hash = compute_sha256(artifact)
            artifacts_hashes[artifact.name] = file_hash
            logger.info(f"Hashed {artifact.name}: {file_hash[:16]}...")
        except Exception as e:
            logger.error(f"Failed to hash {artifact.name}: {e}")
    
    # Update state file
    try:
        update_state_file(config, artifacts_hashes)
        logger.info("State file updated successfully.")
    except Exception as e:
        exit_with_error(f"Failed to update state file: {e}")

if __name__ == "__main__":
    main()
