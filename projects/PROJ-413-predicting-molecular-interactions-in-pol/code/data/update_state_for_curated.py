"""
Update the project state file with the hash of the curated dataset.
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Paths
CURATED_PATH = project_root / "data" / "curated" / "curated_dataset.csv"
STATE_PATH = project_root / "state" / "projects" / "PROJ-413-predicting-molecular-interactions-in-pol.yaml"

def main():
    """
    Main function to update the state file with the curated dataset hash.
    """
    logger.info("Starting state update for curated dataset...")
    
    if not CURATED_PATH.exists():
        raise DataError(f"Curated dataset not found at {CURATED_PATH}. "
                        "Please run code/data/generate_curated.py first.")
    
    # Compute hash
    logger.info(f"Computing SHA256 hash of {CURATED_PATH}")
    hash_value = compute_sha256(CURATED_PATH)
    logger.info(f"Hash: {hash_value}")
    
    # Update state file
    if not STATE_PATH.exists():
        raise DataError(f"State file not found at {STATE_PATH}")
    
    logger.info(f"Updating state file at {STATE_PATH}")
    update_state_yaml(STATE_PATH, "artifact_hashes.curated_dataset", hash_value)
    
    logger.info("State update completed successfully.")

if __name__ == "__main__":
    main()