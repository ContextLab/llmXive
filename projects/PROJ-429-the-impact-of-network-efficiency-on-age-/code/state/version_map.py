"""
Version Map Management for llmXive Pipeline.

Implements Constitution Principle V: Traceability and Reproducibility.
Manages SHA-256 hashes of source code and data artifacts, along with 
timestamps for version tracking.
"""
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Project root relative to this file's location (code/state/)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Default paths for version map storage
DEFAULT_MAP_PATH = PROJECT_ROOT / "state" / "version_map.json"
DEFAULT_SOURCE_DIRS = [
    "code",
    "specs",
    "contracts"
]
DEFAULT_DATA_DIRS = [
    "data/processed",
    "data/results"
]


def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal SHA-256 hash string.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()


def compute_directory_hash(dir_path: Path, extensions: Optional[List[str]] = None) -> str:
    """
    Compute a composite SHA-256 hash for a directory by hashing all files within it.
    
    The hash is computed by concatenating the sorted relative paths and their 
    individual file hashes, then hashing the result.
    
    Args:
        dir_path: Path to the directory.
        extensions: Optional list of file extensions to include (e.g., ['.py', '.yaml']).
                    If None, all files are included.
                    
    Returns:
        Hexadecimal SHA-256 hash string for the directory content.
        
    Raises:
        FileNotFoundError: If the directory does not exist.
    """
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {dir_path}")
    
    hasher = hashlib.sha256()
    files = []
    
    for root, _, filenames in os.walk(dir_path):
        for filename in filenames:
            file_path = Path(root) / filename
            if extensions:
                if any(filename.endswith(ext) for ext in extensions):
                    files.append(file_path)
            else:
                files.append(file_path)
    
    # Sort files to ensure deterministic order
    files.sort(key=lambda p: str(p.relative_to(dir_path)))
    
    for file_path in files:
        rel_path = file_path.relative_to(dir_path)
        try:
            file_hash = compute_file_hash(file_path)
            # Include relative path in the hash to detect moves/renames
            hasher.update(f"{rel_path}:{file_hash}".encode('utf-8'))
        except (FileNotFoundError, PermissionError):
            # Skip inaccessible files
            continue
    
    return hasher.hexdigest()


def get_timestamp() -> str:
    """
    Get current UTC timestamp in ISO format.
    
    Returns:
        ISO 8601 formatted timestamp string.
    """
    return datetime.utcnow().isoformat() + "Z"


def load_version_map(map_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the existing version map from disk.
    
    Args:
        map_path: Path to the version map file. Defaults to DEFAULT_MAP_PATH.
                
    Returns:
        Dictionary containing the version map data.
        Returns an empty map structure if file does not exist.
    """
    if map_path is None:
        map_path = DEFAULT_MAP_PATH
    
    if not map_path.exists():
        return {
            "version": 1,
            "last_updated": None,
            "sources": {},
            "data": {},
            "artifacts": {}
        }
    
    with open(map_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_version_map(data: Dict[str, Any], map_path: Optional[Path] = None) -> None:
    """
    Save the version map to disk.
    
    Args:
        data: Version map dictionary to save.
        map_path: Path to the version map file. Defaults to DEFAULT_MAP_PATH.
    """
    if map_path is None:
        map_path = DEFAULT_MAP_PATH
    
    # Ensure parent directory exists
    map_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(map_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def update_source_hashes(
    map_data: Dict[str, Any],
    source_dirs: Optional[List[str]] = None,
    extensions: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Update hashes for source code directories in the version map.
    
    Args:
        map_data: Current version map data.
        source_dirs: List of relative directory paths to hash. Defaults to DEFAULT_SOURCE_DIRS.
        extensions: Optional list of file extensions to include.
        
    Returns:
        Updated version map data.
    """
    if source_dirs is None:
        source_dirs = DEFAULT_SOURCE_DIRS
    
    if "sources" not in map_data:
        map_data["sources"] = {}
    
    for dir_rel_path in source_dirs:
        dir_path = PROJECT_ROOT / dir_rel_path
        if dir_path.exists():
            try:
                dir_hash = compute_directory_hash(dir_path, extensions)
                map_data["sources"][dir_rel_path] = {
                    "hash": dir_hash,
                    "updated_at": get_timestamp()
                }
            except (FileNotFoundError, NotADirectoryError) as e:
                # Log but continue with other directories
                print(f"Warning: Could not hash {dir_rel_path}: {e}")
    
    return map_data


def update_data_hashes(
    map_data: Dict[str, Any],
    data_dirs: Optional[List[str]] = None,
    extensions: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Update hashes for processed data directories in the version map.
    
    Args:
        map_data: Current version map data.
        data_dirs: List of relative directory paths to hash. Defaults to DEFAULT_DATA_DIRS.
        extensions: Optional list of file extensions to include.
        
    Returns:
        Updated version map data.
    """
    if data_dirs is None:
        data_dirs = DEFAULT_DATA_DIRS
    
    if "data" not in map_data:
        map_data["data"] = {}
    
    for dir_rel_path in data_dirs:
        dir_path = PROJECT_ROOT / dir_rel_path
        if dir_path.exists():
            try:
                dir_hash = compute_directory_hash(dir_path, extensions)
                map_data["data"][dir_rel_path] = {
                    "hash": dir_hash,
                    "updated_at": get_timestamp()
                }
            except (FileNotFoundError, NotADirectoryError) as e:
                print(f"Warning: Could not hash {dir_rel_path}: {e}")
    
    return map_data


def register_artifact(
    map_data: Dict[str, Any],
    artifact_name: str,
    artifact_path: Path,
    artifact_type: str = "output"
) -> Dict[str, Any]:
    """
    Register a specific artifact file in the version map.
    
    Args:
        map_data: Current version map data.
        artifact_name: Human-readable name for the artifact.
        artifact_path: Absolute or relative path to the artifact file.
        artifact_type: Type of artifact (e.g., 'output', 'config', 'report').
        
    Returns:
        Updated version map data.
        
    Raises:
        FileNotFoundError: If the artifact file does not exist.
    """
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")
    
    if "artifacts" not in map_data:
        map_data["artifacts"] = {}
    
    file_hash = compute_file_hash(artifact_path)
    
    map_data["artifacts"][artifact_name] = {
        "path": str(artifact_path.relative_to(PROJECT_ROOT)),
        "hash": file_hash,
        "type": artifact_type,
        "updated_at": get_timestamp()
    }
    
    return map_data


def generate_trace_id(map_data: Dict[str, Any]) -> str:
    """
    Generate a unique trace ID based on the current state of the version map.
    
    This ID can be used to trace the exact code and data state that produced
    a specific result.
    
    Args:
        map_data: Version map data to hash.
        
    Returns:
        SHA-256 hash string representing the trace ID.
    """
    # Create a deterministic string representation of the map
    # Exclude timestamps to ensure the ID reflects content, not just time
    content_for_hash = json.dumps(map_data, sort_keys=True, default=str)
    trace_hash = hashlib.sha256(content_for_hash.encode('utf-8')).hexdigest()
    return trace_hash


def update_version_map(
    map_path: Optional[Path] = None,
    source_dirs: Optional[List[str]] = None,
    data_dirs: Optional[List[str]] = None,
    artifacts: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Main function to update the version map with current hashes and register artifacts.
    
    Args:
        map_path: Path to the version map file.
        source_dirs: List of source directories to hash.
        data_dirs: List of data directories to hash.
        artifacts: List of artifact dictionaries with 'name' and 'path' keys.
        
    Returns:
        Updated version map data.
    """
    # Load existing map
    map_data = load_version_map(map_path)
    
    # Update source hashes
    map_data = update_source_hashes(map_data, source_dirs)
    
    # Update data hashes
    map_data = update_data_hashes(map_data, data_dirs)
    
    # Register individual artifacts
    if artifacts:
        if "artifacts" not in map_data:
            map_data["artifacts"] = {}
        
        for artifact in artifacts:
            try:
                artifact_path = Path(artifact["path"])
                if not artifact_path.is_absolute():
                    artifact_path = PROJECT_ROOT / artifact_path
                
                map_data = register_artifact(
                    map_data,
                    artifact["name"],
                    artifact_path,
                    artifact.get("type", "output")
                )
            except KeyError as e:
                print(f"Warning: Invalid artifact entry missing key {e}")
            except FileNotFoundError as e:
                print(f"Warning: {e}")
    
    # Update timestamp
    map_data["last_updated"] = get_timestamp()
    
    # Save updated map
    save_version_map(map_data, map_path)
    
    return map_data


def main():
    """
    Command-line entry point for updating the version map.
    
    Usage:
        python -m code.state.version_map
        
    This will update hashes for default source and data directories,
    and save the updated map to state/version_map.json.
    """
    print("Updating version map...")
    
    try:
        map_data = update_version_map(
            source_dirs=DEFAULT_SOURCE_DIRS,
            data_dirs=DEFAULT_DATA_DIRS
        )
        
        print(f"Version map updated successfully.")
        print(f"Last updated: {map_data['last_updated']}")
        print(f"Source directories tracked: {len(map_data.get('sources', {}))}")
        print(f"Data directories tracked: {len(map_data.get('data', {}))}")
        print(f"Artifacts registered: {len(map_data.get('artifacts', {}))}")
        
        # Generate and print a trace ID for this state
        trace_id = generate_trace_id(map_data)
        print(f"Current trace ID: {trace_id}")
        
    except Exception as e:
        print(f"Error updating version map: {e}")
        raise


if __name__ == "__main__":
    main()