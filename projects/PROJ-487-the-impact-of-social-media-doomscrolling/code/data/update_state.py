import os
import sys
import json
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path to resolve imports correctly
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from utils.logging import get_logger

logger = get_logger(__name__)

def load_checksums(checksum_file_path: Path) -> Dict[str, str]:
    """
    Load MD5 checksums from a JSON file.
    
    Args:
        checksum_file_path: Path to the .checksums.json file
        
    Returns:
        Dictionary mapping filenames to their MD5 checksums
    """
    if not checksum_file_path.exists():
        logger.error(f"Checksum file not found: {checksum_file_path}")
        return {}
    
    try:
        with open(checksum_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"Loaded checksums from {checksum_file_path}")
            return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse checksum file: {e}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error loading checksums: {e}")
        return {}

def load_state(state_file_path: Path) -> Dict[str, Any]:
    """
    Load the current project state from a YAML file.
    
    Args:
        state_file_path: Path to the state YAML file
        
    Returns:
        Dictionary representing the project state
    """
    if not state_file_path.exists():
        logger.warning(f"State file not found at {state_file_path}. Creating new state.")
        return {
            "project_id": "PROJ-487",
            "branch": "001-news-volume-anxiety",
            "artifact_hashes": {}
        }
    
    try:
        with open(state_file_path, 'r', encoding='utf-8') as f:
            state = yaml.safe_load(f)
            if state is None:
                state = {
                    "project_id": "PROJ-487",
                    "branch": "001-news-volume-anxiety",
                    "artifact_hashes": {}
                }
            logger.info(f"Loaded existing state from {state_file_path}")
            return state
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse state file: {e}")
        # Return a minimal valid state if parsing fails
        return {
            "project_id": "PROJ-487",
            "branch": "001-news-volume-anxiety",
            "artifact_hashes": {}
        }
    except Exception as e:
        logger.error(f"Unexpected error loading state: {e}")
        return {
            "project_id": "PROJ-487",
            "branch": "001-news-volume-anxiety",
            "artifact_hashes": {}
        }

def save_state(state_file_path: Path, state: Dict[str, Any]) -> bool:
    """
    Save the updated state to a YAML file.
    
    Args:
        state_file_path: Path to save the state file
        state: Dictionary representing the project state
        
    Returns:
        True if save was successful, False otherwise
    """
    try:
        # Ensure directory exists
        state_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(state_file_path, 'w', encoding='utf-8') as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
        logger.info(f"Successfully saved state to {state_file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save state: {e}")
        return False

def update_artifact_hashes(
    state: Dict[str, Any], 
    checksums: Dict[str, str], 
    file_paths: list
) -> Dict[str, Any]:
    """
    Update the artifact_hashes map in the state with checksums for specific files.
    
    Args:
        state: Current project state dictionary
        checksums: Dictionary of filename -> checksum
        file_paths: List of file paths (relative or absolute) to update in state
        
    Returns:
        Updated state dictionary
    """
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}
    
    updated_count = 0
    for file_path in file_paths:
        # Extract just the filename for the key
        filename = os.path.basename(file_path)
        if filename in checksums:
            state["artifact_hashes"][filename] = checksums[filename]
            updated_count += 1
            logger.info(f"Updated hash for {filename}: {checksums[filename]}")
        else:
            logger.warning(f"Checksum not found for {filename} in checksums file")
    
    logger.info(f"Updated {updated_count} artifact hashes in state")
    return state

def main():
    """
    Main entry point for updating the project state file with artifact checksums.
    
    This script:
    1. Loads checksums from data/processed/.checksums.json (or data/raw/.checksums.json if exists)
    2. Loads the current state from state/projects/PROJ-487-the-impact-of-social-media-doomscrolling.yaml
    3. Updates the artifact_hashes map with checksums for gdelt_events.csv and google_trends.csv
    4. Saves the updated state back to the file
    """
    # Define paths
    project_root = Path(__file__).resolve().parents[2]
    
    # Check for checksums in processed first, then raw
    processed_checksums = project_root / "data" / "processed" / ".checksums.json"
    raw_checksums = project_root / "data" / "raw" / ".checksums.json"
    
    checksums = {}
    if processed_checksums.exists():
        checksums = load_checksums(processed_checksums)
    elif raw_checksums.exists():
        checksums = load_checksums(raw_checksums)
    else:
        # If no checksums file exists, try to calculate them from the raw files
        logger.warning("No checksums file found. Attempting to calculate from raw files...")
        raw_gdelt = project_root / "data" / "raw" / "gdelt_events.csv"
        raw_trends = project_root / "data" / "raw" / "google_trends.csv"
        
        if raw_gdelt.exists():
            import hashlib
            with open(raw_gdelt, 'rb') as f:
                checksums['gdelt_events.csv'] = hashlib.md5(f.read()).hexdigest()
        
        if raw_trends.exists():
            import hashlib
            with open(raw_trends, 'rb') as f:
                checksums['google_trends.csv'] = hashlib.md5(f.read()).hexdigest()
        
        if not checksums:
            logger.error("Could not find or calculate checksums for required files.")
            sys.exit(1)

    state_file = project_root / "state" / "projects" / "PROJ-487-the-impact-of-social-media-doomscrolling.yaml"
    
    # Load current state
    state = load_state(state_file)
    
    # Files to update in the state
    files_to_update = ["gdelt_events.csv", "google_trends.csv"]
    
    # Update artifact hashes
    updated_state = update_artifact_hashes(state, checksums, files_to_update)
    
    # Save updated state
    if save_state(state_file, updated_state):
        logger.info("State file updated successfully.")
        # Print the updated artifact hashes for verification
        logger.info(f"Updated artifact hashes: {updated_state.get('artifact_hashes', {})}")
        sys.exit(0)
    else:
        logger.error("Failed to update state file.")
        sys.exit(1)

if __name__ == "__main__":
    main()