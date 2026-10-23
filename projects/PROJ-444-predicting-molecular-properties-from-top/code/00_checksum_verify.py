"""
Checksum verification utility (Task T001b)

This script reads the manifest ``data/checksums.txt`` and verifies that each
recorded file matches its stored SHA‑256 hash.  It prints a concise success
message ``All checksums verified`` when every file matches, otherwise it
reports mismatches and exits with a non‑zero status.
"""

import hashlib
import sys
from pathlib import Path
from typing import Dict

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
    Blank lines and comment lines (starting with '#') are ignored.
    """
    manifest_path = Path("data/checksums.txt")
    checksums: Dict[Path, str] = {}

    if not manifest_path.is_file():
        print(f"Checksum manifest not found at {manifest_path}", file=sys.stderr)
        return checksums

    with manifest_path.open("r") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            # Try "hash  path" format (two‑space delimiter)
            if "  " in line:
                parts = line.split("  ", maxsplit=1)
                if len(parts) == 2:
                    hash_val, rel_path = parts
                    checksums[Path(rel_path)] = hash_val
                    continue

            # Try "path: hash" format
            if ":" in line:
                parts = line.split(":", maxsplit=1)
                if len(parts) == 2:
                    rel_path, hash_val = parts
                    checksums[Path(rel_path.strip())] = hash_val.strip()
                    continue

            # Fallback – unrecognised line
            print(f"Unrecognised checksum line format: {line}", file=sys.stderr)

    return checksums

def verify_checksums() -> bool:
    """
    Re‑compute and compare checksums for all files listed in the manifest.
    Returns ``True`` if all match; otherwise prints mismatches and returns ``False``.
    """
    manifest = load_recorded_checksums()
    all_match = True

    for rel_path, recorded_hash in manifest.items():
        abs_path = Path(rel_path)
        if not abs_path.is_file():
            print(f"Missing file for checksum verification: {abs_path}", file=sys.stderr)
            all_match = False
            continue

        actual_hash = compute_sha256(abs_path)
        if actual_hash != recorded_hash:
            print(
                f"Checksum mismatch for {abs_path}:\n"
                f"  recorded: {recorded_hash}\n"
                f"  actual:   {actual_hash}",
                file=sys.stderr,
            )
            all_match = False

    if all_match:
        # Exact message required by the task description
        print("All checksums verified")
    else:
        print("Checksum verification failed.", file=sys.stderr)

    return all_match

def main() -> None:
    """Entry point."""
    success = verify_checksums()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
