"""
Utility module for generating SHA256 checksums of files within a directory.

This module provides:
- ``compute_sha256``: Compute the SHA256 hash of a single file.
- ``scan_directory``: Recursively collect all file paths under a directory.
- ``generate_checksums``: Write a checksum manifest (relative_path <space> sha256) to a
  target file.
- ``main``: Command‑line interface used by the pipeline to create
  ``data/checksums.txt`` for the raw data directory.

The functions are deliberately simple and have no side‑effects beyond the
manifest file creation, making them easy to test and reuse across the
project.
"""

import argparse
import hashlib
import logging
from pathlib import Path
from typing import List, Tuple

# Configure a module‑level logger; the project's logger utilities can also be
# used, but keeping this module self‑contained avoids circular imports.
logger = logging.getLogger(__name__)


def compute_sha256(file_path: Path, chunk_size: int = 8192) -> str:
    """
    Compute the SHA256 checksum of a file.

    Parameters
    ----------
    file_path: Path
        Path to the file whose checksum is required.
    chunk_size: int, optional
        Number of bytes to read per iteration. Defaults to 8192.

    Returns
    -------
    str
        Hexadecimal SHA256 digest.
    """
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def scan_directory(dir_path: Path) -> List[Path]:
    """
    Recursively collect all regular files under ``dir_path``.

    Parameters
    ----------
    dir_path: Path
        Directory to scan.

    Returns
    -------
    List[Path]
        List of file paths (absolute) found under ``dir_path``.
    """
    if not dir_path.is_dir():
        raise NotADirectoryError(f"{dir_path} is not a directory")
    # Use rglob to include files in sub‑directories.
    return [p for p in dir_path.rglob("*") if p.is_file()]


def generate_checksums(
    input_dir: Path,
    output_file: Path,
    hash_func=compute_sha256,
) -> None:
    """
    Generate a SHA256 checksum manifest for all files in ``input_dir``.

    The manifest is written to ``output_file`` with one line per file:
    ``relative_path <space> checksum``.

    Parameters
    ----------
    input_dir: Path
        Directory containing the raw data files.
    output_file: Path
        Destination file for the checksum manifest.
    hash_func: callable, optional
        Function used to compute the hash of a file. Defaults to
        :func:`compute_sha256`. Allows injection for testing.
    """
    input_dir = input_dir.resolve()
    logger.info("Scanning directory %s for checksum generation", input_dir)

    file_paths = scan_directory(input_dir)
    logger.info("Found %d files to checksum", len(file_paths))

    # Ensure the parent directory for the output file exists.
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", encoding="utf-8") as out_f:
        for file_path in sorted(file_paths):
            # Compute checksum.
            checksum = hash_func(file_path)
            # Store path relative to the input directory.
            rel_path = file_path.relative_to(input_dir).as_posix()
            out_f.write(f"{rel_path} {checksum}\n")
            logger.debug("Checksum for %s: %s", rel_path, checksum)

    logger.info("Checksum manifest written to %s", output_file)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate SHA256 checksums for all files in a directory "
        "and write them to a manifest file."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data/raw"),
        help="Directory containing raw data files (default: data/raw).",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=Path("data/checksums.txt"),
        help="Path to write the checksum manifest (default: data/checksums.txt).",
    )
    return parser


def main() -> None:
    """
    Entry point for the checksum utility.

    The function parses command‑line arguments and invokes
    :func:`generate_checksums`.  It is deliberately lightweight so that it can be
    called from pipelines, CI jobs, or directly via ``python -m``.
    """
    parser = _build_arg_parser()
    args = parser.parse_args()

    try:
        generate_checksums(args.input_dir, args.output_file)
    except Exception as exc:
        logger.error("Failed to generate checksums: %s", exc, exc_info=True)
        raise


if __name__ == "__main__":
    main()
