"""
Verify all project artifacts have corresponding SHA256 hashes in the state YAML.

This script implements Task T053: Verify all artifacts have corresponding SHA256 
hashes in state/projects/PROJ-413-...yaml.

It checks that every artifact produced by the pipeline (data, models, analysis) 
has a recorded hash in the state file and that the computed hash matches the 
recorded one.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import yaml

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.hash_state import compute_sha256, get_state_hash
from utils.exceptions import DataError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define all expected artifacts based on completed tasks
EXPECTED_ARTIFACTS = [
    # Data pipeline artifacts (US1)
    "data/raw/molnet_raw.csv",
    "data/curated/curated_dataset.csv",
    "data/processed/descriptors.csv",
    "data/processed/graphs.pt",
    
    # Model artifacts (US2)
    "results/model.pt",
    "results/checkpoint_10.pt",
    "results/checkpoint_20.pt",
    "results/checkpoint_30.pt",
    "results/performance.json",
    
    # Analysis artifacts (US3)
    "results/permuted_mses.csv",
    "results/stats.csv",
    "results/attribution.json",
    "analysis/topology_audit.md",
    "analysis/power_analysis.md",
    
    # State file (will be updated by this script)
    "state/projects/PROJ-413-predicting-molecular-interactions-in-pol.yaml"
]

def find_state_file() -> Optional[Path]:
    """Find the state YAML file for this project."""
    state_dir = PROJECT_ROOT / "state" / "projects"
    if not state_dir.exists():
        logger.error(f"State directory not found: {state_dir}")
        return None
    
    # Look for PROJ-413 state file
    for f in state_dir.glob("PROJ-413*.yaml"):
        return f
    
    logger.error(f"No PROJ-413 state file found in {state_dir}")
    return None

def verify_artifact_hash(artifact_path: Path, state_data: Dict) -> Tuple[bool, str]:
    """
    Verify that an artifact's computed hash matches the recorded hash.
    
    Returns:
        Tuple of (is_valid, message)
    """
    if not artifact_path.exists():
        return False, f"Artifact missing: {artifact_path}"
    
    # Compute current hash
    computed_hash = compute_sha256(artifact_path)
    
    # Find in state data
    recorded_hash = None
    if "artifacts" in state_data:
        for art in state_data["artifacts"]:
            if art.get("path") == str(artifact_path.relative_to(PROJECT_ROOT)):
                recorded_hash = art.get("sha256")
                break
    
    if not recorded_hash:
        return False, f"No hash recorded for: {artifact_path}"
    
    if computed_hash != recorded_hash:
        return False, f"Hash mismatch for {artifact_path}: computed={computed_hash}, recorded={recorded_hash}"
    
    return True, f"OK: {artifact_path.name}"

def verify_all_artifacts() -> Tuple[bool, List[str]]:
    """
    Verify all expected artifacts have valid hashes in state file.
    
    Returns:
        Tuple of (all_valid, list of messages)
    """
    state_file = find_state_file()
    if not state_file:
        return False, ["State file not found"]
    
    try:
        with open(state_file, 'r') as f:
            state_data = yaml.safe_load(f)
    except Exception as e:
        return False, [f"Failed to load state file: {e}"]
    
    messages = []
    all_valid = True
    
    for artifact_path_str in EXPECTED_ARTIFACTS:
        artifact_path = PROJECT_ROOT / artifact_path_str
        is_valid, msg = verify_artifact_hash(artifact_path, state_data)
        messages.append(msg)
        if not is_valid:
            all_valid = False
            logger.warning(msg)
        else:
            logger.info(msg)
    
    return all_valid, messages

def main():
    """Main entry point for artifact verification."""
    logger.info("Starting artifact verification for T053...")
    
    all_valid, messages = verify_all_artifacts()
    
    print("\n" + "="*60)
    print("ARTIFACT VERIFICATION RESULTS")
    print("="*60)
    for msg in messages:
        print(msg)
    print("="*60)
    
    if all_valid:
        logger.info("✓ All artifacts verified successfully!")
        print("✓ All artifacts verified successfully!")
        return 0
    else:
        logger.error("✗ Some artifacts failed verification.")
        print("✗ Some artifacts failed verification.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
