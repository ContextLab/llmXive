"""
T019 Implementation: Verify Raw Data Integrity.

This module computes SHA-256 hashes of raw data files before processing
and recomputes them after any transformation to ensure no in-place
modification occurred, adhering to Constitution Principle III.

It also provides a workflow to verify that raw files remain unchanged
after the preprocessing pipeline has run.
"""
import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import time

# Add project root to path to allow relative imports if running as script
# but primarily designed to be imported or run within the project context.
sys.path.insert(0, str(Path(__file__).parent))

from utils.validators import compute_sha256, verify_checksum
from utils.logging_utils import log_warning, log_exclusion


def log_header(message: str) -> None:
    """Print a formatted header to stdout and log to exclusion log if needed."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    header = f"[{timestamp}] {message}"
    print(header)
    # Note: This specific log header doesn't necessarily go to exclusion log
    # unless it's a warning or error, but we print it for visibility.


def get_raw_files(raw_dir: Path) -> List[Path]:
    """
    Retrieve all CSV files from the raw data directory.

    Args:
        raw_dir: Path to data/raw/

    Returns:
        List of Path objects pointing to CSV files.
    """
    if not raw_dir.exists():
        log_header(f"ERROR: Raw data directory not found: {raw_dir}")
        return []
    
    files = list(raw_dir.glob("*.csv"))
    if not files:
        log_header(f"WARNING: No CSV files found in {raw_dir}")
    return sorted(files)


def load_expected_checksums(state_file: Path) -> Dict[str, str]:
    """
    Load expected SHA-256 checksums from the project state YAML file.

    Args:
        state_file: Path to state/projects/PROJ-099...yaml

    Returns:
        Dictionary mapping relative file paths to their expected SHA-256 hashes.
    """
    if not state_file.exists():
        log_header(f"WARNING: State file not found at {state_file}. Cannot verify against stored checksums.")
        return {}
    
    import yaml
    try:
        with open(state_file, 'r') as f:
            state_data = yaml.safe_load(f)
        
        # The checksums are expected to be under artifact_hashes or similar structure
        # Based on T009 and T017, they are recorded in the state file.
        # Assuming a structure like: artifact_hashes: { "data/raw/adult.csv": "sha256..." }
        artifact_hashes = state_data.get('artifact_hashes', {})
        return artifact_hashes
    except Exception as e:
        log_header(f"ERROR: Failed to load state file {state_file}: {e}")
        return {}


def verify_integrity_workflow(raw_dir: Path, state_file: Path, log_file: Optional[Path] = None) -> Tuple[bool, Dict[str, str], Dict[str, str]]:
    """
    Execute the full integrity verification workflow.

    1. Compute current hashes of all raw files.
    2. Load expected hashes from state file.
    3. Compare and report mismatches.
    4. Log any discrepancies to the exclusion log.

    Args:
        raw_dir: Path to data/raw/
        state_file: Path to the project state YAML
        log_file: Optional path to the exclusion log (default: logs/exclusion.log)

    Returns:
        Tuple of (success_flag, current_hashes, expected_hashes)
        success_flag is True if all files match expected checksums.
    """
    log_header("Starting Raw Data Integrity Verification (T019)")
    print("Finding raw files...")
    raw_files = get_raw_files(raw_dir)
    
    if not raw_files:
        log_header("FAILURE: No raw files found to verify.")
        return False, {}, {}

    print(f"Found {len(raw_files)} raw file(s). Computing SHA-256 hashes...")
    current_hashes = {}
    for file_path in raw_files:
        try:
            # Compute hash
            hash_val = compute_sha256(file_path)
            current_hashes[str(file_path.relative_to(raw_dir.parent))] = hash_val
            print(f"  {file_path.name}: {hash_val[:16]}...")
        except Exception as e:
            log_header(f"ERROR: Failed to compute hash for {file_path}: {e}")
            log_exclusion(
                dataset_id=file_path.stem,
                missing_variable_name="integrity_check",
                reason=f"Hash computation failed: {e}"
            )

    print("\nLoading expected checksums from state file...")
    expected_hashes = load_expected_checksums(state_file)

    if not expected_hashes:
        log_header("WARNING: No expected checksums found in state file. Cannot perform comparison.")
        # If no expected hashes, we assume the raw files are the baseline, 
        # but strictly speaking, T019 requires comparison. 
        # We return success=False to indicate the check couldn't be fully performed against a baseline.
        return False, current_hashes, {}

    print("\nComparing checksums...")
    all_match = True
    mismatches = []

    # Check all expected files exist and match
    for rel_path, expected_hash in expected_hashes.items():
        full_path = raw_dir.parent / rel_path
        
        if full_path not in [raw_dir.parent / k for k in current_hashes.keys()]:
            # File expected but not found in current scan (might be in subdirs or deleted)
            # We look for it specifically
            found = False
            for f in raw_files:
                if f.name in rel_path: # Simple name match if path structure varies slightly
                    found = True
                    break
            
            if not found:
                log_header(f"FAILURE: Expected file not found: {rel_path}")
                all_match = False
                mismatches.append(rel_path)
                continue

        if rel_path in current_hashes:
            actual = current_hashes[rel_path]
            if actual == expected_hash:
                print(f"  [OK] {rel_path}")
            else:
                log_header(f"FAILURE: Checksum mismatch for {rel_path}")
                log_header(f"       Expected: {expected_hash}")
                log_header(f"       Actual:   {actual}")
                all_match = False
                mismatches.append(rel_path)
                log_exclusion(
                    dataset_id=rel_path.split('/')[-1].split('.')[0],
                    missing_variable_name="integrity_check",
                    reason=f"Checksum mismatch: expected {expected_hash[:8]}..., got {actual[:8]}..."
                )
        else:
            log_header(f"FAILURE: File {rel_path} found on disk but not in current scan results.")
            all_match = False
            mismatches.append(rel_path)

    # Check for unexpected files (files on disk not in expected list)
    for rel_path in current_hashes.keys():
        if rel_path not in expected_hashes:
            log_header(f"WARNING: Unexpected file found: {rel_path}")
            # Not necessarily a failure of integrity, but a deviation from expected state.
            # We log it but don't fail the integrity check unless strict mode is required.
            # For T019, we focus on "unchanged", so extra files are a warning.

    if all_match:
        log_header("SUCCESS: All raw data files match their expected checksums. Integrity verified.")
    else:
        log_header(f"FAILURE: {len(mismatches)} file(s) failed integrity verification.")
        print("\nMismatches:")
        for m in mismatches:
            print(f"  - {m}")

    return all_match, current_hashes, expected_hashes


def main():
    """Main entry point for the script."""
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    raw_dir = project_root / "data" / "raw"
    state_file = project_root / "state" / "projects" / "PROJ-099-statistical-analysis-of-algorithmic-fair.yaml"
    exclusion_log = project_root / "logs" / "exclusion.log"

    if not exclusion_log.exists():
        # Initialize log if missing to ensure logging works
        exclusion_log.parent.mkdir(parents=True, exist_ok=True)
        with open(exclusion_log, 'w') as f:
            f.write("timestamp,dataset_id,missing_variable_name,reason\n")

    success, current, expected = verify_integrity_workflow(raw_dir, state_file, exclusion_log)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()