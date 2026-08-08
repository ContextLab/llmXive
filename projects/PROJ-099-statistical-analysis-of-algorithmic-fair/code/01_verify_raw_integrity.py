"""
T019b: Explicitly verify that raw data files under data/raw/ remain unchanged
after preprocessing completes. Fail if any modification detected.

This script implements the integrity check required by Constitution Principle III
(no in-place modification of raw data) and Task T019b.

It compares the SHA-256 checksums of raw files against the hashes recorded
during the acquisition phase (T014/T019).
"""
import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent directory to path to allow imports from code/
code_dir = Path(__file__).resolve().parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils.validators import compute_sha256, verify_checksum
from utils.logging_utils import log_warning, log_exclusion
from data_model import Dataset  # Using the class if needed for typing, though not strictly used here

# FR-008 Disclaimer
DISCLAIMER = "Findings are associational only; no causal claims are made."

def log_header(script_name: str):
    """Print a standardized header for logging purposes."""
    print(f"--- {script_name} ---")
    print(f"Disclaimer: {DISCLAIMER}")
    print("-" * 40)

def get_raw_files(raw_dir: Path) -> List[Path]:
    """
    Retrieve all CSV files from the raw data directory.
    """
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")
    files = list(raw_dir.glob("*.csv"))
    if not files:
        raise ValueError(f"No CSV files found in {raw_dir}")
    return sorted(files)

def load_expected_checksums(state_file: Path) -> Dict[str, str]:
    """
    Load the expected checksums from the project state file.
    The state file is expected to be in YAML format with a structure like:
    artifact_hashes:
      data/raw/adult.csv: "sha256_hash_string"
      ...
    """
    import yaml
    if not state_file.exists():
        raise FileNotFoundError(f"State file not found: {state_file}")
    
    with open(state_file, 'r') as f:
        data = yaml.safe_load(f)
    
    if not data or 'artifact_hashes' not in data:
        raise ValueError(f"State file missing 'artifact_hashes' section: {state_file}")
    
    return data['artifact_hashes']

def verify_integrity_workflow(raw_dir: Path, state_file: Path) -> Tuple[bool, List[str], List[str]]:
    """
    Main workflow to verify raw data integrity.
    
    Returns:
        (all_passed, passed_files, failed_files)
    """
    raw_files = get_raw_files(raw_dir)
    expected_checksums = load_expected_checksums(state_file)
    
    passed_files = []
    failed_files = []
    missing_expected = []

    for file_path in raw_files:
        filename = file_path.name
        current_hash = compute_sha256(file_path)
        
        if filename not in expected_checksums:
            msg = f"Raw file '{filename}' has no recorded checksum in state file. Cannot verify integrity."
            log_warning(msg)
            missing_expected.append(filename)
            failed_files.append(filename)
            continue

        expected_hash = expected_checksums[filename]
        
        if current_hash == expected_hash:
            passed_files.append(filename)
            print(f"✓ PASS: {filename} (Integrity Verified)")
        else:
            msg = f"✗ FAIL: {filename} - Hash mismatch. Expected: {expected_hash[:16]}..., Got: {current_hash[:16]}..."
            log_warning(msg)
            # Log to exclusion log as a critical failure event
            log_exclusion(
                dataset_id=filename,
                missing_variable_name="INTEGRITY_CHECK",
                reason="Hash mismatch detected. File may have been modified."
            )
            failed_files.append(filename)

    all_passed = len(failed_files) == 0 and len(missing_expected) == 0
    return all_passed, passed_files, failed_files

def main():
    log_header("T019b: Raw Data Integrity Verification")
    
    project_root = code_dir.parent
    raw_dir = project_root / "data" / "raw"
    state_file = project_root / "state" / "projects" / "PROJ-099-statistical-analysis-of-algorithmic-fair.yaml"
    
    try:
        all_passed, passed, failed = verify_integrity_workflow(raw_dir, state_file)
        
        print("-" * 40)
        print(f"Total Checked: {len(passed) + len(failed)}")
        print(f"Passed: {len(passed)}")
        print(f"Failed: {len(failed)}")
        
        if not all_passed:
            print("\nCRITICAL: Raw data integrity verification FAILED.")
            print("The raw data files may have been modified during preprocessing.")
            print("Please investigate the failed files before proceeding.")
            sys.exit(1)
        else:
            print("\nSUCCESS: All raw data files remain unchanged.")
            sys.exit(0)
            
    except Exception as e:
        print(f"\nFATAL ERROR during verification: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()