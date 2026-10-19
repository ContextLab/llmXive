"""
Update checksum manifest for the ESOL raw dataset.

This script recomputes the SHA‑256 hash of ``data/raw/esol.csv`` and
overwrites ``data/checksums.txt`` with a single, idempotent entry
using the ``<hash>  <relative_path>`` format expected by
``code/00_checksum_verify.py``.
"""

import hashlib
from pathlib import Path

def compute_sha256(file_path: Path) -> str:
    """Compute SHA‑256 hash of a file."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def main() -> None:
    # Path to the raw ESOL CSV (downloaded by T001)
    esol_path = Path("data/raw/esol.csv")
    if not esol_path.is_file():
        raise FileNotFoundError(f"Expected ESOL file not found at {esol_path}")

    # Compute its hash
    hash_val = compute_sha256(esol_path)

    # Write a clean manifest with a single line in the "<hash>  <relative_path>" format
    manifest_path = Path("data/checksums.txt")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w") as f:
        f.write(f"{hash_val}  {esol_path.as_posix()}\n")

    print(f"Checksum manifest updated: {manifest_path}")
    print(f"  {hash_val}  {esol_path}")

if __name__ == "__main__":
    main()
