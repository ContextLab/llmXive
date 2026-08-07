"""
I/O utilities for the llmXive physics filter pipeline.

Provides directory management, file checksumming, and data integrity verification.
All paths are relative to the project root under code/
"""
import os
import hashlib
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

# Configure logging
logger = logging.getLogger(__name__)

# Base project root (relative to code/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_ROOT = PROJECT_ROOT / "data"

# Standard data subdirectories
DATA_DIRS = {
    "raw": DATA_ROOT / "raw",
    "curated": DATA_ROOT / "curated",
    "eval": DATA_ROOT / "eval",
    "validation": DATA_ROOT / "validation",
    "control": DATA_ROOT / "control",
    "prompts": DATA_ROOT / "prompts",
    "baseline": DATA_ROOT / "baseline",
}

# Checksum metadata file
CHECKSUM_FILE = DATA_ROOT / ".checksums.json"


def ensure_dirs() -> None:
    """
    Create all required data directories if they don't exist.
    
    Creates:
        - data/raw: Raw generated videos
        - data/curated: Filtered/curated dataset
        - data/eval: Evaluation results and metrics
        - data/validation: Validation checks and sanity tests
        - data/control: Random control indices and data
        - data/prompts: Prompt definitions
        - data/baseline: Baseline comparison data
    """
    for dir_name, dir_path in DATA_DIRS.items():
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory: {dir_path}")
    
    # Ensure checksums file parent exists
    CHECKSUM_FILE.parent.mkdir(parents=True, exist_ok=True)


def calculate_file_checksum(file_path: Union[str, Path]) -> str:
    """
    Calculate SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Hex string of SHA-256 checksum
        
    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Cannot read file {file_path}: {e}")


def calculate_directory_checksums(dir_path: Union[str, Path]) -> Dict[str, str]:
    """
    Calculate checksums for all files in a directory recursively.
    
    Args:
        dir_path: Path to the directory
        
    Returns:
        Dictionary mapping relative file paths to their checksums
        
    Raises:
        NotADirectoryError: If path is not a directory
    """
    dir_path = Path(dir_path)
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {dir_path}")
    
    checksums = {}
    for file_path in dir_path.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(dir_path)
            try:
                checksums[str(rel_path)] = calculate_file_checksum(file_path)
            except (FileNotFoundError, IOError) as e:
                logger.warning(f"Skipping file {file_path}: {e}")
    
    return checksums


def save_checksums(checksums: Dict[str, str], output_path: Optional[Path] = None) -> None:
    """
    Save checksums to a JSON file.
    
    Args:
        checksums: Dictionary of file paths to checksums
        output_path: Optional path to save checksums (defaults to CHECKSUM_FILE)
    """
    if output_path is None:
        output_path = CHECKSUM_FILE
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(checksums, f, indent=2)
    
    logger.info(f"Saved checksums to {output_path}")


def load_checksums(input_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load checksums from a JSON file.
    
    Args:
        input_path: Optional path to load checksums from (defaults to CHECKSUM_FILE)
        
    Returns:
        Dictionary of file paths to checksums
        
    Raises:
        FileNotFoundError: If checksum file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    if input_path is None:
        input_path = CHECKSUM_FILE
    
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Checksum file not found: {input_path}")
    
    with open(input_path, "r") as f:
        return json.load(f)


def verify_directory_integrity(dir_path: Union[str, Path], 
                               checksums: Optional[Dict[str, str]] = None) -> Tuple[bool, List[str]]:
    """
    Verify directory integrity against stored checksums.
    
    Args:
        dir_path: Directory to verify
        checksums: Optional checksums dict (loads from file if None)
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    dir_path = Path(dir_path)
    errors = []
    
    if checksums is None:
        try:
            checksums = load_checksums()
        except FileNotFoundError:
            errors.append("No checksum file found")
            return False, errors
    
    # Check for missing files
    for rel_path, expected_checksum in checksums.items():
        full_path = dir_path / rel_path
        if not full_path.exists():
            errors.append(f"Missing file: {rel_path}")
            continue
        
        # Verify checksum
        try:
            actual_checksum = calculate_file_checksum(full_path)
            if actual_checksum != expected_checksum:
                errors.append(f"Checksum mismatch: {rel_path}")
        except (FileNotFoundError, IOError) as e:
            errors.append(f"Cannot read file {rel_path}: {e}")
    
    # Check for new files not in checksums
    existing_files = {str(p.relative_to(dir_path)) for p in dir_path.rglob("*") if p.is_file()}
    known_files = set(checksums.keys())
    new_files = existing_files - known_files
    if new_files:
        errors.append(f"New files not in checksums: {new_files}")
    
    return len(errors) == 0, errors


def update_checksums(dir_path: Union[str, Path]) -> Dict[str, str]:
    """
    Update checksums for a directory and save them.
    
    Args:
        dir_path: Directory to update checksums for
        
    Returns:
        Updated checksums dictionary
    """
    dir_path = Path(dir_path)
    checksums = calculate_directory_checksums(dir_path)
    save_checksums(checksums)
    logger.info(f"Updated checksums for {dir_path}")
    return checksums


def get_file_size(file_path: Union[str, Path]) -> int:
    """
    Get file size in bytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in bytes
        
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    return file_path.stat().st_size


def get_total_size(dir_path: Union[str, Path]) -> int:
    """
    Get total size of all files in a directory recursively.
    
    Args:
        dir_path: Path to the directory
        
    Returns:
        Total size in bytes
    """
    dir_path = Path(dir_path)
    if not dir_path.is_dir():
        return 0
    
    total = 0
    for file_path in dir_path.rglob("*"):
        if file_path.is_file():
            total += file_path.stat().st_size
    return total


def cleanup_empty_dirs(dir_path: Union[str, Path]) -> int:
    """
    Remove empty directories recursively.
    
    Args:
        dir_path: Directory to clean up
        
    Returns:
        Number of directories removed
    """
    dir_path = Path(dir_path)
    if not dir_path.is_dir():
        return 0
    
    removed_count = 0
    # Walk bottom-up to remove empty dirs
    for root, dirs, files in os.walk(dir_path, topdown=False):
        root_path = Path(root)
        # Check if directory is empty (no files and no subdirs)
        if not files and not dirs:
            try:
                root_path.rmdir()
                removed_count += 1
                logger.debug(f"Removed empty directory: {root_path}")
            except OSError:
                pass  # Directory not empty or permission issue
    
    return removed_count


def move_files_with_checksums(src_dir: Union[str, Path], 
                               dst_dir: Union[str, Path],
                               pattern: Optional[str] = None) -> int:
    """
    Move files from source to destination with checksum verification.
    
    Args:
        src_dir: Source directory
        dst_dir: Destination directory
        pattern: Optional glob pattern to match files
        
    Returns:
        Number of files moved
    """
    src_dir = Path(src_dir)
    dst_dir = Path(dst_dir)
    dst_dir.mkdir(parents=True, exist_ok=True)
    
    # Get files to move
    if pattern:
        files = list(src_dir.glob(pattern))
    else:
        files = list(src_dir.iterdir())
    
    moved_count = 0
    for file_path in files:
        if file_path.is_file():
            # Calculate checksum before move
            try:
                checksum = calculate_file_checksum(file_path)
            except (FileNotFoundError, IOError) as e:
                logger.warning(f"Skipping {file_path}: {e}")
                continue
            
            # Move file
            dst_path = dst_dir / file_path.name
            try:
                shutil.move(str(file_path), str(dst_path))
                
                # Verify checksum after move
                actual_checksum = calculate_file_checksum(dst_path)
                if actual_checksum != checksum:
                    logger.error(f"Checksum mismatch after move: {file_path.name}")
                    # Attempt to restore
                    shutil.move(str(dst_path), str(file_path))
                    continue
                
                moved_count += 1
                logger.debug(f"Moved {file_path} -> {dst_path}")
            except (IOError, OSError) as e:
                logger.error(f"Failed to move {file_path}: {e}")
    
    return moved_count


def validate_project_structure(base_path: Optional[Path] = None) -> Tuple[bool, List[str]]:
    """
    Validate that the project has the required directory structure.
    
    Args:
        base_path: Base path to validate (defaults to PROJECT_ROOT)
        
    Returns:
        Tuple of (is_valid, list_of_missing_paths)
    """
    if base_path is None:
        base_path = PROJECT_ROOT
    
    base_path = Path(base_path)
    errors = []
    
    # Check required directories
    required_dirs = [
        "src",
        "src/generation",
        "src/filtering",
        "src/training",
        "src/evaluation",
        "src/augmentation",
        "src/utils",
        "tests",
        "tests/unit",
        "tests/integration",
        "data",
        "data/raw",
        "data/curated",
        "data/eval",
        "data/validation",
    ]
    
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        if not full_path.exists():
            errors.append(f"Missing directory: {dir_path}")
        elif not full_path.is_dir():
            errors.append(f"Not a directory: {dir_path}")
    
    return len(errors) == 0, errors


def get_data_stats() -> Dict[str, Any]:
    """
    Get statistics about the data directories.
    
    Returns:
        Dictionary with directory sizes and file counts
    """
    stats = {}
    
    for dir_name, dir_path in DATA_DIRS.items():
        if dir_path.exists():
          file_count = sum(1 for _ in dir_path.rglob("*") if _.is_file())
          total_size = get_total_size(dir_path)
          stats[dir_name] = {
              "exists": True,
              "file_count": file_count,
              "total_size_bytes": total_size,
              "total_size_mb": total_size / (1024 * 1024)
          }
        else:
            stats[dir_name] = {
                "exists": False,
                "file_count": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0
            }
    
    return stats


def main():
    """
    Main entry point for command-line usage.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="IO Utilities for llmXive")
    parser.add_argument("command", choices=["ensure", "checksum", "verify", "stats", "validate"],
                      help="Command to execute")
    parser.add_argument("--path", type=str, help="Path for checksum/verify commands")
    parser.add_argument("--dir", type=str, help="Directory for stats/validation")
    
    args = parser.parse_args()
    
    if args.command == "ensure":
        ensure_dirs()
        print("Data directories ensured.")
    
    elif args.command == "checksum":
        if not args.path:
            print("Error: --path required for checksum command")
            return
        path = Path(args.path)
        if path.is_file():
            checksum = calculate_file_checksum(path)
            print(f"Checksum: {checksum}")
        elif path.is_dir():
            checksums = calculate_directory_checksums(path)
            print(json.dumps(checksums, indent=2))
        else:
            print(f"Error: Path not found: {path}")
    
    elif args.command == "verify":
        if not args.path:
            print("Error: --path required for verify command")
            return
        dir_path = Path(args.path)
        is_valid, errors = verify_directory_integrity(dir_path)
        if is_valid:
            print("Directory integrity verified.")
        else:
            print("Integrity check failed:")
            for error in errors:
                print(f"  - {error}")
    
    elif args.command == "stats":
        dir_path = Path(args.dir) if args.dir else DATA_ROOT
        if not dir_path.exists():
            print(f"Error: Directory not found: {dir_path}")
            return
        stats = get_data_stats() if args.dir is None else {
            "path": str(dir_path),
            "file_count": sum(1 for _ in dir_path.rglob("*") if _.is_file()),
            "total_size_bytes": get_total_size(dir_path),
            "total_size_mb": get_total_size(dir_path) / (1024 * 1024)
        }
        print(json.dumps(stats, indent=2))
    
    elif args.command == "validate":
        base = Path(args.dir) if args.dir else PROJECT_ROOT
        is_valid, errors = validate_project_structure(base)
        if is_valid:
            print("Project structure validated.")
        else:
            print("Structure validation failed:")
            for error in errors:
                print(f"  - {error}")


if __name__ == "__main__":
    main()
