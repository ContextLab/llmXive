"""
Data hygiene utilities for the llmXive pipeline.

Provides functions for:
- MD5 checksum generation for files and directories
- Artifact metadata extraction
- Loading and saving artifact hash registries (YAML)
- Integrity verification of artifacts
- Cleanup of stale hash entries
"""
import hashlib
import os
from pathlib import Path
from typing import Optional, Union, Dict, Any, List, Tuple
import yaml
from datetime import datetime
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)

# Default paths
DEFAULT_HASH_FILE = Path("state/artifact_hashes.yaml")
DEFAULT_EXCLUDE_PATTERNS = {'.git', '__pycache__', '.pyc', '.o', '.so'}


def calculate_md5(file_path: Union[str, Path]) -> str:
    """
    Calculate the MD5 checksum of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hexadecimal MD5 hash string.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path points to a directory.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if path.is_dir():
        raise IsADirectoryError(f"Path is a directory, expected a file: {path}")
    
    hash_md5 = hashlib.md5()
    try:
        with open(path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
    except PermissionError as e:
        logger.error(f"Permission denied reading file: {path}")
        raise e
    
    return hash_md5.hexdigest()


def calculate_dir_md5(dir_path: Union[str, Path], exclude: Optional[set] = None) -> str:
    """
    Calculate a composite MD5 checksum for all files in a directory.
    
    Files are processed in sorted order to ensure deterministic results.
    Subdirectories are traversed recursively.
    
    Args:
        dir_path: Path to the directory.
        exclude: Set of filename patterns to exclude (e.g., '.pyc', '__pycache__').
                
    Returns:
        Hexadecimal MD5 hash string representing the directory contents.
        
    Raises:
        NotADirectoryError: If the path is not a directory.
    """
    path = Path(dir_path)
    if not path.exists():
        raise FileNotFoundError(f"Directory not found: {path}")
    if not path.is_dir():
        raise NotADirectoryError(f"Path is a file, expected a directory: {path}")
    
    if exclude is None:
        exclude = DEFAULT_EXCLUDE_PATTERNS
        
    combined_hash = hashlib.md5()
    
    # Get all files sorted by relative path for determinism
    files = []
    for root, dirs, filenames in os.walk(path):
        # Filter directories in-place to prevent descending into excluded dirs
        dirs[:] = [d for d in dirs if d not in exclude]
        
        for filename in filenames:
            if any(ex in filename for ex in exclude):
                continue
            file_path = Path(root) / filename
            files.append(file_path)
    
    files.sort(key=lambda p: str(p.relative_to(path)))
    
    for file_path in files:
        try:
            # Include relative path in hash to capture structure
            rel_path = file_path.relative_to(path)
            combined_hash.update(str(rel_path).encode('utf-8'))
            # Include file content hash
            file_hash = calculate_md5(file_path)
            combined_hash.update(file_hash.encode('utf-8'))
        except Exception as e:
            logger.warning(f"Skipping file during dir hash calculation: {file_path} ({e})")
            continue
    
    return combined_hash.hexdigest()


def get_file_metadata(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Extract metadata for a single file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Dictionary containing:
            - path: Absolute path as string
            - size_bytes: File size in bytes
            - modified_time: ISO format timestamp
            - md5: MD5 checksum
            - type: 'file'
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    stat = path.stat()
    return {
        "path": str(path.absolute()),
        "size_bytes": stat.st_size,
        "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "md5": calculate_md5(path),
        "type": "file"
    }


def load_artifact_hashes(hash_file: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Load the artifact hash registry from YAML.
    
    Args:
        hash_file: Path to the YAML file. Defaults to DEFAULT_HASH_FILE.
        
    Returns:
        Dictionary containing the hash registry.
        Returns an empty structure if file does not exist.
    """
    if hash_file is None:
        hash_file = DEFAULT_HASH_FILE
    else:
        hash_file = Path(hash_file)
        
    if not hash_file.exists():
        logger.info(f"Hash file not found at {hash_file}, initializing empty registry.")
        return {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "artifacts": {}
        }
        
    try:
        with open(hash_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if data is None:
                return {
                    "version": "1.0",
                    "last_updated": datetime.now().isoformat(),
                    "artifacts": {}
                }
            return data
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file {hash_file}: {e}")
        raise


def save_artifact_hashes(data: Dict[str, Any], hash_file: Optional[Union[str, Path]] = None) -> None:
    """
    Save the artifact hash registry to YAML.
    
    Args:
        data: The dictionary to save.
        hash_file: Path to the YAML file. Defaults to DEFAULT_HASH_FILE.
    """
    if hash_file is None:
        hash_file = DEFAULT_HASH_FILE
    else:
        hash_file = Path(hash_file)
        
    # Ensure directory exists
    hash_file.parent.mkdir(parents=True, exist_ok=True)
    
    data["last_updated"] = datetime.now().isoformat()
    
    with open(hash_file, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        
    logger.info(f"Artifact hashes saved to {hash_file}")


def update_artifact_hash(
    artifact_path: Union[str, Path],
    registry: Optional[Dict[str, Any]] = None,
    hash_file: Optional[Union[str, Path]] = None
) -> Tuple[Dict[str, Any], str]:
    """
    Calculate hash for an artifact and update the registry.
    
    Args:
        artifact_path: Path to the file or directory to hash.
        registry: Existing registry dict. If None, loads from disk.
        hash_file: Path to the registry file.
        
    Returns:
        Tuple of (updated_registry, new_hash_string)
    """
    path = Path(artifact_path)
    if not path.exists():
        raise FileNotFoundError(f"Artifact not found for hashing: {path}")
        
    if registry is None:
        registry = load_artifact_hashes(hash_file)
        
    if "artifacts" not in registry:
        registry["artifacts"] = {}
        
    # Determine hash based on type
    if path.is_dir():
      # For directories, we use a composite hash of contents
      new_hash = calculate_dir_md5(path)
      artifact_type = "directory"
    else:
      new_hash = calculate_md5(path)
      artifact_type = "file"
      
    rel_key = str(path.relative_to(Path.cwd()))
    
    registry["artifacts"][rel_key] = {
        "hash": new_hash,
        "type": artifact_type,
        "last_verified": datetime.now().isoformat()
    }
    
    return registry, new_hash


def verify_artifact_integrity(
    artifact_path: Union[str, Path],
    expected_hash: str,
    registry: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Verify an artifact's integrity against an expected hash.
    
    Args:
        artifact_path: Path to the artifact.
        expected_hash: The expected MD5 hash.
        registry: Optional registry to load from if needed (not used directly for calculation).
        
    Returns:
        True if the current hash matches the expected hash.
    """
    path = Path(artifact_path)
    if not path.exists():
        logger.error(f"Artifact missing during integrity check: {path}")
        return False
        
    current_hash = calculate_md5(path) if path.is_file() else calculate_dir_md5(path)
    
    if current_hash != expected_hash:
        logger.error(
            f"Integrity check failed for {path}. "
            f"Expected: {expected_hash}, Got: {current_hash}"
        )
        return False
        
    logger.info(f"Integrity check passed for {path}")
    return True


def register_multiple_artifacts(
    artifact_paths: List[Union[str, Path]],
    hash_file: Optional[Union[str, Path]] = None,
    force_update: bool = False
) -> Dict[str, Any]:
    """
    Register multiple artifacts in the hash registry.
    
    Args:
        artifact_paths: List of paths to register.
        hash_file: Path to the registry file.
        force_update: If True, re-calculate hash even if entry exists.
        
    Returns:
        The updated registry.
    """
    registry = load_artifact_hashes(hash_file)
    
    if "artifacts" not in registry:
        registry["artifacts"] = {}
        
    updated_count = 0
    for path_str in artifact_paths:
        path = Path(path_str)
        rel_key = str(path.relative_to(Path.cwd()))
        
        if rel_key in registry["artifacts"] and not force_update:
            # Optional: verify existing hash?
            continue
            
        try:
            registry, _ = update_artifact_hash(path, registry, hash_file=None)
            updated_count += 1
        except FileNotFoundError as e:
            logger.warning(f"Skipping missing artifact: {path} ({e})")
        except Exception as e:
            logger.error(f"Failed to register artifact {path}: {e}")
            
    save_artifact_hashes(registry, hash_file)
    logger.info(f"Registered {updated_count} artifacts.")
    return registry


def cleanup_stale_hashes(
    hash_file: Optional[Union[str, Path]] = None,
    max_age_days: int = 30
) -> List[str]:
    """
    Remove entries from the registry for artifacts that no longer exist.
    
    Args:
        hash_file: Path to the registry file.
        max_age_days: (Reserved for future extension) Age threshold.
        
    Returns:
        List of removed artifact paths.
    """
    registry = load_artifact_hashes(hash_file)
    if "artifacts" not in registry:
        return []
        
    stale_keys = []
    for key in list(registry["artifacts"].keys()):
        full_path = Path.cwd() / key
        if not full_path.exists():
            stale_keys.append(key)
            del registry["artifacts"][key]
            
    if stale_keys:
        save_artifact_hashes(registry, hash_file)
        logger.info(f"Cleaned up {len(stale_keys)} stale artifact entries.")
        
    return stale_keys


def get_artifact_status(
    artifact_path: Union[str, Path],
    hash_file: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """
    Get the current status of an artifact relative to the registry.
    
    Returns:
        Dict with keys:
            - status: 'registered', 'unregistered', 'modified', 'missing'
            - current_hash: (if exists)
            - registered_hash: (if registered)
            - message: Human readable description
    """
    path = Path(artifact_path)
    rel_key = str(path.relative_to(Path.cwd()))
    registry = load_artifact_hashes(hash_file)
    
    result = {
        "path": str(path),
        "status": "unknown",
        "message": ""
    }
    
    if not path.exists():
        result["status"] = "missing"
        result["message"] = "Artifact file does not exist."
        return result
        
    current_hash = calculate_md5(path) if path.is_file() else calculate_dir_md5(path)
    result["current_hash"] = current_hash
    
    if rel_key not in registry.get("artifacts", {}):
        result["status"] = "unregistered"
        result["message"] = "Artifact is not in the registry."
        return result
        
    registered_entry = registry["artifacts"][rel_key]
    registered_hash = registered_entry.get("hash")
    result["registered_hash"] = registered_hash
    
    if current_hash == registered_hash:
        result["status"] = "registered"
        result["message"] = "Artifact matches registry."
    else:
        result["status"] = "modified"
        result["message"] = "Artifact has been modified since registration."
        
    return result


def main() -> None:
    """
    CLI entry point for hygiene utilities.
    Demonstrates usage of the hygiene functions.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Data Hygiene Utilities")
    parser.add_argument("--action", choices=["hash", "verify", "register", "status"], required=True, help="Action to perform")
    parser.add_argument("--path", required=True, help="Path to file or directory")
    parser.add_argument("--expected-hash", help="Expected hash for verification")
    parser.add_argument("--registry", help="Path to registry file (default: state/artifact_hashes.yaml)")
    
    args = parser.parse_args()
    path = Path(args.path)
    
    if args.action == "hash":
        if not path.exists():
            print(f"Error: Path not found: {path}")
            return 1
        try:
            if path.is_file():
                h = calculate_md5(path)
            else:
                h = calculate_dir_md5(path)
            print(f"Hash: {h}")
        except Exception as e:
            print(f"Error calculating hash: {e}")
            return 1
            
    elif args.action == "verify":
        if not args.expected_hash:
            print("Error: --expected-hash is required for verification")
            return 1
        if not path.exists():
            print(f"Error: Path not found: {path}")
            return 1
        try:
            if path.is_file():
                current = calculate_md5(path)
            else:
                current = calculate_dir_md5(path)
            if current == args.expected_hash:
                print("Verification: PASSED")
                return 0
            else:
                print(f"Verification: FAILED (Expected: {args.expected_hash}, Got: {current})")
                return 1
        except Exception as e:
            print(f"Error during verification: {e}")
            return 1
            
    elif args.action == "register":
        try:
            registry, new_hash = update_artifact_hash(path, hash_file=args.registry)
            print(f"Registered {path} with hash: {new_hash}")
        except Exception as e:
            print(f"Error registering artifact: {e}")
            return 1
            
    elif args.action == "status":
        try:
            status = get_artifact_status(path, hash_file=args.registry)
            print(f"Status: {status['status']}")
            print(f"Message: {status['message']}")
            if "current_hash" in status:
                print(f"Current Hash: {status['current_hash']}")
            if "registered_hash" in status:
                print(f"Registered Hash: {status['registered_hash']}")
        except Exception as e:
            print(f"Error checking status: {e}")
            return 1
            
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
