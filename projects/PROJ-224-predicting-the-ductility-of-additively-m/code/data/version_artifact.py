"""
Artifact Versioning Module.
Computes SHA-256 hash and updates state file.
"""
import hashlib
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import yaml

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def ensure_state_file(state_path: Path) -> Dict[str, Any]:
    """Ensure state file exists and return its content."""
    if not state_path.exists():
        state_path.parent.mkdir(parents=True, exist_ok=True)
        return {"artifact_hashes": {}}
    with open(state_path, 'r') as f:
        return yaml.safe_load(f) or {"artifact_hashes": {}}

def save_state(state_path: Path, state: Dict[str, Any]):
    """Save state to YAML file."""
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)

def version_artifact(file_path: Path, state_path: Path):
    """Version an artifact by computing hash and updating state."""
    if not file_path.exists():
        raise FileNotFoundError(f"Artifact not found: {file_path}")
    
    logger.info(f"Versioning artifact: {file_path}")
    hash_value = compute_sha256(file_path)
    
    state = ensure_state_file(state_path)
    state["artifact_hashes"][str(file_path)] = hash_value
    save_state(state_path, state)
    
    logger.info(f"Hash {hash_value} recorded in {state_path}")
    return hash_value

def main():
    """Main entry point for artifact versioning."""
    logger.info("Starting Artifact Versioning...")
    
    project_root = Path(__file__).parent.parent.parent
    artifact_path = project_root / "data" / "curated_builds.csv"
    state_path = project_root / "state" / "projects" / "PROJ-224-predicting-the-ductility-of-additively-m" / "state.yaml"
    
    if not artifact_path.exists():
        logger.error(f"Artifact not found: {artifact_path}")
        sys.exit(1)
    
    try:
        version_artifact(artifact_path, state_path)
        logger.info("Artifact Versioning stage completed.")
    except Exception as e:
        logger.error(f"Artifact Versioning failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
