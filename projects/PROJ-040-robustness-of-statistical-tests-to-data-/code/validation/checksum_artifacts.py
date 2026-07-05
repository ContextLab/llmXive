"""
Generate content hashes (SHA-256) for project scripts and directory structure.
Updates the YAML state file with artifact_hashes map.
"""

import hashlib
import os
import yaml
from pathlib import Path
from typing import Dict, Any

# Import shared utilities from the sibling module
from .validate_citations import compute_sha256, write_state_file

# Project root relative to this script (parent of 'code')
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATE_DIR = PROJECT_ROOT / "state" / "projects"
STATE_FILE = STATE_DIR / "PROJ-040-robustness-of-statistical-tests-to-data-.yaml"

# Directories to scan for scripts
CODE_DIR = PROJECT_ROOT / "code"

# Directories to include in directory structure hash (excluding data/processed, data/results, etc. to avoid transient files)
STRUCTURE_DIRS = [
    "code",
    "tests",
    "data/raw",
    "data/processed",
    "data/results"
]

def get_python_scripts(root: Path) -> list:
    """Find all .py files in the code directory."""
    scripts = []
    if not root.exists():
        return scripts
    for py_file in root.rglob("*.py"):
        if py_file.is_file():
            scripts.append(py_file)
    return sorted(scripts)

def get_directory_structure_hash(root: Path, dirs: list) -> str:
    """
    Generate a deterministic hash of the directory structure.
    Hashes the sorted list of relative paths for files and directories.
    """
    hasher = hashlib.sha256()
    structure_entries = []
    
    base_path = PROJECT_ROOT
    
    for d in dirs:
        dir_path = base_path / d
        if not dir_path.exists():
            continue
        
        # Walk the directory tree
        for path in dir_path.rglob("*"):
            if path.is_file():
                # Get relative path from project root
                rel_path = path.relative_to(base_path)
                structure_entries.append(str(rel_path))
            elif path.is_dir():
                # Include directory markers to distinguish from files
                rel_path = path.relative_to(base_path)
                structure_entries.append(str(rel_path) + "/")
    
    # Sort for determinism
    structure_entries.sort()
    
    # Hash the list of paths
    content = "\n".join(structure_entries).encode('utf-8')
    hasher.update(content)
    return hasher.hexdigest()

def scan_artifacts() -> Dict[str, str]:
    """
    Scan code scripts and directory structure, compute SHA-256 hashes.
    Returns a dict mapping artifact paths to their hashes.
    """
    artifact_hashes = {}
    
    # 1. Hash Python scripts
    scripts = get_python_scripts(CODE_DIR)
    for script in scripts:
        rel_path = script.relative_to(PROJECT_ROOT)
        hash_val = compute_sha256(script)
        artifact_hashes[str(rel_path)] = hash_val
    
    # 2. Hash directory structure
    struct_hash = get_directory_structure_hash(PROJECT_ROOT, STRUCTURE_DIRS)
    # Use a specific key to denote the structure hash
    artifact_hashes["_directory_structure"] = struct_hash
    
    return artifact_hashes

def update_state_file(hashes: Dict[str, str]) -> None:
    """
    Load existing state YAML, update artifact_hashes, and save.
    Creates the file if it doesn't exist.
    """
    state_data = {}
    
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                state_data = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Could not read existing state file: {e}")
    
    # Update the artifact_hashes map
    state_data["artifact_hashes"] = hashes
    
    # Ensure state directory exists
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Write back to file using yaml.dump to ensure YAML format
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=True)
    
    print(f"State file updated: {STATE_FILE}")

def main():
    """Main entry point."""
    print("Scanning artifacts for checksum generation...")
    
    if not PROJECT_ROOT.exists():
        raise FileNotFoundError(f"Project root not found: {PROJECT_ROOT}")
    
    hashes = scan_artifacts()
    
    if not hashes:
        print("No artifacts found to hash.")
        return
    
    print(f"Found {len(hashes)} artifacts.")
    update_state_file(hashes)
    print("Done.")

if __name__ == "__main__":
    main()