"""
Versioning utilities for artifact tracking and timestamp management.
Implements Constitution IV and V requirements.
"""
import os
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from .checksum_utils import load_state_file, save_state_file
import logging

logger = logging.getLogger(__name__)

STATE_PATH = Path("state/projects/PROJ-573-https-arxiv-org-abs-2604-27351.yaml")

def update_artifact_timestamp(artifact_path: str) -> None:
    """
    Update the updated_at timestamp in the project state file
    whenever an artifact is modified.
    
    Args:
        artifact_path: Relative path to the modified artifact
    """
    if not STATE_PATH.exists():
        logger.warning(f"State file not found: {STATE_PATH}")
        return
        
    state_data = load_state_file(STATE_PATH)
    
    # Update project timestamp
    state_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    # Ensure artifact_hashes exists
    if 'artifact_hashes' not in state_data:
        state_data['artifact_hashes'] = {}
        
    # Compute and store hash for the artifact
    from .checksum_utils import compute_file_sha256
    abs_path = Path(artifact_path)
    if abs_path.exists():
        file_hash = compute_file_sha256(abs_path)
        state_data['artifact_hashes'][artifact_path] = {
            'hash': file_hash,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        logger.info(f"Updated hash for artifact: {artifact_path}")
    
    save_state_file(STATE_PATH, state_data)
    logger.info(f"Updated timestamp for project state: {STATE_PATH}")

def update_timestamp_on_change(artifact_path: str) -> None:
    """
    Convenience wrapper that updates both hash and timestamp
    when an artifact changes.
    
    Args:
        artifact_path: Relative path to the modified artifact
    """
    update_artifact_timestamp(artifact_path)

def main() -> None:
    """Main entry point for testing versioning utilities."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m src.utils.versioning <artifact_path>")
        sys.exit(1)
        
    artifact = sys.argv[1]
    update_artifact_timestamp(artifact)
    print(f"Updated timestamp for: {artifact}")

if __name__ == "__main__":
    main()
