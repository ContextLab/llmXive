import os
import sys
import json
import logging
import yaml
from pathlib import Path
from typing import Dict, Any

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging import get_logger

logger = get_logger(__name__)

def load_checksums(checksum_path: Path) -> Dict[str, str]:
    """Load the checksums dictionary from the JSON file."""
    if not checksum_path.exists():
        raise FileNotFoundError(f"Checksum file not found: {checksum_path}")
    
    with open(checksum_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data.get('files', {})

def load_state(state_path: Path) -> Dict[str, Any]:
    """Load the state YAML file if it exists, otherwise return a default structure."""
    if not state_path.exists():
        logger.info(f"State file not found at {state_path}, creating new structure.")
        return {
            "project_id": "PROJ-487",
            "branch": "001-news-volume-anxiety",
            "artifacts": {
                "artifact_hashes": {}
            },
            "status": "in_progress",
            "updated": None
        }
    
    with open(state_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_state(state_path: Path, state: Dict[str, Any]) -> None:
    """Save the updated state to the YAML file."""
    # Ensure directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(state_path, 'w', encoding='utf-8') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"State file saved to {state_path}")

def update_artifact_hashes(state: Dict[str, Any], checksums: Dict[str, str]) -> Dict[str, Any]:
    """Update the artifact_hashes map in the state with new checksums."""
    if 'artifacts' not in state:
        state['artifacts'] = {}
    
    if 'artifact_hashes' not in state['artifacts']:
        state['artifacts']['artifact_hashes'] = {}
    
    current_hashes = state['artifacts']['artifact_hashes']
    
    for filename, md5_hash in checksums.items():
        current_hashes[filename] = md5_hash
        logger.info(f"Updated hash for {filename}: {md5_hash}")
    
    return state

def main():
    """Main entry point for updating the state file with artifact checksums."""
    # Define paths relative to project root
    checksum_file_path = project_root / "data" / "raw" / ".checksums.json"
    state_file_path = project_root / "state" / "projects" / "PROJ-487-the-impact-of-social-media-doomscrolling.yaml"
    
    logger.info(f"Starting state update process.")
    logger.info(f"Checksum source: {checksum_file_path}")
    logger.info(f"State target: {state_file_path}")
    
    try:
        # Load checksums
        checksums = load_checksums(checksum_file_path)
        logger.info(f"Loaded {len(checksums)} checksums.")
        
        if not checksums:
            logger.warning("No checksums found in the source file. State will not be updated.")
            return 1

        # Load current state
        state = load_state(state_file_path)
        
        # Update artifact hashes
        updated_state = update_artifact_hashes(state, checksums)
        
        # Save updated state
        save_state(state_file_path, updated_state)
        
        logger.info("State file updated successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in checksum file: {e}")
        return 1
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in state file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during state update: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())