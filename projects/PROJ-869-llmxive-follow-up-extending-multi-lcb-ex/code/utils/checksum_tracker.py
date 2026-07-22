import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

from code.config import get_path
from code.utils.logger import get_logger
from code.utils.common import ensure_dir, load_json, save_json

logger = get_logger(__name__)

CHECKSUM_REGISTRY_PATH = get_path("data", "registry", "checksums.json")

def compute_file_checksum(file_path: Path) -> str:
    """
    Computes the SHA-256 checksum of a file.
    Reads the file in chunks to handle large files efficiently.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found for checksum: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error computing checksum for {file_path}: {e}")
        raise

def load_registry() -> Dict[str, Any]:
    """Loads the checksum registry from disk or initializes a new one."""
    if not CHECKSUM_REGISTRY_PATH.exists():
        ensure_dir(CHECKSUM_REGISTRY_PATH.parent)
        return {"files": {}}
    return load_json(CHECKSUM_REGISTRY_PATH)

def save_registry(registry: Dict[str, Any]) -> None:
    """Saves the checksum registry to disk."""
    ensure_dir(CHECKSUM_REGISTRY_PATH.parent)
    save_json(CHECKSUM_REGISTRY_PATH, registry)

def register_file(file_path: Path, description: str = "Unknown") -> bool:
    """
    Computes checksum for a file and registers it in the tracking system.
    Returns True if successful, False if the file does not exist.
    """
    if not file_path.exists():
        logger.warning(f"Cannot register non-existent file: {file_path}")
        return False

    checksum = compute_file_checksum(file_path)
    registry = load_registry()
    
    rel_path = str(file_path.relative_to(get_path("data")))
    
    registry["files"][rel_path] = {
        "checksum": checksum,
        "description": description,
        "registered_at": None # Timestamp could be added if needed
    }
    
    save_registry(registry)
    logger.info(f"Registered file: {rel_path} (SHA256: {checksum[:16]}...)")
    return True

def verify_file(file_path: Path) -> bool:
    """
    Verifies a file's checksum against the registry.
    Returns True if valid or if not yet registered (and registers it).
    Returns False if checksum mismatch.
    """
    if not file_path.exists():
        logger.error(f"File to verify does not exist: {file_path}")
        return False

    registry = load_registry()
    rel_path = str(file_path.relative_to(get_path("data")))

    if rel_path not in registry["files"]:
        logger.info(f"File not in registry. Registering: {rel_path}")
        register_file(file_path)
        return True

    stored_checksum = registry["files"][rel_path]["checksum"]
    current_checksum = compute_file_checksum(file_path)

    if stored_checksum != current_checksum:
        logger.error(f"Checksum mismatch for {rel_path}!")
        logger.error(f"  Expected: {stored_checksum}")
        logger.error(f"  Found:    {current_checksum}")
        return False

    logger.debug(f"Checksum verified for {rel_path}")
    return True

def initialize_directories() -> None:
    """
    Creates the data/raw and data/processed directory structures
    and initializes the checksum registry if it doesn't exist.
    """
    raw_dir = get_path("data", "raw")
    processed_dir = get_path("data", "processed")
    
    ensure_dir(raw_dir)
    ensure_dir(processed_dir)
    ensure_dir(CHECKSUM_REGISTRY_PATH.parent)
    
    if not CHECKSUM_REGISTRY_PATH.exists():
        registry = {"files": {}}
        save_registry(registry)
        logger.info("Initialized checksum registry.")
    else:
        logger.info("Checksum registry already exists.")

def track_directory(directory: Path, description_prefix: str = "") -> List[str]:
    """
    Scans a directory for files and registers them in the checksum tracker.
    Returns a list of registered relative paths.
    """
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return []
    
    registered = []
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            if register_file(file_path, f"{description_prefix}{file_path.name}"):
                registered.append(str(file_path.relative_to(get_path("data"))))
    return registered
