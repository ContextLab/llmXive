"""
Module to generate SHA-256 checksums for all files in specified directories.
This module is used for T031 to generate data/checksums.json.
"""
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, List

from config import get_path, load_config


def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash
        
    Returns:
        Hexadecimal string of the SHA-256 hash
        
    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If the file cannot be read
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")


def collect_files(directory: Path, exclude_patterns: List[str] = None) -> List[Path]:
    """
    Recursively collect all files in a directory.
    
    Args:
        directory: Root directory to scan
        exclude_patterns: List of filename patterns to exclude (e.g., ['.gitkeep', '.DS_Store'])
        
    Returns:
        List of Path objects for all files found
    """
    if exclude_patterns is None:
        exclude_patterns = ['.gitkeep', '.DS_Store', '__pycache__']
        
    files = []
    for root, dirs, filenames in os.walk(directory):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_patterns]
        
        for filename in filenames:
            # Skip excluded files
            if any(filename.endswith(pattern) for pattern in exclude_patterns):
                continue
            files.append(Path(root) / filename)
            
    return sorted(files)


def generate_checksums(
    raw_data_dir: Path,
    code_dir: Path,
    output_path: Path
) -> Dict[str, str]:
    """
    Generate checksums for all files in data/raw and code directories.
    
    Args:
        raw_data_dir: Path to data/raw directory
        code_dir: Path to code directory
        output_path: Path where checksums.json will be written
        
    Returns:
        Dictionary mapping relative paths to SHA-256 hashes
        
    Raises:
        FileNotFoundError: If directories don't exist
    """
    if not raw_data_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_data_dir}")
    if not code_dir.exists():
        raise FileNotFoundError(f"Code directory not found: {code_dir}")
        
    checksums = {}
    
    # Process data/raw files
    print(f"Scanning {raw_data_dir}...")
    raw_files = collect_files(raw_data_dir)
    for file_path in raw_files:
        try:
            relative_path = file_path.relative_to(raw_data_dir.parent)
            file_hash = compute_file_hash(file_path)
            checksums[str(relative_path)] = file_hash
            print(f"  {relative_path}: {file_hash[:16]}...")
        except Exception as e:
            print(f"  Warning: Could not hash {file_path}: {e}", file=sys.stderr)
            
    # Process code files
    print(f"Scanning {code_dir}...")
    code_files = collect_files(code_dir)
    for file_path in code_files:
        try:
            relative_path = file_path.relative_to(code_dir.parent)
            file_hash = compute_file_hash(file_path)
            checksums[str(relative_path)] = file_hash
            print(f"  {relative_path}: {file_hash[:16]}...")
        except Exception as e:
            print(f"  Warning: Could not hash {file_path}: {e}", file=sys.stderr)
            
    # Write checksums to output file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(checksums, f, indent=2, sort_keys=True)
        
    print(f"\nGenerated checksums for {len(checksums)} files.")
    print(f"Output written to: {output_path}")
    
    return checksums


def main():
    """Main entry point for checksum generation."""
    try:
        config = load_config()
        raw_data_dir = get_path(config, "raw_data_dir")
        code_dir = get_path(config, "code_dir")
        checksums_path = get_path(config, "checksums_path")
        
        print("Generating checksums for project files...")
        checksums = generate_checksums(raw_data_dir, code_dir, checksums_path)
        
        print("Checksum generation complete.")
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
