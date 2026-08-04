import os
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from src.lib.utils import setup_logging

logger = logging.getLogger(__name__)

CHECKSUMS_FILE_NAME = "checksums.json"

def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a single file.

    Args:
        file_path: Path to the file to hash.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal string of the file hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hasher = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def compute_directory_checksums(
    dir_path: Path,
    algorithm: str = "sha256",
    exclude_patterns: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Compute checksums for all files in a directory recursively.

    Args:
        dir_path: Path to the directory.
        algorithm: Hash algorithm to use.
        exclude_patterns: List of glob patterns to exclude (e.g., ["*.pyc", "__pycache__"]).

    Returns:
        Dictionary mapping relative file paths to their checksums.
    """
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {dir_path}")

    exclude_patterns = exclude_patterns or []
    checksums = {}

    for root, dirs, files in os.walk(dir_path):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if not any(
            Path(root, d).match(pattern) for pattern in exclude_patterns
        )]

        for file_name in files:
            file_path = Path(root) / file_name

            # Check if file matches any exclude pattern
            if any(file_path.match(pattern) for pattern in exclude_patterns):
                continue

            try:
                rel_path = file_path.relative_to(dir_path)
                checksums[str(rel_path)] = compute_file_checksum(file_path, algorithm)
            except Exception as e:
                logger.warning(f"Skipping file {file_path}: {e}")

    return checksums

def save_checksums(checksums: Dict[str, str], output_path: Path) -> None:
    """
    Save checksums dictionary to a JSON file.

    Args:
        checksums: Dictionary of checksums.
        output_path: Path to save the JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    metadata = {
        "generated_at": datetime.utcnow().isoformat(),
        "algorithm": "sha256",
        "checksums": checksums
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Checksums saved to {output_path}")

def load_checksums(checksums_path: Path) -> Dict[str, Any]:
    """
    Load checksums from a JSON file.

    Args:
        checksums_path: Path to the JSON file.

    Returns:
        Dictionary containing metadata and checksums.
    """
    if not checksums_path.exists():
        raise FileNotFoundError(f"Checksums file not found: {checksums_path}")

    with open(checksums_path, "r", encoding="utf-8") as f:
        return json.load(f)

def verify_checksums(
    dir_path: Path,
    stored_checksums: Dict[str, str],
    exclude_patterns: Optional[List[str]] = None
) -> Dict[str, bool]:
    """
    Verify current file checksums against stored ones.

    Args:
        dir_path: Directory to verify.
        stored_checksums: Dictionary of expected checksums.
        exclude_patterns: Patterns to exclude from verification.

    Returns:
        Dictionary mapping relative paths to verification status (True/False).
    """
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")

    exclude_patterns = exclude_patterns or []
    results = {}

    # Check for files that existed before but are now missing
    for rel_path in stored_checksums:
        file_path = dir_path / rel_path
        if not file_path.exists():
            results[rel_path] = False
            logger.warning(f"Missing file during verification: {file_path}")
            continue

        try:
            current_checksum = compute_file_checksum(file_path)
            if current_checksum != stored_checksums[rel_path]:
                results[rel_path] = False
                logger.error(f"Checksum mismatch for {rel_path}")
            else:
                results[rel_path] = True
        except Exception as e:
            results[rel_path] = False
            logger.error(f"Error verifying {rel_path}: {e}")

    # Check for new files not in stored checksums
    current_files = set()
    for root, dirs, files in os.walk(dir_path):
        dirs[:] = [d for d in dirs if not any(
            Path(root, d).match(pattern) for pattern in exclude_patterns
        )]
        for file_name in files:
            file_path = Path(root) / file_name
            if any(file_path.match(pattern) for pattern in exclude_patterns):
                continue
            current_files.add(str(file_path.relative_to(dir_path)))

    new_files = current_files - set(stored_checksums.keys())
    for new_file in new_files:
        results[new_file] = False  # Flag as new/modified
        logger.info(f"New file detected: {new_file}")

    return results

def generate_checksums_for_directories(
    base_dir: Path,
    sub_dirs: List[str],
    output_filename: str = CHECKSUMS_FILE_NAME,
    exclude_patterns: Optional[List[str]] = None
) -> Path:
    """
    Generate checksums for multiple subdirectories under a base directory.

    Args:
        base_dir: Base directory containing subdirectories.
        sub_dirs: List of subdirectory names to process.
        output_filename: Name of the output checksum file.
        exclude_patterns: Patterns to exclude.

    Returns:
        Path to the generated checksums file.
    """
    all_checksums = {}
    for sub_dir in sub_dirs:
        dir_path = base_dir / sub_dir
        if not dir_path.exists():
            logger.warning(f"Skipping non-existent directory: {dir_path}")
            continue

        logger.info(f"Computing checksums for {dir_path}...")
        dir_checksums = compute_directory_checksums(dir_path, exclude_patterns=exclude_patterns)
        # Prefix paths with directory name to avoid collisions
        for rel_path, checksum in dir_checksums.items():
            all_checksums[f"{sub_dir}/{rel_path}"] = checksum

    output_path = base_dir / output_filename
    if all_checksums:
        save_checksums(all_checksums, output_path)
    else:
        logger.warning("No checksums generated. Creating empty metadata file.")
        save_checksums({}, output_path)

    return output_path

def verify_all_checksums(
    base_dir: Path,
    sub_dirs: List[str],
    checksums_filename: str = CHECKSUMS_FILE_NAME,
    exclude_patterns: Optional[List[str]] = None
) -> bool:
    """
    Verify all files in subdirectories against stored checksums.

    Args:
        base_dir: Base directory.
        sub_dirs: List of subdirectory names.
        checksums_filename: Name of the checksums file.
        exclude_patterns: Patterns to exclude.

    Returns:
        True if all checksums match, False otherwise.
    """
    checksums_path = base_dir / checksums_filename
    if not checksums_path.exists():
        logger.error(f"Checksums file not found: {checksums_path}")
        return False

    try:
        stored_data = load_checksums(checksums_path)
        stored_checksums = stored_data.get("checksums", {})
    except Exception as e:
        logger.error(f"Failed to load checksums: {e}")
        return False

    all_valid = True
    for sub_dir in sub_dirs:
        dir_path = base_dir / sub_dir
        if not dir_path.exists():
            logger.warning(f"Directory not found for verification: {dir_path}")
            continue

        logger.info(f"Verifying checksums for {dir_path}...")

        # Filter stored checksums for this directory
        dir_stored = {
            k.replace(f"{sub_dir}/", ""): v
            for k, v in stored_checksums.items()
            if k.startswith(f"{sub_dir}/")
        }

        results = verify_checksums(dir_path, dir_stored, exclude_patterns)
        for path, is_valid in results.items():
            if not is_valid:
                all_valid = False
                logger.error(f"Verification failed for {sub_dir}/{path}")

    if all_valid:
        logger.info("All checksums verified successfully.")
    else:
        logger.error("Checksum verification failed for some files.")

    return all_valid

def main() -> int:
    """
    CLI entry point for checksum generation and verification.

    Usage:
        python -m src.data.checksums generate <base_dir> <sub_dir1> [sub_dir2 ...]
        python -m src.data.checksums verify <base_dir> <sub_dir1> [sub_dir2 ...]
    """
    if len(sys.argv) < 3:
        print("Usage: python -m src.data.checksums <generate|verify> <base_dir> <sub_dir1> [sub_dir2 ...]")
        return 1

    command = sys.argv[1]
    base_dir = Path(sys.argv[2])
    sub_dirs = sys.argv[3:]

    if not base_dir.exists():
        print(f"Error: Base directory does not exist: {base_dir}")
        return 1

    exclude_patterns = ["*.pyc", "__pycache__", "*.log", ".git"]

    if command == "generate":
        generate_checksums_for_directories(base_dir, sub_dirs, exclude_patterns=exclude_patterns)
        print(f"Checksums generated for {sub_dirs} in {base_dir}")
        return 0
    elif command == "verify":
        success = verify_all_checksums(base_dir, sub_dirs, exclude_patterns=exclude_patterns)
        return 0 if success else 1
    else:
        print(f"Unknown command: {command}. Use 'generate' or 'verify'.")
        return 1

if __name__ == "__main__":
    import sys
    setup_logging()
    sys.exit(main())
