"""
Task T002d: Compute SHA-256 checksum of data/raw/era5_full.h5
and record it under artifact_hashes.era5_full in the project state YAML.
Also updates the updated_at timestamp.
"""
import os
import sys
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path

# Ensure we can import from the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import get_path_env_override

# Constants
FILE_PATH = "data/raw/era5_full.h5"
STATE_FILE_PATH = "state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml"
ARTIFACT_KEY = "era5_full"

logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure the state directory exists."""
    state_dir = PROJECT_ROOT / "state" / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directory exists: {state_dir}")

def compute_sha256(file_path: Path) -> str:
    """Compute the SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    logger.info(f"Computing SHA-256 for {file_path}...")
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()

def update_state_file(state_path: Path, artifact_key: str, checksum: str):
    """
    Update the YAML state file with the new checksum and timestamp.
    Uses a simple text-based update to avoid dependency on PyYAML if not installed,
    but assumes standard YAML structure.
    """
    if not state_path.exists():
        raise FileNotFoundError(f"State file not found: {state_path}")
    
    with open(state_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    new_lines = []
    found_key = False
    timestamp_added = False
    now_str = datetime.now(timezone.utc).isoformat()
    
    # We need to find the artifact_hashes section and update/create the key
    # We also need to update or add updated_at at the top level or appropriate place
    
    # Simple approach: find the line with "artifact_hashes:" and then the specific key
    # Or if the key doesn't exist, add it.
    
    # Let's try to parse line by line looking for the artifact key
    # Expected format in YAML:
    # artifact_hashes:
    #   era5_full: <old_hash>
    
    # We will look for "  era5_full:" and update it, or add it if missing.
    # We also look for "updated_at:" and update it.
    
    in_artifact_hashes = False
    added_new_key = False
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Check for updated_at (top level usually, indented 0 or 2)
        if stripped.startswith("updated_at:"):
            new_lines.append(f"updated_at: {now_str}\n")
            timestamp_added = True
            continue
        
        # Check for artifact_hashes section start
        if stripped == "artifact_hashes:":
            in_artifact_hashes = True
            new_lines.append(line)
            continue
        
        if in_artifact_hashes:
            # Check if we are leaving the artifact_hashes section (new top-level key)
            if stripped and not line.startswith(" ") and not line.startswith("\t"):
                in_artifact_hashes = False
            
            # Check for our specific key
            if stripped.startswith(f"{artifact_key}:"):
                new_lines.append(f"  {artifact_key}: {checksum}\n")
                found_key = True
                continue
            
            # If we are at the end of artifact_hashes and haven't found the key, add it
            # We detect end of section by a line that is not indented or is a new section
            if not line.startswith(" ") and not line.startswith("\t") and stripped:
                if not found_key and not added_new_key:
                    # Backtrack slightly to insert before the new section?
                    # Easier: just insert before this line if we haven't added it yet
                    # But we are iterating. Let's handle logic differently.
                    pass
        
        new_lines.append(line)
    
    # If we finished reading and didn't find the key, we need to add it.
    # We need to find where to insert it. Ideally under artifact_hashes.
    if not found_key:
        logger.warning(f"Key '{artifact_key}' not found in artifact_hashes. Adding it.")
        # Re-read to find insertion point
        final_lines = []
        inserted = False
        for line in lines:
            final_lines.append(line)
            if line.strip() == "artifact_hashes:":
                # Insert the new key on the next line with proper indentation
                # Assuming the next line is either empty or the first key
                final_lines.append(f"  {artifact_key}: {checksum}\n")
                inserted = True
        
        if not inserted:
            # If artifact_hashes didn't exist, we might need to add the section too
            # But based on context, it should exist. If not, append at end.
            final_lines.append("\nartifact_hashes:\n")
            final_lines.append(f"  {artifact_key}: {checksum}\n")
        
        new_lines = final_lines

    # Ensure updated_at exists if it wasn't found
    if not timestamp_added:
        # Insert at the beginning or after a top-level key
        # Simple: insert at line 0 if it's not already there
        if not any(l.strip().startswith("updated_at:") for l in new_lines):
            new_lines.insert(0, f"updated_at: {now_str}\n")

    with open(state_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    
    logger.info(f"Updated state file: {state_path}")

def main():
    ensure_directories()
    
    file_path = PROJECT_ROOT / FILE_PATH
    state_path = PROJECT_ROOT / STATE_FILE_PATH
    
    try:
        checksum = compute_sha256(file_path)
        logger.info(f"Checksum computed: {checksum}")
        
        update_state_file(state_path, ARTIFACT_KEY, checksum)
        
        logger.info("Task T002d completed successfully.")
        return 0
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error during task execution: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())