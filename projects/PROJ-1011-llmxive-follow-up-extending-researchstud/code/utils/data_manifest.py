import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union
import logging

from .error_handling import ValidationError

logger = logging.getLogger(__name__)

MANIFEST_FILENAME = "manifest.json"

def _get_manifest_path(data_root: Path) -> Path:
    """Return the path to the manifest file within the data root."""
    return data_root / MANIFEST_FILENAME

def create_directory_structure(data_root: Union[str, Path]) -> Path:
    """
    Create the standard data directory structure:
    - data_root/raw
    - data_root/processed
    - data_root/results

    Args:
        data_root: Path to the base data directory.

    Returns:
        The resolved Path object for the data root.
    """
    root = Path(data_root)
    root.mkdir(parents=True, exist_ok=True)

    subdirs = ["raw", "processed", "results"]
    for subdir in subdirs:
        (root / subdir).mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {root / subdir}")

    # Initialize manifest if it doesn't exist
    manifest_path = _get_manifest_path(root)
    if not manifest_path.exists():
        save_manifest(root, {})
        logger.info(f"Initialized empty manifest at {manifest_path}")

    return root

def calculate_file_checksum(file_path: Union[str, Path]) -> str:
    """
    Calculate SHA-256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal string of the SHA-256 checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
    except PermissionError:
        raise PermissionError(f"Permission denied reading file: {path}")

    return sha256_hash.hexdigest()

def load_manifest(data_root: Union[str, Path]) -> Dict:
    """
    Load the manifest file from the data root.

    Args:
        data_root: Path to the data root directory.

    Returns:
        Dictionary containing the manifest data.

    Raises:
        ValidationError: If the manifest is missing or invalid JSON.
    """
    path = Path(data_root)
    manifest_path = _get_manifest_path(path)

    if not manifest_path.exists():
        raise ValidationError(f"Manifest not found at {manifest_path}. Run create_directory_structure first.")

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise ValidationError("Manifest must be a JSON object.")
            return data
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON in manifest: {e}")

def save_manifest(data_root: Union[str, Path], manifest_data: Dict) -> None:
    """
    Save the manifest data to the manifest file.

    Args:
        data_root: Path to the data root directory.
        manifest_data: Dictionary to save as the manifest.
    """
    path = Path(data_root)
    manifest_path = _get_manifest_path(path)

    # Ensure data root exists
    path.mkdir(parents=True, exist_ok=True)

    try:
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2, sort_keys=True)
        logger.info(f"Saved manifest to {manifest_path}")
    except PermissionError:
        raise PermissionError(f"Permission denied writing to manifest: {manifest_path}")

def update_manifest_with_file(data_root: Union[str, Path], file_path: Union[str, Path], metadata: Optional[Dict] = None) -> None:
    """
    Add or update an entry in the manifest for a specific file.

    Args:
        data_root: Path to the data root directory.
        file_path: Path to the file being registered.
        metadata: Optional additional metadata to store with the file entry.
    """
    file_p = Path(file_path)
    if not file_p.is_absolute():
        # Make path relative to data_root if it isn't already
        root_p = Path(data_root)
        if root_p in file_p.parents or file_p == root_p:
            file_p = file_p.relative_to(root_p)
            file_path = str(file_p)
        else:
            # If it's just a relative path, assume it's relative to root
            file_p = root_p / file_p
            file_path = str(file_p.relative_to(root_p))

    if not file_p.exists():
        raise FileNotFoundError(f"Cannot register non-existent file: {file_p}")

    manifest = load_manifest(data_root)

    entry = {
        "path": str(file_p),
        "checksum": calculate_file_checksum(file_p),
        "size_bytes": file_p.stat().st_size,
        "registered_at": str(file_p.stat().st_mtime),
    }

    if metadata:
        entry.update(metadata)

    manifest[str(file_p)] = entry
    save_manifest(data_root, manifest)

def verify_manifest(data_root: Union[str, Path]) -> bool:
    """
    Verify the integrity of all files listed in the manifest.

    Args:
        data_root: Path to the data root directory.

    Returns:
        True if all files match their checksums, False otherwise.
    """
    manifest = load_manifest(data_root)
    root = Path(data_root)
    all_valid = True

    for rel_path, entry in manifest.items():
        file_path = root / rel_path
        if not file_path.exists():
            logger.warning(f"Missing file in manifest: {file_path}")
            all_valid = False
            continue

        try:
            current_checksum = calculate_file_checksum(file_path)
            if current_checksum != entry.get("checksum"):
                logger.error(f"Checksum mismatch for {file_path}")
                all_valid = False
        except Exception as e:
            logger.error(f"Error verifying {file_path}: {e}")
            all_valid = False

    return all_valid

def register_new_file(data_root: Union[str, Path], file_path: Union[str, Path], metadata: Optional[Dict] = None) -> str:
    """
    Register a new file in the manifest, calculating its checksum.

    Args:
        data_root: Path to the data root directory.
        file_path: Path to the file to register.
        metadata: Optional metadata to include.

    Returns:
        The calculated checksum.
    """
    update_manifest_with_file(data_root, file_path, metadata)
    return calculate_file_checksum(file_path)
