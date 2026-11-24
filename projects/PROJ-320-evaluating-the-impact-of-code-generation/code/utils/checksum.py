"""
Checksum utilities for data integrity (T002).

Primary API: ``sha256_file(path) -> str`` — computes the SHA-256
hex digest of the file at ``path``. Additional helpers provide
checksum verification and manifest generation.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Union

_CHUNK_SIZE = 65536

def sha256_file(path: Union[str, Path]) -> str:
    """
    Compute the SHA-256 checksum of the file at ``path``.

    Args:
        path: Path to the file to checksum.

    Returns:
        The 64-character lowercase hexadecimal SHA-256 digest.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
        IsADirectoryError: If ``path`` is a directory.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"No such file: {file_path}")
    if file_path.is_dir():
        raise IsADirectoryError(f"Is a directory: {file_path}")

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(_CHUNK_SIZE), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def calculate_checksum(file_path: Union[str, Path]) -> str:
    """Calculate SHA-256 checksum of a file (alias of :func:`sha256_file`)."""
    return sha256_file(file_path)

def verify_checksum(file_path: Union[str, Path], expected_checksum: str) -> bool:
    """
    Verify the checksum of a file against an expected value.

    Comparison is case-insensitive; the expected value must be a
    64-character hexadecimal string.
    """
    if not isinstance(expected_checksum, str) or len(expected_checksum) != 64:
        raise ValueError(
            "Expected checksum must be a 64-character hexadecimal string."
        )
    int(expected_checksum, 16)  # raises ValueError if not hex
    actual = sha256_file(file_path)
    return actual == expected_checksum.lower()

def generate_checksum_manifest(
    file_paths: List[Union[str, Path]], output_path: Union[str, Path]
) -> None:
    """
    Generate a JSON manifest of checksums for a list of files.

    Keys are the file basenames; missing files are skipped.
    """
    manifest: Dict[str, str] = {}
    for path in file_paths:
        file_path = Path(path)
        if not file_path.is_file():
            continue
        manifest[file_path.name] = sha256_file(file_path)

    output = Path(output_path)
    if output.parent and not output.parent.exists():
        output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

def load_checksum_manifest(manifest_path: Union[str, Path]) -> Dict[str, str]:
    """Load a checksum manifest from a JSON file."""
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Compute SHA-256 checksum of a file."
    )
    parser.add_argument("file", help="Path to the file to checksum")
    args = parser.parse_args()
    print(sha256_file(args.file))

if __name__ == "__main__":
    main()
