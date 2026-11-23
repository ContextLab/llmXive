"""
generate_checksums.py

Generates a SHA-256 checksum manifest for all files under the
``data/raw/`` directory (including any simulated artifacts). The manifest
is written to ``data/checksums.sha256`` with one line per file:

    <hash>  <relative_path>

where ``relative_path`` is the path relative to the project root
(e.g. ``data/raw/participants_simulated.csv``).

The script is designed to be run as part of the pipeline's quickstart:

    python -m code.validation.generate_checksums

It fails loudly if any file cannot be read.
"""

import hashlib
from pathlib import Path

from llmxive_toolkit import paths


def _hash_file(file_path: Path, chunk_size: int = 8192) -> str:
    """Return the hex SHA‑256 digest of ``file_path``."""
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def generate_checksums(raw_root: Path = None, output_path: Path = None) -> Path:
    """
    Walk ``raw_root`` (defaults to ``data/raw``) and write a checksum manifest.

    Args:
        raw_root: Directory containing raw files. If ``None`` the default
            ``paths.data('raw')`` is used.
        output_path: Destination for the manifest. If ``None`` the default
            ``paths.data('checksums.sha256')`` is used.

    Returns:
        The path to the written manifest file.
    """
    if raw_root is None:
        raw_root = paths.data("raw")
    if output_path is None:
        output_path = paths.data("checksums.sha256")

    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    manifest_lines = []
    for file_path in raw_root.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(paths.root).as_posix()
            file_hash = _hash_file(file_path)
            manifest_lines.append(f"{file_hash}  {rel_path}")

    # Write the manifest
    output_path.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    return output_path


def main() -> int:
    """
    Entry point for ``python -m code.validation.generate_checksums``.

    Returns:
        Exit code (0 on success, non‑zero on failure).
    """
    try:
        generate_checksums()
        print(f"Checksum manifest written to {paths.data('checksums.sha256')}")
        return 0
    except Exception as e:
        print(f"ERROR generating checksums: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
