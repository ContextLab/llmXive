"""
Checksum configuration script for project artifacts.

Computes SHA256 hashes for key configuration and documentation files
and writes them to the project state file.

Target files:
- README.md
- .gitignore
- requirements.txt
- pytest.ini

Output:
- state/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p.yaml
  (updates 'artifact_hashes' section)
"""
import os
import sys
import hashlib
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Project root relative to this script (assuming script is in code/)
PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state" / "projects"
STATE_FILE = STATE_DIR / "PROJ-860-llmxive-follow-up-extending-dragmesh-2-p.yaml"

# Files to hash (relative to project root)
CONFIG_FILES = [
    "README.md",
    ".gitignore",
    "code/requirements.txt",
    "code/pytest.ini"
]

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_state() -> Dict:
    """Load existing state file or return empty structure."""
    if STATE_FILE.exists():
        with open(STATE_FILE, "r") as f:
            return yaml.safe_load(f) or {}
    return {}

def save_state(state: Dict) -> None:
    """Save state to YAML file."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def main() -> int:
    """Main entry point for checksum configuration."""
    print(f"Computing checksums for project artifacts in: {PROJECT_ROOT}")

    # Verify all target files exist
    missing_files = []
    for rel_path in CONFIG_FILES:
        full_path = PROJECT_ROOT / rel_path
        if not full_path.exists():
            missing_files.append(rel_path)

    if missing_files:
        print(f"ERROR: Missing required files: {missing_files}")
        print("Ensure T001a and T001b have been completed successfully.")
        return 1

    # Compute hashes
    artifact_hashes = {}
    for rel_path in CONFIG_FILES:
        full_path = PROJECT_ROOT / rel_path
        try:
            file_hash = compute_sha256(full_path)
            artifact_hashes[rel_path] = file_hash
            print(f"  {rel_path}: {file_hash[:16]}...")
        except Exception as e:
            print(f"ERROR: Failed to hash {rel_path}: {e}")
            return 1

    # Load existing state and update
    state = load_state()
    state["artifact_hashes"] = artifact_hashes
    state["updated_at"] = datetime.utcnow().isoformat() + "Z"

    # Save updated state
    save_state(state)
    print(f"\nChecksums written to: {STATE_FILE}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
