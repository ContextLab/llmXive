"""
Utility module to compute SHA-256 checksums for data and stats artifacts.
Implements Constitution Principle V: Data Integrity and Reproducibility.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

# Default directories to scan if no specific paths are provided
DEFAULT_SCAN_DIRS = [
    "data",
    "docs/reports",
    "figures"
]

# Patterns for artifacts to include (extensions)
ARTIFACT_EXTENSIONS = {
    ".csv",
    ".json",
    ".parquet",
    ".yaml",
    ".yml",
    ".png",
    ".pdf",
    ".txt",
    ".log"
}

# Excluded files (e.g., intermediate caches)
EXCLUDED_FILES = {
    ".gitkeep",
    ".DS_Store",
    "thumbs.db"
}

def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")

def find_artifacts(
    base_dir: Path,
    extensions: Optional[set] = None,
    excluded: Optional[set] = None
) -> List[Path]:
    """
    Recursively find all artifact files in a directory tree.
    
    Args:
        base_dir: Root directory to search.
        extensions: Set of file extensions to include. Defaults to ARTIFACT_EXTENSIONS.
        excluded: Set of filenames to exclude. Defaults to EXCLUDED_FILES.
        
    Returns:
        List of Path objects for matching files.
    """
    if extensions is None:
        extensions = ARTIFACT_EXTENSIONS
    if excluded is None:
        excluded = EXCLUDED_FILES

    artifacts = []
    if not base_dir.exists():
        return artifacts

    for root, _, files in os.walk(base_dir):
        for filename in files:
            if filename in excluded:
                continue
            
            file_ext = Path(filename).suffix.lower()
            if file_ext in extensions:
                artifacts.append(Path(root) / filename)
    
    return sorted(artifacts)

def hash_directory(
    dir_path: Path,
    output_path: Optional[Path] = None,
    extensions: Optional[set] = None,
    excluded: Optional[set] = None
) -> Dict[str, str]:
    """
    Compute hashes for all artifacts in a directory and optionally save results.
    
    Args:
        dir_path: Directory to scan.
        output_path: Path to save the JSON checksum file. If None, results are not saved.
        extensions: File extensions to include.
        excluded: Filenames to exclude.
        
    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes.
    """
    artifacts = find_artifacts(dir_path, extensions, excluded)
    checksums = {}
    
    for artifact in artifacts:
        try:
            rel_path = artifact.relative_to(dir_path)
            checksums[str(rel_path)] = compute_sha256(artifact)
        except Exception as e:
            # Log warning but continue processing other files
            print(f"Warning: Could not hash {artifact}: {e}")
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(checksums, f, indent=2, sort_keys=True)
        print(f"Checksums saved to: {output_path}")
    
    return checksums

def hash_multiple_dirs(
    base_paths: List[str],
    output_dir: Optional[Path] = None,
    extensions: Optional[set] = None,
    excluded: Optional[set] = None
) -> Dict[str, Dict[str, str]]:
    """
    Compute hashes for multiple directories.
    
    Args:
        base_paths: List of directory paths to scan.
        output_dir: Directory to save individual checksum files.
        extensions: File extensions to include.
        excluded: Filenames to exclude.
        
    Returns:
        Dictionary mapping directory names to their checksum dictionaries.
    """
    results = {}
    
    for path_str in base_paths:
        dir_path = Path(path_str)
        if not dir_path.exists():
            print(f"Warning: Directory does not exist, skipping: {dir_path}")
            continue
        
        dir_name = dir_path.name
        output_file = None
        
        if output_dir:
            output_file = output_dir / f"checksums_{dir_name}.json"
        
        print(f"Hashing directory: {dir_path}")
        checksums = hash_directory(
            dir_path, 
            output_file, 
            extensions, 
            excluded
        )
        results[dir_name] = checksums
    
    return results

def verify_checksums(checksum_file: Path) -> bool:
    """
    Verify files against a stored checksum file.
    
    Args:
        checksum_file: Path to the JSON file containing checksums.
        
    Returns:
        True if all files match, False otherwise.
    """
    if not checksum_file.exists():
        raise FileNotFoundError(f"Checksum file not found: {checksum_file}")
    
    with open(checksum_file, "r", encoding="utf-8") as f:
        stored_checksums = json.load(f)
    
    base_dir = checksum_file.parent
    all_valid = True
    
    for rel_path, expected_hash in stored_checksums.items():
        file_path = base_dir / rel_path
        
        if not file_path.exists():
            print(f"MISSING: {rel_path}")
            all_valid = False
            continue
        
        try:
            actual_hash = compute_sha256(file_path)
            if actual_hash == expected_hash:
                print(f"OK: {rel_path}")
            else:
                print(f"MISMATCH: {rel_path}")
                print(f"  Expected: {expected_hash}")
                print(f"  Actual:   {actual_hash}")
                all_valid = False
        except Exception as e:
            print(f"ERROR: {rel_path} - {e}")
            all_valid = False
    
    return all_valid

def main():
    """
    CLI entry point for hashing artifacts.
    Usage:
      python code/utils/hash_artifacts.py [directory_to_scan] [output_file]
      python code/utils/hash_artifacts.py --verify [checksum_file]
    """
    import sys

    if len(sys.argv) < 2:
        # Default behavior: hash default directories
        print("Running default hash scan...")
        base_paths = [Path.cwd() / p for p in DEFAULT_SCAN_DIRS]
        hash_multiple_dirs(base_paths, output_dir=Path("data"))
        return

    command = sys.argv[1]

    if command == "--verify":
        if len(sys.argv) < 3:
            print("Error: --verify requires a checksum file path")
            sys.exit(1)
        checksum_file = Path(sys.argv[2])
        try:
            if verify_checksums(checksum_file):
                print("\nAll checksums verified successfully.")
                sys.exit(0)
            else:
                print("\nChecksum verification failed.")
                sys.exit(1)
        except Exception as e:
            print(f"Verification error: {e}")
            sys.exit(1)
    else:
        # Assume first arg is a directory or list of directories
        paths_to_scan = sys.argv[1:]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        
        if output_file:
            output_path = Path(output_file)
            # If single directory, hash it directly
            if len(paths_to_scan) == 1:
                dir_path = Path(paths_to_scan[0])
                hash_directory(dir_path, output_path)
            else:
                # Multiple directories, save to output_dir
                hash_multiple_dirs(paths_to_scan, output_dir=Path(output_file))
        else:
            hash_multiple_dirs(paths_to_scan)

if __name__ == "__main__":
    main()
