"""
Utility to compute SHA‑256 checksums for data artefacts.

The manifest is written to ``data/checksums/manifest.sha256`` with one
line per file: "<hex-digest>  <relative-path>".

Only files under the project ``data`` directory are considered; the
function skips directories and only processes regular files.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import sys

def _ensure_parent_dir(p: Path) -> None:
    """Create the parent directory of ``p`` if it does not exist."""
    p.parent.mkdir(parents=True, exist_ok=True)

def _sha256_of_file(file_path: Path) -> str:
    """Return the hex SHA‑256 digest of ``file_path``."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def compute_checksums() -> None:
    """Compute checksums for all files under ``data`` and write the manifest."""
    data_root = Path("data")
    manifest_path = data_root / "checksums" / "manifest.sha256"
    _ensure_parent_dir(manifest_path)

    lines = []
    for file_path in data_root.rglob("*"):
        if file_path.is_file():
            # Compute relative path using forward slashes
            rel_path = file_path.as_posix()
            digest = _sha256_of_file(file_path)
            lines.append(f"{digest}  {rel_path}")

    # Write sorted lines for deterministic output
    manifest_path.write_text("\n".join(sorted(lines)) + "\n", encoding="utf-8")
    print(f"Updated checksum manifest: {manifest_path}")

def main() -> None:
    """CLI entry point."""
    compute_checksums()

if __name__ == "__main__":
    main()
