"""
Utility script to ensure that the SHA‑256 checksum for the packed
Möbius array (``data/raw/mobius_2bit.npy``) is present in the
``data/checksums/manifest.sha256`` file.

It is intended to be run after the sieve step has generated both the
raw and packed files.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

def _sha256_of_file(file_path: Path) -> str:
    """Return the hex SHA‑256 digest of the given file."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> None:
    # Paths
    packed_path = Path("data/raw/mobius_2bit.npy")
    manifest_path = Path("data/checksums/manifest.sha256")

    if not packed_path.is_file():
        raise FileNotFoundError(f"Packed Möbius file not found: {packed_path}")

    # Compute checksum
    digest = _sha256_of_file(packed_path)

    # Ensure the manifest directory exists
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    # Read existing manifest (if any)
    existing_lines = []
    if manifest_path.is_file():
        existing_lines = manifest_path.read_text().splitlines()

    # Build new manifest content, replacing any existing entry for the packed file
    rel_path = packed_path.as_posix()
    new_line = f"{digest}  {rel_path}"
    updated = False
    new_lines = []
    for line in existing_lines:
        # Skip comment lines or empty lines
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            new_lines.append(line)
            continue
        if stripped.endswith(rel_path):
            new_lines.append(new_line)
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        new_lines.append(new_line)

    manifest_path.write_text("\n".join(new_lines) + "\n")
    print(f"Updated checksum manifest: {manifest_path}")

if __name__ == "__main__":
    main()
