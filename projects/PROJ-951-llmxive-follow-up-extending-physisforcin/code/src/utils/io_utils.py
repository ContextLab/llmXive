"""
I/O Utilities for llmXive pipeline.
Provides checksumming, directory management, and integrity verification.
"""
import os
import hashlib
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

logger = logging.getLogger(__name__)


def calculate_file_checksum(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Calculate the checksum of a single file.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal checksum string.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hasher = hashlib.new(algorithm)
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating checksum for {file_path}: {e}")
        raise


def calculate_directory_checksums(
    dir_path: Union[str, Path],
    algorithm: str = "sha256",
    recursive: bool = True
) -> Dict[str, str]:
    """
    Calculate checksums for all files in a directory.

    Args:
        dir_path: Path to the directory.
        algorithm: Hash algorithm to use.
        recursive: If True, process subdirectories recursively.

    Returns:
        Dictionary mapping relative file paths to their checksums.
    """
    dir_path = Path(dir_path)
    if not dir_path.exists() or not dir_path.is_dir():
        raise NotADirectoryError(f"Directory not found or invalid: {dir_path}")

    checksums = {}
    glob_pattern = "**/*" if recursive else "*"

    for file_path in dir_path.glob(glob_pattern):
        if file_path.is_file():
            try:
                rel_path = file_path.relative_to(dir_path)
                checksums[str(rel_path)] = calculate_file_checksum(file_path, algorithm)
            except Exception as e:
                logger.warning(f"Skipping file {file_path} due to error: {e}")

    return checksums


def save_checksums(checksums: Dict[str, str], output_path: Union[str, Path]) -> None:
    """
    Save checksums dictionary to a JSON file.

    Args:
        checksums: Dictionary of checksums.
        output_path: Path to the output JSON file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Checksums saved to {output_path}")


def load_checksums(input_path: Union[str, Path]) -> Dict[str, str]:
    """
    Load checksums from a JSON file.

    Args:
        input_path: Path to the input JSON file.

    Returns:
        Dictionary of checksums.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Checksum file not found: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        return json.load(f)


def verify_directory_integrity(
    dir_path: Union[str, Path],
    expected_checksums: Dict[str, str],
    algorithm: str = "sha256"
) -> Tuple[bool, List[str]]:
    """
    Verify the integrity of a directory against expected checksums.

    Args:
        dir_path: Path to the directory to verify.
        expected_checksums: Dictionary of expected checksums.
        algorithm: Hash algorithm to use.

    Returns:
        Tuple of (is_valid, list_of_mismatched_or_missing_files).
    """
    dir_path = Path(dir_path)
    mismatches = []

    for rel_path_str, expected_hash in expected_checksums.items():
        file_path = dir_path / rel_path_str

        if not file_path.exists():
            mismatches.append(f"Missing: {rel_path_str}")
            continue

        try:
            actual_hash = calculate_file_checksum(file_path, algorithm)
            if actual_hash != expected_hash:
                mismatches.append(f"Mismatch: {rel_path_str} (expected: {expected_hash[:16]}..., got: {actual_hash[:16]}...)")
        except Exception as e:
            mismatches.append(f"Error reading {rel_path_str}: {e}")

    is_valid = len(mismatches) == 0
    return is_valid, mismatches


def update_checksums(
    dir_path: Union[str, Path],
    output_path: Union[str, Path],
    algorithm: str = "sha256",
    recursive: bool = True
) -> Dict[str, str]:
    """
    Calculate checksums for a directory and save them.

    Args:
        dir_path: Source directory.
        output_path: Output JSON file path.
        algorithm: Hash algorithm.
        recursive: Process recursively.

    Returns:
        The calculated checksums dictionary.
    """
    checksums = calculate_directory_checksums(dir_path, algorithm, recursive)
    save_checksums(checksums, output_path)
    return checksums


def ensure_dirs(dir_paths: List[Union[str, Path]]) -> None:
    """
    Ensure that a list of directories exists, creating them if necessary.

    Args:
        dir_paths: List of directory paths.
    """
    for path in dir_paths:
        path_obj = Path(path)
        path_obj.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {path_obj}")


def get_file_size(file_path: Union[str, Path]) -> int:
    """
    Get the size of a file in bytes.

    Args:
        file_path: Path to the file.

    Returns:
        Size in bytes.
    """
    return Path(file_path).stat().st_size


def get_total_size(dir_path: Union[str, Path], recursive: bool = True) -> int:
    """
    Get the total size of a directory in bytes.

    Args:
        dir_path: Path to the directory.
        recursive: Sum sizes of files in subdirectories.

    Returns:
        Total size in bytes.
    """
    dir_path = Path(dir_path)
    total = 0
    pattern = "**/*" if recursive else "*"

    for file_path in dir_path.glob(pattern):
        if file_path.is_file():
            total += file_path.stat().st_size

    return total


def cleanup_empty_dirs(dir_path: Union[str, Path], recursive: bool = True) -> int:
    """
    Remove empty directories starting from the deepest level.

    Args:
        dir_path: Root directory to scan.
        recursive: Scan subdirectories.

    Returns:
        Number of directories removed.
    """
    dir_path = Path(dir_path)
    removed_count = 0

    # Sort by depth (deepest first) to ensure bottom-up cleanup
    dirs_to_check = sorted(
        [d for d in dir_path.rglob("*") if d.is_dir()],
        key=lambda p: len(p.parts),
        reverse=True
    )

    for d in dirs_to_check:
        try:
            if not any(d.iterdir()):
                d.rmdir()
                removed_count += 1
                logger.debug(f"Removed empty directory: {d}")
        except OSError:
            # Directory not empty or permission issue
            continue

    return removed_count


def move_files_with_checksums(
    src_dir: Union[str, Path],
    dst_dir: Union[str, Path],
    files: List[str],
    algorithm: str = "sha256"
) -> bool:
    """
    Move specific files from src to dst, verifying checksums after move.

    Args:
        src_dir: Source directory.
        dst_dir: Destination directory.
        files: List of relative file paths to move.
        algorithm: Hash algorithm.

    Returns:
        True if all moves and verifications succeeded, False otherwise.
    """
    src_dir = Path(src_dir)
    dst_dir = Path(dst_dir)
    dst_dir.mkdir(parents=True, exist_ok=True)

    success = True

    for rel_file in files:
        src_file = src_dir / rel_file
        dst_file = dst_dir / rel_file

        if not src_file.exists():
            logger.error(f"Source file missing: {src_file}")
            success = False
            continue

        try:
            # Calculate pre-move checksum
            pre_checksum = calculate_file_checksum(src_file, algorithm)

            # Move file
            shutil.move(str(src_file), str(dst_file))

            # Verify post-move checksum
            if dst_file.exists():
                post_checksum = calculate_file_checksum(dst_file, algorithm)
                if pre_checksum != post_checksum:
                    logger.error(f"Checksum mismatch after move: {rel_file}")
                    success = False
                else:
                    logger.debug(f"Successfully moved and verified: {rel_file}")
            else:
                logger.error(f"Destination file not created: {dst_file}")
                success = False

        except Exception as e:
            logger.error(f"Error moving {rel_file}: {e}")
            success = False

    return success


def validate_project_structure(base_path: Union[str, Path], required_dirs: List[str]) -> Tuple[bool, List[str]]:
    """
    Validate that a project structure contains required directories.

    Args:
        base_path: Root of the project.
        required_dirs: List of relative directory paths that must exist.

    Returns:
        Tuple of (is_valid, list_of_missing_dirs).
    """
    base_path = Path(base_path)
    missing = []

    for rel_dir in required_dirs:
        full_path = base_path / rel_dir
        if not full_path.exists() or not full_path.is_dir():
            missing.append(rel_dir)

    return len(missing) == 0, missing


def get_data_stats(dir_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Gather statistics about a data directory.

    Args:
        dir_path: Path to the data directory.

    Returns:
        Dictionary with file count, total size, and directory count.
    """
    dir_path = Path(dir_path)
    if not dir_path.exists():
        return {
            "exists": False,
            "file_count": 0,
            "directory_count": 0,
            "total_size_bytes": 0
        }

    file_count = 0
    dir_count = 0
    total_size = 0

    for item in dir_path.rglob("*"):
        if item.is_file():
            file_count += 1
            total_size += item.stat().st_size
        elif item.is_dir():
            dir_count += 1

    return {
        "exists": True,
        "file_count": file_count,
        "directory_count": dir_count,
        "total_size_bytes": total_size
    }


def main():
    """
    CLI entry point for basic I/O utility testing.
    """
    import argparse

    parser = argparse.ArgumentParser(description="I/O Utilities CLI")
    parser.add_argument("action", choices=["checksum", "verify", "stats"], help="Action to perform")
    parser.add_argument("path", help="Path to file or directory")
    parser.add_argument("--output", help="Output path for checksums (for 'checksum' action)")
    parser.add_argument("--expected", help="Expected checksums JSON path (for 'verify' action)")

    args = parser.parse_args()

    if args.action == "checksum":
        path = Path(args.path)
        if path.is_file():
            print(calculate_file_checksum(path))
        elif path.is_dir():
            checksums = calculate_directory_checksums(path)
            if args.output:
                save_checksums(checksums, args.output)
            else:
                print(json.dumps(checksums, indent=2))
        else:
            print("Error: Path not found", file=sys.stderr)
            sys.exit(1)

    elif args.action == "verify":
        if not args.expected:
            print("Error: --expected required for verify action", file=sys.stderr)
            sys.exit(1)
        expected = load_checksums(args.expected)
        is_valid, mismatches = verify_directory_integrity(args.path, expected)
        if is_valid:
            print("Integrity check passed.")
        else:
            print("Integrity check failed:")
            for m in mismatches:
                print(f"  - {m}")
            sys.exit(1)

    elif args.action == "stats":
        stats = get_data_stats(args.path)
        print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    import sys
    main()
