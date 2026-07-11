import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from data.download import calculate_sha256, load_existing_checksums, save_checksums

def generate_checksums_for_directory(directory: Path, recursive: bool = True) -> Dict[str, str]:
    """
    Generate SHA256 checksums for all files in a directory.
    
    Args:
        directory: Path to the directory to scan
        recursive: If True, scan subdirectories as well
    
    Returns:
        Dictionary mapping relative file paths to their SHA256 hashes
    """
    checksums = {}
    
    if recursive:
        files = list(directory.rglob("*"))
    else:
        files = list(directory.glob("*"))
    
    for file_path in files:
        if file_path.is_file():
            relative_path = str(file_path.relative_to(directory))
            checksums[relative_path] = calculate_sha256(file_path)
    
    return checksums

def verify_checksums_against_file(checksum_path: Path, base_dir: Path) -> Tuple[bool, List[str]]:
    """
    Verify files in base_dir against checksums in checksum_path.
    
    Args:
        checksum_path: Path to the JSON file containing checksums
        base_dir: Directory containing the files to verify
    
    Returns:
        Tuple of (success, list of error messages)
    """
    if not checksum_path.exists():
        return False, ["Checksum file not found"]
    
    stored_checksums = load_existing_checksums(checksum_path)
    
    if not stored_checksums:
        return False, ["No checksums to verify"]
    
    errors = []
    
    for relative_path, expected_hash in stored_checksums.items():
        file_path = base_dir / relative_path
        
        if not file_path.exists():
            errors.append(f"Missing file: {relative_path}")
            continue
        
        actual_hash = calculate_sha256(file_path)
        
        if actual_hash != expected_hash:
            errors.append(f"Checksum mismatch for {relative_path}: expected {expected_hash}, got {actual_hash}")
    
    return len(errors) == 0, errors

def create_checksum_file(directory: Path, output_path: Path, recursive: bool = True) -> None:
    """
    Generate checksums for a directory and save to a JSON file.
    
    Args:
        directory: Directory to scan for files
        output_path: Path where the checksum JSON file will be saved
        recursive: Whether to scan subdirectories
    """
    checksums = generate_checksums_for_directory(directory, recursive)
    save_checksums(output_path, checksums)

def main():
    """Main entry point for checksum generation and verification."""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python checksum_manager.py <command> <path> [options]")
        print("Commands:")
        print("  generate <directory> <output_file>  - Generate checksums for directory")
        print("  verify <checksum_file> <base_dir>   - Verify files against checksums")
        sys.exit(1)
    
    command = sys.argv[1]
    path = Path(sys.argv[2])
    
    if command == "generate":
        if len(sys.argv) < 4:
            print("Error: output file path required")
            sys.exit(1)
        output_path = Path(sys.argv[3])
        create_checksum_file(path, output_path)
        print(f"Checksums saved to {output_path}")
    
    elif command == "verify":
        if len(sys.argv) < 4:
            print("Error: base directory path required")
            sys.exit(1)
        base_dir = Path(sys.argv[3])
        success, errors = verify_checksums_against_file(path, base_dir)
        if success:
            print("All files verified successfully")
        else:
            print("Verification failed:")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
