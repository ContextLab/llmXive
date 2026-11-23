"""
Initialize the project state file for PROJ-548.

This script creates the state directory structure and initializes the
`state/projects/PROJ-548-exploring-the-relationship-between-prime.yaml`
file with the required schema.

It satisfies:
- Constitution Principle III (Data Hygiene): Ensures the state file exists.
- Constitution Principle V (Versioning Discipline): Sets the initial timestamp.

The file contains:
- `project_id`: The unique identifier for this project.
- `artifact_hashes`: An empty map to be populated by T008/T008b.
- `updated_at`: ISO 8601 timestamp of initialization.
- `status`: Initial status "initialized".
"""

import os
import sys
from pathlib import Path
import time
from datetime import datetime, timezone

# Add project root to path to import utils if needed, though we write raw YAML here
# to avoid circular dependencies during initialization.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATE_DIR = PROJECT_ROOT / "state" / "projects"
PROJECT_ID = "PROJ-548-exploring-the-relationship-between-prime"
STATE_FILE = STATE_DIR / f"{PROJECT_ID}.yaml"

def ensure_directories():
    """Create the state directory if it doesn't exist."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)

def main():
    """Initialize the state file."""
    print(f"Initializing state file for project: {PROJECT_ID}")
    
    ensure_directories()

    if STATE_FILE.exists():
        print(f"Warning: State file {STATE_FILE} already exists. Overwriting.")
    
    # Generate the initial timestamp
    now = datetime.now(timezone.utc).isoformat()

    # Define the initial state structure
    # We write YAML manually to avoid dependency on PyYAML if not strictly needed,
    # but since T002 added pyyaml, we can use it for safety.
    try:
        import yaml
        state_data = {
            "project_id": PROJECT_ID,
            "artifact_hashes": {},
            "updated_at": now,
            "status": "initialized",
            "version": "1.0.0"
        }
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
    except ImportError:
        # Fallback to manual YAML writing if yaml is not installed
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            f.write(f"project_id: {PROJECT_ID}\n")
            f.write("artifact_hashes: {}\n")
            f.write(f"updated_at: {now}\n")
            f.write("status: initialized\n")
            f.write("version: 1.0.0\n")

    print(f"State file created successfully at: {STATE_FILE}")
    print(f"Contents:\n")
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        print(f.read())

    return 0

if __name__ == "__main__":
    sys.exit(main())