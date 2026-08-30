"""
T043: Update project state YAML with hashes for final US3 artifacts.

This script computes SHA256 hashes for:
- results/stats.csv
- results/attribution.json
- results/performance.json

And updates the project state file (state/projects/PROJ-413-*.yaml)
with these hashes under the 'us3_artifacts' section.
"""
import os
import sys
import logging
from pathlib import Path

# Import from existing utility module
from utils.hash_state import compute_sha256, update_state_yaml
from utils.exceptions import DataError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the artifacts to hash
ARTIFACTS = [
    "results/stats.csv",
    "results/attribution.json",
    "results/performance.json"
]

def main():
    project_root = Path(__file__).resolve().parent.parent
    state_dir = project_root / "state" / "projects"
    
    # Ensure state directory exists
    state_dir.mkdir(parents=True, exist_ok=True)
    
    # Find the state file for this project
    state_file = None
    for f in state_dir.glob("PROJ-413-*.yaml"):
        state_file = f
        break
    
    if not state_file:
        logger.error("No state file found for PROJ-413. Run T018 or T030 first.")
        raise DataError("No state file found for PROJ-413")
    
    logger.info(f"Using state file: {state_file}")
    
    # Compute hashes for all required artifacts
    hashes = {}
    for artifact_rel in ARTIFACTS:
        artifact_path = project_root / artifact_rel
        
        if not artifact_path.exists():
            logger.error(f"Missing required artifact: {artifact_path}")
            raise DataError(f"Missing artifact: {artifact_rel}")
        
        hash_value = compute_sha256(artifact_path)
        hashes[artifact_rel] = hash_value
        logger.info(f"Hashed {artifact_rel}: {hash_value[:16]}...")
    
    # Update the state YAML file
    update_state_yaml(
        state_file=state_file,
        key_path="us3_artifacts",
        data=hashes
    )
    
    logger.info(f"Successfully updated {state_file} with US3 artifact hashes")
    return 0

if __name__ == "__main__":
    sys.exit(main())