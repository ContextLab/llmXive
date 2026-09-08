"""
Data hygiene utilities for the LST Wear Resistance project.
Provides MD5 checksum generation, artifact metadata extraction, and
persistent storage of artifact hashes in state/artifact_hashes.yaml.
"""
import hashlib
import os
from pathlib import Path
from typing import Optional, Union, Dict, Any, List, Tuple
import yaml
from datetime import datetime
import logging

# Configure logging for hygiene operations
logger = logging.getLogger(__name__)

# Constants
STATE_DIR = Path("state")
ARTIFACT_HASH_FILE = STATE_DIR / "artifact_hashes.yaml"
SUPPORTED_EXTENSIONS = {".csv", ".json", ".yaml", ".yml", ".txt", ".pkl", ".joblib"}


def calculate_md5(file_path: Union[str, Path]) -> str:
    """
    Calculate the MD5 checksum of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal MD5 hash string.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the path is not a file.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
        
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_file_metadata(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Extract basic metadata for a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Dictionary containing file size, modification time, and extension.
    """
    file_path = Path(file_path)
    stats = file_path.stat()
    return {
        "size_bytes": stats.st_size,
        "modified_time": datetime.fromtimestamp(stats.st_mtime).isoformat(),
        "extension": file_path.suffix.lower(),
        "filename": file_path.name
    }


def load_artifact_hashes() -> Dict[str, Any]:
    """
    Load the artifact hash registry from state/artifact_hashes.yaml.
    
    Returns:
        Dictionary containing artifact hashes and metadata.
        Returns an empty dict with structure if file doesn't exist.
    """
    if not ARTIFACT_HASH_FILE.exists():
        logger.info(f"Artifact hash file not found at {ARTIFACT_HASH_FILE}. Initializing empty registry.")
        return {
            "last_updated": datetime.now().isoformat(),
            "artifacts": {}
        }
    
    try:
        with open(ARTIFACT_HASH_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data is None:
                return {
                    "last_updated": datetime.now().isoformat(),
                    "artifacts": {}
                }
            return data
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML file {ARTIFACT_HASH_FILE}: {e}")
        raise


def save_artifact_hashes(data: Dict[str, Any]) -> None:
    """
    Save the artifact hash registry to state/artifact_hashes.yaml.
    
    Args:
        data: Dictionary containing artifact hashes and metadata.
    """
    # Ensure state directory exists
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Update timestamp
    data["last_updated"] = datetime.now().isoformat()
    
    try:
        with open(ARTIFACT_HASH_FILE, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        logger.info(f"Successfully saved artifact hashes to {ARTIFACT_HASH_FILE}")
    except IOError as e:
        logger.error(f"Failed to write artifact hashes to {ARTIFACT_HASH_FILE}: {e}")
        raise


def update_artifact_hash(
    file_path: Union[str, Path], 
    registry: Dict[str, Any],
    custom_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate hash for a file and update the registry.
    
    Args:
        file_path: Path to the file.
        registry: Current artifact registry dictionary.
        custom_key: Optional custom key for the artifact. If None, uses relative path.
        
    Returns:
        Updated registry dictionary.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot hash non-existent file: {file_path}")
        
    key = custom_key if custom_key else str(file_path.relative_to(Path.cwd()))
    md5_hash = calculate_md5(file_path)
    metadata = get_file_metadata(file_path)
    
    if "artifacts" not in registry:
        registry["artifacts"] = {}
        
    registry["artifacts"][key] = {
        "md5": md5_hash,
        "metadata": metadata,
        "updated_at": datetime.now().isoformat()
    }
    
    logger.debug(f"Updated hash for artifact '{key}': {md5_hash}")
    return registry


def verify_artifact_integrity(
    file_path: Union[str, Path], 
    expected_hash: str,
    custom_key: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Verify a file's integrity by comparing its MD5 hash to an expected value.
    
    Args:
        file_path: Path to the file to verify.
        expected_hash: Expected MD5 hash.
        custom_key: Optional key for logging purposes.
        
    Returns:
        Tuple of (is_valid, message)
    """
    file_path = Path(file_path)
    key = custom_key if custom_key else str(file_path)
    
    if not file_path.exists():
        return False, f"File not found: {key}"
        
    try:
        actual_hash = calculate_md5(file_path)
        if actual_hash == expected_hash:
            return True, f"Integrity verified for {key}"
        else:
            return False, f"Integrity mismatch for {key}. Expected: {expected_hash}, Got: {actual_hash}"
    except Exception as e:
        return False, f"Error verifying {key}: {str(e)}"


def register_multiple_artifacts(
    file_paths: List[Union[str, Path]],
    registry: Optional[Dict[str, Any]] = None,
    custom_keys: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Register multiple artifacts in the hash registry.
    
    Args:
        file_paths: List of file paths to register.
        registry: Existing registry to update. If None, loads from disk.
        custom_keys: Optional list of custom keys matching file_paths.
        
    Returns:
        Updated registry dictionary.
    """
    if registry is None:
        registry = load_artifact_hashes()
        
    if custom_keys is not None and len(custom_keys) != len(file_paths):
        raise ValueError("custom_keys length must match file_paths length")
        
    for i, path in enumerate(file_paths):
        key = custom_keys[i] if custom_keys else None
        registry = update_artifact_hash(path, registry, custom_key=key)
        
    return registry


def cleanup_stale_hashes(
    registry: Dict[str, Any],
    threshold_days: int = 30
) -> Dict[str, Any]:
    """
    Remove artifact entries that are older than the threshold.
    
    Args:
        registry: Artifact registry dictionary.
        threshold_days: Age threshold in days.
        
    Returns:
        Cleaned registry dictionary.
    """
    from datetime import timedelta, datetime
    
    if "artifacts" not in registry:
        return registry
        
    cutoff = datetime.now() - timedelta(days=threshold_days)
    cleaned_artifacts = {}
    
    for key, data in registry["artifacts"].items():
        updated_at_str = data.get("updated_at", "")
        try:
            updated_at = datetime.fromisoformat(updated_at_str)
            if updated_at > cutoff:
                cleaned_artifacts[key] = data
            else:
                logger.debug(f"Removing stale artifact: {key} (updated: {updated_at_str})")
        except (ValueError, TypeError):
            # Keep entries with invalid dates to avoid data loss
            cleaned_artifacts[key] = data
            
    registry["artifacts"] = cleaned_artifacts
    return registry


def get_artifact_status(
    file_path: Union[str, Path],
    registry: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Get the status of an artifact (new, updated, unchanged, missing).
    
    Args:
        file_path: Path to the file.
        registry: Optional registry to check against.
        
    Returns:
        Dictionary with status information.
    """
    file_path = Path(file_path)
    key = str(file_path.relative_to(Path.cwd()))
    
    if registry is None:
        registry = load_artifact_hashes()
        
    result = {
        "path": str(file_path),
        "key": key,
        "exists": file_path.exists(),
        "status": "unknown"
    }
    
    if not result["exists"]:
        result["status"] = "missing"
        return result
        
    if "artifacts" not in registry or key not in registry["artifacts"]:
        result["status"] = "new"
        result["current_hash"] = calculate_md5(file_path)
        return result
        
    stored_hash = registry["artifacts"][key].get("md5")
    current_hash = calculate_md5(file_path)
    
    if stored_hash == current_hash:
        result["status"] = "unchanged"
    else:
        result["status"] = "updated"
        
    result["stored_hash"] = stored_hash
    result["current_hash"] = current_hash
    return result


def main():
    """
    CLI entry point for hygiene utilities.
    Demonstrates registering artifacts and verifying integrity.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Data hygiene utilities")
    parser.add_argument("--register", nargs="+", help="Register file paths")
    parser.add_argument("--verify", nargs="+", help="Verify file paths")
    parser.add_argument("--status", nargs="+", help="Check status of file paths")
    parser.add_argument("--save", action="store_true", help="Save registry after operations")
    
    args = parser.parse_args()
    
    registry = load_artifact_hashes()
    
    if args.register:
        registry = register_multiple_artifacts(args.register, registry)
        if args.save:
            save_artifact_hashes(registry)
            
    if args.verify:
        for path in args.verify:
            is_valid, msg = verify_artifact_integrity(path, "dummy_hash")
            print(f"{path}: {msg}")
            
    if args.status:
        for path in args.status:
            status = get_artifact_status(path, registry)
            print(f"{status['path']}: {status['status']}")
            
    if not any([args.register, args.verify, args.status]):
        print("Usage: python hygiene.py --register <paths...> [--save]")
        print("       python hygiene.py --verify <paths...>")
        print("       python hygiene.py --status <paths...>")


if __name__ == "__main__":
    main()
