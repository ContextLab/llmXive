"""
Checksum validation utility for data integrity (SC-004).
Provides SHA-256 verification for downloaded datasets.
"""
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from error_handler import handle_error, raise_dataset_error
from exceptions import E_DATASET

logger = logging.getLogger(__name__)


def calculate_sha256(file_path: Path) -> str:
    """
    Calculate SHA-256 checksum of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise


def validate_checksums(
    checksums_file: Path,
    data_dir: Path,
    expected_coverage: float = 0.99
) -> Dict[str, any]:
    """
    Validate SHA-256 checksums for files in a directory against a manifest.

    Args:
        checksums_file: Path to JSON manifest containing {filename: expected_hash}.
        data_dir: Directory containing the files to validate.
        expected_coverage: Minimum fraction of files that must pass validation (default 0.99).

    Returns:
        Dictionary with validation results:
        {
            "passed": List[str],
            "failed": List[str],
            "missing": List[str],
            "total": int,
            "coverage": float,
            "success": bool
        }

    Raises:
        E_DATASET: If coverage is below expected_threshold or critical files are missing.
    """
    if not checksums_file.exists():
        raise_dataset_error(f"Checksums manifest not found: {checksums_file}", E_DATASET)

    if not data_dir.exists():
        raise_dataset_error(f"Data directory not found: {data_dir}", E_DATASET)

    try:
        with open(checksums_file, "r") as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        raise_dataset_error(f"Invalid JSON in checksums manifest: {e}", E_DATASET)

    passed = []
    failed = []
    missing = []

    for filename, expected_hash in manifest.items():
        file_path = data_dir / filename
        if not file_path.exists():
            missing.append(filename)
            logger.warning(f"Missing file during validation: {filename}")
            continue

        try:
            actual_hash = calculate_sha256(file_path)
            if actual_hash.lower() == expected_hash.lower():
                passed.append(filename)
            else:
                failed.append(filename)
                logger.error(
                    f"Checksum mismatch for {filename}: "
                    f"expected {expected_hash}, got {actual_hash}"
                )
        except Exception as e:
            failed.append(filename)
            logger.error(f"Error validating {filename}: {e}")

    total = len(manifest)
    valid_count = len(passed)
    coverage = valid_count / total if total > 0 else 0.0

    result = {
        "passed": passed,
        "failed": failed,
        "missing": missing,
        "total": total,
        "coverage": coverage,
        "success": coverage >= expected_coverage and len(missing) == 0
    }

    logger.info(
        f"Checksum validation complete: {valid_count}/{total} passed "
        f"(coverage: {coverage:.2%})"
    )

    if not result["success"]:
        reason = []
        if coverage < expected_coverage:
            reason.append(f"Coverage {coverage:.2%} < required {expected_coverage:.2%}")
        if missing:
            reason.append(f"{len(missing)} files missing")
        if failed:
            reason.append(f"{len(failed)} files failed checksum")

        raise_dataset_error(
            f"Data integrity check failed: {'; '.join(reason)}",
            E_DATASET
        )

    return result


def generate_checksums(data_dir: Path, output_file: Path) -> Dict[str, str]:
    """
    Generate SHA-256 checksums for all files in a directory and save to JSON.

    Args:
        data_dir: Directory containing files to hash.
        output_file: Path where the JSON manifest will be written.

    Returns:
        Dictionary mapping filenames to their SHA-256 hashes.
    """
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    checksums = {}
    files = [f for f in data_dir.iterdir() if f.is_file()]

    logger.info(f"Generating checksums for {len(files)} files in {data_dir}")

    for file_path in files:
        try:
            file_hash = calculate_sha256(file_path)
            checksums[file_path.name] = file_hash
        except Exception as e:
            logger.error(f"Failed to hash {file_path.name}: {e}")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(checksums, f, indent=2)

    logger.info(f"Checksums saved to {output_file}")
    return checksums


def main():
    """
    CLI entry point for checksum validation utility.
    Usage:
        python code/checksum_utils.py generate <data_dir> <output_manifest>
        python code/checksum_utils.py validate <manifest_path> <data_dir> [--threshold 0.99]
    """
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="SHA-256 checksum utility for data integrity")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate checksums for files in a directory")
    gen_parser.add_argument("data_dir", type=Path, help="Directory containing files to hash")
    gen_parser.add_argument("output", type=Path, help="Output path for JSON manifest")

    # Validate command
    val_parser = subparsers.add_parser("validate", help="Validate files against a checksum manifest")
    val_parser.add_argument("manifest", type=Path, help="Path to JSON checksum manifest")
    val_parser.add_argument("data_dir", type=Path, help="Directory containing files to validate")
    val_parser.add_argument(
        "--threshold",
        type=float,
        default=0.99,
        help="Minimum coverage fraction required (default: 0.99)"
    )

    args = parser.parse_args()

    if args.command == "generate":
        try:
            generate_checksums(args.data_dir, args.output)
            print(f"Generated checksums: {args.output}")
        except Exception as e:
            handle_error(e)
            sys.exit(1)

    elif args.command == "validate":
        try:
            result = validate_checksums(args.manifest, args.data_dir, args.threshold)
            print(f"Validation successful. Coverage: {result['coverage']:.2%}")
            print(f"Passed: {len(result['passed'])}, Failed: {len(result['failed'])}, Missing: {len(result['missing'])}")
        except Exception as e:
            handle_error(e)
            sys.exit(1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
