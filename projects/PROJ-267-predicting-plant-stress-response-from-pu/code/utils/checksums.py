import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Any

from .logging_config import get_logger, log_warning

logger = get_logger(__name__)

# Constants
CHECKSUM_FILE_NAME = "checksums.json"
CHUNK_SIZE = 8192  # 8KB chunks for reading large files


def compute_sha256(file_path: str) -> str:
    """
    Compute the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file to compute checksum for.

    Returns:
        Hexadecimal string representation of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise


def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """
    Verify the SHA-256 checksum of a file against an expected value.

    Args:
        file_path: Path to the file to verify.
        expected_checksum: Expected SHA-256 hex string.

    Returns:
        True if checksum matches, False otherwise.
    """
    try:
        actual_checksum = compute_sha256(file_path)
        return actual_checksum.lower() == expected_checksum.lower()
    except (FileNotFoundError, IOError) as e:
        logger.error(f"Verification failed for {file_path}: {e}")
        return False


def save_checksums(checksums: Dict[str, str], output_path: str) -> None:
    """
    Save a dictionary of file paths to checksums to a JSON file.

    Args:
        checksums: Dictionary mapping file paths to their SHA-256 checksums.
        output_path: Path to the output JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Checksums saved to {output_path}")


def load_checksums(input_path: str) -> Dict[str, str]:
    """
    Load a dictionary of file paths to checksums from a JSON file.

    Args:
        input_path: Path to the input JSON file.

    Returns:
        Dictionary mapping file paths to SHA-256 checksums.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Checksum file not found: {input_path}")

    with open(path, "r") as f:
        data = json.load(f)
    logger.info(f"Loaded {len(data)} checksums from {input_path}")
    return data


def verify_all_downloads(
    checksum_file_path: str,
    base_dir: Optional[str] = None
) -> Tuple[List[str], List[str]]:
    """
    Verify all files listed in a checksum file against their stored checksums.

    Args:
        checksum_file_path: Path to the JSON file containing checksums.
        base_dir: Optional base directory to prepend to relative paths in the checksum file.

    Returns:
        Tuple of (list of verified files, list of failed files).
    """
    checksums = load_checksums(checksum_file_path)
    verified = []
    failed = []

    for rel_path, expected_checksum in checksums.items():
        if base_dir:
            full_path = os.path.join(base_dir, rel_path)
        else:
            full_path = rel_path

        if verify_checksum(full_path, expected_checksum):
            verified.append(full_path)
            logger.debug(f"Verified: {full_path}")
        else:
            failed.append(full_path)
            logger.warning(f"Checksum mismatch for: {full_path}")

    return verified, failed


def generate_checksums_for_directory(
    directory_path: str,
    recursive: bool = True,
    extensions: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Generate checksums for all files in a directory.

    Args:
        directory_path: Path to the directory to scan.
        recursive: If True, scan subdirectories.
        extensions: Optional list of file extensions to include (e.g., ['.csv', '.txt']).
                    If None, include all files.

    Returns:
        Dictionary mapping relative file paths to their SHA-256 checksums.
    """
    base_path = Path(directory_path)
    if not base_path.exists() or not base_path.is_dir():
        raise ValueError(f"Directory not found: {directory_path}")

    checksums = {}

    if recursive:
        files = base_path.rglob("*")
    else:
        files = base_path.glob("*")

    for file_path in files:
        if file_path.is_file():
            if extensions:
                if file_path.suffix.lower() not in [ext.lower() for ext in extensions]:
                    continue

            rel_path = str(file_path.relative_to(base_path))
            try:
                checksum = compute_sha256(str(file_path))
                checksums[rel_path] = checksum
                logger.debug(f"Generated checksum for: {rel_path}")
            except Exception as e:
                log_warning(f"Failed to generate checksum for {file_path}: {e}")

    return checksums


def main() -> None:
    """
    Command-line interface for checksum operations.

    Usage:
        python -m utils.checksums <command> [args]

    Commands:
        verify <checksum_file> [base_dir]
            Verify files against a checksum file.

        generate <directory> [--recursive] [--ext .ext1,.ext2]
            Generate checksums for a directory and print/save them.

        verify_all <checksum_file> [base_dir]
            Same as verify, but returns exit code 1 if any fail.
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m utils.checksums <command> [args]")
        print("Commands: verify, generate, verify_all")
        sys.exit(1)

    command = sys.argv[1]

    if command == "verify":
        if len(sys.argv) < 3:
            print("Error: verify requires a checksum file path")
            sys.exit(1)
        checksum_file = sys.argv[2]
        base_dir = sys.argv[3] if len(sys.argv) > 3 else None
        verified, failed = verify_all_downloads(checksum_file, base_dir)
        print(f"Verified: {len(verified)} files")
        print(f"Failed: {len(failed)} files")
        if failed:
            for f in failed:
                print(f"  FAILED: {f}")
            sys.exit(1)
        else:
            print("All checksums verified successfully.")
            sys.exit(0)

    elif command == "generate":
        if len(sys.argv) < 3:
            print("Error: generate requires a directory path")
            sys.exit(1)
        directory = sys.argv[2]
        recursive = "--recursive" in sys.argv
        extensions = None
        if "--ext" in sys.argv:
            idx = sys.argv.index("--ext")
            if idx + 1 < len(sys.argv):
                extensions = sys.argv[idx + 1].split(",")

        try:
            checksums = generate_checksums_for_directory(directory, recursive, extensions)
            print(json.dumps(checksums, indent=2))
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif command == "verify_all":
        # Alias for verify, but ensures non-zero exit on failure
        if len(sys.argv) < 3:
            print("Error: verify_all requires a checksum file path")
            sys.exit(1)
        checksum_file = sys.argv[2]
        base_dir = sys.argv[3] if len(sys.argv) > 3 else None
        verified, failed = verify_all_downloads(checksum_file, base_dir)
        if failed:
            sys.exit(1)
        else:
            sys.exit(0)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()