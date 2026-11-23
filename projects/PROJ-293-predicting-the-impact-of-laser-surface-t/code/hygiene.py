import hashlib
import os
from pathlib import Path
from typing import Optional, Union, Dict, Any, List, Tuple
import yaml
from datetime import datetime

from logging_config import get_logger

logger = get_logger(__name__)

ARTIFACT_HASHES_PATH = Path("state/artifact_hashes.yaml")

def calculate_md5(file_path: Union[str, Path]) -> str:
    """
    Calculate the MD5 hash of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hexadecimal MD5 hash string.
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def calculate_dir_md5(dir_path: Union[str, Path]) -> str:
    """
    Calculate a combined MD5 hash for all files in a directory.
    
    Args:
        dir_path: Path to the directory.
        
    Returns:
        Hexadecimal MD5 hash string of the directory contents.
    """
    hash_md5 = hashlib.md5()
    dir_path = Path(dir_path)
    
    # Sort files for deterministic ordering
    for file_path in sorted(dir_path.rglob("*")):
        if file_path.is_file():
            relative_path = file_path.relative_to(dir_path)
            hash_md5.update(relative_path.as_posix().encode())
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
    
    return hash_md5.hexdigest()

def get_file_metadata(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Get metadata for a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Dictionary with metadata.
    """
    file_path = Path(file_path)
    stat = file_path.stat()
    return {
        "path": str(file_path),
        "size_bytes": stat.st_size,
        "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "md5": calculate_md5(file_path)
    }

def load_artifact_hashes() -> Dict[str, Any]:
    """
    Load artifact hashes from the YAML file.
    
    Returns:
        Dictionary of artifact hashes.
    """
    if not ARTIFACT_HASHES_PATH.exists():
        return {}
    
    with open(ARTIFACT_HASHES_PATH, "r") as f:
        return yaml.safe_load(f) or {}

def save_artifact_hashes(hashes: Dict[str, Any]) -> None:
    """
    Save artifact hashes to the YAML file.
    
    Args:
        hashes: Dictionary of artifact hashes.
    """
    ARTIFACT_HASHES_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(ARTIFACT_HASHES_PATH, "w") as f:
        yaml.dump(hashes, f, default_flow_style=False)

def update_artifact_hash(file_path: Union[str, Path]) -> None:
    """
    Update the hash for a specific artifact.
    
    Args:
        file_path: Path to the artifact.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        logger.warning(f"Artifact not found, skipping hash update: {file_path}")
        return
    
    hashes = load_artifact_hashes()
    relative_path = str(file_path)
    
    hashes[relative_path] = {
        "md5": calculate_md5(file_path),
        "updated_at": datetime.now().isoformat()
    }
    
    save_artifact_hashes(hashes)
    logger.info(f"Updated hash for: {relative_path}")

def register_multiple_artifacts(file_paths: List[Union[str, Path]]) -> None:
    """
    Register multiple artifacts and update their hashes.
    
    Args:
        file_paths: List of artifact paths.
    """
    for path in file_paths:
        update_artifact_hash(path)

def verify_artifact_integrity(file_path: Union[str, Path]) -> bool:
    """
    Verify the integrity of an artifact by comparing its current hash to the stored one.
    
    Args:
        file_path: Path to the artifact.
        
    Returns:
        True if integrity is verified, False otherwise.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        logger.error(f"Artifact not found: {file_path}")
        return False
    
    hashes = load_artifact_hashes()
    relative_path = str(file_path)
    
    if relative_path not in hashes:
        logger.warning(f"No stored hash for: {relative_path}")
        return False
    
    stored_md5 = hashes[relative_path].get("md5")
    current_md5 = calculate_md5(file_path)
    
    if stored_md5 != current_md5:
        logger.error(f"Integrity check failed for {relative_path}: "
                     f"Stored={stored_md5}, Current={current_md5}")
        return False
    
    logger.info(f"Integrity verified for: {relative_path}")
    return True

def get_artifact_status(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Get the status of an artifact.
    
    Args:
        file_path: Path to the artifact.
        
    Returns:
        Dictionary with status information.
    """
    file_path = Path(file_path)
    status = {
        "path": str(file_path),
        "exists": file_path.exists()
    }
    
    if status["exists"]:
        status["metadata"] = get_file_metadata(file_path)
        status["integrity_verified"] = verify_artifact_integrity(file_path)
    else:
        status["integrity_verified"] = False
        
    return status

def cleanup_stale_hashes() -> int:
    """
    Remove hashes for artifacts that no longer exist.
    
    Returns:
        Number of hashes removed.
    """
    hashes = load_artifact_hashes()
    paths_to_remove = []
    
    for path_str in hashes:
        if not Path(path_str).exists():
            paths_to_remove.append(path_str)
    
    for path_str in paths_to_remove:
        del hashes[path_str]
        logger.info(f"Removed stale hash for: {path_str}")
    
    if paths_to_remove:
        save_artifact_hashes(hashes)
        
    return len(paths_to_remove)

def main():
    """
    Main entry point for hygiene utilities.
    Currently used for testing or manual execution.
    """
    logger.info("Hygiene module loaded. Use specific functions directly.")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())