"""
State management module for tracking content hashes of project artifacts.

This module provides functionality to compute SHA-256 hashes of files,
scan directories for relevant artifacts, and maintain a persistent
state.yaml file that tracks the current state of the project.
"""
import hashlib
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

STATE_FILE = Path("state.yaml")
# Define which directories to scan for artifacts
ARTIFACT_DIRS = [
    Path("data/raw"),
    Path("data/processed"),
    Path("models"),
    Path("artifacts/reports"),
    Path("artifacts/figures"),
    Path("data")  # For metadata.yaml
]
# File extensions to include in hash tracking
TRACKED_EXTENSIONS = {'.json', '.parquet', '.csv', '.png', '.yaml', '.yml', '.txt', '.pkl'}


def compute_sha256(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash
        
    Returns:
        Hexadecimal string of the SHA-256 hash
        
    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If the file cannot be read
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks for large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise


def scan_directory(base_dir: Path) -> Dict[str, str]:
    """
    Scan a directory for tracked files and compute their hashes.
    
    Args:
        base_dir: Base directory to scan
        
    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes
    """
    hashes = {}
    
    if not base_dir.exists():
        logger.warning(f"Directory does not exist, skipping: {base_dir}")
        return hashes
    
    for file_path in base_dir.rglob('*'):
        if file_path.is_file():
            # Check if file has a tracked extension
            if file_path.suffix.lower() in TRACKED_EXTENSIONS:
                try:
                    relative_path = file_path.relative_to(Path.cwd())
                    file_hash = compute_sha256(file_path)
                    hashes[str(relative_path)] = file_hash
                    logger.debug(f"Hashed: {relative_path}")
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
    
    return hashes


def load_state(state_file: Path = STATE_FILE) -> Dict[str, Any]:
    """
    Load the current state from state.yaml.
    
    Args:
        state_file: Path to the state file
        
    Returns:
        Dictionary containing the current state, or empty dict if file doesn't exist
    """
    if not state_file.exists():
        logger.info("No existing state file found. Starting fresh.")
        return {
            "last_updated": None,
            "artifacts": {},
            "pipeline_runs": []
        }
    
    try:
        with open(state_file, 'r') as f:
            # Simple YAML-like parsing for our specific format
            content = f.read()
            # If it's valid JSON, use json.loads
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Otherwise, try to parse as simple YAML
                # For now, return empty state if we can't parse
                logger.warning("Could not parse state file. Starting fresh.")
                return {
                    "last_updated": None,
                    "artifacts": {},
                    "pipeline_runs": []
                }
    except Exception as e:
        logger.error(f"Error loading state file: {e}")
        return {
            "last_updated": None,
            "artifacts": {},
            "pipeline_runs": []
        }


def save_state(state: Dict[str, Any], state_file: Path = STATE_FILE) -> None:
    """
    Save the current state to state.yaml.
    
    Args:
        state: Dictionary containing the state to save
        state_file: Path to the state file
    """
    try:
        # Ensure parent directory exists
        state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to JSON for reliable serialization
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
        
        logger.info(f"State saved to {state_file}")
    except Exception as e:
        logger.error(f"Error saving state file: {e}")
        raise


def verify_hashes(current_hashes: Dict[str, str], previous_hashes: Dict[str, str]) -> Dict[str, List[str]]:
    """
    Compare current hashes with previous hashes to identify changes.
    
    Args:
        current_hashes: Current file hashes
        previous_hashes: Previous file hashes
        
    Returns:
        Dictionary with keys 'added', 'modified', 'deleted' containing lists of file paths
    """
    changes = {
        'added': [],
        'modified': [],
        'deleted': []
    }
    
    current_files = set(current_hashes.keys())
    previous_files = set(previous_hashes.keys())
    
    # Files that are new
    changes['added'] = list(current_files - previous_files)
    
    # Files that are deleted
    changes['deleted'] = list(previous_files - current_files)
    
    # Files that might be modified
    for file_path in current_files & previous_files:
        if current_hashes[file_path] != previous_hashes[file_path]:
            changes['modified'].append(file_path)
    
    return changes


def main() -> None:
    """
    Main function to update the state.yaml file with current content hashes.
    
    This function:
    1. Loads the previous state
    2. Scans all tracked directories for artifacts
    3. Computes SHA-256 hashes for all tracked files
    4. Compares with previous state to identify changes
    5. Updates the state file with new hashes and metadata
    6. Logs a summary of changes
    """
    logger.info("Starting state update...")
    
    # Load previous state
    previous_state = load_state()
    previous_hashes = previous_state.get('artifacts', {})
    
    # Scan all artifact directories
    all_hashes = {}
    for art_dir in ARTIFACT_DIRS:
        dir_hashes = scan_directory(art_dir)
        all_hashes.update(dir_hashes)
    
    # Verify hashes against previous state
    changes = verify_hashes(all_hashes, previous_hashes)
    
    # Update state
    current_state = {
        "last_updated": datetime.now().isoformat(),
        "artifacts": all_hashes,
        "pipeline_runs": previous_state.get('pipeline_runs', []) + [{
            "timestamp": datetime.now().isoformat(),
            "changes": {
                "added_count": len(changes['added']),
                "modified_count": len(changes['modified']),
                "deleted_count": len(changes['deleted'])
            }
        }]
    }
    
    # Save updated state
    save_state(current_state)
    
    # Log summary
    logger.info("State update completed!")
    logger.info(f"  Total artifacts tracked: {len(all_hashes)}")
    logger.info(f"  Added: {len(changes['added'])}")
    logger.info(f"  Modified: {len(changes['modified'])}")
    logger.info(f"  Deleted: {len(changes['deleted'])}")
    
    if changes['added']:
        logger.info(f"  New files: {', '.join(changes['added'])}")
    if changes['modified']:
        logger.info(f"  Modified files: {', '.join(changes['modified'])}")
    if changes['deleted']:
        logger.info(f"  Deleted files: {', '.join(changes['deleted'])}")


if __name__ == "__main__":
    main()
