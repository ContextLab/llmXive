"""
Pre-flight check for teacher weights.
Verifies existence and SHA256 checksum of user-provided weights against the manifest.
Also verifies the optional teacher_ground_truth.parquet if it exists.
"""
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from utils.config import get_config


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_file_size(file_path: Path) -> int:
    """Get file size in bytes."""
    return os.path.getsize(file_path)


def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Load and return the weights manifest JSON."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    with open(manifest_path, "r") as f:
        return json.load(f)


def verify_file(file_path: Path, expected_hash: str, expected_size: int) -> Tuple[bool, str]:
    """
    Verify a file's SHA256 hash and size against expected values.
    Returns (is_valid, message).
    """
    if not file_path.exists():
        return False, f"File not found: {file_path}"

    actual_size = get_file_size(file_path)
    if actual_size != expected_size:
        return False, f"Size mismatch for {file_path.name}: expected {expected_size}, got {actual_size}"

    actual_hash = calculate_sha256(file_path)
    if actual_hash != expected_hash:
        return False, f"Hash mismatch for {file_path.name}: expected {expected_hash}, got {actual_hash}"

    return True, f"Verified: {file_path.name} (size={actual_size}, hash={actual_hash[:16]}...)"


def verify_ground_truth(manifest: Dict[str, Any], raw_dir: Path) -> bool:
    """
    Verify the teacher_ground_truth.parquet if it exists in the manifest.
    If it exists and is valid, returns True.
    If it does not exist, returns False (indicating it must be generated).
    If it exists but is invalid, raises SystemExit(1).
    """
    gt_entry = manifest.get("teacher_ground_truth.parquet")
    if not gt_entry:
        # Manifest doesn't list ground truth, we can't verify it as a fallback
        return False

    gt_path = raw_dir / "teacher_ground_truth.parquet"
    if not gt_path.exists():
        # File doesn't exist, not a valid fallback
        return False

    expected_hash = gt_entry.get("sha256")
    expected_size = gt_entry.get("size")

    if not expected_hash or not expected_size:
        print("Error: Manifest entry for teacher_ground_truth.parquet is missing hash or size.", file=sys.stderr)
        return False

    is_valid, msg = verify_file(gt_path, expected_hash, expected_size)
    if is_valid:
        print(f"[OK] {msg}")
        return True
    else:
        print(f"[FAIL] {msg}", file=sys.stderr)
        return False


def main():
    """
    Main entry point for weight verification.
    Exits with code 0 if all required weights are valid or if a valid ground truth fallback exists.
    Exits with code 1 if manifest is missing, files are missing, or checksums/size mismatch.
    """
    config = get_config()
    raw_dir = Path(config.get_path("raw_data_dir"))
    manifest_path = raw_dir / "weights_manifest.json"

    print("Starting pre-flight weight check...")

    # 1. Check manifest existence
    if not manifest_path.exists():
        print(f"[FAIL] Manifest file not found: {manifest_path}", file=sys.stderr)
        print("Please ensure data/raw/weights_manifest.json exists with expected weights.", file=sys.stderr)
        return 1

    try:
        manifest = load_manifest(manifest_path)
    except json.JSONDecodeError as e:
        print(f"[FAIL] Invalid JSON in manifest: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[FAIL] Error loading manifest: {e}", file=sys.stderr)
        return 1

    print(f"[INFO] Manifest loaded: {manifest_path}")

    # 2. Verify all required weight files listed in manifest
    required_files = manifest.get("required_files", [])
    if not required_files:
        print("[WARN] No 'required_files' list found in manifest.", file=sys.stderr)
        # If there are no required files, we rely solely on ground truth check below

    all_weights_valid = True
    for file_name, details in required_files:
        file_path = raw_dir / file_name
        expected_hash = details.get("sha256")
        expected_size = details.get("size")

        if not expected_hash or not expected_size:
            print(f"[FAIL] Missing hash or size for {file_name} in manifest.", file=sys.stderr)
            all_weights_valid = False
            continue

        is_valid, msg = verify_file(file_path, expected_hash, expected_size)
        if is_valid:
            print(f"[OK] {msg}")
        else:
            print(f"[FAIL] {msg}", file=sys.stderr)
            all_weights_valid = False

    # 3. Check for valid ground truth fallback
    has_valid_fallback = False
    if not all_weights_valid:
        print("[INFO] Required weights missing or invalid. Checking for ground truth fallback...")
        has_valid_fallback = verify_ground_truth(manifest, raw_dir)
        if has_valid_fallback:
            print("[OK] Valid ground truth fallback found. Proceeding with fallback.")
        else:
            print("[FAIL] No valid ground truth fallback available.", file=sys.stderr)
            return 1
    else:
        # Weights are valid, check if ground truth exists as a bonus (optional)
        gt_entry = manifest.get("teacher_ground_truth.parquet")
        if gt_entry:
            gt_path = raw_dir / "teacher_ground_truth.parquet"
            if gt_path.exists():
                is_valid, msg = verify_file(gt_path, gt_entry.get("sha256"), gt_entry.get("size"))
                if is_valid:
                    print(f"[OK] {msg} (optional check)")
                else:
                    print(f"[WARN] Ground truth exists but failed verification: {msg}", file=sys.stderr)
                    # Not fatal if weights are valid, but good to know

    if all_weights_valid or has_valid_fallback:
        print("[SUCCESS] Pre-flight check passed.")
        return 0
    else:
        print("[FAIL] Pre-flight check failed.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
