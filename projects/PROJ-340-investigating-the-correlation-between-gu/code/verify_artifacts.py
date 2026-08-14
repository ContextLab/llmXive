"""
Artifact Checksum Verification Script.

This script recalculates SHA256 checksums for all generated artifacts
defined in the project state file and compares them against the
recorded checksums in `state/projects/PROJ-340-investigating-the-correlation-between-gu.yaml`.

It addresses Constitution Principle III by ensuring data integrity
and detecting any tampering or corruption of pipeline outputs.

Usage:
    python code/verify_artifacts.py
"""
import os
import sys
import json
import hashlib
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
STATE_FILE = PROJECT_ROOT / "state" / "projects" / "PROJ-340-investigating-the-correlation-between-gu.yaml"

# Artifacts to verify (derived from task descriptions and expected outputs)
# These are the critical outputs that must be tracked for integrity
ARTIFACTS_TO_VERIFY = [
    "data/raw/synthetic_data.csv",
    "data/processed/filtered_data.parquet",
    "data/results/variable_load_metrics.json",
    "data/results/outlier_report.json",
    "data/results/correlation_matrix.json",
    "data/results/sensitivity_analysis.json",
    "data/results/vif_report.json",
    "data/results/power_analysis.json",
    "data/results/timing_evidence.json",
    "data/results/final_report.md",
    "data/metadata/method_selection_log.json",
    "data/metadata/static_collinearity_map.json",
    "data/metadata/compositionality_flag.json",
    "data/metadata/validation_mode_flag.json",
    "data/config/required_variables.yaml",
]

def calculate_file_checksum(file_path: Path) -> Optional[str]:
    """
    Calculate SHA256 checksum of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hex string of the SHA256 hash, or None if file doesn't exist.
    """
    if not file_path.exists():
        return None
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def load_state_file() -> Dict:
    """
    Load the project state file containing recorded checksums.
    
    Returns:
        Dictionary containing the state file contents.
        
    Raises:
        FileNotFoundError: If the state file doesn't exist.
        yaml.YAMLError: If the state file is malformed.
    """
    if not STATE_FILE.exists():
        raise FileNotFoundError(f"State file not found: {STATE_FILE}")
    
    with open(STATE_FILE, "r") as f:
        return yaml.safe_load(f)

def verify_artifacts() -> Tuple[bool, List[Dict]]:
    """
    Verify all registered artifacts against stored checksums.
    
    Returns:
        Tuple of (all_passed: bool, details: List[Dict])
        where details contains the status of each artifact.
    """
    if not STATE_FILE.exists():
        print(f"Error: State file not found at {STATE_FILE}")
        print("No checksums to verify against. Please ensure the pipeline has run and recorded checksums.")
        return False, []

    try:
        state_data = load_state_file()
    except Exception as e:
        print(f"Error loading state file: {e}")
        return False, []

    artifact_hashes = state_data.get("artifact_hashes", {})
    all_passed = True
    results = []

    print(f"{'Artifact':<50} {'Status':<10} {'Expected':<16} {'Actual':<16}")
    print("-" * 92)

    # Check all artifacts defined in our list
    for artifact_path in ARTIFACTS_TO_VERIFY:
        full_path = PROJECT_ROOT / artifact_path
        relative_path = artifact_path
        
        # Get expected checksum from state file
        expected_hash = artifact_hashes.get(relative_path)
        
        if expected_hash is None:
            # Check if file exists but wasn't recorded
            if full_path.exists():
                status = "MISSING_RECORD"
                all_passed = False
                actual_hash = calculate_file_checksum(full_path)
                results.append({
                    "path": relative_path,
                    "status": status,
                    "expected": None,
                    "actual": actual_hash,
                    "message": "File exists but no checksum recorded in state file."
                })
                print(f"{relative_path:<50} {status:<10} {'N/A':<16} {actual_hash[:16] if actual_hash else 'N/A':<16}")
            else:
                status = "MISSING_FILE"
                all_passed = False
                results.append({
                    "path": relative_path,
                    "status": status,
                    "expected": None,
                    "actual": None,
                    "message": "File does not exist and no checksum recorded."
                })
                print(f"{relative_path:<50} {status:<10} {'N/A':<16} {'N/A':<16}")
            continue

        # Remove 'sha256:' prefix if present
        expected_hash_clean = expected_hash
        if expected_hash.startswith("sha256:"):
            expected_hash_clean = expected_hash[7:]

        # Calculate actual checksum
        actual_hash = calculate_file_checksum(full_path)

        if actual_hash is None:
            status = "FILE_NOT_FOUND"
            all_passed = False
            results.append({
                "path": relative_path,
                "status": status,
                "expected": expected_hash_clean,
                "actual": None,
                "message": "File does not exist."
            })
            print(f"{relative_path:<50} {status:<10} {expected_hash_clean:<16} {'N/A':<16}")
        elif actual_hash == expected_hash_clean:
            status = "PASS"
            results.append({
                "path": relative_path,
                "status": status,
                "expected": expected_hash_clean,
                "actual": actual_hash,
                "message": "Checksum verified."
            })
            print(f"{relative_path:<50} {status:<10} {expected_hash_clean:<16} {actual_hash[:16]:<16}")
        else:
            status = "MISMATCH"
            all_passed = False
            results.append({
                "path": relative_path,
                "status": status,
                "expected": expected_hash_clean,
                "actual": actual_hash,
                "message": "Checksum mismatch detected!"
            })
            print(f"{relative_path:<50} {status:<10} {expected_hash_clean:<16} {actual_hash[:16]:<16}")

    # Check for extra artifacts in state file that aren't in our list
    for recorded_path in artifact_hashes.keys():
        if recorded_path not in ARTIFACTS_TO_VERIFY:
            full_path = PROJECT_ROOT / recorded_path
            if full_path.exists():
                actual_hash = calculate_file_checksum(full_path)
                expected_hash = artifact_hashes[recorded_path]
                if expected_hash.startswith("sha256:"):
                    expected_hash = expected_hash[7:]
                
                if actual_hash and actual_hash == expected_hash:
                    status = "PASS (UNLISTED)"
                    print(f"{recorded_path:<50} {status:<10} {expected_hash:<16} {actual_hash[:16]:<16}")
                else:
                    status = "MISMATCH (UNLISTED)"
                    all_passed = False
                    print(f"{recorded_path:<50} {status:<10} {expected_hash:<16} {actual_hash[:16] if actual_hash else 'N/A':<16}")

    return all_passed, results

def main():
    """Main entry point for the verification script."""
    print("=" * 92)
    print("ARTIFACT CHECKSUM VERIFICATION")
    print("Constitution Principle III: Data Integrity Check")
    print("=" * 92)
    print()

    if not STATE_FILE.exists():
        print("ERROR: State file not found.")
        print("The pipeline must run successfully at least once to record checksums.")
        sys.exit(1)

    all_passed, results = verify_artifacts()

    print()
    print("=" * 92)
    if all_passed:
        print("RESULT: ALL ARTIFACTS VERIFIED SUCCESSFULLY")
        print("Constitution Principle III satisfied.")
        sys.exit(0)
    else:
        print("RESULT: VERIFICATION FAILED")
        print("One or more artifacts are missing, corrupted, or tampered with.")
        print("Please investigate the failures above.")
        sys.exit(1)

if __name__ == "__main__":
    main()