"""
I/O Utilities for llmXive project.

Provides functions for directory management, file checksums,
integrity verification, and data statistics.
"""

import os
import hashlib
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union

# Configure logging for this module
logger = logging.getLogger(__name__)


def ensure_dirs(base_path: Union[str, Path]) -> Path:
    """
    Ensure that the data directory structure exists.
    Creates: data/raw, data/curated, data/eval
    
    Args:
        base_path: The root directory to start from (e.g., project root)
        
    Returns:
        The Path object for the base directory
    """
    base = Path(base_path)
    data_dirs = ['data/raw', 'data/curated', 'data/eval']
    
    for dir_path in data_dirs:
        full_path = base / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {full_path}")
        
    return base


def calculate_file_checksum(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
    """
    Calculate the checksum of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hexadecimal checksum string
        
    Raises:
        FileNotFoundError: If the file does not exist
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    hash_obj = hashlib.new(algorithm)
    
    with open(path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b''):
            hash_obj.update(chunk)
            
    return hash_obj.hexdigest()


def calculate_directory_checksums(dir_path: Union[str, Path], 
                                  algorithm: str = 'sha256') -> Dict[str, str]:
    """
    Calculate checksums for all files in a directory recursively.
    
    Args:
        dir_path: Path to the directory
        algorithm: Hash algorithm to use
        
    Returns:
        Dictionary mapping relative file paths to their checksums
    """
    path = Path(dir_path)
    if not path.is_dir():
        raise NotADirectoryError(f"Not a directory: {dir_path}")
        
    checksums = {}
    
    for file_path in path.rglob('*'):
        if file_path.is_file():
            rel_path = str(file_path.relative_to(path))
            checksums[rel_path] = calculate_file_checksum(file_path, algorithm)
            
    return checksums


def save_checksums(checksums: Dict[str, str], output_path: Union[str, Path]) -> None:
    """
    Save checksums to a JSON file.
    
    Args:
        checksums: Dictionary of relative paths to checksums
        output_path: Path to the output JSON file
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(checksums, f, indent=2)
        
    logger.info(f"Saved checksums to {output_path}")


def load_checksums(input_path: Union[str, Path]) -> Dict[str, str]:
    """
    Load checksums from a JSON file.
    
    Args:
        input_path: Path to the input JSON file
        
    Returns:
        Dictionary of relative paths to checksums
        
    Raises:
        FileNotFoundError: If the file does not exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Checksum file not found: {input_path}")
        
    with open(path, 'r') as f:
        return json.load(f)


def verify_directory_integrity(dir_path: Union[str, Path], 
                               checksums: Dict[str, str]) -> Tuple[bool, List[str]]:
    """
    Verify the integrity of a directory against stored checksums.
    
    Args:
        dir_path: Path to the directory to verify
        checksums: Dictionary of expected checksums (relative path -> checksum)
        
    Returns:
        Tuple of (is_valid, list_of_failed_files)
    """
    path = Path(dir_path)
    failed_files = []
    
    for rel_file, expected_checksum in checksums.items():
        file_path = path / rel_file
        
        if not file_path.exists():
            failed_files.append(f"{rel_file} (missing)")
            continue
            
        try:
            actual_checksum = calculate_file_checksum(file_path)
            if actual_checksum != expected_checksum:
                failed_files.append(f"{rel_file} (checksum mismatch)")
        except Exception as e:
            failed_files.append(f"{rel_file} (error: {str(e)})")
            
    is_valid = len(failed_files) == 0
    return is_valid, failed_files


def update_checksums(dir_path: Union[str, Path], 
                     checksum_file: Union[str, Path]) -> Dict[str, str]:
    """
    Update the checksum file for a directory.
    
    Args:
        dir_path: Path to the directory
        checksum_file: Path to the checksum file to update
        
    Returns:
        The updated checksums dictionary
    """
    new_checksums = calculate_directory_checksums(dir_path)
    save_checksums(new_checksums, checksum_file)
    return new_checksums


def get_file_size(file_path: Union[str, Path]) -> int:
    """
    Get the size of a file in bytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in bytes
    """
    return Path(file_path).stat().st_size


def get_total_size(dir_path: Union[str, Path]) -> int:
    """
    Get the total size of a directory in bytes.
    
    Args:
        dir_path: Path to the directory
        
    Returns:
        Total size in bytes
    """
    path = Path(dir_path)
    total = 0
    
    for file_path in path.rglob('*'):
        if file_path.is_file():
            total += file_path.stat().st_size
            
    return total


def cleanup_empty_dirs(dir_path: Union[str, Path]) -> int:
    """
    Remove empty directories recursively.
    
    Args:
        dir_path: Path to the directory to clean
        
    Returns:
        Number of directories removed
    """
    path = Path(dir_path)
    count = 0
    
    # Sort by depth (deepest first) to remove children before parents
    dirs = sorted([d for d in path.rglob('*') if d.is_dir()], 
                 key=lambda x: len(x.parts), reverse=True)
                 
    for dir_to_remove in dirs:
        try:
            if not any(dir_to_remove.iterdir()):
                dir_to_remove.rmdir()
                count += 1
                logger.debug(f"Removed empty directory: {dir_to_remove}")
        except Exception as e:
            logger.warning(f"Could not remove directory {dir_to_remove}: {e}")
            
    return count


def move_files_with_checksums(source_dir: Union[str, Path], 
                              dest_dir: Union[str, Path],
                              files: List[str],
                              checksum_file: Optional[Union[str, Path]] = None) -> Dict[str, str]:
    """
    Move files from source to destination and optionally update checksums.
    
    Args:
        source_dir: Source directory
        dest_dir: Destination directory
        files: List of relative file paths to move
        checksum_file: Optional path to checksum file to update
        
    Returns:
        Dictionary of relative paths to their checksums
    """
    src = Path(source_dir)
    dst = Path(dest_dir)
    dst.mkdir(parents=True, exist_ok=True)
    
    checksums = {}
    
    for file_rel in files:
        src_file = src / file_rel
        dst_file = dst / file_rel
        
        if src_file.exists():
            # Calculate checksum before moving
            checksums[file_rel] = calculate_file_checksum(src_file)
            
            # Move file
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src_file), str(dst_file))
            logger.info(f"Moved {src_file} to {dst_file}")
        else:
            logger.warning(f"File not found for moving: {src_file}")
            
    if checksum_file:
        save_checksums(checksums, checksum_file)
        
    return checksums


def validate_project_structure(base_path: Union[str, Path]) -> Tuple[bool, List[str]]:
    """
    Validate that the project directory structure is correct.
    
    Args:
        base_path: Root path of the project
        
    Returns:
        Tuple of (is_valid, list_of_missing_components)
    """
    base = Path(base_path)
    required_dirs = [
        'data/raw', 'data/curated', 'data/eval',
        'src/generation', 'src/filtering', 'src/training', 
        'src/evaluation', 'src/utils',
        'tests/unit', 'tests/integration'
    ]
    
    missing = []
    
    for dir_path in required_dirs:
        if not (base / dir_path).exists():
            missing.append(dir_path)
            
    is_valid = len(missing) == 0
    return is_valid, missing


def get_data_stats(base_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Get statistics about the data directories.
    
    Args:
        base_path: Root path of the project
        
    Returns:
        Dictionary with statistics for each data directory
    """
    base = Path(base_path)
    stats = {}
    
    for dir_name in ['raw', 'curated', 'eval']:
        dir_path = base / 'data' / dir_name
        
        if dir_path.exists():
            file_count = sum(1 for _ in dir_path.rglob('*') if _.is_file())
            total_size = get_total_size(dir_path)
            
            stats[dir_name] = {
                'path': str(dir_path),
                'file_count': file_count,
                'total_size_bytes': total_size,
                'total_size_mb': total_size / (1024 * 1024),
                'total_size_gb': total_size / (1024 * 1024 * 1024)
            }
        else:
            stats[dir_name] = {
                'path': str(dir_path),
                'exists': False
            }
            
    return stats


def main():
    """
    Main function to demonstrate I/O utilities.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='llmXive I/O Utilities')
    parser.add_argument('--base-path', type=str, default='.', 
                      help='Base project path')
    parser.add_argument('--ensure-dirs', action='store_true',
                      help='Ensure data directories exist')
    parser.add_argument('--validate', action='store_true',
                      help='Validate project structure')
    parser.add_argument('--stats', action='store_true',
                      help='Get data statistics')
    parser.add_argument('--checksum-dir', type=str,
                      help='Calculate checksums for a directory')
    parser.add_argument('--verify-dir', type=str,
                      help='Verify a directory against checksums')
    parser.add_argument('--checksum-file', type=str,
                      help='Path to checksum file for verification')
                      
    args = parser.parse_args()
    
    base = Path(args.base_path)
    
    if args.ensure_dirs:
        ensure_dirs(base)
        print(f"Data directories ensured at {base / 'data'}")
        
    if args.validate:
        is_valid, missing = validate_project_structure(base)
        if is_valid:
            print("Project structure is valid.")
        else:
            print(f"Project structure is INVALID. Missing: {missing}")
            
    if args.stats:
        stats = get_data_stats(base)
        print(json.dumps(stats, indent=2))
        
    if args.checksum_dir:
        checksums = calculate_directory_checksums(args.checksum_dir)
        print(json.dumps(checksums, indent=2))
        
    if args.verify_dir and args.checksum_file:
        checksums = load_checksums(args.checksum_file)
        is_valid, failed = verify_directory_integrity(args.verify_dir, checksums)
        if is_valid:
            print(f"Directory {args.verify_dir} integrity verified.")
        else:
            print(f"Directory {args.verify_dir} integrity check FAILED:")
            for f in failed:
                print(f"  - {f}")


if __name__ == '__main__':
    main()
