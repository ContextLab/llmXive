"""
Script to validate the state file structure for PROJ-006-agriculture-optimization.
This script asserts the file exists, is valid YAML, and contains the required schema.
"""
import sys
import yaml
from pathlib import Path

STATE_FILE_PATH = "state/projects/PROJ-006-agriculture-optimization.yaml"

def main():
    path = Path(STATE_FILE_PATH)
    if not path.exists():
        print(f"ERROR: State file not found at {STATE_FILE_PATH}")
        sys.exit(1)

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"ERROR: Invalid YAML in state file: {e}")
        sys.exit(1)

    # Verify required keys
    required_keys = ['project_id', 'artifact_hashes']
    for key in required_keys:
        if key not in data:
            print(f"ERROR: Missing required key '{key}' in state file")
            sys.exit(1)

    if data['project_id'] != 'PROJ-006-agriculture-optimization':
        print(f"ERROR: project_id mismatch. Expected 'PROJ-006-agriculture-optimization', got '{data['project_id']}'")
        sys.exit(1)

    if not isinstance(data['artifact_hashes'], dict):
        print(f"ERROR: artifact_hashes must be a dictionary/map")
        sys.exit(1)

    print(f"SUCCESS: State file is valid and contains correct schema.")
    sys.exit(0)

if __name__ == "__main__":
    main()
