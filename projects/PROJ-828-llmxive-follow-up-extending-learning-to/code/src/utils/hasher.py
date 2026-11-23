"""
Hash utility module for computing and verifying SHA-256 hashes of project artifacts.

This module provides functions to:
- Compute SHA-256 hashes of individual files
- Compute hashes of directories (optionally filtered by extension)
- Save and load hash manifests (JSON)
- Verify artifacts against stored hashes
- Generate hash strings for arbitrary data
"""

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union, Any


def compute_file_hash(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Compute the SHA-256 hash of a file's contents.
    
    Args:
        file_path: Path to the file to hash
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hexadecimal string of the hash
        
    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If the file cannot be read
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    hasher = hashlib.new(algorithm)
    
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
            
    return hasher.hexdigest()


def compute_directory_hash(
    dir_path: Union[str, Path],
    algorithm: str = "sha256",
    include_extensions: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None
) -> str:
    """
    Compute a combined SHA-256 hash of all files in a directory.
    
    Files are processed in sorted order to ensure deterministic results.
    
    Args:
        dir_path: Path to the directory
        algorithm: Hash algorithm to use
        include_extensions: If provided, only hash files with these extensions
        exclude_patterns: If provided, exclude files matching these patterns
        
    Returns:
        Hexadecimal string of the combined hash
        
    Raises:
        NotADirectoryError: If the path is not a directory
    """
    dir_path = Path(dir_path)
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {dir_path}")
        
    hasher = hashlib.new(algorithm)
    
    # Collect files to hash
    files_to_hash = []
    for root, _, files in os.walk(dir_path):
        for file in sorted(files):
            file_path = Path(root) / file
            relative_path = file_path.relative_to(dir_path)
            
            # Check include extensions
            if include_extensions:
                if file_path.suffix.lower() not in [ext.lower() for ext in include_extensions]:
                    continue
                    
            # Check exclude patterns
            if exclude_patterns:
                skip = False
                pattern_str = str(relative_path).lower()
                for pattern in exclude_patterns:
                    if pattern.lower() in pattern_str:
                        skip = True
                        break
                if skip:
                    continue
                    
            files_to_hash.append(file_path)
    
    # Hash file paths and contents in sorted order
    for file_path in sorted(files_to_hash):
        # Include relative path in hash to detect renames
        hasher.update(str(file_path.relative_to(dir_path)).encode("utf-8"))
        hasher.update(b"\x00")  # Separator
        
        # Hash file contents
        file_hash = compute_file_hash(file_path, algorithm)
        hasher.update(file_hash.encode("utf-8"))
        
    return hasher.hexdigest()


def generate_artifact_hash(data: Union[str, bytes]) -> str:
    """
    Generate a SHA-256 hash from string or bytes data.
    
    Args:
        data: String or bytes to hash
        
    Returns:
        Hexadecimal string of the hash
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
        
    return hashlib.sha256(data).hexdigest()


def save_hash_manifest(
    artifacts: Dict[str, str],
    output_path: Union[str, Path],
    metadata: Optional[Dict[str, Any]] = None
) -> Path:
    """
    Save a manifest of artifact hashes to a JSON file.
    
    Args:
        artifacts: Dictionary mapping file paths to their hashes
        output_path: Path to save the manifest
        metadata: Optional metadata to include in the manifest
        
    Returns:
        Path to the saved manifest
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    manifest = {
        "version": "1.0",
        "algorithm": "sha256",
        "artifacts": artifacts,
    }
    
    if metadata:
        manifest["metadata"] = metadata
        
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    return output_path


def load_hash_manifest(manifest_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a hash manifest from a JSON file.
    
    Args:
        manifest_path: Path to the manifest file
        
    Returns:
        Dictionary containing the manifest data
        
    Raises:
        FileNotFoundError: If the manifest file does not exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
        
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def verify_artifacts(
    artifacts: Dict[str, str],
    base_path: Optional[Union[str, Path]] = None
) -> Dict[str, bool]:
    """
    Verify that artifacts match their stored hashes.
    
    Args:
        artifacts: Dictionary mapping file paths to expected hashes
        base_path: Base directory for relative paths (default: current directory)
        
    Returns:
        Dictionary mapping file paths to verification results (True/False)
    """
    results = {}
    base_path = Path(base_path) if base_path else Path.cwd()
    
    for rel_path, expected_hash in artifacts.items():
        file_path = base_path / rel_path if not Path(rel_path).is_absolute() else Path(rel_path)
        
        if not file_path.exists():
            results[rel_path] = False
            continue
            
        try:
            actual_hash = compute_file_hash(file_path)
            results[rel_path] = (actual_hash == expected_hash)
        except Exception:
            results[rel_path] = False
            
    return results


def main():
    """
    Command-line interface for hash operations.
    
    Usage:
        python -m src.utils.hasher <command> [options]
        
    Commands:
        file <path>          - Compute hash of a file
        dir <path>           - Compute hash of a directory
        verify <manifest>    - Verify artifacts against a manifest
        create <dir> <out>   - Create a manifest for a directory
    """
    if len(sys.argv) < 2:
        print("Usage: python -m src.utils.hasher <command> [options]")
        print("Commands: file, dir, verify, create")
        sys.exit(1)
        
    command = sys.argv[1]
    
    if command == "file" and len(sys.argv) >= 3:
        file_path = sys.argv[2]
        try:
            hash_val = compute_file_hash(file_path)
            print(f"{hash_val}  {file_path}")
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
            
    elif command == "dir" and len(sys.argv) >= 3:
        dir_path = sys.argv[2]
        try:
            hash_val = compute_directory_hash(dir_path)
            print(f"{hash_val}  {dir_path}/")
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
            
    elif command == "verify" and len(sys.argv) >= 3:
        manifest_path = sys.argv[2]
        try:
            manifest = load_hash_manifest(manifest_path)
            artifacts = manifest.get("artifacts", {})
            base_path = manifest_path.parent
            
            results = verify_artifacts(artifacts, base_path)
            
            all_valid = True
            for path, valid in results.items():
                status = "OK" if valid else "FAILED"
                print(f"{status}: {path}")
                if not valid:
                    all_valid = False
                    
            if not all_valid:
                sys.exit(1)
                
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
            
    elif command == "create" and len(sys.argv) >= 4:
        dir_path = sys.argv[2]
        output_path = sys.argv[3]
        try:
            artifacts = {}
            dir_path = Path(dir_path)
            
            for file_path in dir_path.rglob("*"):
                if file_path.is_file():
                    rel_path = str(file_path.relative_to(dir_path))
                    artifacts[rel_path] = compute_file_hash(file_path)
                    
            save_hash_manifest(artifacts, output_path, {
                "source_directory": str(dir_path),
            })
            print(f"Manifest created: {output_path}")
            
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
            
    else:
        print(f"Unknown command or invalid arguments: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
