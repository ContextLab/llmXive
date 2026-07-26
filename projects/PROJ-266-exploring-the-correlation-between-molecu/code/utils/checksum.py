"""
Checksum Utility for Data Integrity Verification.

This module computes SHA-256 checksums for files in the project's data directory
and registers them in a centralized log file for governance tracking.

Per Constitution Principle V, this script writes to a log file only.
It does NOT write to state YAML files directly.
"""

import hashlib
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from utils.logging import get_logger, configure_root_logger
from utils.config import get_project_root, get_data_path, get_state_path


def get_logger_for_module() -> logging.Logger:
    """Get a logger configured for this module."""
    return get_logger("utils.checksum")


def compute_file_checksum(file_path: Path) -> str:
    """
    Compute the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def load_state_file(log_path: Path) -> List[Dict[str, Any]]:
    """
    Load existing checksum log entries from the log file.

    Args:
        log_path: Path to the checksums.log file.

    Returns:
        List of existing log entries (parsed as dicts if valid, empty list otherwise).
    """
    if not log_path.exists():
        return []

    entries = []
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # Simple parsing: expecting format "timestamp | filepath | checksum"
                # We store raw lines for append-only safety, but return empty list
                # if we can't parse, as we just append new ones.
                # For this utility, we treat the log as append-only text.
                pass
    except Exception as e:
        logger = get_logger_for_module()
        logger.warning(f"Could not read existing checksum log: {e}")

    return entries


def save_state_file(log_path: Path, entry: str) -> None:
    """
    Append a new checksum entry to the log file.

    Args:
        log_path: Path to the checksums.log file.
        entry: The formatted log line to append.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry + "\n")


def register_checksum(
    file_path: Path,
    log_path: Path,
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """
    Compute checksum for a file and register it in the log.

    Args:
        file_path: Path to the file to checksum.
        log_path: Path to the checksums.log file.
        logger: Logger instance to use.

    Returns:
        Dictionary with 'file', 'checksum', 'timestamp', 'status'.
    """
    if logger is None:
        logger = get_logger_for_module()

    if not file_path.exists():
        logger.error(f"File not found for checksum: {file_path}")
        return {
            "file": str(file_path),
            "checksum": None,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "failed",
            "error": "File not found"
        }

    try:
        checksum = compute_file_checksum(file_path)
        timestamp = datetime.utcnow().isoformat()
        entry = f"{timestamp} | {file_path.relative_to(get_project_root())} | {checksum}"

        save_state_file(log_path, entry)
        logger.info(f"Registered checksum for {file_path}: {checksum}")

        return {
            "file": str(file_path),
            "checksum": checksum,
            "timestamp": timestamp,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Failed to compute checksum for {file_path}: {e}")
        return {
            "file": str(file_path),
            "checksum": None,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "failed",
            "error": str(e)
        }


def scan_and_register_data_files(
    data_dir: Optional[Path] = None,
    log_path: Optional[Path] = None,
    recursive: bool = True,
    extensions: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Scan the data directory for files and register their checksums.

    Args:
        data_dir: Path to the data directory. Defaults to project's data/ path.
        log_path: Path to the checksums.log file. Defaults to project's state/checksums.log.
        recursive: Whether to scan subdirectories.
        extensions: Optional list of file extensions to include (e.g., ['.csv', '.parquet']).
                   If None, all files are processed.

    Returns:
        List of registration result dictionaries.
    """
    if data_dir is None:
        data_dir = get_data_path()

    if log_path is None:
        log_path = get_state_path() / "checksums.log"

    if not data_dir.exists():
        logger = get_logger_for_module()
        logger.warning(f"Data directory does not exist: {data_dir}")
        return []

    logger = get_logger_for_module()
    logger.info(f"Scanning {data_dir} for files to checksum...")

    results = []
    files_to_process = []

    if recursive:
        for root, _, files in os.walk(data_dir):
            for file in files:
                files_to_process.append(Path(root) / file)
    else:
        files_to_process = list(data_dir.iterdir())

    for file_path in files_to_process:
        if file_path.is_file():
            if extensions is None or file_path.suffix.lower() in extensions:
                result = register_checksum(file_path, log_path, logger)
                results.append(result)

    logger.info(f"Processed {len(results)} files.")
    return results


def verify_checksum(
    file_path: Path,
    expected_checksum: str,
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Verify a file's checksum against an expected value.

    Args:
        file_path: Path to the file to verify.
        expected_checksum: The expected SHA-256 hex string.
        logger: Logger instance to use.

    Returns:
        True if checksum matches, False otherwise.
    """
    if logger is None:
        logger = get_logger_for_module()

    if not file_path.exists():
        logger.error(f"File not found for verification: {file_path}")
        return False

    try:
        actual_checksum = compute_file_checksum(file_path)
        if actual_checksum == expected_checksum:
            logger.info(f"Checksum verified for {file_path}")
            return True
        else:
            logger.error(f"Checksum MISMATCH for {file_path}: expected {expected_checksum}, got {actual_checksum}")
            return False
    except Exception as e:
        logger.error(f"Failed to verify checksum for {file_path}: {e}")
        return False


def main() -> int:
    """
    Main entry point for the checksum utility.

    Scans the data directory and registers checksums for all files.
    Writes results to state/checksums.log.

    Returns:
        0 on success, 1 on error.
    """
    configure_root_logger()
    logger = get_logger_for_module()
    logger.info("Starting checksum utility...")

    try:
        data_dir = get_data_path()
        log_path = get_state_path() / "checksums.log"

        # Ensure directories exist
        data_dir.mkdir(parents=True, exist_ok=True)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        results = scan_and_register_data_files(
            data_dir=data_dir,
            log_path=log_path,
            recursive=True
        )

        success_count = sum(1 for r in results if r["status"] == "success")
        fail_count = sum(1 for r in results if r["status"] == "failed")

        logger.info(f"Checksum scan complete. Success: {success_count}, Failed: {fail_count}")

        if fail_count > 0:
            logger.warning(f"{fail_count} files failed checksum registration.")
            return 1

        return 0

    except Exception as e:
        logger.exception(f"Fatal error in checksum utility: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())