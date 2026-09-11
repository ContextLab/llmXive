import os
import sys
import yaml
import logging
from pathlib import Path
from typing import Dict, Any
from config import CONFIG
from utils.logging import get_logger
from utils.checksums import generate_all_checksums

logger = get_logger(__name__)

def load_checksums(checksum_file: Path) -> Dict[str, str]:
    """Load checksums from a text file (filename: hash format)."""
    checksums = {}
    if not checksum_file.exists():
        logger.warning(f"Checksum file not found: {checksum_file}")
        return checksums
    
    with open(checksum_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and ':' in line:
                # Format: "filename: hash" or "filename hash"
                parts = line.split(':')
                if len(parts) == 2:
                    filename, hash_val = parts
                    checksums[filename.strip()] = hash_val.strip()
                else:
                    # Fallback for space-separated
                    parts = line.split()
                    if len(parts) >= 2:
                        checksums[parts[0]] = parts[1]
    return checksums

def load_or_create_state(state_path: Path) -> Dict[str, Any]:
    """Load existing state file or create a new one."""
    if state_path.exists():
        with open(state_path, 'r') as f:
            try:
                return yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                logger.error(f"Error parsing existing state file: {e}")
                return {}
    else:
        # Ensure parent directory exists
        state_path.parent.mkdir(parents=True, exist_ok=True)
        return {
            "project_id": "PROJ-537-predicting-the-yield-strength-of-bcc-ste",
            "last_updated": None,
            "artifacts": {}
        }

def update_state_with_checksums(state: Dict[str, Any], checksums: Dict[str, str]) -> None:
    """Update the state dictionary with artifact hashes."""
    import datetime
    state["last_updated"] = datetime.datetime.now().isoformat()
    
    # Map relative paths to their hashes
    for filename, hash_val in checksums.items():
        # Normalize path separators
        norm_path = filename.replace('\\', '/')
        state["artifacts"][norm_path] = {
            "hash": hash_val,
            "type": "sha256"
        }
    
    logger.info(f"Updated state with {len(checksums)} artifact hashes")

def save_state(state: Dict[str, Any], state_path: Path) -> None:
    """Save the state dictionary to a YAML file."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    logger.info(f"State saved to {state_path}")

def main():
    """Main entry point for updating project state with artifact hashes."""
    logger.info("Starting state update process...")
    
    # Define paths
    checksum_file = CONFIG.DATA_PROVENANCE_DIR / "checksums.txt"
    state_file = CONFIG.ROOT_DIR / "state" / "projects" / "PROJ-537-predicting-the-yield-strength-of-bcc-ste.yaml"
    
    # Ensure directories exist
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Load checksums
    logger.info(f"Loading checksums from {checksum_file}")
    checksums = load_checksums(checksum_file)
    
    if not checksums:
        logger.warning("No checksums found. Ensure T019 has been completed successfully.")
        # We can still create the state file, just with empty artifacts
    
    # Load or create state
    state = load_or_create_state(state_file)
    
    # Update state with checksums
    update_state_with_checksums(state, checksums)
    
    # Save state
    save_state(state, state_file)
    
    logger.info("State update completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
