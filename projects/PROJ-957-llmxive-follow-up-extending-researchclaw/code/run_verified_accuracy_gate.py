"""
Verified Accuracy Gate Implementation (Task T007b)

This script implements the gate sequence to verify data integrity:
1. Read checksum file at data/raw/checksum.txt
2. Verify hash matches expected value in src/config.py
3. If mismatch: log FAIL, create .failed file, exit(1)
4. If match: log PASS, create .done file, proceed

This is a standalone executable script that can be run after T007.
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

# Add src to path for imports
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from config import Config
from utils.checksum import read_checksum


def main() -> int:
    """
    Execute the Verified Accuracy Gate logic.
    
    Returns:
        int: 0 if gate passes, 1 if gate fails
    """
    # Initialize configuration
    config = Config.load()
    
    # Define paths
    project_root = Path(__file__).parent
    checksum_file = project_root / "data" / "raw" / "checksum.txt"
    results_dir = project_root / "results"
    log_file = results_dir / "verified_accuracy_gate.log"
    failed_marker = results_dir / "verified_accuracy_gate.failed"
    done_marker = results_dir / "verified_accuracy_gate.done"
    
    # Ensure results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Log entry
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Step 1: Read checksum file
    if not checksum_file.exists():
        error_msg = f"ERROR: Checksum file not found at {checksum_file}"
        print(error_msg, file=sys.stderr)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {error_msg}\n")
        return 1
    
    try:
        file_checksum = read_checksum(checksum_file)
    except Exception as e:
        error_msg = f"ERROR: Failed to read checksum file: {e}"
        print(error_msg, file=sys.stderr)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {error_msg}\n")
        return 1
    
    # Step 2: Verify against expected value
    expected_checksum = config.EXPECTED_DATASET_CHECKSUM
    
    if file_checksum != expected_checksum:
        # MISMATCH - Gate fails
        fail_msg = "GATE: Verified Accuracy [FAIL]"
        detail_msg = f"Checksum mismatch: expected {expected_checksum}, got {file_checksum}"
        
        print(fail_msg)
        print(detail_msg, file=sys.stderr)
        
        # Write to log
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {fail_msg}\n")
            f.write(f"[{timestamp}] {detail_msg}\n")
        
        # Create failed marker
        with open(failed_marker, "w", encoding="utf-8") as f:
            f.write(f"FAIL: Checksum mismatch at {timestamp}\n")
            f.write(f"Expected: {expected_checksum}\n")
            f.write(f"Got: {file_checksum}\n")
        
        # Remove done marker if it exists (shouldn't, but safety)
        if done_marker.exists():
            done_marker.unlink()
        
        return 1
    
    # Step 3: Match - Gate passes
    pass_msg = "GATE: Verified Accuracy [PASS]"
    
    print(pass_msg)
    
    # Write to log
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {pass_msg}\n")
        f.write(f"[{timestamp}] Checksum verified: {file_checksum}\n")
    
    # Create done marker
    with open(done_marker, "w", encoding="utf-8") as f:
        f.write(f"PASS: Checksum verified at {timestamp}\n")
        f.write(f"Checksum: {file_checksum}\n")
    
    # Remove failed marker if it exists (shouldn't, but safety)
    if failed_marker.exists():
        failed_marker.unlink()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
