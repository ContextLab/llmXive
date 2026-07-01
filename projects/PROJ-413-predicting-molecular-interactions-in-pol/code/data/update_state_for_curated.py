"""
Update project state with SHA256 hash of the curated dataset.

This script computes the SHA256 hash of `data/curated/curated_dataset.csv`
and updates the project state YAML file located at
`state/projects/PROJ-413-predicting-molecular-interactions-in-pol.yaml`.
It uses the utility functions from `code/utils/hash_state.py`.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path to allow relative imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from utils.hash_state import compute_sha256, update_state_yaml
from utils.exceptions import DataError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    curated_path = project_root / "data" / "curated" / "curated_dataset.csv"
    state_file = project_root / "state" / "projects" / "PROJ-413-predicting-molecular-interactions-in-pol.yaml"

    if not curated_path.exists():
        logger.error(f"Curated dataset not found at {curated_path}. "
                     "Please ensure T016 has been completed.")
        raise DataError(f"Curated dataset not found: {curated_path}")

    if not state_file.parent.exists():
        logger.info(f"Creating state directory: {state_file.parent}")
        state_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Computing SHA256 hash for {curated_path}...")
    file_hash = compute_sha256(curated_path)
    logger.info(f"Hash computed: {file_hash}")

    logger.info(f"Updating state file: {state_file}")
    update_state_yaml(state_file, "curated_dataset.csv", file_hash)

    logger.info("State update completed successfully.")

if __name__ == "__main__":
    main()
