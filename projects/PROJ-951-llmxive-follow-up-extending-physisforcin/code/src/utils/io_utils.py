import os
import hashlib
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# Core directory structure as per tasks.md
DATA_DIRS = [
    "data/raw",
    "data/curated",
    "data/eval",
    "data/validation"
]

def ensure_dirs(base_path: Optional[Union[str, Path]] = None) -> List[Path]:
    """
    Creates the required data directory structure under the project root.
    
    Args:
        base_path: Project root path. Defaults to current working directory if None.
        
    Returns:
        List of created Path objects.
    """
    if base_path is None:
        base_path = Path.cwd()
    else:
        base_path = Path(base_path)

    created_dirs = []
    for dir_name in DATA_DIRS:
        full_path = base_path / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
        created_dirs.append(full_path)
    
    return created_dirs

def calculate_file_checksum(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Calculates the checksum of a file.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        Hexadecimal checksum string.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is a directory.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if file_path.is_dir():
        raise ValueError(f"Cannot calculate checksum for a directory: {file_path}")

    hash_func = hashlib.new(algorithm)
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except IOError as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise

def calculate_directory_checksums(dir_path: Union[str, Path], algorithm: str = "sha256") -> Dict[str, str]:
    """
    Calculates checksums for all files in a directory recursively.
    
    Args:
        dir_path: Path to the directory.
        algorithm: Hash algorithm to use.
        
    Returns:
        Dictionary mapping relative file paths to their checksums.
    """
    dir_path = Path(dir_path)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    if not dir_path.is_dir():
        raise ValueError(f"Path is not a directory: {dir_path}")

    checksums = {}
    for file_path in dir_path.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(dir_path)
            try:
                checksum = calculate_file_checksum(file_path, algorithm)
                checksums[str(rel_path)] = checksum
            except Exception as e:
                logger.warning(f"Skipping file {file_path} due to error: {e}")
    
    return checksums

def save_checksums(checksums: Dict[str, str], output_path: Union[str, Path]) -> None:
    """
    Saves a dictionary of checksums to a JSON file.
    
    Args:
        checksums: Dictionary of file paths to checksums.
        output_path: Path to the output JSON file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Saved checksums to {output_path}")

def load_checksums(input_path: Union[str, Path]) -> Dict[str, str]:
    """
    Loads a dictionary of checksums from a JSON file.
    
    Args:
        input_path: Path to the input JSON file.
        
    Returns:
        Dictionary of file paths to checksums.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Checksum file not found: {input_path}")
    
    with open(input_path, "r", encoding="utf-8") as f:
        return json.load(f)

def verify_directory_integrity(dir_path: Union[str, Path], expected_checksums: Dict[str, str]) -> Tuple[bool, List[str]]:
    """
    Verifies the integrity of a directory against expected checksums.
    
    Args:
        dir_path: Path to the directory to verify.
        expected_checksums: Dictionary of expected file paths to checksums.
        
    Returns:
        Tuple of (is_valid, list_of_mismatched_files).
    """
    dir_path = Path(dir_path)
    mismatches = []
    
    # Check for missing files
    for rel_path_str, expected_checksum in expected_checksums.items():
        file_path = dir_path / rel_path_str
        if not file_path.exists():
            mismatches.append(f"Missing: {rel_path_str}")
            continue
        
        try:
            actual_checksum = calculate_file_checksum(file_path)
            if actual_checksum != expected_checksum:
                mismatches.append(f"Checksum mismatch: {rel_path_str}")
        except Exception as e:
            mismatches.append(f"Error reading {rel_path_str}: {e}")
    
    # Check for unexpected new files (optional strictness could be added here)
    # For now, we only verify that expected files exist and match.
    
    return len(mismatches) == 0, mismatches

def update_checksums(dir_path: Union[str, Path], checksum_file: Union[str, Path]) -> None:
    """
    Updates the checksum file for a directory.
    
    Args:
        dir_path: Path to the directory.
        checksum_file: Path to the checksum JSON file.
    """
    current_checksums = calculate_directory_checksums(dir_path)
    save_checksums(current_checksums, checksum_file)
    logger.info(f"Updated checksums for {dir_path}")

def get_file_size(file_path: Union[str, Path]) -> int:
    """
    Gets the size of a file in bytes.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Size in bytes.
    """
    return Path(file_path).stat().st_size

def get_total_size(dir_path: Union[str, Path]) -> int:
    """
    Gets the total size of a directory in bytes.
    
    Args:
        dir_path: Path to the directory.
        
    Returns:
        Total size in bytes.
    """
    total = 0
    dir_path = Path(dir_path)
    if not dir_path.exists():
        return 0
    for path in dir_path.rglob("*"):
        if path.is_file():
            total += path.stat().st_size
    return total

def cleanup_empty_dirs(dir_path: Union[str, Path]) -> int:
    """
    Removes empty directories recursively.
    
    Args:
        dir_path: Path to the root directory.
        
    Returns:
        Number of directories removed.
    """
    dir_path = Path(dir_path)
    removed_count = 0
    
    # Walk bottom-up
    for root, dirs, files in os.walk(dir_path, topdown=False):
        for name in dirs:
            dir_to_check = Path(root) / name
            try:
                if not any(dir_to_check.iterdir()):
                    dir_to_check.rmdir()
                    removed_count += 1
                    logger.debug(f"Removed empty directory: {dir_to_check}")
            except OSError:
                pass
    
    return removed_count

def move_files_with_checksums(src_dir: Union[str, Path], dst_dir: Union[str, Path], files: List[str]) -> List[Tuple[str, str]]:
    """
    Moves specified files from src to dst, verifying checksums.
    
    Args:
        src_dir: Source directory.
        dst_dir: Destination directory.
        files: List of relative file paths to move.
        
    Returns:
        List of (file_path, checksum) tuples for moved files.
        
    Raises:
        RuntimeError: If checksum verification fails after move.
    """
    src_dir = Path(src_dir)
    dst_dir = Path(dst_dir)
    moved_files = []
    
    for rel_path_str in files:
        src_file = src_dir / rel_path_str
        dst_file = dst_dir / rel_path_str
        
        if not src_file.exists():
            logger.warning(f"Source file not found: {src_file}")
            continue
        
        # Calculate checksum before move
        try:
            checksum = calculate_file_checksum(src_file)
        except Exception as e:
            logger.error(f"Failed to calculate checksum for {src_file}: {e}")
            continue
        
        # Ensure destination directory exists
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Move file
        shutil.move(str(src_file), str(dst_file))
        
        # Verify checksum after move
        try:
            new_checksum = calculate_file_checksum(dst_file)
            if new_checksum != checksum:
                raise RuntimeError(f"Checksum mismatch after move for {rel_path_str}")
            moved_files.append((rel_path_str, checksum))
            logger.info(f"Moved and verified: {rel_path_str}")
        except Exception as e:
            logger.error(f"Verification failed for {rel_path_str}: {e}")
            # Attempt to rollback? For now, just log.
            raise
    
    return moved_files

def validate_project_structure(base_path: Union[str, Path]) -> Tuple[bool, List[str]]:
    """
    Validates that the project directory structure matches requirements.
    
    Args:
        base_path: Project root path.
        
    Returns:
        Tuple of (is_valid, list_of_missing_dirs).
    """
    base_path = Path(base_path)
    missing = []
    for dir_name in DATA_DIRS:
        if not (base_path / dir_name).exists():
            missing.append(dir_name)
    
    return len(missing) == 0, missing

def get_data_stats(dir_path: Union[str, Path]) -> Dict[str, Union[int, float]]:
    """
    Returns statistics about a data directory.
    
    Args:
        dir_path: Path to the directory.
        
    Returns:
        Dictionary with file count, total size, and average file size.
    """
    dir_path = Path(dir_path)
    if not dir_path.exists():
        return {"file_count": 0, "total_size": 0, "avg_size": 0.0}
    
    files = [f for f in dir_path.rglob("*") if f.is_file()]
    count = len(files)
    total_size = sum(f.stat().st_size for f in files)
    avg_size = total_size / count if count > 0 else 0.0
    
    return {
        "file_count": count,
        "total_size": total_size,
        "avg_size": avg_size
    }

def main():
    """Main entry point for CLI execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="IO Utilities for llmXive project")
    parser.add_argument("--base", type=str, default=".", help="Base project path")
    parser.add_argument("--action", type=str, choices=["setup", "verify", "stats"], default="setup", help="Action to perform")
    parser.add_argument("--dir", type=str, default=None, help="Target directory for verify/stats")
    
    args = parser.parse_args()
    base_path = Path(args.base)
    
    if args.action == "setup":
        logger.info(f"Setting up directories under {base_path}")
        dirs = ensure_dirs(base_path)
        logger.info(f"Created/Verified: {[str(d) for d in dirs]}")
        
        # Create checksum file
        checksum_file = base_path / "data" / "checksums.json"
        checksum_file.parent.mkdir(parents=True, exist_ok=True)
        # Initialize with empty or existing
        if not checksum_file.exists():
            save_checksums({}, checksum_file)
        
    elif args.action == "verify":
        target = Path(args.dir) if args.dir else base_path / "data"
        if not target.exists():
            logger.error(f"Target directory not found: {target}")
            return 1
        
        # Load checksums
        checksum_file = base_path / "data" / "checksums.json"
        if not checksum_file.exists():
            logger.warning("No checksum file found. Generating new one.")
            update_checksums(target, checksum_file)
            return 0
        
        expected = load_checksums(checksum_file)
        is_valid, mismatches = verify_directory_integrity(target, expected)
        
        if is_valid:
            logger.info("Directory integrity verified.")
        else:
            logger.error(f"Integrity check failed. Mismatches: {mismatches}")
            return 1
            
    elif args.action == "stats":
        target = Path(args.dir) if args.dir else base_path / "data"
        if not target.exists():
            logger.error(f"Target directory not found: {target}")
            return 1
        
        stats = get_data_stats(target)
        logger.info(f"Stats for {target}: {stats}")
        
    return 0

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    exit(main())
