import json
import hashlib
import os
from pathlib import Path
from typing import Any, Dict, Optional

# Define the standard path for the manifest relative to project root
# Assuming the project root is the parent of 'code' based on the provided API surface structure
# However, the task specifies paths relative to project root under 'state/'.
# We will resolve this dynamically or assume a standard root.
# Based on T004, 'state/' is a directory at project root.
# The code structure provided is 'code/src/...'.
# We will assume the script runs from the project root or we resolve relative to the manifest location.

MANIFEST_FILENAME = "manifest.json"
MANIFEST_DIR = Path("state")
MANIFEST_PATH = MANIFEST_DIR / MANIFEST_FILENAME

def compute_file_hash(file_path: Path) -> Optional[str]:
    """
    Computes the SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hex digest string or None if file not found.
    """
    if not file_path.exists():
        return None
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        # Log error if needed, but return None for failure
        print(f"Error computing hash for {file_path}: {e}")
        return None

def load_manifest(manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Loads the manifest JSON file.
    
    Args:
        manifest_path: Optional path override. Defaults to MANIFEST_PATH.
        
    Returns:
        Dictionary containing manifest data. Returns empty structure if file missing.
    """
    path = manifest_path or MANIFEST_PATH
    if not path.exists():
        return {
            "initialized": False,
            "artifacts": {},
            "metadata": {
                "version": "1.0",
                "created_at": None,
                "updated_at": None
            }
        }
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # If corrupted, return empty structure to force re-initialization or error handling
        return {
            "initialized": False,
            "artifacts": {},
            "metadata": {}
        }

def save_manifest(manifest_data: Dict[str, Any], manifest_path: Optional[Path] = None) -> bool:
    """
    Saves the manifest dictionary to JSON.
    
    Args:
        manifest_data: The dictionary to save.
        manifest_path: Optional path override.
        
    Returns:
        True if successful, False otherwise.
    """
    path = manifest_path or MANIFEST_PATH
    try:
        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving manifest to {path}: {e}")
        return False

def initialize_manifest(manifest_path: Optional[Path] = None) -> bool:
    """
    Initializes a new manifest.json file if it doesn't exist or is empty/corrupted.
    Sets up the tracking structure for artifact hashes.
    
    Args:
        manifest_path: Optional path override.
        
    Returns:
        True if initialized or already valid, False on failure.
    """
    path = manifest_path or MANIFEST_PATH
    
    # Check if exists and is valid
    if path.exists():
        try:
            with open(path, "r") as f:
                data = json.load(f)
                if "artifacts" in data and isinstance(data["artifacts"], dict):
                    # Already initialized
                    return True
        except (json.JSONDecodeError, FileNotFoundError):
            pass # Proceed to re-initialize
    
    # Create new structure
    manifest_data = {
        "initialized": True,
        "metadata": {
            "version": "1.0",
            "created_at": str(Path.cwd()), # Or timestamp if preferred
            "updated_at": str(Path.cwd())
        },
        "artifacts": {}
    }
    
    return save_manifest(manifest_data, path)

def register_artifact(artifact_path: Path, manifest_path: Optional[Path] = None) -> bool:
    """
    Registers an artifact in the manifest by computing its hash.
    
    Args:
        artifact_path: Path to the artifact file.
        manifest_path: Optional path override.
        
    Returns:
        True if registered successfully, False otherwise.
    """
    path = manifest_path or MANIFEST_PATH
    manifest = load_manifest(path)
    
    if not manifest.get("initialized", False):
        # Auto-initialize if not done yet
        if not initialize_manifest(path):
            return False
        manifest = load_manifest(path)
    
    if not artifact_path.exists():
        print(f"Artifact not found: {artifact_path}")
        return False
    
    file_hash = compute_file_hash(artifact_path)
    if file_hash is None:
        return False
    
    # Use relative path for storage
    try:
        relative_path = str(artifact_path.relative_to(Path.cwd()))
    except ValueError:
        # If not relative to cwd, use absolute or just the filename
        relative_path = str(artifact_path)
    
    manifest["artifacts"][relative_path] = {
        "hash": file_hash,
        "registered_at": str(Path.cwd()) # Or timestamp
    }
    
    manifest["metadata"]["updated_at"] = str(Path.cwd())
    return save_manifest(manifest, path)

def verify_artifact(artifact_path: Path, manifest_path: Optional[Path] = None) -> bool:
    """
    Verifies an artifact's hash against the manifest.
    
    Args:
        artifact_path: Path to the artifact file.
        manifest_path: Optional path override.
        
    Returns:
        True if hash matches or artifact not in manifest, False if mismatch.
    """
    path = manifest_path or MANIFEST_PATH
    manifest = load_manifest(path)
    
    try:
        relative_path = str(artifact_path.relative_to(Path.cwd()))
    except ValueError:
        relative_path = str(artifact_path)
    
    if relative_path not in manifest.get("artifacts", {}):
        # Artifact not tracked, consider it valid (or log warning)
        return True
    
    stored_hash = manifest["artifacts"][relative_path].get("hash")
    if not stored_hash:
        return False
    
    current_hash = compute_file_hash(artifact_path)
    if current_hash is None:
        return False
    
    return current_hash == stored_hash
