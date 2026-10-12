"""
Compute SHA-256 checksums for all files in the raw data directory and write them
to ``data/checksums.txt`` in the format required by ``sha256sum -c``.

This script is intended to be run after the data download step (T005a). It
discovers every file under ``data/raw/`` (recursively), computes a SHA‑256 hash
for each file in a memory‑efficient streaming fashion, and writes a checksum
manifest that can be validated with the standard ``sha256sum`` utility.

Usage
-----
The script is executed as part of the task runner:

.. code-block:: bash
    python -m src.compute_checksums
    
It produces the file ``data/checksums.txt``. No command‑line arguments are
required.
"""

import hashlib
from pathlib import Path
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)


def _iter_file_chunks(file_path: Path, chunk_size: int = 8192):
    """Yield ``chunk_size``‑byte pieces of ``file_path``."""
    with file_path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk


def compute_sha256(file_path: Path) -> str:
    """Return the hexadecimal SHA‑256 digest of ``file_path``."""
    sha256 = hashlib.sha256()
    for chunk in _iter_file_chunks(file_path):
        sha256.update(chunk)
    return sha256.hexdigest()


def main() -> None:
    """
    Locate all files under ``data/raw/`` and write their SHA‑256 checksums
    to ``data/checksums.txt``.
    
    The output format matches the expectations of ``sha256sum -c``:
    
    ``<hash><space><space><relative_path>``
    
    where ``relative_path`` is the path relative to the project root
    (e.g. ``data/raw/example.mtx``).
    """
    raw_dir: Path = paths.data("raw")
    if not raw_dir.is_dir():
        log.error("Raw data directory does not exist: %s", raw_dir)
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")

    checksum_path: Path = paths.data("checksums.txt")
    checksum_path.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    for file_path in raw_dir.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(Path.cwd())
            hash_hex = compute_sha256(file_path)
            lines.append(f"{hash_hex}  {rel_path}\n")
            log.debug("Checksum for %s: %s", rel_path, hash_hex)

    # Write all checksum lines atomically
    with checksum_path.open("w", encoding="utf-8") as out_f:
        out_f.writelines(lines)

    log.info("Wrote %d checksum entries to %s", len(lines), checksum_path)


if __name__ == "__main__":
    main()
