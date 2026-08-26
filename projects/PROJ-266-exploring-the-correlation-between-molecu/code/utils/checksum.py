"""
Checksum Utility Module.

This module computes SHA-256 checksums for data files and writes the results
to a pending checksums file. It is used to ensure data integrity and track
generated artifacts.
"""

import hashlib
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import yaml

from utils.logging import get_logger
from utils.config import get_project_root

logger = get_logger(__name__)

def compute_file_checksum(file_path: Path) -> str:
    """
    Compute SHA-256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal checksum string.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def scan_data_files(data_dir: Path) -> List[Path]:
    """
    Scan a directory for data files (CSV, JSON, etc.).

    Args:
        data_dir: Path to the data directory.

    Returns:
        List of file paths.
    """
    extensions = {'.csv', '.json', '.yaml', '.yml', '.parquet', '.txt', '.tsv'}
    files = []
    for ext in extensions:
        files.extend(data_dir.rglob(f'*{ext}'))
    return files

def generate_checksum_record(file_path: Path, checksum: str) -> Dict[str, Any]:
    """
    Generate a checksum record for a file.

    Args:
        file_path: Path to the file.
        checksum: SHA-256 checksum.

    Returns:
        Dictionary with file metadata and checksum.
    """
    stat = file_path.stat()
    return {
        'file_path': str(file_path),
        'checksum': checksum,
        'size_bytes': stat.st_size,
        'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
        'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat()
    }

def write_checksums_to_pending(checksums: List[Dict[str, Any]], pending_path: Path) -> None:
    """
    Write checksums to a pending YAML file.

    Args:
        checksums: List of checksum records.
        pending_path: Path to the pending checksums file.
    """
    pending_path.parent.mkdir(parents=True, exist_ok=True)

    record = {
        'generated_at': datetime.now().isoformat(),
        'checksums': checksums
    }

    with open(pending_path, 'w', encoding='utf-8') as f:
        yaml.dump(record, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Wrote checksums to {pending_path}")

def scan_and_register_data_files() -> None:
    """
    Scan data directories and register checksums to the pending file.
    """
    project_root = get_project_root()
    data_dir = project_root / 'data'
    pending_dir = project_root / 'state' / 'pending'
    pending_path = pending_dir / 'checksums.yaml'

    if not data_dir.exists():
        logger.warning(f"Data directory {data_dir} does not exist. Skipping checksum generation.")
        return

    files = scan_data_files(data_dir)
    if not files:
        logger.warning("No data files found to checksum.")
        return

    checksums = []
    for file_path in files:
        try:
            checksum = compute_file_checksum(file_path)
            record = generate_checksum_record(file_path, checksum)
            checksums.append(record)
            logger.debug(f"Checksum for {file_path}: {checksum}")
        except Exception as e:
            logger.error(f"Failed to compute checksum for {file_path}: {e}")

    if checksums:
        write_checksums_to_pending(checksums, pending_path)
    else:
        logger.warning("No valid checksums generated.")

def verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    """
    Verify the checksum of a file against an expected value.

    Args:
        file_path: Path to the file.
        expected_checksum: Expected SHA-256 checksum.

    Returns:
        True if checksum matches, False otherwise.
    """
    actual_checksum = compute_file_checksum(file_path)
    return actual_checksum == expected_checksum

def main():
    """
    Main entry point for checksum utility.
    """
    logger.info("Running checksum utility.")
    scan_and_register_data_files()
    logger.info("Checksum utility completed.")

if __name__ == '__main__':
    main()