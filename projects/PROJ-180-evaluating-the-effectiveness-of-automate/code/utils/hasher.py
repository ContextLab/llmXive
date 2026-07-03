"""
Hashing utilities for artifact integrity verification.

Implements SHA-256 hashing for files and directories to ensure
data integrity as per Constitution Principle V.
"""
import hashlib
import os
import json
from pathlib import Path
from typing import Dict, List, Union, Optional


def hash_file(filepath: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Calculate the hash of a single file.
    
    Args:
        filepath: Path to the file to hash.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        Hexadecimal hash string.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    hasher = hashlib.new(algorithm)
    
    with open(filepath, "rb") as f:
        # Read in chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    
    return hasher.hexdigest()


def hash_directory(
    dirpath: Union[str, Path],
    algorithm: str = "sha256",
    recursive: bool = True,
    exclude_patterns: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Calculate hashes for all files in a directory.
    
    Args:
        dirpath: Path to the directory.
        algorithm: Hash algorithm to use (default: sha256).
        recursive: If True, include files in subdirectories.
        exclude_patterns: List of glob patterns to exclude (e.g., ["*.pyc", "__pycache__"]).
        
    Returns:
        Dictionary mapping relative file paths to their hashes.
        
    Raises:
        NotADirectoryError: If the path is not a directory.
    """
    dirpath = Path(dirpath)
    if not dirpath.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {dirpath}")
    
    if exclude_patterns is None:
        exclude_patterns = []
    
    hashes = {}
    
    if recursive:
        files = dirpath.rglob("*")
    else:
        files = dirpath.glob("*")
    
    for filepath in files:
        if filepath.is_file():
            # Check exclusion patterns
            rel_path = str(filepath.relative_to(dirpath))
            excluded = False
            for pattern in exclude_patterns:
                if filepath.match(pattern) or rel_path.startswith(pattern):
                    excluded = True
                    break
            
            if not excluded:
                try:
                    hashes[str(filepath.relative_to(dirpath))] = hash_file(filepath, algorithm)
                except (FileNotFoundError, ValueError) as e:
                    # Log warning but continue processing other files
                    print(f"Warning: Could not hash {filepath}: {e}")
    
    return hashes


def verify_file_hash(filepath: Union[str, Path], expected_hash: str, algorithm: str = "sha256") -> bool:
    """
    Verify a file's hash against an expected value.
    
    Args:
        filepath: Path to the file to verify.
        expected_hash: Expected hexadecimal hash string.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        True if the hash matches, False otherwise.
    """
    actual_hash = hash_file(filepath, algorithm)
    return actual_hash == expected_hash


def generate_manifest(
    dirpath: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    algorithm: str = "sha256",
    recursive: bool = True
) -> Dict:
    """
    Generate a manifest of file hashes for a directory.
    
    Args:
        dirpath: Path to the directory to manifest.
        output_path: Optional path to save the manifest JSON file.
        algorithm: Hash algorithm to use (default: sha256).
        recursive: If True, include files in subdirectories.
        
    Returns:
        Dictionary containing the manifest data.
    """
    dirpath = Path(dirpath)
    hashes = hash_directory(dirpath, algorithm, recursive)
    
    manifest = {
        "directory": str(dirpath.absolute()),
        "algorithm": algorithm,
        "recursive": recursive,
        "file_count": len(hashes),
        "files": hashes
    }
    
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
    
    return manifest


def verify_manifest(manifest_path: Union[str, Path]) -> Dict[str, bool]:
    """
    Verify all files against a manifest.
    
    Args:
        manifest_path: Path to the manifest JSON file.
        
    Returns:
        Dictionary mapping file paths to verification status (True/False).
    """
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    results = {}
    base_dir = Path(manifest["directory"])
    
    for rel_path, expected_hash in manifest["files"].items():
        full_path = base_dir / rel_path
        if full_path.exists():
            try:
                actual_hash = hash_file(full_path, manifest["algorithm"])
                results[rel_path] = actual_hash == expected_hash
            except Exception as e:
                results[rel_path] = False
                print(f"Error verifying {rel_path}: {e}")
        else:
            results[rel_path] = False
            print(f"File not found: {rel_path}")
    
    return results


def main():
    """
    CLI entry point for hashing operations.
    
    Usage:
        python -m code.utils.hasher hash <file_path>
        python -m code.utils.hasher hash_dir <dir_path> [--output <output.json>]
        python -m code.utils.hasher verify <file_path> <expected_hash>
        python -m code.utils.hasher verify_manifest <manifest_path>
    """
    import sys
    
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python -m code.utils.hasher hash <file_path>")
        print("  python -m code.utils.hasher hash_dir <dir_path> [--output <output.json>]")
        print("  python -m code.utils.hasher verify <file_path> <expected_hash>")
        print("  python -m code.utils.hasher verify_manifest <manifest_path>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    try:
        if command == "hash":
            file_path = sys.argv[2]
            result = hash_file(file_path)
            print(result)
        
        elif command == "hash_dir":
            dir_path = sys.argv[2]
            output_path = None
            for i, arg in enumerate(sys.argv[3:], 3):
                if arg == "--output" and i + 1 < len(sys.argv):
                    output_path = sys.argv[i + 1]
            
            result = generate_manifest(dir_path, output_path)
            if not output_path:
                print(json.dumps(result, indent=2))
            else:
                print(f"Manifest saved to: {output_path}")
        
        elif command == "verify":
            file_path = sys.argv[2]
            expected_hash = sys.argv[3]
            result = verify_file_hash(file_path, expected_hash)
            print("PASS" if result else "FAIL")
        
        elif command == "verify_manifest":
            manifest_path = sys.argv[2]
            results = verify_manifest(manifest_path)
            passed = sum(1 for v in results.values() if v)
            total = len(results)
            print(f"Verification complete: {passed}/{total} files passed")
            if passed < total:
                for path, status in results.items():
                    if not status:
                        print(f"  FAILED: {path}")
                sys.exit(1)
        
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
