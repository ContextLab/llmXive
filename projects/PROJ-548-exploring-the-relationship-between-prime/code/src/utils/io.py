import hashlib
import os
from pathlib import Path
from typing import Optional, Dict, Any
import yaml
import time

# Path constants relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATE_FILE_PATH = PROJECT_ROOT / "state" / "state.yaml"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        Hexadecimal string of the checksum.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_func = hashlib.new(algorithm)
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception as e:
        raise IOError(f"Failed to compute checksum for {file_path}: {e}")

def compute_directory_checksum(dir_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute a deterministic checksum for a directory by hashing all files recursively.
    The checksum depends on relative file paths and their contents.
    
    Args:
        dir_path: Path to the directory.
        algorithm: Hash algorithm to use.
        
    Returns:
        Hexadecimal string of the directory checksum.
        
    Raises:
        FileNotFoundError: If the directory does not exist.
    """
    if not dir_path.exists() or not dir_path.is_dir():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    
    dir_hash = hashlib.new(algorithm)
    # Sort files to ensure deterministic order
    files = sorted(dir_path.rglob("*"))
    
    for file_path in files:
        if file_path.is_file():
          # Include relative path in the hash
          rel_path = file_path.relative_to(dir_path)
          dir_hash.update(rel_path.as_posix().encode("utf-8"))
          # Include file content hash
          file_content_hash = compute_file_checksum(file_path, algorithm)
          dir_hash.update(file_content_hash.encode("utf-8"))
          
    return dir_hash.hexdigest()

def load_state() -> Dict[str, Any]:
    """
    Load the state.yaml file.
    
    Returns:
        Dictionary containing state data.
        
    Raises:
        FileNotFoundError: If state.yaml does not exist.
    """
    if not STATE_FILE_PATH.exists():
        # Initialize with default structure if missing
        return {
            "version": "1.0",
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "data_checksums": {},
            "pipeline_status": "pending"
        }
    
    with open(STATE_FILE_PATH, "r") as f:
        return yaml.safe_load(f) or {}

def save_state(state: Dict[str, Any]) -> None:
    """
    Save the state dictionary to state.yaml.
    
    Args:
        state: Dictionary to save.
    """
    state["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    STATE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE_PATH, "w") as f:
        yaml.safe_dump(state, f, sort_keys=False)

def update_state_checksums() -> Dict[str, Any]:
    """
    Scan processed data files, compute their checksums, and update state.yaml.
    
    This function implements the core requirement of T008:
    "Implement checksumming logic in src/utils/io.py for state.yaml updates on data changes"
    
    Returns:
        A summary dictionary of changes made.
    """
    state = load_state()
    current_checksums = {}
    changes = {"added": [], "updated": [], "removed": []}
    
    if not PROCESSED_DATA_DIR.exists():
        # Create directory if it doesn't exist
        PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        state["data_checksums"] = {}
        save_state(state)
        return changes
    
    # Scan all files in the processed directory
    for file_path in PROCESSED_DATA_DIR.rglob("*"):
        if file_path.is_file():
            rel_path = str(file_path.relative_to(PROCESSED_DATA_DIR))
            try:
                checksum = compute_file_checksum(file_path)
                current_checksums[rel_path] = {
                    "checksum": checksum,
                    "size": file_path.stat().st_size,
                    "mtime": file_path.stat().st_mtime
                }
            except Exception as e:
                # Log error but continue processing other files
                print(f"Warning: Could not checksum {file_path}: {e}")
    
    # Compare with previous state
    previous_checksums = state.get("data_checksums", {})
    
    # Detect added/updated files
    for path, info in current_checksums.items():
        if path not in previous_checksums:
            changes["added"].append(path)
        elif previous_checksums[path]["checksum"] != info["checksum"]:
            changes["updated"].append(path)
    
    # Detect removed files
    for path in previous_checksums:
        if path not in current_checksums:
            changes["removed"].append(path)
    
    # Update state
    state["data_checksums"] = current_checksums
    state["checksum_version"] = state.get("checksum_version", 0) + 1
    save_state(state)
    
    return changes

def verify_data_integrity() -> bool:
    """
    Verify that all files recorded in state.yaml still exist and match their checksums.
    
    Returns:
        True if all files match, False otherwise.
    """
    state = load_state()
    checksums = state.get("data_checksums", {})
    
    if not checksums:
        return True  # No data to verify
    
    all_valid = True
    for rel_path, info in checksums.items():
        file_path = PROCESSED_DATA_DIR / rel_path
        if not file_path.exists():
            print(f"Integrity check failed: File missing {file_path}")
            all_valid = False
            continue
        
        try:
            current_checksum = compute_file_checksum(file_path)
            if current_checksum != info["checksum"]:
                print(f"Integrity check failed: Checksum mismatch for {file_path}")
                all_valid = False
        except Exception as e:
            print(f"Integrity check failed: Error reading {file_path}: {e}")
            all_valid = False
            
    return all_valid

def get_data_change_summary() -> str:
    """
    Generate a human-readable summary of recent data changes.
    
    Returns:
        Formatted string describing changes.
    """
    changes = update_state_checksums()
    lines = [
        f"Data Change Summary ({time.strftime('%Y-%m-%d %H:%M:%S')}):",
        f"  Added: {len(changes['added'])} files",
        f"  Updated: {len(changes['updated'])} files",
        f"  Removed: {len(changes['removed'])} files"
    ]
    
    if changes["added"]:
        lines.append("  Added files:")
        for f in changes["added"][:5]:  # Limit to first 5 for readability
            lines.append(f"    - {f}")
        if len(changes["added"]) > 5:
            lines.append(f"    ... and {len(changes['added']) - 5} more")
            
    if changes["updated"]:
        lines.append("  Updated files:")
        for f in changes["updated"][:5]:
            lines.append(f"    - {f}")
            
    if changes["removed"]:
        lines.append("  Removed files:")
        for f in changes["removed"][:5]:
            lines.append(f"    - {f}")
            
    return "\n".join(lines)
