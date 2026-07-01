import hashlib
from pathlib import Path
from typing import Union
from .logger import get_logger
from .config import get_project_root

logger = get_logger(__name__)

def compute_checksum(file_path: Union[str, Path]) -> str:
    """Compute MD5 checksum of a file."""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def verify_checksum(file_path: Union[str, Path], expected_checksum: str) -> bool:
    """Verify file checksum against expected value."""
    actual = compute_checksum(file_path)
    return actual == expected_checksum

def generate_checksum_manifest(directory: Union[str, Path]) -> dict:
    """Generate a manifest of checksums for all files in a directory."""
    directory = Path(directory)
    manifest = {}
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(directory)
            manifest[str(relative_path)] = compute_checksum(file_path)
    return manifest
