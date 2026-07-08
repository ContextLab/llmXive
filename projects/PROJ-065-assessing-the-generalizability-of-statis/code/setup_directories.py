import os
import hashlib
from pathlib import Path
from typing import Optional

def ensure_directory_structure(base_path: Optional[str] = None) -> dict:
    """
    Creates the required directory structure for the project and generates
    SHA-256 checksums for the root data directories to ensure integrity.
    
    Args:
        base_path: Optional root path. Defaults to the project root relative
                   to this file's location (two levels up from code/).
    
    Returns:
        dict: A mapping of directory names to their absolute paths.
    """
    if base_path is None:
        # Assume this file is at code/setup_directories.py
        # Project root is two levels up
        base_path = Path(__file__).resolve().parent.parent
    
    base_path = Path(base_path)
    
    # Define relative paths based on project structure
    # data/raw, data/processed, outputs (which contains figures and reports)
    paths = {
        "data_raw": base_path / "data" / "raw",
        "data_processed": base_path / "data" / "processed",
        "outputs": base_path / "outputs",
        "outputs_figures": base_path / "outputs" / "figures",
        "outputs_reports": base_path / "outputs" / "reports",
    }
    
    # Create directories
    created = []
    for name, path in paths.items():
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(name)
        else:
            created.append(f"{name}_exists")
    
    # Generate checksums for the root data directories
    # We checksum the directory structure itself (list of files) to ensure
    # no files are added/removed unexpectedly later, or simply record the
    # state of the empty directories as a baseline.
    checksums = {}
    for name, path in paths.items():
        if name.startswith("data_"):
            checksum = _calculate_directory_checksum(path)
            checksums[name] = checksum
    
    return {
        "paths": {k: str(v) for k, v in paths.items()},
        "created": created,
        "checksums": checksums
    }

def _calculate_directory_checksum(dir_path: Path) -> str:
    """
    Calculates a SHA-256 checksum of the directory's contents.
    For empty directories, it returns a hash of the empty string.
    For non-empty, it hashes the sorted list of relative file paths
    concatenated with a placeholder (since we don't read file contents here).
    """
    hasher = hashlib.sha256()
    
    if not dir_path.exists():
        return "directory_missing"
    
    # Get all files and directories relative to the target
    items = []
    for item in dir_path.rglob("*"):
        rel = item.relative_to(dir_path)
        # Include type indicator (f for file, d for dir) to be safe
        prefix = "f" if item.is_file() else "d"
        items.append(f"{prefix}:{rel}")
    
    items.sort()
    content_str = "\n".join(items)
    hasher.update(content_str.encode('utf-8'))
    
    return hasher.hexdigest()
