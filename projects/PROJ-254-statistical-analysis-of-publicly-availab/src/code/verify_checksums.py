"""
Checksum verification script for raw data integrity.

This module computes SHA-256 checksums for files in the raw data directory
and verifies them against a manifest file. It is designed to ensure data
integrity before processing begins (Constitution Check).
"""

import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

# Import logging setup from utils
from utils import get_logger, setup_logging, set_deterministic_seed

# Constants
MANIFEST_FILENAME = "manifest.json"
RAW_DATA_DIR = Path("data/raw")
CHECKSUM_ALGORITHM = "sha256"
CHUNK_SIZE = 1024 * 1024  # 1MB chunks for large file processing


def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file to checksum.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def load_manifest(manifest_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load the checksum manifest from a JSON file.

    Args:
        manifest_path: Optional path to the manifest file. Defaults to
                       RAW_DATA_DIR / MANIFEST_FILENAME.

    Returns:
        Dictionary mapping relative file paths to their expected checksums.

    Raises:
        FileNotFoundError: If the manifest file does not exist.
        json.JSONDecodeError: If the manifest file is not valid JSON.
    """
    if manifest_path is None:
        manifest_path = RAW_DATA_DIR / MANIFEST_FILENAME

    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found at {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    return manifest_data.get("checksums", {})


def verify_checksums(
    manifest: Dict[str, str],
    data_dir: Optional[Path] = None,
    logger: Optional[logging.Logger] = None
) -> Tuple[List[str], List[str], List[str]]:
    """
    Verify checksums of files against the manifest.

    Args:
        manifest: Dictionary mapping relative file paths to expected checksums.
        data_dir: Optional base directory for files. Defaults to RAW_DATA_DIR.
        logger: Optional logger instance.

    Returns:
        Tuple of (passed_files, failed_files, missing_files) where each is a list
        of relative file paths.
    """
    if data_dir is None:
        data_dir = RAW_DATA_DIR

    if logger is None:
        logger = get_logger("checksum_verification")

    passed = []
    failed = []
    missing = []

    for rel_path, expected_checksum in manifest.items():
        full_path = data_dir / rel_path

        if not full_path.exists():
            missing.append(rel_path)
            logger.warning(f"File missing: {rel_path}")
            continue

        try:
            actual_checksum = compute_sha256(full_path)
            if actual_checksum == expected_checksum:
                passed.append(rel_path)
                logger.debug(f"Checksum passed: {rel_path}")
            else:
                failed.append(rel_path)
                logger.error(
                    f"Checksum mismatch for {rel_path}: "
                    f"expected {expected_checksum}, got {actual_checksum}"
                )
        except Exception as e:
            failed.append(rel_path)
            logger.error(f"Error computing checksum for {rel_path}: {str(e)}")

    return passed, failed, missing


def print_summary(
    passed: List[str],
    failed: List[str],
    missing: List[str],
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Print a summary of the verification results.

    Args:
        passed: List of files that passed checksum verification.
        failed: List of files that failed checksum verification.
        missing: List of files that were not found.
        logger: Optional logger instance.
    """
    total = len(passed) + len(failed) + len(missing)

    if logger is None:
        logger = get_logger("checksum_verification")

    logger.info("=" * 60)
    logger.info("CHECKSUM VERIFICATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total files in manifest: {total}")
    logger.info(f"Passed: {len(passed)}")
    logger.info(f"Failed: {len(failed)}")
    logger.info(f"Missing: {len(missing)}")
    logger.info("-" * 60)

    if passed:
        logger.info("Files with valid checksums:")
        for f in passed:
            logger.info(f"  ✓ {f}")

    if failed:
        logger.warning("Files with checksum mismatches:")
        for f in failed:
            logger.warning(f"  ✗ {f}")

    if missing:
        logger.warning("Files not found:")
        for f in missing:
            logger.warning(f"  ? {f}")

    logger.info("=" * 60)

    # Return exit code based on results
    if failed or missing:
        logger.error("Verification FAILED: Some files are missing or corrupted.")
    else:
        logger.info("Verification PASSED: All files are intact.")


def main() -> int:
    """
    Main entry point for the checksum verification script.

    Returns:
        Exit code: 0 if all checksums pass, 1 otherwise.
    """
    # Setup logging
    setup_logging()
    logger = get_logger("checksum_verification")
    logger.info("Starting checksum verification...")

    # Set deterministic seed for reproducibility (though not strictly needed here)
    set_deterministic_seed(42)

    try:
        # Load manifest
        logger.info(f"Loading manifest from {RAW_DATA_DIR / MANIFEST_FILENAME}")
        manifest = load_manifest()

        if not manifest:
            logger.warning("Manifest is empty or not found. No files to verify.")
            return 0

        logger.info(f"Found {len(manifest)} files in manifest.")

        # Verify checksums
        passed, failed, missing = verify_checksums(manifest, logger=logger)

        # Print summary
        print_summary(passed, failed, missing, logger=logger)

        # Return appropriate exit code
        if failed or missing:
            return 1
        return 0

    except FileNotFoundError as e:
        logger.error(f"Manifest not found: {str(e)}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in manifest: {str(e)}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during verification: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())