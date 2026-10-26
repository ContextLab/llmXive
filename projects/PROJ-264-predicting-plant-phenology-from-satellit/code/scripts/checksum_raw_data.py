"""Checksum raw data files.

This script iterates over all files in the ``data/raw`` directory,
computes a SHA‑256 hash for each file, and writes a manifest
``data/checksums.txt`` with lines of the form::

    <sha256_hash>  <relative_path>

The relative path is expressed with respect to the project root.
The script is idempotent – running it multiple times will overwrite
the existing ``checksums.txt`` file with the current checksums.

Usage
-----
Run the script directly:

    python code/scripts/checksum_raw_data.py

The script exits with status ``0`` on success and ``1`` on failure.
"""

import hashlib
from pathlib import Path
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def compute_sha256(file_path: Path, chunk_size: int = 8192) -> str:
    """Compute the SHA‑256 checksum of a file.

    Parameters
    ----------
    file_path: Path
        Path to the file whose checksum is to be calculated.
    chunk_size: int, optional
        Size of chunks to read the file in bytes. Default is 8192.

    Returns
    -------
    str
        Hexadecimal SHA‑256 digest.
    """
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def main() -> int:
    """Generate checksums for all files under ``data/raw``."""
    try:
        # Ensure the raw data directory exists (creates it if missing)
        raw_dir: Path = paths.data("raw")
        raw_dir.mkdir(parents=True, exist_ok=True)

        # Destination manifest file
        checksum_file: Path = paths.data("checksums.txt")
        # Ensure the parent ``data`` directory exists (handled by paths.data)

        log.info("Computing SHA‑256 checksums for files in %s", raw_dir)

        lines = []
        for file_path in raw_dir.rglob("*"):
            if file_path.is_file():
                checksum = compute_sha256(file_path)
                # Relative path from project root for reproducibility
                rel_path = file_path.relative_to(paths.root).as_posix()
                lines.append(f"{checksum}  {rel_path}")

        # Write the manifest (overwrites any previous version)
        checksum_file.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        log.info("Checksum manifest written to %s (%d entries)", checksum_file, len(lines))
        return 0
    except Exception as exc:  # pragma: no cover – any unexpected error is logged and causes failure
        log.error("Failed to generate checksums: %s", exc, exc_info=True)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
