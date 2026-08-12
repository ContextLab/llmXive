import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_file_size(file_path: Path) -> int:
    """Get file size in bytes."""
    return file_path.stat().st_size


def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Load and parse the weights manifest JSON."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    with open(manifest_path, "r") as f:
        return json.load(f)


def verify_file(file_path: Path, expected_hash: str, expected_size: int) -> Tuple[bool, str]:
    """
    Verify a single file against expected hash and size.
    Returns (success, message).
    """
    if not file_path.exists():
        return False, f"File not found: {file_path}"
    
    actual_size = get_file_size(file_path)
    if actual_size != expected_size:
        return False, f"Size mismatch for {file_path}: expected {expected_size}, got {actual_size}"
    
    actual_hash = calculate_sha256(file_path)
    if actual_hash != expected_hash:
        return False, f"Hash mismatch for {file_path}: expected {expected_hash}, got {actual_hash}"
    
    return True, f"Verified: {file_path.name}"


def verify_ground_truth(gt_path: Path, manifest: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Verify the teacher ground truth parquet file if it exists in the manifest.
    Returns (success, message).
    """
    if gt_path.exists():
        if "teacher_ground_truth.parquet" not in manifest:
            return False, f"Ground truth file exists but not in manifest: {gt_path}"
        
        expected_entry = manifest["teacher_ground_truth.parquet"]
        success, msg = verify_file(gt_path, expected_entry["sha256"], expected_entry["size_bytes"])
        return success, msg
    
    # File doesn't exist - this is handled by the main logic
    return True, "Ground truth file not present (will check other weights)"


def main():
    """
    Pre-flight check script for DanceOPD weights.
    
    Verifies:
    1. Manifest file exists
    2. All files listed in manifest exist and match checksums
    3. If teacher_ground_truth.parquet exists, it is validated
    
    Exit codes:
    0: All checks passed
    1: Check failed (missing manifest, missing files, checksum/size mismatch)
    """
    # Determine paths relative to project root
    # Assuming this script is run from project root or code/ directory
    project_root = Path(__file__).parent.parent.parent
    data_raw_dir = project_root / "data" / "raw"
    manifest_path = data_raw_dir / "weights_manifest.json"
    gt_path = data_raw_dir / "teacher_ground_truth.parquet"
    
    # Check if manifest exists
    if not manifest_path.exists():
        print(f"ERROR: Manifest file not found at {manifest_path}", file=sys.stderr)
        print("Please ensure data/raw/weights_manifest.json exists with SHA256 checksums.", file=sys.stderr)
        sys.exit(1)
    
    # Load manifest
    try:
        manifest = load_manifest(manifest_path)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in manifest: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Check if manifest is empty
    if not manifest:
        print("ERROR: Manifest file is empty", file=sys.stderr)
        sys.exit(1)
    
    # Separate weight files from ground truth
    weight_files = {k: v for k, v in manifest.items() if k != "teacher_ground_truth.parquet"}
    
    # Verify all weight files
    all_passed = True
    for filename, expected in weight_files.items():
        file_path = data_raw_dir / filename
        success, msg = verify_file(file_path, expected["sha256"], expected["size_bytes"])
        
        if success:
            print(f"✓ {msg}")
        else:
            print(f"✗ ERROR: {msg}", file=sys.stderr)
            all_passed = False
    
    # Verify ground truth if it exists
    if gt_path.exists():
        success, msg = verify_ground_truth(gt_path, manifest)
        if success:
            print(f"✓ {msg}")
        else:
            print(f"✗ ERROR: {msg}", file=sys.stderr)
            all_passed = False
    else:
        # Ground truth doesn't exist - check if any weights were verified
        if not weight_files:
            print("ERROR: No weight files found in manifest and teacher_ground_truth.parquet is missing", file=sys.stderr)
            sys.exit(1)
        elif all_passed:
            # All weights verified but no ground truth - this is acceptable if weights are sufficient
            print("⚠ Warning: teacher_ground_truth.parquet not found. Downstream tasks will require GPU inference or a verified fallback.", file=sys.stderr)
        else:
            # Weights failed verification
            print("ERROR: Weight verification failed and teacher_ground_truth.parquet is missing", file=sys.stderr)
            sys.exit(1)
    
    # Final result
    if all_passed:
        print("\n✓ All pre-flight checks passed!")
        sys.exit(0)
    else:
        print("\n✗ Pre-flight checks failed!", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()