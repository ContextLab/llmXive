"""Generate SHA-256 checksums for all files under the ``data`` directory.

This script computes the SHA‑256 digest of every file (recursively) inside
the project's ``data`` folder and writes a manifest file
``data/checksums/manifest.sha256``.  Each line of the manifest follows the
conventional format used by ``sha256sum``:

    <hex‑digest> <relative‑path>

The relative path is expressed with forward slashes and is relative to the
project root (the same format expected by the unit tests in
``tests/unit/test_sieve.py``).

The script is idempotent: running it multiple times will simply overwrite
the existing manifest with an up‑to‑date version.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from llmxive_toolkit import paths

def _sha256_of_file(file_path: Path) -> str:
    """Return the hexadecimal SHA‑256 digest of *file_path*."""
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def generate_checksum_manifest() -> None:
    """Compute checksums for every file under ``data`` and write the manifest."""
    data_root = paths.data()  # ``data`` directory (creates it if missing)
    manifest_path = paths.data("checksums", "manifest.sha256")
    # Ensure the checksums folder exists
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    entries = []
    for file_path in data_root.rglob("*"):
        if file_path.is_file():
            digest = _sha256_of_file(file_path)
            # Path relative to the project root, using forward slashes
            rel_path = file_path.relative_to(paths.root).as_posix()
            entries.append(f"{digest} {rel_path}")

    # Write entries sorted for reproducibility
    entries.sort()
    manifest_path.write_text("\n".join(entries) + "\n", encoding="utf-8")
    print(f"Checksum manifest written to {manifest_path}")

if __name__ == "__main__":
    generate_checksum_manifest()
