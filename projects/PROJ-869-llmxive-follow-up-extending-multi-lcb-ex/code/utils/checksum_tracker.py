import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from code.config import get_path
from code.utils.common import ensure_dir, load_json, save_json
from code.utils.logger import get_logger

REGISTRY_PATH = "data/.checksum_registry.json"

def compute_file_checksum(file_path: Path) -> str:
    """
    Compute SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to checksum.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def load_registry() -> Dict[str, Any]:
    """
    Load the checksum registry from disk.
    
    Returns:
        Dictionary containing the checksum registry, or an empty dict if not found.
    """
    registry_path = Path(get_path(REGISTRY_PATH))
    if registry_path.exists():
        return load_json(registry_path)
    return {"files": {}, "directories": []}

def save_registry(registry: Dict[str, Any]) -> None:
    """
    Save the checksum registry to disk.
    
    Args:
        registry: The registry dictionary to save.
    """
    registry_path = Path(get_path(REGISTRY_PATH))
    ensure_dir(registry_path.parent)
    save_json(registry_path, registry)

def register_file(file_path: Path, registry: Dict[str, Any]) -> None:
    """
    Register a file in the checksum registry.
    
    Args:
        file_path: Path to the file to register.
        registry: The registry dictionary to update.
    """
    if file_path.exists():
        checksum = compute_file_checksum(file_path)
        relative_path = str(file_path.relative_to(Path(get_path("data_root"))))
        registry["files"][relative_path] = {
            "checksum": checksum,
            "size": file_path.stat().st_size,
            "registered_at": str(file_path.stat().st_mtime)
        }

def verify_file(file_path: Path, registry: Dict[str, Any]) -> bool:
    """
    Verify a file's checksum against the registry.
    
    Args:
        file_path: Path to the file to verify.
        registry: The registry dictionary to check against.
        
    Returns:
        True if the file exists and checksum matches, False otherwise.
    """
    if not file_path.exists():
        return False
        
    relative_path = str(file_path.relative_to(Path(get_path("data_root"))))
    if relative_path not in registry["files"]:
        return False
        
    stored_checksum = registry["files"][relative_path]["checksum"]
    current_checksum = compute_file_checksum(file_path)
    
    return stored_checksum == current_checksum

def initialize_directories(dir_paths: List[Path]) -> None:
    """
    Create directories if they don't exist and initialize the registry.
    
    Args:
        dir_paths: List of directory paths to create.
    """
    for dir_path in dir_paths:
        ensure_dir(dir_path)
        
    # Initialize registry if it doesn't exist
    registry = load_registry()
    if "directories" not in registry:
        registry["directories"] = []
        
    for dir_path in dir_paths:
        dir_str = str(dir_path.relative_to(Path(get_path("data_root"))))
        if dir_str not in registry["directories"]:
            registry["directories"].append(dir_str)
            
    save_registry(registry)

def track_directory(dir_path: Path) -> None:
    """
    Scan a directory and register all files in the checksum registry.
    
    Args:
        dir_path: Path to the directory to scan.
    """
    registry = load_registry()
    
    if not dir_path.exists():
        return
        
    for file_path in dir_path.rglob("*"):
        if file_path.is_file():
            # Skip the registry file itself
            if str(file_path) == get_path(REGISTRY_PATH):
                continue
            register_file(file_path, registry)
            
    save_registry(registry)
