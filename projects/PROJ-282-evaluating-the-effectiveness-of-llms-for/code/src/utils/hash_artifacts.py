import os
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.utils.logger import get_logger, log_artifact

logger = get_logger(__name__)

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATE_FILE_PATH = PROJECT_ROOT / "state" / "projects" / "PROJ-282-evaluating-the-effectiveness-of-llms-for.yaml"
# Ensure state directory exists
STATE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or unreadable.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
    except Exception as e:
        raise ValueError(f"Failed to read file {file_path}: {e}")
    
    return sha256_hash.hexdigest()

def load_current_state() -> Dict[str, Any]:
    """
    Load the existing state file if it exists, otherwise return a fresh state structure.
    
    Returns:
        Dictionary containing the current state.
    """
    if STATE_FILE_PATH.exists():
        try:
            with open(STATE_FILE_PATH, "r") as f:
                content = f.read().strip()
                if not content:
                    return {"artifacts": {}, "last_updated": None}
                return json.loads(content)
        except json.JSONDecodeError:
            logger.warning(f"State file {STATE_FILE_PATH} is corrupted. Resetting state.")
            return {"artifacts": {}, "last_updated": None}
    return {"artifacts": {}, "last_updated": None}

def save_state(state: Dict[str, Any]) -> None:
    """
    Save the state dictionary to the state file as JSON.
    
    Args:
        state: The state dictionary to save.
    """
    with open(STATE_FILE_PATH, "w") as f:
        json.dump(state, f, indent=2)
    logger.info(f"State saved to {STATE_FILE_PATH}")

def hash_directory(directory: Path, pattern: str = "*.csv") -> Dict[str, str]:
    """
    Recursively compute checksums for all files matching a pattern in a directory.
    
    Args:
        directory: Path to the directory to scan.
        pattern: Glob pattern to match files (e.g., "*.csv", "*.json").
        
    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes.
    """
    if not directory.exists():
        logger.warning(f"Directory not found: {directory}")
        return {}
    
    hashes = {}
    for file_path in directory.rglob(pattern):
        if file_path.is_file():
            try:
                rel_path = str(file_path.relative_to(PROJECT_ROOT))
                hashes[rel_path] = compute_sha256(file_path)
                logger.debug(f"Hashed: {rel_path}")
            except Exception as e:
                logger.error(f"Failed to hash {file_path}: {e}")
    return hashes

def generate_artifact_manifest(directories: List[Path], patterns: List[str] = ["*.csv", "*.json"]) -> Dict[str, Any]:
    """
    Generate a manifest of all artifacts in specified directories.
    
    Args:
        directories: List of directory paths to scan.
        patterns: List of glob patterns to match files.
        
    Returns:
        Dictionary containing the artifact manifest.
    """
    manifest = {
        "generated_at": datetime.utcnow().isoformat(),
        "artifacts": {}
    }
    
    for directory in directories:
        if not directory.exists():
            logger.warning(f"Skipping non-existent directory: {directory}")
            continue
        
        for pattern in patterns:
            hashes = hash_directory(directory, pattern)
            for rel_path, hash_val in hashes.items():
                manifest["artifacts"][rel_path] = {
                    "hash": hash_val,
                    "pattern": pattern
                }
    
    return manifest

def update_state_with_manifest(manifest: Dict[str, Any]) -> None:
    """
    Update the project state file with a new artifact manifest.
    
    Args:
        manifest: The manifest dictionary to merge into the state.
    """
    current_state = load_current_state()
    
    # Merge new artifacts, overwriting existing ones with same path
    if "artifacts" in manifest:
        current_state["artifacts"].update(manifest["artifacts"])
    
    current_state["last_updated"] = datetime.utcnow().isoformat()
    
    save_state(current_state)
    logger.info("State updated with new artifact manifest.")

def run_checksum_verification(directories: List[Path], patterns: List[str] = ["*.csv", "*.json"]) -> bool:
    """
    Run checksum verification against the stored state.
    
    Args:
        directories: List of directory paths to verify.
        patterns: List of glob patterns to match files.
        
    Returns:
        True if all checksums match, False otherwise.
    """
    current_state = load_current_state()
    stored_artifacts = current_state.get("artifacts", {})
    
    if not stored_artifacts:
        logger.warning("No stored state found. Skipping verification.")
        return False
    
    # Generate current manifest
    current_manifest = generate_artifact_manifest(directories, patterns)
    current_artifacts = current_manifest.get("artifacts", {})
    
    all_match = True
    for path, info in stored_artifacts.items():
        stored_hash = info.get("hash")
        current_hash = current_artifacts.get(path, {}).get("hash")
        
        if current_hash is None:
            logger.error(f"Missing file in current scan: {path}")
            all_match = False
        elif stored_hash != current_hash:
            logger.error(f"Checksum mismatch for {path}: stored={stored_hash}, current={current_hash}")
            all_match = False
        else:
            logger.debug(f"Verified: {path}")
    
    # Check for new files not in stored state
    for path in current_artifacts:
        if path not in stored_artifacts:
            logger.warning(f"New file detected (not in stored state): {path}")
    
    return all_match

def main():
    """
    Main entry point for the hash_artifacts utility.
    
    Usage:
        python src/utils/hash_artifacts.py [verify | update | report]
    
    Commands:
        verify: Compare current file hashes against stored state.
        update: Scan directories and update state with new hashes.
        report: Print current state summary.
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python src/utils/hash_artifacts.py [verify | update | report]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    # Define directories to scan based on project structure
    scan_dirs = [
        PROJECT_ROOT / "data" / "processed",
        PROJECT_ROOT / "data" / "results",
        PROJECT_ROOT / "data" / "human_review"
    ]
    
    if command == "verify":
        logger.info("Starting checksum verification...")
        success = run_checksum_verification(scan_dirs)
        if success:
            logger.info("Verification successful: All checksums match.")
            sys.exit(0)
        else:
            logger.error("Verification failed: Checksum mismatches detected.")
            sys.exit(1)
    
    elif command == "update":
        logger.info("Updating artifact manifest...")
        manifest = generate_artifact_manifest(scan_dirs)
        update_state_with_manifest(manifest)
        logger.info("Update complete.")
        sys.exit(0)
    
    elif command == "report":
        state = load_current_state()
        print(f"State File: {STATE_FILE_PATH}")
        print(f"Last Updated: {state.get('last_updated', 'Never')}")
        print(f"Total Artifacts: {len(state.get('artifacts', {}))}")
        for path, info in state.get("artifacts", {}).items():
            print(f"  - {path}: {info.get('hash', 'N/A')[:16]}...")
        sys.exit(0)
    
    else:
        print(f"Unknown command: {command}")
        print("Usage: python src/utils/hash_artifacts.py [verify | update | report]")
        sys.exit(1)

if __name__ == "__main__":
    main()
