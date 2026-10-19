"""
Checksum Verification Script (Task T001a)
-----------------------------------------

This script recomputes the SHA‑256 checksums for all files listed in
``data/checksums.txt`` and verifies that they match the recorded values.
It **does not** rewrite the checksum file or update any project state.
The script exits with status 0 when all checksums match; otherwise it
prints the mismatched file paths and exits with status 1.

The manifest may contain lines in either of the following formats:
  <hash>  <relative_path>
  <relative_path>: <hash>

Both are accepted for backward compatibility.
"""

import hashlib
import sys
from pathlib import Path
from typing import Dict

# Project root (parent of the ``code`` directory)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Expected location of the checksum manifest
CHECKSUMS_FILE = PROJECT_ROOT / "data" / "checksums.txt"


def compute_sha256(file_path: Path) -> str:
    """Compute SHA‑256 hash of a file."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_recorded_checksums() -> Dict[Path, str]:
    """
    Parse ``data/checksums.txt`` and return a mapping from absolute file
    paths to the recorded hash.

    Supported line formats:
      <hash>  <relative_path>
      <relative_path>: <hash>
    """
    if not CHECKSUMS_FILE.is_file():
        print(f"Checksum file not found at {CHECKSUMS_FILE}", file=sys.stderr)
        sys.exit(1)

    recorded: Dict[Path, str] = {}
    with CHECKSUMS_FILE.open("r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Try space‑separated format first
            if "  " in line:
                parts = line.split("  ")
                if len(parts) == 2:
                    hash_val, rel_path = parts
                    abs_path = (PROJECT_ROOT / rel_path).resolve()
                    recorded[abs_path] = hash_val
                    continue
            # Fallback to colon format
            if ":" in line:
                rel_path, hash_val = line.split(":", 1)
                rel_path = rel_path.strip()
                hash_val = hash_val.strip()
                abs_path = (PROJECT_ROOT / rel_path).resolve()
                recorded[abs_path] = hash_val
    return recorded


def verify_checksums() -> bool:
    """
    Re‑compute and compare checksums for all files listed in the manifest.
    Returns ``True`` if all match; otherwise prints mismatches and returns ``False``.
    """
    recorded = load_recorded_checksums()
    if not recorded:
        print("No valid checksum entries found in the manifest.", file=sys.stderr)
        return False

    mismatches = []
    for file_path, expected_hash in recorded.items():
        if not file_path.is_file():
            mismatches.append((file_path, "MISSING"))
            continue
        actual_hash = compute_sha256(file_path)
        if actual_hash != expected_hash:
            mismatches.append((file_path, f"EXPECTED {expected_hash}, GOT {actual_hash}"))

    if mismatches:
        print("Checksum verification failed for the following file(s):", file=sys.stderr)
        for fp, reason in mismatches:
            print(f" - {fp.relative_to(PROJECT_ROOT)}: {reason}", file=sys.stderr)
        return False

    print(f"All {len(recorded)} checksum(s) verified successfully.")
    return True


def main() -> None:
    """Entry point."""
    success = verify_checksums()
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()