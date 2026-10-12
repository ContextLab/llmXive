"""
Checksum Utility Module.

This module walks the project's ``data/`` directory recursively,
computes a SHA‑256 checksum for every file, and writes a YAML mapping
to a project‑owned location (``data/checksums.yaml``). The output file
contains a ``generated_at`` timestamp and a ``checksums`` dictionary
mapping each file's path (relative to the project root) to its checksum.

The utility is intended to be invoked after any data‑producing step
to provide reproducible integrity verification.
"""

import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import yaml

from utils.logging import get_logger
from utils.config import get_project_root

# Configure a module‑level logger
logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Core checksum helpers
# ----------------------------------------------------------------------
def compute_file_checksum(file_path: Path) -> str:
    """
    Compute the SHA‑256 checksum of a file.

    Parameters
    ----------
    file_path: Path
        Path to the file whose checksum is to be computed.

    Returns
    -------
    str
        Hexadecimal SHA‑256 checksum.
    """
    sha256 = hashlib.sha256()
    # Read the file in binary chunks to avoid loading large files into memory
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def generate_checksum_record(file_path: Path, checksum: str) -> Dict[str, any]:
    """
    Create a detailed checksum record for a single file.

    The record includes the file path (as a string), the checksum,
    file size in bytes, and ISO‑formatted creation / modification timestamps.

    Parameters
    ----------
    file_path: Path
        Path to the file.
    checksum: str
        SHA‑256 checksum computed by :func:`compute_file_checksum`.

    Returns
    -------
    dict
        Mapping with keys ``file_path``, ``checksum``, ``size_bytes``,
        ``modified_at`` and ``created_at``.
    """
    stat = file_path.stat()
    return {
        "file_path": str(file_path),
        "checksum": checksum,
        "size_bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
    }


def gather_checksums(data_dir: Path, project_root: Path) -> Dict[str, str]:
    """
    Walk ``data_dir`` recursively and build a mapping of relative file
    paths to their SHA‑256 checksums.

    Parameters
    ----------
    data_dir: Path
        Root directory containing data files (usually ``<project>/data``).
    project_root: Path
        Root of the repository; used to compute relative paths.

    Returns
    -------
    Dict[str, str]
        Mapping ``relative_path -> checksum``.
    """
    if not data_dir.is_dir():
        logger.warning(f"Data directory {data_dir} does not exist or is not a directory.")
        return {}

    checksums: Dict[str, str] = {}
    for file_path in data_dir.rglob("*"):
        if file_path.is_file():
            try:
                checksum = compute_file_checksum(file_path)
                # Store path relative to the project root for portability
                rel_path = str(file_path.relative_to(project_root))
                checksums[rel_path] = checksum
                logger.debug(f"Checksum computed for {rel_path}: {checksum}")
            except Exception as exc:
                logger.error(f"Failed to compute checksum for {file_path}: {exc}")
    return checksums


def write_checksums_yaml(checksums: Dict[str, str], output_path: Path) -> None:
    """
    Write the checksum mapping to a YAML file.

    The file will contain a ``generated_at`` timestamp and a ``checksums``
    dictionary.

    Parameters
    ----------
    checksums: Dict[str, str]
        Mapping of relative file paths to SHA‑256 checksums.
    output_path: Path
        Destination path for the YAML file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "generated_at": datetime.now().isoformat(),
        "checksums": checksums,
    }

    with output_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Checksum file written to {output_path}")


def write_checksums_to_pending(records: List[Dict[str, any]], pending_path: Path) -> None:
    """
    Write a list of checksum *records* (as produced by
    :func:`generate_checksum_record`) to a YAML file.

    The resulting file mirrors the format expected by the unit tests:
    it contains a ``generated_at`` timestamp and a top‑level ``checksums``
    list where each element is a record dictionary.

    Parameters
    ----------
    records: List[dict]
        List of checksum record dictionaries.
    pending_path: Path
        Path where the YAML file should be written.
    """
    pending_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "generated_at": datetime.now().isoformat(),
        "checksums": records,
    }

    with pending_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Checksum records written to {pending_path}")


# ----------------------------------------------------------------------
# Public API used by other pipeline steps
# ----------------------------------------------------------------------
def run_checksum_utility() -> None:
    """
    Main driver that discovers the project root, gathers checksums for all
    files under ``data/``, and writes the result to the project‑owned
    ``data/checksums.yaml`` file.
    """
    project_root = get_project_root()
    data_dir = project_root / "data"
    output_path = project_root / "data" / "checksums.yaml"

    logger.info(f"Scanning data files in {data_dir}")
    checksums = gather_checksums(data_dir, project_root)

    if not checksums:
        logger.warning("No data files found – checksums file will be empty.")
    write_checksums_yaml(checksums, output_path)


def invoke_checksum_utility() -> None:
    """
    Compatibility wrapper used by legacy pipeline scripts (e.g.
    ``code/data/retrieval.py``). It simply forwards to
    :func:`run_checksum_utility`.
    """
    logger.info("Invoking checksum utility via legacy entry point.")
    run_checksum_utility()


def main() -> None:
    """
    Entry point for ``python -m code.utils.checksum`` or direct script
    execution. It runs the checksum utility.
    """
    logger.info("Starting checksum utility.")
    run_checksum_utility()
    logger.info("Checksum utility completed.")


if __name__ == "__main__":
    main()