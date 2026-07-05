"""
validators.py

Enforces the "Real Data Only" constraint for the statistical evaluation pipeline.
This module prevents the use of synthetic, simulated, or placeholder data in
the `data/raw` directory, ensuring research integrity.
"""

import os
import sys
import logging
import hashlib
import json
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

# Import config to access paths and project root
from config import Config, ensure_paths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Known synthetic/placeholder signatures and patterns
SYNTHETIC_SIGNATURES = [
    b'synthetic',
    b'simulated',
    b'generated',
    b'placeholder',
    b'fake',
    b'mock',
    b'random_data',
    b'test_data',
    b'example',
]

# Known file patterns that indicate non-real data
PLACEHOLDER_FILE_PATTERNS = [
    'synthetic',
    'simulated',
    'mock',
    'fake',
    'placeholder',
    'example',
]

# Minimum expected file size for a real count matrix (bytes)
# Real scRNA-seq count matrices are typically > 100KB
MIN_REAL_FILE_SIZE = 1024 * 100  # 100KB

# Maximum allowed file size for a real count matrix (bytes)
# Extremely large files might indicate corrupted or malformed data
MAX_REAL_FILE_SIZE = 1024 * 1024 * 1024 * 10  # 10GB

# Expected file extensions for count matrices
VALID_COUNT_EXTENSIONS = {'.csv', '.tsv', '.txt', '.mtx', '.h5', '.h5ad', '.loom'}


class RealDataValidationError(Exception):
    """Raised when real data constraints are violated."""
    pass


def check_file_for_synthetic_content(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Check if a file contains synthetic or placeholder content.

    Args:
        file_path: Path to the file to check.

    Returns:
        Tuple of (is_synthetic, list_of_detected_patterns)
    """
    detected_patterns = []

    try:
        # Check file extension first
        if file_path.suffix.lower() not in VALID_COUNT_EXTENSIONS:
            # Not a standard count matrix format, but not necessarily synthetic
            logger.warning(f"Non-standard file extension: {file_path.suffix}")

        # Check file size
        file_size = file_path.stat().st_size
        if file_size < MIN_REAL_FILE_SIZE:
            logger.warning(f"File too small to be real count matrix: {file_path} ({file_size} bytes)")
            detected_patterns.append("file_too_small")

        # Check filename for synthetic patterns
        filename_lower = file_path.name.lower()
        for pattern in PLACEHOLDER_FILE_PATTERNS:
            if pattern in filename_lower:
                detected_patterns.append(f"filename_contains_{pattern}")

        # Read file content and check for synthetic signatures
        # Only read first few KB to avoid performance issues with large files
        try:
            with open(file_path, 'rb') as f:
                header_bytes = f.read(8192)  # Read first 8KB
                header_str = header_bytes.decode('utf-8', errors='ignore').lower()

                for signature in SYNTHETIC_SIGNATURES:
                    sig_str = signature.decode('utf-8')
                    if sig_str in header_str:
                        detected_patterns.append(f"contains_{sig_str}")

                # Check for common synthetic data patterns in text files
                if file_path.suffix.lower() in {'.csv', '.tsv', '.txt'}:
                    # Look for rows that might indicate synthetic data
                    lines = header_str.split('\n')[:10]
                    for line in lines:
                        # Check for sequential numbers that might indicate synthetic data
                        if 'gene1' in line or 'cell1' in line:
                            detected_patterns.append("sequential_naming_pattern")

                        # Check for uniform values that might indicate synthetic data
                        if 'all_zeros' in line or 'all_ones' in line:
                            detected_patterns.append("uniform_value_pattern")

        except UnicodeDecodeError:
            # Binary file, skip content check
            pass

    except Exception as e:
        logger.error(f"Error checking file {file_path}: {e}")
        raise

    is_synthetic = len(detected_patterns) > 0
    return is_synthetic, detected_patterns


def validate_raw_directory(raw_dir: Path) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Validate that all files in the raw data directory are real (not synthetic).

    Args:
        raw_dir: Path to the raw data directory.

    Returns:
        Tuple of (is_valid, list_of_violations)
    """
    violations = []

    if not raw_dir.exists():
        logger.warning(f"Raw data directory does not exist: {raw_dir}")
        return True, violations  # No files to validate

    if not raw_dir.is_dir():
        raise RealDataValidationError(f"Raw data path is not a directory: {raw_dir}")

    # Scan all files in the raw directory
    for file_path in raw_dir.rglob('*'):
        if file_path.is_file():
            is_synthetic, patterns = check_file_for_synthetic_content(file_path)

            if is_synthetic:
                violation = {
                    'file': str(file_path),
                    'detected_patterns': patterns,
                    'file_size': file_path.stat().st_size,
                    'status': 'REJECTED'
                }
                violations.append(violation)
                logger.error(f"Synthetic data detected: {file_path} - Patterns: {patterns}")

    is_valid = len(violations) == 0
    return is_valid, violations


def enforce_real_data_constraint(raw_dir: Optional[Path] = None) -> bool:
    """
    Enforce the "Real Data Only" constraint by validating the raw data directory.

    This function should be called before any data processing steps to ensure
    that no synthetic or placeholder data is used in the analysis.

    Args:
        raw_dir: Optional path to the raw data directory. If None, uses config.

    Returns:
        True if all data passes validation, False otherwise.

    Raises:
        RealDataValidationError: If synthetic data is detected.
    """
    if raw_dir is None:
        # Use config to get the raw data directory
        ensure_paths()
        raw_dir = Path(Config.DATA_RAW)

    logger.info(f"Validating real data constraint for: {raw_dir}")

    is_valid, violations = validate_raw_directory(raw_dir)

    if not is_valid:
        error_msg = (
            f"Real data validation failed! Found {len(violations)} synthetic/placeholder file(s):\n"
        )
        for v in violations:
            error_msg += f"  - {v['file']}: {v['detected_patterns']}\n"
        error_msg += "\nAborting pipeline to prevent analysis of synthetic data."

        logger.error(error_msg)
        raise RealDataValidationError(error_msg)

    logger.info("Real data validation passed. All files appear to be genuine.")
    return True


def validate_accession_data(accession: str, raw_dir: Optional[Path] = None) -> bool:
    """
    Validate that data for a specific accession is real (not synthetic).

    Args:
        accession: GEO accession ID to validate.
        raw_dir: Optional path to the raw data directory.

    Returns:
        True if the accession data passes validation, False otherwise.

    Raises:
        RealDataValidationError: If synthetic data is detected for this accession.
    """
    if raw_dir is None:
        ensure_paths()
        raw_dir = Path(Config.DATA_RAW)

    # Look for files related to this accession
    accession_files = list(raw_dir.glob(f"*{accession}*"))

    if not accession_files:
        logger.warning(f"No files found for accession {accession} in {raw_dir}")
        return True  # No files to validate

    for file_path in accession_files:
        if file_path.is_file():
            is_synthetic, patterns = check_file_for_synthetic_content(file_path)

            if is_synthetic:
                error_msg = (
                    f"Real data validation failed for accession {accession}!\n"
                    f"File: {file_path}\n"
                    f"Detected patterns: {patterns}\n"
                    f"Aborting pipeline to prevent analysis of synthetic data."
                )
                logger.error(error_msg)
                raise RealDataValidationError(error_msg)

    logger.info(f"Real data validation passed for accession {accession}")
    return True


def main():
    """
    Main entry point for running the real data validator as a standalone script.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate that raw data contains only real (non-synthetic) data."
    )
    parser.add_argument(
        "--raw-dir",
        type=str,
        default=None,
        help="Path to the raw data directory (default: from config)"
    )
    parser.add_argument(
        "--accession",
        type=str,
        default=None,
        help="Specific accession ID to validate (optional)"
    )

    args = parser.parse_args()

    try:
        if args.accession:
            validate_accession_data(args.accession, args.raw_dir)
            print(f"✓ Validation passed for accession: {args.accession}")
        else:
            enforce_real_data_constraint(args.raw_dir)
            print("✓ Real data validation passed for all files.")

        return 0

    except RealDataValidationError as e:
        print(f"✗ Real data validation failed: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"✗ Unexpected error during validation: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
