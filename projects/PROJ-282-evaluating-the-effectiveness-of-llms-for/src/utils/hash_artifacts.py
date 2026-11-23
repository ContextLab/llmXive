import os
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.utils.config import get_project_root, get_config

# State file path relative to project root
STATE_FILE_PATH = "state/projects/PROJ-282-evaluating-the-effectiveness-of-llms-for.yaml"


def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")


def load_current_state() -> Dict[str, Any]:
    """
    Load the current project state from the state file.
    
    Returns:
        Dictionary containing the current state, or an empty dict if file missing.
    """
    project_root = get_project_root()
    state_file = project_root / STATE_FILE_PATH
    
    if not state_file.exists():
        return {}
    
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        # If state is corrupted or unreadable, start fresh
        return {}


def save_state(state: Dict[str, Any]) -> None:
    """
    Save the project state to the state file.
    
    Args:
        state: Dictionary containing the state to save.
    """
    project_root = get_project_root()
    state_file = project_root / STATE_FILE_PATH
    
    # Ensure directory exists
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, default=str)


def hash_directory(directory: Path, extensions: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Compute checksums for all files in a directory recursively.
    
    Args:
        directory: Path to the directory to hash.
        extensions: Optional list of file extensions to include (e.g., ['.csv', '.json']).
                    If None, all files are hashed.
                    
    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes.
    """
    if not directory.exists():
        return {}
    
    hashes = {}
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            if extensions is None or any(file_path.suffix == ext for ext in extensions):
                try:
                    rel_path = file_path.relative_to(directory)
                    hashes[str(rel_path)] = compute_sha256(file_path)
                except (ValueError, IOError):
                    # Skip files we can't process
                    continue
    return hashes


def generate_artifact_manifest(artifacts_dir: Path) -> Dict[str, Any]:
    """
    Generate a manifest of all artifacts in a directory.
    
    Args:
        artifacts_dir: Path to the artifacts directory.
        
    Returns:
        Dictionary containing metadata and checksums.
    """
    if not artifacts_dir.exists():
        return {
            "directory": str(artifacts_dir),
            "generated_at": datetime.utcnow().isoformat(),
            "files": {},
            "total_files": 0,
            "total_size_bytes": 0
        }
    
    files = {}
    total_size = 0
    
    for file_path in artifacts_dir.rglob("*"):
        if file_path.is_file():
            try:
                rel_path = str(file_path.relative_to(artifacts_dir))
                file_size = file_path.stat().st_size
                total_size += file_size
                file_hash = compute_sha256(file_path)
                
                files[rel_path] = {
                    "size_bytes": file_size,
                    "sha256": file_hash,
                    "last_modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                }
            except (IOError, ValueError):
                continue
    
    return {
        "directory": str(artifacts_dir),
        "generated_at": datetime.utcnow().isoformat(),
        "files": files,
        "total_files": len(files),
        "total_size_bytes": total_size
    }


def update_state_with_manifest(
    state: Dict[str, Any],
    manifest: Dict[str, Any],
    stage_name: str
) -> Dict[str, Any]:
    """
    Update the project state with a new artifact manifest.
    
    Args:
        state: Current project state dictionary.
        manifest: Artifact manifest to add.
        stage_name: Name of the pipeline stage that produced the artifacts.
        
    Returns:
        Updated state dictionary.
    """
    if "artifacts" not in state:
        state["artifacts"] = {}
    
    state["artifacts"][stage_name] = {
        "manifest": manifest,
        "updated_at": datetime.utcnow().isoformat()
    }
    
    # Update overall metadata
    state["last_hash_update"] = datetime.utcnow().isoformat()
    state["version"] = state.get("version", 0) + 1
    
    return state


def run_checksum_verification(
    current_state: Dict[str, Any],
    artifacts_dir: Path,
    stage_name: str
) -> Dict[str, Any]:
    """
    Verify that current artifacts match the stored state.
    
    Args:
        current_state: The saved project state.
        artifacts_dir: Path to the directory to verify.
        stage_name: Name of the stage to verify.
        
    Returns:
        Dictionary with verification results.
    """
    result = {
        "stage": stage_name,
        "verified_at": datetime.utcnow().isoformat(),
        "status": "unknown",
        "missing_files": [],
        "modified_files": [],
        "unchanged_files": []
    }
    
    if "artifacts" not in current_state or stage_name not in current_state["artifacts"]:
        result["status"] = "no_previous_state"
        return result
    
    stored_manifest = current_state["artifacts"][stage_name].get("manifest", {})
    stored_files = stored_manifest.get("files", {})
    
    if not stored_files:
        result["status"] = "no_stored_files"
        return result
    
    current_files = hash_directory(artifacts_dir)
    
    # Check for missing files
    for file_path in stored_files:
        if file_path not in current_files:
            result["missing_files"].append(file_path)
    
    # Check for modified or unchanged files
    for file_path, stored_info in stored_files.items():
        if file_path in current_files:
            current_hash = current_files[file_path]
            stored_hash = stored_info.get("sha256")
            
            if current_hash != stored_hash:
                result["modified_files"].append(file_path)
            else:
                result["unchanged_files"].append(file_path)
    
    # Determine overall status
    if result["missing_files"] or result["modified_files"]:
        result["status"] = "verification_failed"
    elif len(result["unchanged_files"]) == len(stored_files):
        result["status"] = "verified"
    else:
        result["status"] = "partial_verification"
    
    return result


def main():
    """
    Main entry point for the hash artifacts utility.
    
    This function:
    1. Loads the current project state.
    2. Generates manifests for processed and results directories.
    3. Updates the state with new manifests.
    4. Saves the updated state.
    5. Prints a summary of the operation.
    """
    project_root = get_project_root()
    
    # Define directories to hash
    processed_dir = project_root / "data" / "processed"
    results_dir = project_root / "data" / "results"
    
    print(f"Project Root: {project_root}")
    print(f"Processing directory: {processed_dir}")
    print(f"Results directory: {results_dir}")
    
    # Load current state
    state = load_current_state()
    print(f"Loaded state version: {state.get('version', 0)}")
    
    # Generate manifests
    processed_manifest = generate_artifact_manifest(processed_dir)
    results_manifest = generate_artifact_manifest(results_dir)
    
    print(f"\nProcessed artifacts: {processed_manifest['total_files']} files, {processed_manifest['total_size_bytes']} bytes")
    print(f"Results artifacts: {results_manifest['total_files']} files, {results_manifest['total_size_bytes']} bytes")
    
    # Update state
    state = update_state_with_manifest(state, processed_manifest, "processed_data")
    state = update_state_with_manifest(state, results_manifest, "results")
    
    # Save updated state
    save_state(state)
    
    print(f"\nState updated and saved to: {project_root / STATE_FILE_PATH}")
    print(f"New state version: {state['version']}")
    
    # Verify previous state (if exists)
    if state.get("version", 0) > 1:
        print("\nVerifying previous artifacts...")
        processed_verification = run_checksum_verification(state, processed_dir, "processed_data")
        results_verification = run_checksum_verification(state, results_dir, "results")
        
        print(f"Processed data verification: {processed_verification['status']}")
        if processed_verification['modified_files']:
            print(f"  Modified: {processed_verification['modified_files']}")
        if processed_verification['missing_files']:
            print(f"  Missing: {processed_verification['missing_files']}")
            
        print(f"Results verification: {results_verification['status']}")
        if results_verification['modified_files']:
            print(f"  Modified: {results_verification['modified_files']}")
        if results_verification['missing_files']:
            print(f"  Missing: {results_verification['missing_files']}")


if __name__ == "__main__":
    main()
