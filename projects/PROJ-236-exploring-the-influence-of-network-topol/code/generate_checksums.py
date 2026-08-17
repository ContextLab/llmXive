"""
Utility script to generate SHA-256 checksums for all files under the ``data/`` directory
and write them to ``data/checksums.txt``. This script can be run manually to (re)create
the checksum manifest that the verification test expects.

The script uses the ``compute_file_checksum`` helper from ``utils.io`` to ensure a
single, consistent implementation of the checksum algorithm across the project.
"""

import pathlib
from utils.io import compute_file_checksum


def generate_checksums(data_root: pathlib.Path = pathlib.Path("data")) -> None:
    """
    Walk ``data_root`` recursively, compute SHA-256 checksums for every regular file
    (excluding the checksum manifest itself), and write a space‑separated list of
    ``relative_path checksum`` lines to ``data/checksums.txt``.

    Parameters
    ----------
    data_root:
        Root directory containing data artifacts. Defaults to the repository‑wide
        ``data`` directory.
    """
    checksum_file = data_root / "checksums.txt"
    lines = []

    for file_path in data_root.rglob("*"):
        # Skip directories and the manifest file itself
        if not file_path.is_file() or file_path == checksum_file:
            continue
        # Compute checksum using the shared utility
        checksum = compute_file_checksum(file_path)
        # Store path relative to the data root (POSIX style for consistency)
        rel_path = file_path.relative_to(data_root).as_posix()
        lines.append(f"{rel_path} {checksum}")

    # Write (or overwrite) the manifest
    checksum_file.write_text("\n".join(lines) + ("\n" if lines else ""))


if __name__ == "__main__":
    generate_checksums()
