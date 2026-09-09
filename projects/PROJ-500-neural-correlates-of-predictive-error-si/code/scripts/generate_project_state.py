"""
T005d: Generate initial project state YAML with content hashes.

This script satisfies Constitution Principle V by generating a state file
that records the content hashes of the project's configuration files
(requirements.txt and pyproject.toml).

Dependency: T005c (Git Init) - assumes .git directory exists.
"""
import os
import sys
import hashlib
import yaml
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path to ensure imports work if needed, 
# though this script is self-contained.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "state" / "projects"
CONFIG_FILES = ["requirements.txt", "pyproject.toml"]
PROJECT_ID = "PROJ-500-neural-correlates-of-predictive-error-si"

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file's contents."""
    if not file_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    """Generate the project state YAML file."""
    # Ensure directory structure exists
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    output_file = STATE_DIR / f"{PROJECT_ID}.yaml"

    # Verify git repository exists (T005c dependency)
    git_dir = PROJECT_ROOT / ".git"
    if not git_dir.exists():
        print("Error: .git directory not found. Please run T005c (git init) first.")
        sys.exit(1)

    print(f"Generating project state for {PROJECT_ID}...")
    
    content_hashes = {}
    missing_files = []

    for config_file in CONFIG_FILES:
        file_path = PROJECT_ROOT / config_file
        try:
            file_hash = compute_file_hash(file_path)
            content_hashes[config_file] = file_hash
            print(f"  Hashed {config_file}: {file_hash[:16]}...")
        except FileNotFoundError as e:
            missing_files.append(str(e))
            print(f"  Warning: {e}")

    if missing_files:
        print("Warning: Some configuration files were missing. State file will be generated with available data.")
        print("         Ensure requirements.txt and pyproject.toml are created before running the full pipeline.")

    state_data = {
        "project_id": PROJECT_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_status": "initialized",
        "constitution_principle_v": {
            "description": "Content hashes of project configuration files",
            "files": content_hashes
        },
        "dependencies": {
            "T005c": "git_init"
        }
    }

    with open(output_file, "w", encoding="utf-8") as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)

    print(f"Successfully generated: {output_file}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
