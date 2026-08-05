"""
Utility functions for hashing files and directories.
Provides SHA-256 hashing and manifest generation/validation.
"""
import hashlib
import os
import json
from pathlib import Path
from typing import Dict, List, Union, Optional
import logging

logger = logging.getLogger(__name__)


def hash_file(file_path: Union[str, Path]) -> str:
    """
    Calculate the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        str: Hexadecimal SHA-256 hash string.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If there is an error reading the file.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error hashing file {file_path}: {e}")
        raise IOError(f"Failed to hash file {file_path}: {e}")


def hash_directory(dir_path: Union[str, Path]) -> Dict[str, str]:
    """
    Calculate SHA-256 hashes for all files in a directory (non-recursive).

    Args:
        dir_path: Path to the directory.

    Returns:
        Dict[str, str]: Dictionary mapping relative file paths to their hashes.
    """
    dir_path = Path(dir_path)
    if not dir_path.exists() or not dir_path.is_dir():
        raise NotADirectoryError(f"Directory not found: {dir_path}")
    
    hashes = {}
    for file_path in dir_path.iterdir():
        if file_path.is_file() and not file_path.name.startswith('.'):
            try:
                relative_path = file_path.relative_to(dir_path)
                hashes[str(relative_path)] = hash_file(file_path)
            except Exception as e:
                logger.warning(f"Skipping file {file_path}: {e}")
    
    return hashes


def verify_file_hash(file_path: Union[str, Path], expected_hash: str) -> bool:
    """
    Verify that a file's hash matches the expected hash.

    Args:
        file_path: Path to the file to verify.
        expected_hash: Expected SHA-256 hash.

    Returns:
        bool: True if hash matches, False otherwise.
    """
    try:
        actual_hash = hash_file(file_path)
        return actual_hash == expected_hash
    except Exception as e:
        logger.error(f"Error verifying hash for {file_path}: {e}")
        return False


def generate_manifest(dir_path: Union[str, Path], output_path: Union[str, Path]) -> bool:
    """
    Generate a manifest file containing hashes of all files in a directory.

    Args:
        dir_path: Path to the directory to hash.
        output_path: Path where the manifest file will be saved.

    Returns:
        bool: True if manifest was generated successfully, False otherwise.
    """
    try:
        dir_path = Path(dir_path)
        output_path = Path(output_path)
        
        if not dir_path.exists() or not dir_path.is_dir():
            logger.error(f"Directory not found: {dir_path}")
            return False
        
        hashes = hash_directory(dir_path)
        
        manifest = {
            "directory": str(dir_path),
            "files": hashes,
            "file_count": len(hashes)
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"Generated manifest with {len(hashes)} files at {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to generate manifest: {e}")
        return False


def verify_manifest(manifest_path: Union[str, Path]) -> Tuple[bool, List[str]]:
    """
    Verify files against a manifest.

    Args:
        manifest_path: Path to the manifest file.

    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_failed_files)
    """
    try:
        manifest_path = Path(manifest_path)
        
        if not manifest_path.exists():
            logger.error(f"Manifest not found: {manifest_path}")
            return False, [str(manifest_path)]
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        dir_path = Path(manifest["directory"])
        expected_hashes = manifest["files"]
        
        failed_files = []
        
        for relative_path, expected_hash in expected_hashes.items():
            file_path = dir_path / relative_path
            
            if not file_path.exists():
                logger.warning(f"File missing: {file_path}")
                failed_files.append(relative_path)
                continue
            
            if not verify_file_hash(file_path, expected_hash):
                logger.warning(f"Hash mismatch for: {file_path}")
                failed_files.append(relative_path)
        
        is_valid = len(failed_files) == 0
        return is_valid, failed_files
    except Exception as e:
        logger.error(f"Error verifying manifest: {e}")
        return False, [str(e)]


def main():
    """
    Main entry point for running hash operations from the command line.
    """
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) < 2:
        print("Usage: python hasher.py <command> <path> [output_path]")
        print("Commands: hash_file, hash_dir, generate_manifest, verify_manifest")
        return 1
    
    command = sys.argv[1]
    
    if command == "hash_file":
        if len(sys.argv) < 3:
            print("Error: file path required")
            return 1
        file_path = sys.argv[2]
        try:
            hash_value = hash_file(file_path)
            print(f"SHA-256: {hash_value}")
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    elif command == "hash_dir":
        if len(sys.argv) < 3:
            print("Error: directory path required")
            return 1
        dir_path = sys.argv[2]
        try:
            hashes = hash_directory(dir_path)
            print(json.dumps(hashes, indent=2))
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    elif command == "generate_manifest":
        if len(sys.argv) < 4:
            print("Error: directory path and output path required")
            return 1
        dir_path = sys.argv[2]
        output_path = sys.argv[3]
        if not generate_manifest(dir_path, output_path):
            return 1
    
    elif command == "verify_manifest":
        if len(sys.argv) < 3:
            print("Error: manifest path required")
            return 1
        manifest_path = sys.argv[2]
        is_valid, failed = verify_manifest(manifest_path)
        if is_valid:
            print("Verification passed")
            return 0
        else:
            print(f"Verification failed for {len(failed)} files:")
            for f in failed:
                print(f"  - {f}")
            return 1
    
    else:
        print(f"Unknown command: {command}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
