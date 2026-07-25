"""
I/O Utilities for llmXive project.
Provides directory management, checksumming, and integrity verification.
"""
import os
import hashlib
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

# Configure logger
logger = logging.getLogger(__name__)

# Data directories to be managed
DATA_DIRS = [
    "data/raw",
    "data/curated",
    "data/eval",
    "data/validation",
]

def ensure_dirs(base_path: Optional[Union[str, Path]] = None) -> List[Path]:
    """
    Ensure all required data directories exist.
    
    Args:
        base_path: Base project path. Defaults to current working directory.
        
    Returns:
        List of created directory paths.
    """
    if base_path is None:
        base_path = Path.cwd()
    else:
        base_path = Path(base_path)
        
    created_dirs = []
    for dir_name in DATA_DIRS:
        full_path = base_path / dir_name
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(full_path)
            logger.info(f"Ensured directory: {full_path}")
        except PermissionError as e:
            logger.error(f"Permission denied creating directory {full_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            raise
    
    return created_dirs

def calculate_file_checksum(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Calculate the checksum of a file.
    
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
    
    try:
        hash_func = hashlib.new(algorithm)
    except ValueError as e:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}") from e
    
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except PermissionError as e:
        logger.error(f"Permission denied reading file {file_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error calculating checksum for {file_path}: {e}")
        raise

def calculate_directory_checksums(dir_path: Union[str, Path], 
                                  algorithm: str = "sha256",
                                  recursive: bool = True) -> Dict[str, str]:
    """
    Calculate checksums for all files in a directory.
    
    Args:
        dir_path: Path to the directory.
        algorithm: Hash algorithm to use.
        recursive: Whether to include subdirectories.
        
    Returns:
        Dictionary mapping relative file paths to their checksums.
        
    Raises:
        NotADirectoryError: If path is not a directory.
    """
    dir_path = Path(dir_path)
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {dir_path}")
    
    checksums = {}
    
    if recursive:
        pattern = "**/*"
    else:
        pattern = "*"
        
    for file_path in dir_path.glob(pattern):
        if file_path.is_file():
            try:
                rel_path = file_path.relative_to(dir_path)
                checksums[str(rel_path)] = calculate_file_checksum(file_path, algorithm)
            except Exception as e:
                logger.warning(f"Skipping file {file_path} during checksum calculation: {e}")
    
    return checksums

def save_checksums(checksums: Dict[str, str], 
                   output_path: Union[str, Path],
                   algorithm: str = "sha256") -> None:
    """
    Save checksums to a JSON file.
    
    Args:
        checksums: Dictionary of file paths to checksums.
        output_path: Path to the output JSON file.
        algorithm: Algorithm used for the checksums.
    """
    output_path = Path(output_path)
    data = {
        "algorithm": algorithm,
        "checksums": checksums
    }
    
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved checksums to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save checksums to {output_path}: {e}")
        raise

def load_checksums(checksum_path: Union[str, Path]) -> Dict[str, str]:
    """
    Load checksums from a JSON file.
    
    Args:
        checksum_path: Path to the checksum JSON file.
        
    Returns:
        Dictionary of file paths to checksums.
        
    Raises:
        FileNotFoundError: If the checksum file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    checksum_path = Path(checksum_path)
    if not checksum_path.exists():
        raise FileNotFoundError(f"Checksum file not found: {checksum_path}")
    
    try:
        with open(checksum_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        algorithm = data.get("algorithm", "sha256")
        checksums = data.get("checksums", {})
        
        logger.info(f"Loaded checksums ({len(checksums)} files) from {checksum_path}")
        return checksums
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in checksum file {checksum_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to load checksums from {checksum_path}: {e}")
        raise

def verify_directory_integrity(dir_path: Union[str, Path], 
                               checksum_path: Union[str, Path],
                               strict: bool = True) -> Dict[str, bool]:
    """
    Verify directory integrity against stored checksums.
    
    Args:
        dir_path: Path to the directory to verify.
        checksum_path: Path to the checksum file.
        strict: If True, fail if files are missing from checksums.
        
    Returns:
        Dictionary mapping file paths to verification status (True/False).
    """
    dir_path = Path(dir_path)
    stored_checksums = load_checksums(checksum_path)
    results = {}
    
    # Check files in stored checksums
    for rel_path_str, expected_checksum in stored_checksums.items():
        file_path = dir_path / rel_path_str
        
        if not file_path.exists():
            results[rel_path_str] = False
            logger.warning(f"Missing file during verification: {file_path}")
            continue
            
        try:
            actual_checksum = calculate_file_checksum(file_path)
            is_valid = actual_checksum == expected_checksum
            results[rel_path_str] = is_valid
            
            if not is_valid:
                logger.warning(f"Checksum mismatch for {file_path}")
        except Exception as e:
            results[rel_path_str] = False
            logger.error(f"Error verifying {file_path}: {e}")
    
    # Check for new files if not strict
    if not strict:
        current_files = set(str(p.relative_to(dir_path)) 
                          for p in dir_path.rglob("*") if p.is_file())
        stored_files = set(stored_checksums.keys())
        
        new_files = current_files - stored_files
        for new_file in new_files:
            results[new_file] = True
            logger.info(f"New file detected (non-strict mode): {new_file}")
    
    # Report missing files if strict
    if strict:
        current_files = set(str(p.relative_to(dir_path)) 
                          for p in dir_path.rglob("*") if p.is_file())
        stored_files = set(stored_checksums.keys())
        missing_files = stored_files - current_files
        
        if missing_files:
            logger.warning(f"Files missing in strict mode: {missing_files}")
    
    return results

def update_checksums(dir_path: Union[str, Path], 
                     checksum_path: Union[str, Path],
                     algorithm: str = "sha256") -> None:
    """
    Update checksums for a directory.
    
    Args:
        dir_path: Path to the directory.
        checksum_path: Path to the checksum file.
        algorithm: Hash algorithm to use.
    """
    dir_path = Path(dir_path)
    checksums = calculate_directory_checksums(dir_path, algorithm)
    save_checksums(checksums, checksum_path, algorithm)
    logger.info(f"Updated checksums for {dir_path}")

def get_file_size(file_path: Union[str, Path]) -> int:
    """
    Get the size of a file in bytes.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        File size in bytes.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    return file_path.stat().st_size

def get_total_size(dir_path: Union[str, Path]) -> int:
    """
    Get the total size of a directory in bytes.
    
    Args:
        dir_path: Path to the directory.
        
    Returns:
        Total size in bytes.
    """
    dir_path = Path(dir_path)
    total = 0
    for file_path in dir_path.rglob("*"):
        if file_path.is_file():
            total += file_path.stat().st_size
    return total

def cleanup_empty_dirs(dir_path: Union[str, Path]) -> int:
    """
    Remove empty directories recursively.
    
    Args:
        dir_path: Path to the directory to clean.
        
    Returns:
        Number of directories removed.
    """
    dir_path = Path(dir_path)
    removed_count = 0
    
    # Sort by depth (deepest first)
    dirs_to_check = sorted(dir_path.rglob("*"), key=lambda p: len(p.parts), reverse=True)
    
    for dir_to_check in dirs_to_check:
        if dir_to_check.is_dir():
            try:
                if not any(dir_to_check.iterdir()):
                    dir_to_check.rmdir()
                    removed_count += 1
                    logger.debug(f"Removed empty directory: {dir_to_check}")
            except PermissionError:
                logger.warning(f"Permission denied removing {dir_to_check}")
            except Exception as e:
                logger.warning(f"Error removing {dir_to_check}: {e}")
    
    return removed_count

def move_files_with_checksums(source_dir: Union[str, Path], 
                              dest_dir: Union[str, Path],
                              files: List[str],
                              algorithm: str = "sha256") -> Dict[str, bool]:
    """
    Move files and verify checksums.
    
    Args:
        source_dir: Source directory.
        dest_dir: Destination directory.
        files: List of relative file paths to move.
        algorithm: Hash algorithm to use.
        
    Returns:
        Dictionary mapping file paths to success status.
    """
    source_dir = Path(source_dir)
    dest_dir = Path(dest_dir)
    results = {}
    
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    for rel_path_str in files:
        src_file = source_dir / rel_path_str
        dest_file = dest_dir / rel_path_str
        
        if not src_file.exists():
            results[rel_path_str] = False
            logger.warning(f"Source file missing: {src_file}")
            continue
        
        try:
            # Calculate checksum before move
            checksum = calculate_file_checksum(src_file, algorithm)
            
            # Ensure destination directory exists
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Move file
            shutil.move(str(src_file), str(dest_file))
            
            # Verify checksum after move
            actual_checksum = calculate_file_checksum(dest_file, algorithm)
            
            if actual_checksum == checksum:
                results[rel_path_str] = True
                logger.info(f"Moved and verified: {rel_path_str}")
            else:
                results[rel_path_str] = False
                logger.error(f"Checksum mismatch after move: {rel_path_str}")
                
        except Exception as e:
            results[rel_path_str] = False
            logger.error(f"Error moving {rel_path_str}: {e}")
    
    return results

def validate_project_structure(base_path: Union[str, Path]) -> Dict[str, bool]:
    """
    Validate that the project structure matches expected directories.
    
    Args:
        base_path: Base project path.
        
    Returns:
        Dictionary mapping directory names to existence status.
    """
    base_path = Path(base_path)
    results = {}
    
    for dir_name in DATA_DIRS:
        dir_path = base_path / dir_name
        exists = dir_path.exists() and dir_path.is_dir()
        results[dir_name] = exists
        
        if not exists:
            logger.warning(f"Missing expected directory: {dir_path}")
        else:
            logger.debug(f"Validated directory: {dir_path}")
    
    return results

def get_data_stats(base_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Get statistics about the data directories.
    
    Args:
        base_path: Base project path.
        
    Returns:
        Dictionary with directory statistics.
    """
    base_path = Path(base_path)
    stats = {}
    
    for dir_name in DATA_DIRS:
        dir_path = base_path / dir_name
        if dir_path.exists() and dir_path.is_dir():
            file_count = sum(1 for _ in dir_path.rglob("*") if _.is_file())
            total_size = get_total_size(dir_path)
            stats[dir_name] = {
                "exists": True,
                "file_count": file_count,
                "total_bytes": total_size,
                "total_mb": total_size / (1024 * 1024)
            }
        else:
            stats[dir_name] = {
                "exists": False,
                "file_count": 0,
                "total_bytes": 0,
                "total_mb": 0
            }
    
    return stats

def main():
    """Main entry point for CLI usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="I/O Utilities for llmXive")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Ensure dirs command
    parser_ensure = subparsers.add_parser("ensure", help="Ensure data directories exist")
    parser_ensure.add_argument("--base", type=str, default=".", help="Base path")
    
    # Checksum command
    parser_checksum = subparsers.add_parser("checksum", help="Calculate checksums")
    parser_checksum.add_argument("path", type=str, help="Path to file or directory")
    parser_checksum.add_argument("--output", type=str, help="Output file for directory checksums")
    
    # Verify command
    parser_verify = subparsers.add_parser("verify", help="Verify directory integrity")
    parser_verify.add_argument("dir", type=str, help="Directory to verify")
    parser_verify.add_argument("checksum_file", type=str, help="Checksum file")
    parser_verify.add_argument("--strict", action="store_true", help="Strict mode")
    
    # Stats command
    parser_stats = subparsers.add_parser("stats", help="Get data statistics")
    parser_stats.add_argument("--base", type=str, default=".", help="Base path")
    
    args = parser.parse_args()
    
    if args.command == "ensure":
        ensure_dirs(args.base)
    elif args.command == "checksum":
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
            parser.error(f"Path does not exist: {args.path}")
    elif args.command == "verify":
        results = verify_directory_integrity(args.dir, args.checksum_file, args.strict)
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        print(f"Verification: {passed}/{total} files passed")
    elif args.command == "stats":
        stats = get_data_stats(args.base)
        print(json.dumps(stats, indent=2))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
