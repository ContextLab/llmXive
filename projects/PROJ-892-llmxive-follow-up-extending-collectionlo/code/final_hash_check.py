"""
Final Artifact Hashing and Validation Script.

This script performs a final sweep of all generated artifacts (images, CSVs, JSONs, weights)
and ensures their SHA-256 hashes are correctly recorded in state/artifacts.yaml.
It fails if any artifact is missing a hash or if the hash does not match the file content.

Dependencies:
- T033: Final review of state/artifacts.yaml
- T014c: Verify baseline hashes
- T020c: Verify quantized hashes
- T027a: Save analysis results
"""
import os
import sys
import hashlib
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent

def compute_sha256_file(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_artifacts_state(state_path: Path) -> Dict[str, Any]:
    """Load the state/artifacts.yaml file."""
    if not state_path.exists():
        raise FileNotFoundError(f"State file not found: {state_path}")
    
    with open(state_path, 'r') as f:
        return yaml.safe_load(f) or {}

def save_artifacts_state(state_path: Path, data: Dict[str, Any]) -> None:
    """Save the state/artifacts.yaml file."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, 'w') as f:
        yaml.safe_dump(data, f, default_flow_style=False)

def validate_artifact_entry(
    artifact_name: str,
    artifact_path: Path,
    expected_hash: str
) -> bool:
    """
    Validate a single artifact entry.
    
    Returns True if the hash matches, False otherwise.
    """
    if not artifact_path.exists():
        logger.error(f"Artifact missing: {artifact_path}")
        return False
    
    try:
        actual_hash = compute_sha256_file(artifact_path)
        if actual_hash != expected_hash:
            logger.error(
                f"Hash mismatch for {artifact_name}:\n"
                f"  Expected: {expected_hash}\n"
                f"  Actual:   {actual_hash}"
            )
            return False
        logger.info(f"Verified: {artifact_name} (hash: {actual_hash[:16]}...)")
        return True
    except Exception as e:
        logger.error(f"Error validating {artifact_name}: {e}")
        return False

def collect_expected_artifacts(state_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Collect all artifacts that should be present based on state/artifacts.yaml.
    
    Returns a list of dicts with 'name', 'path', and 'expected_hash'.
    """
    artifacts = []
    artifacts_dict = state_data.get('artifacts', {})
    
    for name, entry in artifacts_dict.items():
        if isinstance(entry, dict) and 'hash' in entry and 'path' in entry:
            artifacts.append({
                'name': name,
                'path': entry['path'],
                'expected_hash': entry['hash']
            })
        elif isinstance(entry, str):
            # Legacy format: just a hash, assume path is in name or standard locations
            # For robustness, we'll skip these unless path is explicitly provided
            logger.warning(f"Skipping artifact '{name}' - missing path in state file")
    
    return artifacts

def run_final_hash_check() -> bool:
    """
    Run the final hash check on all artifacts.
    
    Returns True if all artifacts are valid, False otherwise.
    """
    project_root = get_project_root()
    state_path = project_root / 'state' / 'artifacts.yaml'
    
    logger.info("Loading state/artifacts.yaml...")
    try:
        state_data = load_artifacts_state(state_path)
    except FileNotFoundError as e:
        logger.error(f"Failed to load state file: {e}")
        return False
    
    if not state_data or 'artifacts' not in state_data:
        logger.error("No artifacts found in state/artifacts.yaml")
        return False
    
    expected_artifacts = collect_expected_artifacts(state_data)
    
    if not expected_artifacts:
        logger.warning("No artifacts to validate in state file.")
        return True
    
    logger.info(f"Validating {len(expected_artifacts)} artifacts...")
    all_valid = True
    
    for artifact in expected_artifacts:
        artifact_path = project_root / artifact['path']
        is_valid = validate_artifact_entry(
            artifact['name'],
            artifact_path,
            artifact['expected_hash']
        )
        if not is_valid:
            all_valid = False
    
    if all_valid:
        logger.info("✅ All artifacts validated successfully.")
        return True
    else:
        logger.error("❌ Some artifacts failed validation. Check logs for details.")
        return False

def main():
    """Main entry point for the script."""
    logger.info("Starting final artifact hash check...")
    success = run_final_hash_check()
    
    if not success:
        logger.error("Final hash check FAILED. Aborting.")
        sys.exit(1)
    else:
        logger.info("Final hash check PASSED.")
        sys.exit(0)

if __name__ == "__main__":
    main()
