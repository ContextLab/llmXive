import os
import sys
import tempfile
import yaml
import hashlib
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "code"))

from versioning import compute_sha256, load_state, save_state, invalidate_stale_reviews, update_version_state

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("versioning_verification")

def create_dummy_artifact(path: Path, content: str = "dummy content for verification"):
    """Creates a dummy file artifact for testing."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)
    logger.info(f"Created dummy artifact at: {path}")

def main():
    logger.info("Starting versioning verification task T005b")
    
    # Define paths relative to project root
    state_file = project_root / "state" / "projects" / "PROJ-786-multi-property-trade-offs-in-alloy-desig.yaml"
    reviews_file = project_root / "state" / "projects" / "PROJ-786-multi-property-trade-offs-in-alloy-desig_reviews.yaml"
    
    # Ensure state directory exists
    state_file.parent.mkdir(parents=True, exist_ok=True)
    reviews_file.parent.mkdir(parents=True, exist_ok=True)

    # 1. Create a dummy artifact to hash
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
        tmp.write("Test content for versioning verification")
        tmp_path = Path(tmp.name)
    
    try:
        # 2. Compute hash of the dummy artifact
        artifact_hash = compute_sha256(tmp_path)
        logger.info(f"Computed SHA-256 for dummy artifact: {artifact_hash}")

        # 3. Load current state (or initialize if missing)
        if not state_file.exists():
            logger.info(f"State file {state_file} not found. Initializing new state.")
            current_state = {
                "project_id": "PROJ-786-multi-property-trade-offs-in-alloy-desig",
                "artifact_hashes": {},
                "updated_at": None,
                "version": 1
            }
        else:
            logger.info(f"Loading existing state from {state_file}")
            current_state = load_state(state_file)

        # 4. Update state with new artifact hash
        old_hash = current_state.get("artifact_hashes", {}).get(tmp_path.name)
        current_state["artifact_hashes"][tmp_path.name] = artifact_hash
        current_state["updated_at"] = datetime.utcnow().isoformat()
        
        # 5. Invalidate stale reviews if hash changed
        if old_hash and old_hash != artifact_hash:
            logger.warning(f"Hash changed for {tmp_path.name}. Invalidating stale reviews.")
            invalidate_stale_reviews(reviews_file, tmp_path.name, old_hash)
        elif not old_hash:
            logger.info(f"New artifact {tmp_path.name} detected. No invalidation needed.")
        else:
            logger.info(f"Hash unchanged for {tmp_path.name}.")

        # 6. Save updated state
        save_state(current_state, state_file)
        logger.info(f"Successfully updated state file: {state_file}")

        # 7. Verification: Reload and print
        verified_state = load_state(state_file)
        logger.info(f"Verification: State updated at {verified_state['updated_at']}")
        logger.info(f"Verification: Artifact hash in state: {verified_state['artifact_hashes'].get(tmp_path.name)}")
        
        if verified_state["artifact_hashes"].get(tmp_path.name) == artifact_hash:
            logger.info("SUCCESS: Versioning verification completed. State updated correctly.")
            return 0
        else:
            logger.error("FAILURE: Hash mismatch in state file.")
            return 1

    finally:
        # Cleanup dummy artifact
        if tmp_path.exists():
            tmp_path.unlink()
            logger.info(f"Cleaned up dummy artifact: {tmp_path}")

if __name__ == "__main__":
    sys.exit(main())