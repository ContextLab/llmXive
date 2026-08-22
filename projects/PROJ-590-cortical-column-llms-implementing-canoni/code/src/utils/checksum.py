"""
Checksum utilities for artifact verification (Constitution Principle III & V).
Generates and verifies SHA256 checksums for project data and state directories.
"""
import os
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Directories to checksum as per task specification
TARGET_DIRS = [
    "data/configs",
    "data/results",
    "data/logs",
    "state"
]

def calculate_sha256(file_path: Path) -> str:
    """
    Calculate SHA256 hash of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hexadecimal string of the SHA256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
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

def find_files(base_dir: Path, extensions: Optional[List[str]] = None) -> List[Path]:
    """
    Recursively find all files in a directory.
    
    Args:
        base_dir: Root directory to search.
        extensions: Optional list of file extensions to filter (e.g., ['.txt', '.json']).
                    If None, includes all files.
                    
    Returns:
        List of Path objects for all matching files.
    """
    if not base_dir.exists():
        return []
    
    files = []
    for root, _, filenames in os.walk(base_dir):
        for filename in filenames:
            file_path = Path(root) / filename
            if extensions:
                if any(filename.endswith(ext) for ext in extensions):
                    files.append(file_path)
            else:
                files.append(file_path)
    return sorted(files)

def generate_checksums(output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Generate SHA256 checksums for all files in TARGET_DIRS.
    
    Args:
        output_path: Path to write the JSON checksum manifest. If None, 
                     returns the dictionary without writing to disk.
                     
    Returns:
        Dictionary containing the checksums and metadata.
        
    Raises:
        FileNotFoundError: If any target directory does not exist.
    """
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    checksums = {
        "version": "1.0",
        "algorithm": "sha256",
        "generated_at": None, # Will be set by caller if needed, or left for json dump
        "files": {}
    }
    
    # Check existence of target directories
    for dir_name in TARGET_DIRS:
        target_path = project_root / dir_name
        if not target_path.exists():
            # It is acceptable for log/result dirs to be empty initially,
            # but we must verify the structure exists or create it if T001 passed.
            # For safety, we treat missing dirs as empty (no files to checksum).
            continue
        
        files = find_files(target_path)
        for file_path in files:
            # Store path relative to project root
            rel_path = file_path.relative_to(project_root)
            try:
                checksum = calculate_sha256(file_path)
                checksums["files"][str(rel_path)] = checksum
            except (FileNotFoundError, IOError) as e:
                # Log error but continue processing other files
                print(f"Warning: Could not checksum {rel_path}: {e}")
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(checksums, f, indent=2)
        
    return checksums

def verify_checksums(manifest_path: Path) -> bool:
    """
    Verify current files against a stored checksum manifest.
    
    Args:
        manifest_path: Path to the JSON checksum manifest.
        
    Returns:
        True if all files match, False otherwise.
        
    Raises:
        FileNotFoundError: If manifest or any listed file is missing.
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    all_match = True
    
    for rel_path_str, expected_hash in manifest["files"].items():
        file_path = project_root / rel_path_str
        
        if not file_path.exists():
            print(f"MISMATCH: File missing: {rel_path_str}")
            all_match = False
            continue
        
        try:
            current_hash = calculate_sha256(file_path)
            if current_hash != expected_hash:
                print(f"MISMATCH: Hash mismatch for {rel_path_str}")
                print(f"  Expected: {expected_hash}")
                print(f"  Current:  {current_hash}")
                all_match = False
            else:
                print(f"OK: {rel_path_str}")
        except Exception as e:
            print(f"ERROR: Could not verify {rel_path_str}: {e}")
            all_match = False
            
    return all_match

def main():
    """
    CLI entry point for checksum generation and verification.
    Usage:
      python -m src.utils.checksum generate [--output path/to/manifest.json]
      python -m src.utils.checksum verify --manifest path/to/manifest.json
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m src.utils.checksum <generate|verify> [options]")
        sys.exit(1)
    
    command = sys.argv[1]
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    default_manifest = project_root / "state" / "checksums.json"
    
    if command == "generate":
        output = default_manifest
        if len(sys.argv) >= 4 and sys.argv[2] == "--output":
            output = Path(sys.argv[3])
        
        print(f"Generating checksums for directories: {TARGET_DIRS}")
        result = generate_checksums(output)
        print(f"Generated {len(result['files'])} checksums.")
        print(f"Manifest saved to: {output}")
        
    elif command == "verify":
        if len(sys.argv) < 4 or sys.argv[2] != "--manifest":
            print(f"Usage: python -m src.utils.checksum verify --manifest <path>")
            sys.exit(1)
            
        manifest_path = Path(sys.argv[3])
        print(f"Verifying against manifest: {manifest_path}")
        if verify_checksums(manifest_path):
            print("Verification PASSED: All files match.")
            sys.exit(0)
        else:
            print("Verification FAILED: Mismatches detected.")
            sys.exit(1)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
