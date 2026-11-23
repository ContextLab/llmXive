"""
Artifact Verification Module (T050)

Verifies existence, checksums, and schema validity of all pipeline artifacts
against the state.yaml registry.
"""

import os
import sys
import logging
import hashlib
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import local project modules based on API surface
from config import get_project_root, get_config_dict
from state_manager import load_state, verify_file, verify_all

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("verify_artifacts")

# Define the artifacts to verify as per T050 requirements
REQUIRED_ARTIFACTS = [
    "data/processed/ingested_cohort.parquet",
    "data/processed/user_track_pairs.parquet",
    "data/final/regression_summary.csv",
    "data/final/sensitivity_analysis.csv",
    "data/final/bootstrap_results.csv"
]

def calculate_file_checksum(file_path: Path) -> str:
    """
    Calculate SHA-256 checksum of a file.

    Args:
        file_path: Path to the file

    Returns:
        Hex digest of the SHA-256 hash
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Failed to calculate checksum for {file_path}: {e}")
        raise

def validate_schema(file_path: Path, schema_type: str) -> bool:
    """
    Validate a file against its corresponding schema.

    Note: For this implementation, we perform basic structural validation.
    A full schema validator would load contracts/ schemas and validate.
    """
    if not file_path.exists():
        return False

    try:
        ext = file_path.suffix.lower()
        if ext == '.csv':
            import pandas as pd
            pd.read_csv(file_path)
        elif ext == '.parquet':
            import pandas as pd
            pd.read_parquet(file_path)
        else:
            # Unknown format, skip deep validation
            pass
        return True
    except Exception as e:
        logger.error(f"Schema validation failed for {file_path}: {e}")
        return False

def verify_artifacts() -> bool:
    """
    Main verification routine for T050.

    Checks:
    1. Existence of all required artifacts
    2. Checksums match state.yaml
    3. Basic schema validity

    Returns:
        True if all checks pass, False otherwise.
        Raises RuntimeError if any critical check fails.
    """
    project_root = get_project_root()
    state_path = project_root / "state.yaml"

    # Load state
    if not state_path.exists():
        logger.error("state.yaml not found. Cannot verify artifacts.")
        raise RuntimeError("state.yaml not found. Cannot verify artifacts.")

    try:
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load state.yaml: {e}")
        raise RuntimeError(f"Failed to load state.yaml: {e}")

    # Use state_manager's verify_all if available, otherwise manual check
    # Manual check for specific T050 requirements
    all_passed = True

    logger.info(f"Verifying {len(REQUIRED_ARTIFACTS)} artifacts...")

    for rel_path in REQUIRED_ARTIFACTS:
        full_path = project_root / rel_path

        # 1. Existence Check
        if not full_path.exists():
            logger.error(f"MISSING: {rel_path}")
            all_passed = False
            continue

        # 2. Checksum Check
        current_checksum = calculate_file_checksum(full_path)
        registered_entry = state.get("files", {}).get(rel_path, {})
        registered_checksum = registered_entry.get("checksum")

        if not registered_checksum:
            logger.warning(f"NO CHECKSUM REGISTERED: {rel_path}")
            # Depending on strictness, this might be a failure.
            # T050 says "Compare against state.yaml". If missing, we can't compare.
            # We will log but not fail unless we find a mismatch.
            # However, T050 criteria: "If mismatch, Raise RuntimeError".
            # If missing in state, it's a mismatch with "expected".
            # Let's treat missing checksum in state as a failure for T050 strictness.
            all_passed = False
            logger.error(f"CHECKSUM MISMATCH (Missing in state): {rel_path}")
            continue

        if current_checksum != registered_checksum:
            logger.error(f"CHECKSUM MISMATCH: {rel_path}")
            logger.error(f"  Expected: {registered_checksum}")
            logger.error(f"  Found:    {current_checksum}")
            all_passed = False
            continue

        # 3. Schema Check
        if not validate_schema(full_path, rel_path):
            logger.error(f"SCHEMA INVALID: {rel_path}")
            all_passed = False
            continue

        logger.info(f"OK: {rel_path} (Checksum: {current_checksum[:8]}...)")

    if not all_passed:
        logger.error("Artifact verification FAILED.")
        raise RuntimeError("Artifact verification failed. See logs for details.")

    logger.info("Artifact verification PASSED.")
    return True

def main():
    """Entry point for the verification script."""
    try:
        verify_artifacts()
        logger.info("All checks passed. Exiting with code 0.")
        sys.exit(0)
    except RuntimeError as e:
        logger.error(f"Verification failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()