"""
State Manager Module for llmXive.

Implements Constitution Principle V by tracking file integrity via SHA-256 hashes.
Scans 'data/' and 'code/' directories, computes hashes, and updates the state file.
"""
import hashlib
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from utils.logging import get_logger, error, info

logger = get_logger(__name__)

def get_project_root() -> Path:
    """Returns the absolute path to the project root."""
    # Assuming the script is run from code/ or code/utils/
    current_file = Path(__file__).resolve()
    # Navigate up: code/utils -> code -> root
    return current_file.parent.parent.parent

def calculate_sha256(file_path: Path) -> str:
    """
    Calculates the SHA-256 hash of a file's contents.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hex digest of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Failed to hash file {file_path}: {e}")
        raise

def scan_directory_for_hashes(directory: Path, base_path: Path) -> Dict[str, str]:
    """
    Recursively scans a directory and computes SHA-256 hashes for all files.
    
    Args:
        directory: The directory to scan.
        base_path: The base path to strip from the result keys (relative path).
        
    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes.
    """
    hashes = {}
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return hashes
    
    for root, _, files in os.walk(directory):
        for file in files:
            full_path = Path(root) / file
            # Calculate relative path from base_path (e.g., project root)
            try:
                rel_path = full_path.relative_to(base_path)
            except ValueError:
                # Should not happen if directory is under base_path, but safety check
                continue
            
            # Skip the state file itself to avoid circular dependency or changing hash during write
            if "state" in str(rel_path) and rel_path.suffix == ".yaml":
                continue
                
            try:
                file_hash = calculate_sha256(full_path)
                hashes[str(rel_path)] = file_hash
            except Exception as e:
                logger.error(f"Skipping file {rel_path} due to hash error: {e}")
                
    return hashes

def load_state_file(state_path: Path) -> Dict[str, Any]:
    """
    Loads the existing state file or returns a default structure if it doesn't exist.
    
    Args:
        state_path: Path to the state YAML file.
        
    Returns:
        Dictionary containing the state data.
    """
    if state_path.exists():
        try:
            with open(state_path, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load state file {state_path}: {e}")
            return {}
    return {
        "project_id": "PROJ-864-llmxive-follow-up-extending-improved-lar",
        "artifact_hashes": {},
        "last_updated": None
    }

def save_state_file(state_path: Path, state_data: Dict[str, Any]) -> None:
    """
    Saves the state dictionary to the YAML file.
    
    Args:
        state_path: Path to the state YAML file.
        state_data: Dictionary to save.
    """
    try:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(state_path, "w") as f:
            yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
        logger.info(f"State file saved to {state_path}")
    except Exception as e:
        logger.error(f"Failed to save state file {state_path}: {e}")
        raise

def get_artifact_hash(relative_path: str, current_hashes: Dict[str, str]) -> Optional[str]:
    """
    Retrieves the hash for a specific relative path from the current state.
    """
    return current_hashes.get(relative_path)

def update_project_state() -> Dict[str, Any]:
    """
    Main function to update the project state file.
    
    Scans 'data/' and 'code/' directories relative to the project root,
    computes SHA-256 hashes for all files, and updates the state file.
    
    Returns:
        The updated state dictionary.
    """
    project_root = get_project_root()
    data_dir = project_root / "data"
    code_dir = project_root / "code"
    state_dir = project_root / "state"
    state_file_path = state_dir / "projects" / "PROJ-864-llmxive-follow-up-extending-improved-lar.yaml"
    
    logger.info(f"Starting state update. Project root: {project_root}")
    
    # Load existing state
    state_data = load_state_file(state_file_path)
    
    # Initialize artifact_hashes if missing
    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}
        
    # Scan directories
    all_hashes = {}
    
    logger.info(f"Scanning directory: {data_dir}")
    all_hashes.update(scan_directory_for_hashes(data_dir, project_root))
    
    logger.info(f"Scanning directory: {code_dir}")
    all_hashes.update(scan_directory_for_hashes(code_dir, project_root))
    
    # Update state data
    state_data["artifact_hashes"] = all_hashes
    state_data["last_updated"] = str(Path.cwd().parent) # Placeholder for timestamp if needed, or use datetime
    from datetime import datetime
    state_data["last_updated"] = datetime.now().isoformat()
    
    # Save updated state
    save_state_file(state_file_path, state_data)
    
    logger.info(f"State update complete. Total artifacts tracked: {len(all_hashes)}")
    return state_data

def main():
    """CLI entry point for state manager."""
    try:
        update_project_state()
        print("State updated successfully.")
    except Exception as e:
        error(f"State update failed: {e}")
        raise

if __name__ == "__main__":
    main()