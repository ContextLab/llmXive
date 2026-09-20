import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

logger = logging.getLogger(__name__)

def compute_file_sha256(file_path: Union[str, Path]) -> str:
    """Computes the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_string_sha256(content: str) -> str:
    """Computes the SHA-256 hash of a string."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def verify_file_checksum(file_path: Union[str, Path], manifest: Dict[str, Any]) -> bool:
    """Verifies a file against a checksum manifest."""
    path = Path(file_path)
    filename = path.name
    
    if filename not in manifest.get('checksums', {}):
        logger.warning(f"No checksum found for {filename} in manifest.")
        return False
    
    expected_hash = manifest['checksums'][filename]['sha256']
    actual_hash = compute_file_sha256(path)
    
    if actual_hash == expected_hash:
        logger.info(f"Checksum verification passed for {filename}")
        return True
    else:
        logger.error(f"Checksum verification FAILED for {filename}. Expected: {expected_hash}, Got: {actual_hash}")
        return False

def generate_checksum_manifest(file_paths: List[Union[str, Path]]) -> Dict[str, Any]:
    """Generates a manifest of checksums for a list of files."""
    manifest = {
        "generated_by": "checksums.py",
        "files": [],
        "checksums": {}
    }
    
    for path in file_paths:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"File not found for checksum: {p}")
        
        file_hash = compute_file_sha256(p)
        manifest["files"].append(str(p))
        manifest["checksums"][p.name] = {
            "sha256": file_hash,
            "size": p.stat().st_size
        }
        
    return manifest

def verify_checksum_manifest(manifest_path: Union[str, Path]) -> bool:
    """Verifies all files in a manifest against their stored checksums."""
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    all_valid = True
    for filename, details in manifest.get('checksums', {}).items():
        # Assuming files are in the same directory as manifest or relative path logic
        # For simplicity, we assume the manifest stores relative paths or we search
        # In a real scenario, we'd store full paths or resolve relative to a root.
        # Here we assume the file exists in the current working directory or relative to manifest.
        file_path = Path(manifest_path).parent / filename
        if not file_path.exists():
            logger.error(f"File missing for checksum verification: {file_path}")
            all_valid = False
            continue
        
        if not verify_file_checksum(file_path, {"checksums": {filename: details}}):
            all_valid = False
    
    return all_valid

def check_code_drift(file_paths: List[Union[str, Path]], manifest: Dict[str, Any]) -> bool:
    """
    Checks if the code files have drifted from the expected state in the manifest.
    Returns True if no drift (or drift is acceptable), False if drift detected.
    """
    # In this context, we treat 'code drift' as a checksum mismatch of the generated artifacts
    # or source files if they were included in the manifest.
    # We verify the files against the provided manifest.
    for path in file_paths:
        p = Path(path)
        if p.name not in manifest.get('checksums', {}):
            logger.warning(f"File {p.name} not in manifest, skipping drift check.")
            continue
        
        if not verify_file_checksum(p, manifest):
            logger.error(f"Code drift detected: {p.name} has changed since manifest generation.")
            return False
    
    logger.info("Code drift check passed.")
    return True

# Import logging at the top level to avoid circular issues if any
import logging