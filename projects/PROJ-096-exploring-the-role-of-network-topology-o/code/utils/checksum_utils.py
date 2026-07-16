"""
Utility functions for generating and managing checksums of project artifacts.
"""
import os
import hashlib
from pathlib import Path
from typing import List, Tuple

def compute_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Compute the checksum of a file using the specified algorithm.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal digest of the file hash.
    """
    hasher = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    return hasher.hexdigest()

def generate_checksums_for_directory(
    directory: Path,
    extensions: List[str] = None,
    recursive: bool = True
) -> List[Tuple[str, str, str]]:
    """
    Generate checksums for all files in a directory.

    Args:
        directory: Root directory to scan.
        extensions: List of file extensions to include (e.g., ['.gpickle', '.json']).
                   If None, all files are included.
        recursive: Whether to scan subdirectories.

    Returns:
        List of tuples: (algorithm, relative_path, checksum).
    """
    checksums = []
    algorithm = 'sha256'

    if recursive:
        files = directory.rglob('*')
    else:
        files = directory.glob('*')

    for file_path in files:
        if file_path.is_file():
            # Filter by extension if specified
            if extensions:
                if file_path.suffix not in extensions:
                    continue
            
            # Compute checksum
            checksum = compute_file_checksum(file_path, algorithm)
            
            # Store relative path from project root
            relative_path = file_path.relative_to(directory.parent)
            
            checksums.append((algorithm, str(relative_path), checksum))
    
    return checksums

def write_checksums_file(
    checksums: List[Tuple[str, str, str]],
    output_path: Path,
    header_comments: List[str] = None
) -> None:
    """
    Write checksums to a file in the standard format.

    Args:
        checksums: List of (algorithm, path, checksum) tuples.
        output_path: Path to the output file.
        header_comments: List of comment lines to include at the top.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Write header comments
        if header_comments:
            for comment in header_comments:
                f.write(f"# {comment}\n")
        
        # Write format description
        f.write("# Format: <algorithm> <relative_path>\n")
        f.write(f"# Generated at: {output_path.parent.name}\n")
        f.write("#\n")
        
        # Write checksums
        for algorithm, path, checksum in checksums:
            f.write(f"{algorithm} {path} {checksum}\n")

def verify_checksums_file(checksums_path: Path) -> bool:
    """
    Verify all checksums listed in a checksums file.

    Args:
        checksums_path: Path to the checksums file.

    Returns:
        True if all checksums match, False otherwise.
    """
    if not checksums_path.exists():
        return False

    all_valid = True
    project_root = checksums_path.parent.parent

    with open(checksums_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            parts = line.split()
            if len(parts) < 3:
                continue
            
            algorithm = parts[0]
            relative_path = parts[1]
            expected_checksum = parts[2]
            
            full_path = project_root / relative_path
            
            if not full_path.exists():
                print(f"MISSING: {relative_path}")
                all_valid = False
                continue
            
            actual_checksum = compute_file_checksum(full_path, algorithm)
            
            if actual_checksum != expected_checksum:
                print(f"MISMATCH: {relative_path}")
                print(f"  Expected: {expected_checksum}")
                print(f"  Actual:   {actual_checksum}")
                all_valid = False
            else:
                print(f"OK: {relative_path}")
    
    return all_valid
