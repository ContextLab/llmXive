"""
T020: Update project state with artifact hashes.

Reads checksums from data/provenance/checksums.txt and updates
state/projects/PROJ-537-predicting-the-yield-strength-of-bcc-ste.yaml
with the artifact hashes.
"""
import os
import sys
import yaml
import logging
from pathlib import Path
from typing import Dict, Any

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import CONFIG
from utils.logging import get_logger

logger = get_logger(__name__)


def load_checksums(checksum_file: Path) -> Dict[str, str]:
    """
    Load checksums from the generated checksums.txt file.
    
    Expected format:
    <hash>  <relative_path>
    """
    checksums = {}
    if not checksum_file.exists():
        logger.warning(f"Checksum file not found: {checksum_file}")
        return checksums
    
    with open(checksum_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split(None, 1)
            if len(parts) == 2:
                hash_val, file_path = parts
                checksums[file_path] = hash_val
            else:
                logger.warning(f"Malformed checksum line: {line}")
    
    return checksums


def load_or_create_state(state_file: Path) -> Dict[str, Any]:
    """Load existing state file or create a new one with project metadata."""
    if state_file.exists():
        with open(state_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    # Create new state structure
    return {
        "project_id": "PROJ-537-predicting-the-yield-strength-of-bcc-ste",
        "project_name": "Predicting the Yield Strength of BCC Steels",
        "status": "in_progress",
        "last_updated": None,
        "artifacts": {}
    }


def update_state_with_checksums(state: Dict[str, Any], checksums: Dict[str, str]) -> Dict[str, Any]:
    """Update state dictionary with artifact hashes from checksums."""
    from datetime import datetime
    
    # Update timestamp
    state["last_updated"] = datetime.utcnow().isoformat() + "Z"
    
    # Update artifacts section with checksums
    if "artifacts" not in state:
        state["artifacts"] = {}
    
    for file_path, hash_val in checksums.items():
        state["artifacts"][file_path] = {
            "hash": hash_val,
            "last_verified": datetime.utcnow().isoformat() + "Z"
        }
    
    logger.info(f"Updated state with {len(checksums)} artifact hashes")
    return state


def save_state(state: Dict[str, Any], state_file: Path) -> None:
    """Save the updated state to YAML file."""
    # Ensure directory exists
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(state_file, 'w', encoding='utf-8') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    logger.info(f"State saved to {state_file}")


def main() -> int:
    """Main entry point for T020."""
    logger.info("Starting T020: Update project state with artifact hashes")
    
    # Define paths
    checksum_file = Path(CONFIG.PROVENANCE_DIR) / "checksums.txt"
    state_file = Path(CONFIG.STATE_DIR) / "projects" / "PROJ-537-predicting-the-yield-strength-of-bcc-ste.yaml"
    
    # Load checksums
    checksums = load_checksums(checksum_file)
    if not checksums:
        logger.error("No checksums found. Cannot update state.")
        return 1
    
    logger.info(f"Loaded {len(checksums)} checksums from {checksum_file}")
    
    # Load or create state
    state = load_or_create_state(state_file)
    
    # Update state with checksums
    updated_state = update_state_with_checksums(state, checksums)
    
    # Save updated state
    save_state(updated_state, state_file)
    
    logger.info("T020 completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
