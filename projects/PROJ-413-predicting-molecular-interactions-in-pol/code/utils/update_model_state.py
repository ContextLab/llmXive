"""
Update project state YAML with hashes for trained model and processed graphs.

This script computes SHA256 hashes for `results/model.pt` and `data/processed/graphs.pt`
and updates the project state file at `state/projects/PROJ-413-...yaml`.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.hash_state import compute_sha256, update_state_yaml
from utils.exceptions import DataError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define artifact paths relative to project root
MODEL_PATH = project_root / "results" / "model.pt"
GRAPHS_PATH = project_root / "data" / "processed" / "graphs.pt"
STATE_DIR = project_root / "state" / "projects"
PROJECT_ID = "PROJ-413-predicting-molecular-interactions-in-pol"

def find_state_file():
    """Find the specific state YAML file for this project."""
    if not STATE_DIR.exists():
        raise DataError(f"State directory not found: {STATE_DIR}")
    
    pattern = f"{PROJECT_ID}*.yaml"
    matches = list(STATE_DIR.glob(pattern))
    
    if not matches:
        raise DataError(f"No state file found matching pattern: {pattern}")
    
    if len(matches) > 1:
        logger.warning(f"Multiple state files found: {matches}. Using the first one.")
    
    return matches[0]

def main():
    """Main entry point to update state with model and graph hashes."""
    logger.info("Starting state update for model and graphs artifacts.")

    # Check if artifacts exist
    if not MODEL_PATH.exists():
        raise DataError(f"Model artifact not found: {MODEL_PATH}")
    if not GRAPHS_PATH.exists():
        raise DataError(f"Graphs artifact not found: {GRAPHS_PATH}")

    state_file = find_state_file()
    logger.info(f"Found state file: {state_file}")

    # Compute hashes
    logger.info(f"Computing hash for: {MODEL_PATH}")
    model_hash = compute_sha256(MODEL_PATH)
    logger.info(f"Model hash: {model_hash}")

    logger.info(f"Computing hash for: {GRAPHS_PATH}")
    graphs_hash = compute_sha256(GRAPHS_PATH)
    logger.info(f"Graphs hash: {graphs_hash}")

    # Update state file
    artifacts = {
        "results/model.pt": model_hash,
        "data/processed/graphs.pt": graphs_hash
    }

    try:
        update_state_yaml(state_file, artifacts)
        logger.info(f"Successfully updated state file: {state_file}")
        logger.info("State update completed.")
        return 0
    except Exception as e:
        logger.error(f"Failed to update state file: {e}")
        raise DataError(f"State update failed: {e}")

if __name__ == "__main__":
    sys.exit(main())