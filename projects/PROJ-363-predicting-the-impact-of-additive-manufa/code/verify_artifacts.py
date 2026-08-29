"""
Task T040: Verify all artifacts in state.yaml match the latest hashes.

This script loads the state.yaml file, iterates through all registered artifacts,
computes their current SHA-256 hashes, and compares them against the stored values.
It exits with code 0 if all match, or code 1 if any mismatch or missing file is found.
"""
import os
import sys
import logging
import hashlib
from pathlib import Path

# Import shared utilities from the project
from utils import load_state, setup_logging

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Artifact file not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_artifacts() -> bool:
    """
    Verify all artifacts listed in state.yaml against their stored hashes.
    
    Returns:
        True if all artifacts match, False otherwise.
    """
    state_path = Path("state/state.yaml")
    if not state_path.exists():
        logging.error("state.yaml not found at state/state.yaml")
        return False

    state = load_state(state_path)
    
    if "artifacts" not in state:
        logging.warning("No artifacts section found in state.yaml")
        return True  # Nothing to verify

    artifacts = state["artifacts"]
    all_match = True
    mismatch_count = 0
    missing_count = 0

    logging.info(f"Verifying {len(artifacts)} artifacts...")

    for artifact_name, artifact_info in artifacts.items():
        file_path = Path(artifact_info.get("path"))
        stored_hash = artifact_info.get("hash")

        if not file_path.exists():
            logging.error(f"MISSING: {artifact_name} -> {file_path}")
            missing_count += 1
            all_match = False
            continue

        try:
            current_hash = compute_file_hash(file_path)
            if current_hash != stored_hash:
                logging.error(
                    f"MISMATCH: {artifact_name} -> {file_path}\n"
                    f"  Expected: {stored_hash}\n"
                    f"  Found:    {current_hash}"
                )
                mismatch_count += 1
                all_match = False
            else:
                logging.debug(f"OK: {artifact_name} -> {file_path}")
        except Exception as e:
            logging.error(f"ERROR reading {artifact_name}: {e}")
            all_match = False

    if missing_count > 0:
        logging.error(f"Summary: {missing_count} missing, {mismatch_count} mismatched.")
    elif mismatch_count > 0:
        logging.error(f"Summary: {mismatch_count} mismatched.")
    else:
        logging.info("Summary: All artifacts verified successfully.")

    return all_match

def main():
    """Entry point for the verification script."""
    setup_logging(level=logging.INFO)
    
    logging.info("Starting artifact verification (T040)...")
    
    try:
        success = verify_artifacts()
        if success:
            logging.info("Verification PASSED.")
            sys.exit(0)
        else:
            logging.error("Verification FAILED.")
            sys.exit(1)
    except Exception as e:
        logging.critical(f"Verification failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
