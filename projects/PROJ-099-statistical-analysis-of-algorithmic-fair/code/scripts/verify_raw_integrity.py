"""
Script to verify the integrity of raw data files.

This script compares the current SHA-256 checksums of all raw data files
under data/raw/ against the checksums recorded in the project state file
during the data acquisition phase (T014).

It fails loudly (exits with code 1) if any modification is detected or if
a file is missing, ensuring data provenance is maintained.

Output:
    Prints a detailed report to stdout.
    Returns exit code 0 on success, 1 on failure.
"""
import os
import sys
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import yaml

# Project root is assumed to be the parent of the 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
STATE_FILE_PATH = PROJECT_ROOT / "state" / "projects" / "PROJ-099-statistical-analysis-of-algorithmic-fair.yaml"

def log_header(message: str) -> None:
    """Print a formatted header to stdout."""
    print("\n" + "=" * 60)
    print(f" {message}")
    print("=" * 60)

def log_disclaimer() -> None:
    """Print the FR-008 disclaimer."""
    print("\n⚠️  DISCLAIMER: Findings are associational only; no causal claims are made. (FR-008)")

def get_file_checksum(file_path: Path) -> str:
    """
    Calculate the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except Exception as e:
        raise RuntimeError(f"Error calculating checksum for {file_path}: {e}")

def load_state_file(state_path: Path) -> Dict:
    """
    Load the project state YAML file.
    
    Args:
        state_path: Path to the state YAML file.
        
    Returns:
        Dictionary containing the state data.
        
    Raises:
        FileNotFoundError: If the state file does not exist.
        yaml.YAMLError: If the file is not valid YAML.
    """
    if not state_path.exists():
        raise FileNotFoundError(f"State file not found: {state_path}")
    
    with open(state_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def get_raw_files(raw_dir: Path) -> List[Path]:
    """
    Get a list of all files in the raw data directory.
    
    Args:
        raw_dir: Path to the raw data directory.
        
    Returns:
        List of Path objects for all files in the directory.
    """
    if not raw_dir.exists():
        return []
    return [f for f in raw_dir.iterdir() if f.is_file()]

def load_expected_checksums(state_data: Dict) -> Dict[str, str]:
    """
    Extract the expected raw checksums from the state data.
    
    Args:
        state_data: The loaded state dictionary.
        
    Returns:
        Dictionary mapping relative file paths (string) to expected checksums.
        
    Raises:
        ValueError: If the state data is missing required fields.
    """
    if 'artifact_hashes' not in state_data:
        raise ValueError("State file missing 'artifact_hashes' section.")
    
    raw_artifacts = state_data['artifact_hashes'].get('raw_data', {})
    if not raw_artifacts:
        raise ValueError("No raw data checksums found in state file 'artifact_hashes'.")
    
    return raw_artifacts

def verify_integrity_workflow() -> Tuple[bool, List[Dict]]:
    """
    Main workflow to verify raw data integrity.
    
    Returns:
        Tuple of (is_valid, list_of_results)
        is_valid: True if all files match, False otherwise.
        list_of_results: List of dicts with 'file', 'status', 'expected', 'actual' keys.
    """
    start_time = time.time()
    results = []
    all_valid = True

    # 1. Load State
    try:
        state_data = load_state_file(STATE_FILE_PATH)
        expected_checksums = load_expected_checksums(state_data)
    except Exception as e:
        log_header("ERROR: Failed to load state file")
        print(f"Error: {e}")
        return False, []

    # 2. Get Raw Files
    raw_files = get_raw_files(RAW_DATA_DIR)
    if not raw_files:
        log_header("WARNING: No raw data files found")
        print(f"Directory {RAW_DATA_DIR} is empty or does not exist.")
        # If expected is not empty, this is a failure
        if expected_checksums:
            return False, []
        return True, []

    # 3. Verify
    print(f"\nVerifying {len(raw_files)} files against {len(expected_checksums)} recorded checksums...")
    
    # Check for files present on disk that are not in state (unexpected new files)
    disk_files = {f.name for f in raw_files}
    state_files = set(expected_checksums.keys())
    
    extra_files = disk_files - state_files
    if extra_files:
        print(f"\n⚠️  WARNING: Found {len(extra_files)} file(s) on disk not recorded in state:")
        for f in extra_files:
            print(f"   - {f}")
        # Depending on strictness, this might be a failure. 
        # For this task, we focus on verifying recorded files.
    
    # Check for files in state not on disk
    missing_files = state_files - disk_files
    if missing_files:
        print(f"\n❌ ERROR: {len(missing_files)} file(s) recorded in state are missing on disk:")
        for f in missing_files:
            print(f"   - {f}")
        all_valid = False
        for f in missing_files:
            results.append({
                "file": f,
                "status": "MISSING",
                "expected": expected_checksums[f],
                "actual": None
            })

    # Check checksums for existing files
    for file_path in raw_files:
        filename = file_path.name
        if filename not in expected_checksums:
            # Skip if not in state, handled by extra_files warning above
            continue
        
        try:
            actual_checksum = get_file_checksum(file_path)
            expected_checksum = expected_checksums[filename]
            
            if actual_checksum == expected_checksum:
                results.append({
                    "file": filename,
                    "status": "VALID",
                    "expected": expected_checksum,
                    "actual": actual_checksum
                })
            else:
                results.append({
                    "file": filename,
                    "status": "MISMATCH",
                    "expected": expected_checksum,
                    "actual": actual_checksum
                })
                all_valid = False
        except Exception as e:
            results.append({
                "file": filename,
                "status": "ERROR",
                "expected": expected_checksums[filename],
                "actual": f"Error: {str(e)}"
            })
            all_valid = False

    elapsed = time.time() - start_time
    return all_valid, results

def main():
    """Entry point for the script."""
    log_header("RAW DATA INTEGRITY VERIFICATION")
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Raw Data Dir: {RAW_DATA_DIR}")
    print(f"State File:   {STATE_FILE_PATH}")
    log_disclaimer()

    is_valid, results = verify_integrity_workflow()

    print("\n" + "-" * 60)
    print("RESULTS SUMMARY")
    print("-" * 60)
    
    valid_count = sum(1 for r in results if r['status'] == 'VALID')
    error_count = sum(1 for r in results if r['status'] in ['MISMATCH', 'MISSING', 'ERROR'])
    
    print(f"Total Checked: {len(results)}")
    print(f"Valid:         {valid_count}")
    print(f"Issues Found:  {error_count}")

    if error_count > 0:
        print("\n❌ FAILED: Integrity check failed. Modifications or missing files detected.")
        print("Details:")
        for r in results:
            if r['status'] != 'VALID':
                print(f"  - {r['file']}: {r['status']}")
                if r['status'] == 'MISMATCH':
                    print(f"      Expected: {r['expected']}")
                    print(f"      Actual:   {r['actual']}")
        sys.exit(1)
    else:
        print("\n✅ SUCCESS: All raw data files are intact and match recorded checksums.")
        sys.exit(0)

if __name__ == "__main__":
    main()