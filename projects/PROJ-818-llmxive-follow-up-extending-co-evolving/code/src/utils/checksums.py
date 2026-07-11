import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

class ChecksumError(Exception):
    """Raised when checksum operations fail."""
    pass

def compute_file_sha256(filepath: Path) -> str:
    """
    Compute SHA-256 hash of a file.
    
    Args:
        filepath: Path to the file to hash
        
    Returns:
        Hexadecimal SHA-256 hash string
        
    Raises:
        ChecksumError: If file cannot be read
    """
    if not filepath.exists():
        raise ChecksumError(f"File not found: {filepath}")
        
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise ChecksumError(f"Failed to read file {filepath}: {e}")

def load_checksums(checksum_file: Path) -> Dict[str, str]:
    """
    Load existing checksums from JSON file.
    
    Args:
        checksum_file: Path to the checksums JSON file
        
    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes
    """
    if not checksum_file.exists():
        return {}
        
    try:
        with open(checksum_file, "r") as f:
            data = json.load(f)
            return data.get("checksums", {})
    except (json.JSONDecodeError, IOError) as e:
        raise ChecksumError(f"Failed to load checksums from {checksum_file}: {e}")

def save_checksums(checksums: Dict[str, str], checksum_file: Path) -> None:
    """
    Save checksums to JSON file.
    
    Args:
        checksums: Dictionary mapping relative file paths to SHA-256 hashes
        checksum_file: Path to the checksums JSON file
    """
    checksum_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(checksum_file, "w") as f:
            json.dump({"checksums": checksums}, f, indent=2)
    except IOError as e:
        raise ChecksumError(f"Failed to save checksums to {checksum_file}: {e}")

def update_checksum_for_file(
    filepath: Path, 
    checksum_file: Path
) -> str:
    """
    Compute hash for a file and update the checksums registry.
    
    Args:
        filepath: Path to the file to hash (must exist)
        checksum_file: Path to the checksums JSON file
        
    Returns:
        The computed SHA-256 hash
    """
    if not filepath.exists():
        raise ChecksumError(f"Cannot checksum non-existent file: {filepath}")
        
    # Load existing checksums
    checksums = load_checksums(checksum_file)
    
    # Compute new hash
    file_hash = compute_file_sha256(filepath)
    
    # Use relative path from project root for consistency
    # Assume project root is the parent of 'code' directory
    project_root = checksum_file.parent.parent.parent
    try:
        relative_path = str(filepath.relative_to(project_root))
    except ValueError:
        # Fallback to absolute path if relative computation fails
        relative_path = str(filepath)
        
    checksums[relative_path] = file_hash
    
    # Save updated checksums
    save_checksums(checksums, checksum_file)
    
    return file_hash

def verify_file_integrity(
    filepath: Path, 
    checksum_file: Path
) -> bool:
    """
    Verify a file's integrity against stored checksum.
    
    Args:
        filepath: Path to the file to verify
        checksum_file: Path to the checksums JSON file
        
    Returns:
        True if file matches stored checksum, False otherwise
        
    Raises:
        ChecksumError: If no checksum exists for the file
    """
    if not filepath.exists():
        raise ChecksumError(f"File not found for verification: {filepath}")
        
    checksums = load_checksums(checksum_file)
    
    project_root = checksum_file.parent.parent.parent
    try:
        relative_path = str(filepath.relative_to(project_root))
    except ValueError:
        relative_path = str(filepath)
        
    if relative_path not in checksums:
        raise ChecksumError(f"No checksum found for file: {relative_path}")
        
    stored_hash = checksums[relative_path]
    current_hash = compute_file_sha256(filepath)
    
    return stored_hash == current_hash
