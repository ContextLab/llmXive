"""
Versioning module for llmXive pipeline.
Computes content hashes for artifacts in data/ and code/ directories
and updates the project state file.
"""
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import yaml


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file's contents."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def scan_directory(base_path: Path, extensions: tuple = (".py", ".csv", ".json", ".yaml", ".yml", ".txt", ".md")) -> Dict[str, str]:
    """
    Recursively scan a directory for artifacts and compute their hashes.
    
    Args:
        base_path: Root directory to scan
        extensions: File extensions to include (default: common text/code formats)
        
    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes
    """
    hashes = {}
    if not base_path.exists():
        return hashes
        
    for file_path in base_path.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in extensions:
            # Store relative path from base_path
            rel_path = str(file_path.relative_to(base_path))
            hashes[rel_path] = compute_sha256(file_path)
            
    return hashes


def update_state_file(state_path: Path, data_hashes: Dict[str, str], code_hashes: Dict[str, str]) -> None:
    """
    Update the project state file with artifact hashes.
    
    The state file is updated with a flat 'artifact_hashes' map containing
    entries for all scanned files, and an 'updated_at' ISO 8601 timestamp.
    
    Args:
        state_path: Path to the state YAML file
        data_hashes: Hashes from data directory
        code_hashes: Hashes from code directory
    """
    state_dir = state_path.parent
    state_dir.mkdir(parents=True, exist_ok=True)
    
    current_state = {}
    if state_path.exists():
        with open(state_path, "r", encoding="utf-8") as f:
            current_state = yaml.safe_load(f) or {}
    
    # Merge data and code hashes into a single flat map as per task requirement
    all_hashes = {}
    all_hashes.update(data_hashes)
    all_hashes.update(code_hashes)
    
    # Build the new state structure
    new_state = {
        "artifact_hashes": all_hashes,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Merge with existing state if needed (preserve other keys)
    for key, value in new_state.items():
        current_state[key] = value
        
    with open(state_path, "w", encoding="utf-8") as f:
        yaml.dump(current_state, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def main() -> None:
    """Main entry point for versioning script."""
    # Determine project root based on script location
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Define paths
    data_dir = project_root / "data"
    code_dir = project_root / "code"
    state_path = project_root / "state" / "projects" / "PROJ-905-llmxive-follow-up-extending-fastcontext.yaml"
    
    # Compute hashes
    data_hashes = scan_directory(data_dir)
    code_hashes = scan_directory(code_dir)
    
    # Update state file
    update_state_file(state_path, data_hashes, code_hashes)
    
    print(f"Versioning complete. Updated {state_path}")
    print(f"  Data artifacts: {len(data_hashes)}")
    print(f"  Code artifacts: {len(code_hashes)}")


if __name__ == "__main__":
    main()