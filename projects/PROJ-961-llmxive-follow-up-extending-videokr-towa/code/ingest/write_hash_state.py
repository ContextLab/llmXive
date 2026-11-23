"""
T016: Write hash of annotated_videokr.csv to state/projects/PROJ-961-llmxive-follow-up-extending-videokr-towa.yaml

This script computes the SHA-256 hash of the annotated dataset produced by T013
and writes it to the project state YAML file, satisfying Constitution Principle V.
"""
import hashlib
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Import from project utils
from utils.config import get_project_root, get_path, ensure_dir, get_config
from utils.versioning import compute_sha256, write_project_state_yaml

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ID = "PROJ-961-llmxive-follow-up-extending-videokr-towa"
ARTIFACT_NAME = "annotated_videokr.csv"
ARTIFACT_PATH_REL = f"data/processed/{ARTIFACT_NAME}"
STATE_DIR_REL = "state/projects"
STATE_FILE_NAME = f"{PROJECT_ID}.yaml"

def main() -> int:
    """
    Main entry point for T016.
    
    Returns:
        int: 0 on success, 1 on failure
    """
    project_root = get_project_root()
    logger.info(f"Project root: {project_root}")

    # Construct paths
    artifact_path = project_root / ARTIFACT_PATH_REL
    state_dir = project_root / STATE_DIR_REL
    state_file_path = state_dir / STATE_FILE_NAME

    # Verify artifact exists
    if not artifact_path.exists():
        logger.error(f"Artifact not found: {artifact_path}")
        logger.error("Please ensure T013 (annotate_graph.py) has completed successfully.")
        return 1

    logger.info(f"Computing hash for: {artifact_path}")
    
    # Compute SHA-256 hash
    try:
        file_hash = compute_sha256(artifact_path)
        logger.info(f"SHA-256 hash computed: {file_hash}")
    except Exception as e:
        logger.error(f"Failed to compute hash: {e}")
        return 1

    # Ensure state directory exists
    ensure_dir(state_dir)

    # Prepare state data
    # The state file tracks versioning of key artifacts for the project
    state_data: Dict[str, Any] = {
        "project_id": PROJECT_ID,
        "last_updated": None,  # write_project_state_yaml will set this or we can leave it for the function
        "artifacts": {
            ARTIFACT_NAME: {
                "path": ARTIFACT_PATH_REL,
                "hash": file_hash,
                "algorithm": "sha256",
                "status": "verified"
            }
        }
    }

    logger.info(f"Writing state to: {state_file_path}")
    
    try:
        # Use the existing versioning utility to write the YAML
        # This ensures consistent formatting and includes necessary metadata
        write_project_state_yaml(state_file_path, state_data)
        logger.info(f"State file successfully written: {state_file_path}")
    except Exception as e:
        logger.error(f"Failed to write state file: {e}")
        return 1

    logger.info("T016 completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
