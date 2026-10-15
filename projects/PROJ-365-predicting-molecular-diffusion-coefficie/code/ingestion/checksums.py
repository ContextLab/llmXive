"""
Compute SHA-256 checksums for all files in the raw data directory.

This script reads every file under ``data/raw/``, computes its SHA‑256 hash,
and writes a manifest file ``data/checksums.txt`` where each line has the
format::

    <hash>  <relative_path>

The ``relative_path`` is expressed relative to the project root (e.g.
``data/raw/dataset.csv``).  The script is idempotent – running it multiple
times overwrites the previous checksum file with up‑to‑date values.

The script is intended to be invoked directly::

    python code/ingestion/checksums.py

It logs progress via the project's standard logger.
"""

import hashlib
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _hash_file(file_path: Path) -> str:
    """Return the SHA‑256 hex digest of *file_path*."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def main() -> None:
    """Compute checksums for all files in ``data/raw``."""
    raw_dir = paths.data("raw")
    if not raw_dir.is_dir():
        log.error("Raw data directory does not exist: %s", raw_dir)
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")

    checksum_path = paths.data("checksums.txt")
    lines = []

    for file_path in raw_dir.rglob("*"):
        if file_path.is_file():
            try:
                file_hash = _hash_file(file_path)
            except Exception as exc:
                log.error("Failed to hash %s: %s", file_path, exc)
                raise

            # Relative path from the project root
            rel_path = file_path.relative_to(Path.cwd())
            lines.append(f"{file_hash}  {rel_path}")

            log.info("Hashed %s -> %s", rel_path, file_hash)

    # Write the checksum manifest
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    checksum_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log.info("Checksums written to %s (%d entries)", checksum_path, len(lines))

if __name__ == "__main__":
    main()
