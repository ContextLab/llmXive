import os
import hashlib
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)

def ensure_dirs(dir_paths: List[Path]) -> None:
    """Ensure all specified directories exist, creating them if necessary."""
    for dir_path in dir_paths:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {dir_path}")

def calculate_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """Calculate the checksum of a single file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_func = hashlib.new(algorithm)
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating checksum for {file_path}: {e}")
        raise

def calculate_directory_checksums(dir_path: Path, algorithm: str = 'sha256') -> Dict[str, str]:
    """Calculate checksums for all files in a directory recursively."""
    if not dir_path.exists() or not dir_path.is_dir():
        raise NotADirectoryError(f"Directory not found: {dir_path}")
    
    checksums = {}
    for file_path in sorted(dir_path.rglob('*')):
        if file_path.is_file():
          relative_path = file_path.relative_to(dir_path)
          checksums[str(relative_path)] = calculate_file_checksum(file_path, algorithm)
    
    return checksums

def save_checksums(checksums: Dict[str, Any], output_path: Path) -> None:
    """Save checksums to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Checksums saved to {output_path}")

def load_checksums(input_path: Path) -> Dict[str, Any]:
    """Load checksums from a JSON file."""
    if not input_path.exists():
        raise FileNotFoundError(f"Checksum file not found: {input_path}")
    
    with open(input_path, 'r') as f:
        return json.load(f)

def verify_directory_integrity(dir_path: Path, expected_checksums: Dict[str, str], algorithm: str = 'sha256') -> Tuple[bool, List[str]]:
    """Verify the integrity of a directory against expected checksums."""
    if not dir_path.exists() or not dir_path.is_dir():
        return False, [f"Directory not found: {dir_path}"]
    
    current_checksums = calculate_directory_checksums(dir_path, algorithm)
    missing_files = []
    corrupted_files = []
    
    # Check for missing files
    for file_key in expected_checksums:
        if file_key not in current_checksums:
            missing_files.append(file_key)
    
    # Check for corrupted files
    for file_key, expected_hash in expected_checksums.items():
        if file_key in current_checksums:
            if current_checksums[file_key] != expected_hash:
                corrupted_files.append(file_key)
        elif file_key not in missing_files:
             # Should be covered by missing check, but safety net
             missing_files.append(file_key)

    is_valid = len(missing_files) == 0 and len(corrupted_files) == 0
    errors = [f"Missing: {f}" for f in missing_files] + [f"Corrupted: {f}" for f in corrupted_files]
    
    return is_valid, errors

def update_checksums(dir_path: Path, checksum_file: Path) -> None:
    """Update the checksum file with current directory state."""
    if not dir_path.exists():
        raise NotADirectoryError(f"Directory not found: {dir_path}")
    
    current_checksums = calculate_directory_checksums(dir_path)
    save_checksums(current_checksums, checksum_file)
    logger.info(f"Updated checksums for {dir_path} in {checksum_file}")

def get_file_size(file_path: Path) -> int:
    """Get the size of a file in bytes."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    return file_path.stat().st_size

def get_total_size(dir_path: Path) -> int:
    """Get the total size of a directory in bytes."""
    if not dir_path.exists() or not dir_path.is_dir():
        return 0
    total_size = 0
    for file_path in dir_path.rglob('*'):
        if file_path.is_file():
            total_size += file_path.stat().st_size
    return total_size

def cleanup_empty_dirs(dir_path: Path) -> int:
    """Remove empty directories recursively. Returns count of removed dirs."""
    removed_count = 0
    if not dir_path.exists():
        return 0
    
    # Walk bottom-up
    for dir_to_remove in sorted(dir_path.rglob('*'), reverse=True):
        if dir_to_remove.is_dir() and not any(dir_to_remove.iterdir()):
            try:
                dir_to_remove.rmdir()
                removed_count += 1
                logger.debug(f"Removed empty directory: {dir_to_remove}")
            except OSError as e:
                logger.warning(f"Could not remove directory {dir_to_remove}: {e}")
    
    return removed_count

def move_files_with_checksums(source_dir: Path, dest_dir: Path, files: List[str], checksum_file: Path) -> None:
    """Move specific files from source to destination and update checksums."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    for file_name in files:
        src_file = source_dir / file_name
        dest_file = dest_dir / file_name
        
        if not src_file.exists():
            logger.warning(f"Source file not found: {src_file}")
            continue
        
        shutil.move(str(src_file), str(dest_file))
        logger.info(f"Moved {src_file} to {dest_file}")
    
    if checksum_file.exists():
        update_checksums(dest_dir, checksum_file)

def validate_project_structure(base_dir: Path, required_dirs: List[str]) -> Tuple[bool, List[str]]:
    """Validate that a project structure contains all required directories."""
    missing = []
    for rel_path in required_dirs:
        full_path = base_dir / rel_path
        if not full_path.exists() or not full_path.is_dir():
            missing.append(rel_path)
    
    return len(missing) == 0, missing

def get_data_stats(base_dir: Path, data_dirs: List[str]) -> Dict[str, Any]:
    """Get statistics about data directories (file counts, total size)."""
    stats = {}
    for rel_path in data_dirs:
        full_path = base_dir / rel_path
        if full_path.exists() and full_path.is_dir():
            file_count = sum(1 for _ in full_path.rglob('*') if _.is_file())
            total_size = get_total_size(full_path)
            stats[rel_path] = {
                "file_count": file_count,
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024)
            }
        else:
            stats[rel_path] = {"error": "Directory not found"}
    return stats

def main():
    """Main entry point for CLI usage."""
    import argparse
    parser = argparse.ArgumentParser(description="IO Utilities for llmXive")
    parser.add_argument("command", choices=["ensure", "checksum", "verify", "update", "stats", "cleanup"], help="Command to run")
    parser.add_argument("--path", type=str, required=True, help="Target path (file or directory)")
    parser.add_argument("--output", type=str, help="Output path for checksums (required for checksum/update)")
    parser.add_argument("--expected", type=str, help="Path to expected checksums (required for verify)")
    
    args = parser.parse_args()
    path = Path(args.path)
    
    if args.command == "ensure":
        ensure_dirs([path])
        print(f"Directory ensured: {path}")
    elif args.command == "checksum":
        if not args.output:
            print("Error: --output required for checksum command")
            return 1
        if path.is_file():
            checksum = calculate_file_checksum(path)
            print(f"Checksum: {checksum}")
        elif path.is_dir():
            checksums = calculate_directory_checksums(path)
            save_checksums(checksums, Path(args.output))
            print(f"Checksums saved to {args.output}")
    elif args.command == "verify":
        if not args.expected:
            print("Error: --expected required for verify command")
            return 1
        expected = load_checksums(Path(args.expected))
        valid, errors = verify_directory_integrity(path, expected)
        if valid:
            print("Integrity check passed.")
        else:
            print("Integrity check failed:")
            for err in errors:
                print(f"  - {err}")
            return 1
    elif args.command == "update":
        if not args.output:
            print("Error: --output required for update command")
            return 1
        update_checksums(path, Path(args.output))
        print(f"Checksums updated at {args.output}")
    elif args.command == "stats":
        # For stats, path is usually base dir, we need to know subdirs. 
        # Simplified for CLI: just report on path itself if it's a dir.
        if path.is_dir():
            stats = get_data_stats(path.parent, [str(path.relative_to(path.parent))])
            print(json.dumps(stats, indent=2))
        else:
            print(f"Size: {get_file_size(path)} bytes")
    elif args.command == "cleanup":
        count = cleanup_empty_dirs(path)
        print(f"Removed {count} empty directories.")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
