"""
update_state.py - Compute checksums for data/ and code/ directories.

Implements Constitution Principle V: Artifact integrity verification via checksums.

This script computes SHA-256 checksums for all files in the 'data/' and 'code/'
directories and writes the results to 'state/checksums.json'.

Usage:
    python scripts/update_state.py

Output:
    state/checksums.json - JSON file containing checksums for all tracked files.
"""
import os
import sys
import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Project root is the parent of the 'scripts' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
STATE_DIR = PROJECT_ROOT / "state"
CHECKSUM_FILE = STATE_DIR / "checksums.json"

# Directories to exclude from checksumming (e.g., __pycache__, .git)
EXCLUDED_DIRS = {"__pycache__", ".git", ".pytest_cache", "node_modules", "venv", ".venv"}
# File extensions to exclude
EXCLUDED_EXTENSIONS = {".pyc", ".pyo", ".pyd", ".so", ".dll", ".o"}

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except (IOError, OSError) as e:
        raise RuntimeError(f"Failed to read file {file_path}: {e}")

def collect_files(directory: Path) -> List[Path]:
    """
    Collect all files in the given directory, excluding specified directories and extensions.
    
    Args:
        directory: Path to the directory to scan.
        
    Returns:
        List of file paths.
    """
    if not directory.exists():
        print(f"Warning: Directory {directory} does not exist. Skipping.")
        return []
    
    files = []
    for root, dirs, filenames in os.walk(directory):
        # Modify dirs in-place to skip excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        
        for filename in filenames:
            file_path = Path(root) / filename
            if file_path.suffix.lower() not in EXCLUDED_EXTENSIONS:
                files.append(file_path)
    
    return sorted(files)

def compute_checksums(directory: Path, relative_to: Path) -> Dict[str, str]:
    """
    Compute checksums for all files in a directory.
    
    Args:
        directory: Path to the directory to scan.
        relative_to: Base path for relative paths in the output.
        
    Returns:
        Dictionary mapping relative file paths to their SHA-256 checksums.
    """
    checksums = {}
    files = collect_files(directory)
    
    for file_path in files:
        try:
            checksum = compute_sha256(file_path)
            relative_path = file_path.relative_to(relative_to)
            checksums[str(relative_path)] = checksum
        except Exception as e:
            print(f"Error processing {file_path}: {e}", file=sys.stderr)
    
    return checksums

def main():
    """Main entry point for the script."""
    print(f"Computing checksums for project: {PROJECT_ROOT}")
    
    # Ensure state directory exists
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Compute checksums for code/ and data/
    code_checksums = compute_checksums(CODE_DIR, PROJECT_ROOT)
    data_checksums = compute_checksums(DATA_DIR, PROJECT_ROOT)
    
    # Combine results
    results = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "project_root": str(PROJECT_ROOT),
        "code_checksums": code_checksums,
        "data_checksums": data_checksums,
        "total_files": len(code_checksums) + len(data_checksums)
    }
    
    # Write to JSON file
    try:
        with open(CHECKSUM_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"Checksums written to: {CHECKSUM_FILE}")
        print(f"Total files processed: {results['total_files']}")
        print(f"Code files: {len(code_checksums)}, Data files: {len(data_checksums)}")
    except (IOError, OSError) as e:
        print(f"Failed to write checksums to {CHECKSUM_FILE}: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()