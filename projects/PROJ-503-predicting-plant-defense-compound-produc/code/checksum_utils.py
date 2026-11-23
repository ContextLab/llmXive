"""
SHA-256 Checksum Validation Utility for Data Integrity (SC-004).

This module provides functions to calculate, generate, load, and validate
SHA-256 checksums for data files. It is used to ensure data integrity
during the download and processing phases of the pipeline.

Usage:
    - Generate checksums for raw data files:
      python -m code.checksum_utils generate --input data/raw/ --output data/raw/checksums.json
    - Validate downloaded files against stored checksums:
      python -m code.checksum_utils validate --input data/raw/ --checksums data/raw/checksums.json
"""
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def calculate_sha256(file_path: Path) -> str:
    """
    Calculate the SHA-256 hash of a file.

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


def generate_checksums(
    input_dir: Path,
    output_path: Path,
    recursive: bool = True,
    extensions: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Generate SHA-256 checksums for all files in a directory.

    Args:
        input_dir: Directory containing files to hash.
        output_path: Path to save the JSON checksum file.
        recursive: Whether to search subdirectories.
        extensions: Optional list of file extensions to include (e.g., ['.csv', '.tsv']).
                   If None, all files are included.

    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes.
    """
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    checksums = {}
    files_processed = 0

    logger.info(f"Generating checksums for files in: {input_dir}")

    if recursive:
        file_iterator = input_dir.rglob('*')
    else:
        file_iterator = input_dir.glob('*')

    for file_path in file_iterator:
        if file_path.is_file():
            if extensions:
                if file_path.suffix.lower() not in extensions:
                    continue

            try:
                relative_path = file_path.relative_to(input_dir)
                file_hash = calculate_sha256(file_path)
                checksums[str(relative_path)] = file_hash
                files_processed += 1
                logger.debug(f"Hashed: {relative_path}")
            except Exception as e:
                logger.error(f"Failed to hash {file_path}: {e}")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save checksums to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(checksums, f, indent=2)

    logger.info(f"Generated checksums for {files_processed} files. Saved to: {output_path}")
    return checksums


def load_checksums(checksum_path: Path) -> Dict[str, str]:
    """
    Load checksums from a JSON file.

    Args:
        checksum_path: Path to the JSON file containing checksums.

    Returns:
        Dictionary mapping file paths to their expected SHA-256 hashes.

    Raises:
        FileNotFoundError: If the checksum file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not checksum_path.exists():
        raise FileNotFoundError(f"Checksum file not found: {checksum_path}")

    with open(checksum_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_checksums(
    input_dir: Path,
    checksums: Dict[str, str],
    strict: bool = True
) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
    """
    Validate files in a directory against a dictionary of expected checksums.

    Args:
        input_dir: Directory containing files to validate.
        checksums: Dictionary mapping relative file paths to expected hashes.
        strict: If True, raise an error if any file is missing or mismatched.

    Returns:
        Tuple of (passed_files, failed_files, missing_files) where each is a dict
        mapping file path to its hash (or error reason for missing).
    """
    passed = {}
    failed = {}
    missing = {}

    logger.info(f"Validating {len(checksums)} files in: {input_dir}")

    for rel_path, expected_hash in checksums.items():
        file_path = input_dir / rel_path

        if not file_path.exists():
            missing[rel_path] = "File not found"
            logger.warning(f"Missing file: {rel_path}")
            continue

        try:
            actual_hash = calculate_sha256(file_path)
            if actual_hash == expected_hash:
                passed[rel_path] = actual_hash
            else:
                failed[rel_path] = f"Mismatch: expected {expected_hash}, got {actual_hash}"
                logger.error(f"Checksum mismatch for {rel_path}: {failed[rel_path]}")
        except Exception as e:
            failed[rel_path] = f"Error reading file: {e}"
            logger.error(f"Error validating {rel_path}: {e}")

    # Check for files in directory that are not in checksums (optional warning)
    existing_files = set()
    for f in input_dir.rglob('*'):
        if f.is_file():
            existing_files.add(str(f.relative_to(input_dir)))
    
    unexpected_files = existing_files - set(checksums.keys())
    if unexpected_files:
        logger.warning(f"Found {len(unexpected_files)} files in {input_dir} not covered by checksums: {unexpected_files}")

    total = len(checksums)
    passed_count = len(passed)
    failed_count = len(failed)
    missing_count = len(missing)

    logger.info(f"Validation complete: {passed_count}/{total} passed, {failed_count} failed, {missing_count} missing")

    if strict and (failed_count > 0 or missing_count > 0):
        error_msg = f"Validation failed: {failed_count} mismatches, {missing_count} missing files."
        raise RuntimeError(error_msg)

    return passed, failed, missing


def main():
    """
    Command-line interface for checksum utility.

    Usage:
        python -m code.checksum_utils generate --input <dir> --output <file>
        python -m code.checksum_utils validate --input <dir> --checksums <file> [--strict]
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="SHA-256 Checksum Utility for Data Integrity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Generate checksums:
    python -m code.checksum_utils generate --input data/raw --output data/raw/checksums.json

  Validate checksums:
    python -m code.checksum_utils validate --input data/raw --checksums data/raw/checksums.json
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate checksums for files in a directory')
    gen_parser.add_argument('--input', '-i', type=Path, required=True, help='Input directory containing files')
    gen_parser.add_argument('--output', '-o', type=Path, required=True, help='Output JSON file for checksums')
    gen_parser.add_argument('--recursive', '-r', action='store_true', default=True, help='Search subdirectories (default: True)')
    gen_parser.add_argument('--extensions', '-e', nargs='+', help='File extensions to include (e.g., .csv .tsv)')

    # Validate command
    val_parser = subparsers.add_parser('validate', help='Validate files against a checksum file')
    val_parser.add_argument('--input', '-i', type=Path, required=True, help='Input directory containing files to validate')
    val_parser.add_argument('--checksums', '-c', type=Path, required=True, help='JSON file containing expected checksums')
    val_parser.add_argument('--strict', '-s', action='store_true', default=True, help='Raise error on any mismatch/missing (default: True)')

    args = parser.parse_args()

    if args.command == 'generate':
        try:
            generate_checksums(
                input_dir=args.input,
                output_path=args.output,
                recursive=args.recursive,
                extensions=args.extensions
            )
            print(f"Checksums generated successfully: {args.output}")
        except Exception as e:
            logger.error(f"Checksum generation failed: {e}")
            exit(1)

    elif args.command == 'validate':
        try:
            checksums = load_checksums(args.checksums)
            passed, failed, missing = validate_checksums(
                input_dir=args.input,
                checksums=checksums,
                strict=args.strict
            )
            print(f"Validation complete: {len(passed)} passed, {len(failed)} failed, {len(missing)} missing")
            if not args.strict and (failed or missing):
                print("Non-strict mode: errors logged but process continued.")
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            exit(1)

    else:
        parser.print_help()
        exit(1)


if __name__ == '__main__':
    main()