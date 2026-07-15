import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Optional, List, Any

def calculate_file_checksum(file_path: str, algorithm: str = 'sha256') -> str:
    """
    Calculate the checksum of a file.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use.
        
    Returns:
        The checksum as a hexadecimal string.
    """
    hasher = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hasher.update(chunk)
    return hasher.hexdigest()

def generate_checksum_manifest(file_paths: List[str], output_path: str, algorithm: str = 'sha256') -> Dict[str, str]:
    """
    Generate a checksum manifest for multiple files.
    
    Args:
        file_paths: List of file paths.
        output_path: Path to save the manifest.
        algorithm: Hash algorithm to use.
        
    Returns:
        A dictionary mapping file paths to checksums.
    """
    manifest = {}
    for file_path in file_paths:
        if os.path.exists(file_path):
            checksum = calculate_file_checksum(file_path, algorithm)
            manifest[file_path] = checksum
        else:
            print(f"Warning: File not found: {file_path}")
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    return manifest

def verify_checksum_manifest(manifest_path: str, base_dir: Optional[str] = None) -> Dict[str, bool]:
    """
    Verify files against a checksum manifest.
    
    Args:
        manifest_path: Path to the manifest file.
        base_dir: Base directory for file paths.
        
    Returns:
        A dictionary mapping file paths to verification status.
    """
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    results = {}
    for file_path, expected_checksum in manifest.items():
        if base_dir:
            full_path = os.path.join(base_dir, file_path)
        else:
            full_path = file_path
        
        if os.path.exists(full_path):
            actual_checksum = calculate_file_checksum(full_path)
            results[file_path] = actual_checksum == expected_checksum
        else:
            results[file_path] = False
            print(f"Warning: File not found: {full_path}")
    
    return results

def main():
    """Main function for testing checksum utilities."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python checksums.py <command> [args]")
        print("Commands:")
        print("  generate <file1> [file2 ...] <output_manifest>")
        print("  verify <manifest_path> [base_dir]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'generate':
        if len(sys.argv) < 4:
            print("Usage: python checksums.py generate <file1> [file2 ...] <output_manifest>")
            sys.exit(1)
        
        file_paths = sys.argv[2:-1]
        output_path = sys.argv[-1]
        manifest = generate_checksum_manifest(file_paths, output_path)
        print(f"Generated manifest with {len(manifest)} files")
        
    elif command == 'verify':
        if len(sys.argv) < 3:
            print("Usage: python checksums.py verify <manifest_path> [base_dir]")
            sys.exit(1)
        
        manifest_path = sys.argv[2]
        base_dir = sys.argv[3] if len(sys.argv) > 3 else None
        results = verify_checksum_manifest(manifest_path, base_dir)
        
        all_valid = all(results.values())
        for file_path, valid in results.items():
            status = "OK" if valid else "FAILED"
            print(f"{file_path}: {status}")
        
        if not all_valid:
            sys.exit(1)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
