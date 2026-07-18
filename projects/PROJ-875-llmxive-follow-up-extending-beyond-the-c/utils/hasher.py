import os
import hashlib
import json
from typing import List, Dict, Any

def calculate_file_hash(filepath: str, algorithm: str = 'sha256') -> str:
    """
    Calculate the hash of a file.
    
    Args:
        filepath: Path to the file
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hex digest of the file hash
    """
    hash_func = hashlib.new(algorithm)
    
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()

def generate_version_hash(filepath: str, metadata: Dict[str, Any] = None) -> str:
    """
    Generate a version hash for an artifact, incorporating file content and metadata.
    
    Args:
        filepath: Path to the artifact file
        metadata: Optional metadata to include in the hash
        
    Returns:
        Version hash string
    """
    # Start with file content hash
    content_hash = calculate_file_hash(filepath)
    
    # Incorporate metadata if provided
    if metadata:
        metadata_str = json.dumps(metadata, sort_keys=True)
        combined = f"{content_hash}:{metadata_str}"
    else:
        combined = content_hash
    
    # Hash the combined string
    version_hash = hashlib.sha256(combined.encode('utf-8')).hexdigest()[:16]
    
    return version_hash

def hash_directory(directory: str, pattern: str = "*") -> Dict[str, str]:
    """
    Generate hashes for all files in a directory.
    
    Args:
        directory: Path to the directory
        pattern: Glob pattern to match files
        
    Returns:
        Dictionary mapping filenames to their hashes
    """
    import glob
    
    hashes = {}
    for filepath in glob.glob(os.path.join(directory, pattern)):
        if os.path.isfile(filepath):
            filename = os.path.basename(filepath)
            hashes[filename] = calculate_file_hash(filepath)
    
    return hashes

def main():
    """Main entry point for the hasher utility."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python hasher.py <filepath> [output_file]")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    
    if os.path.isdir(filepath):
        # Hash directory
        hashes = hash_directory(filepath)
        print(json.dumps(hashes, indent=2))
    else:
        # Hash single file
        file_hash = calculate_file_hash(filepath)
        version_hash = generate_version_hash(filepath)
        
        result = {
            "file": filepath,
            "sha256": file_hash,
            "version_hash": version_hash
        }
        
        if len(sys.argv) >= 3:
            output_file = sys.argv[2]
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"Hash written to {output_file}")
        else:
            print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
