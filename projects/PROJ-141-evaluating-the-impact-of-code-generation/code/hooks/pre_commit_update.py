"""
Pre-commit hook to update the project state file timestamp.

This script is designed to be called by a git pre-commit hook.
It scans the git staged files for changes in the `data/`, `code/`, `tests/`, 
`models/`, `logs/`, or `figures/` directories. If any changes are detected,
it updates the `updated_at` field in the project state YAML file.

Constitution V Compliance: Ensures the state file reflects the current 
timestamp of the last artifact modification.
"""
import os
import sys
import subprocess
import yaml
from datetime import datetime, timezone
from pathlib import Path

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATE_FILE_PATH = PROJECT_ROOT / "state" / "projects" / "PROJ-141-evaluating-the-impact-of-code-generation.yaml"
TRIGGERED_DIRS = {"data", "code", "tests", "models", "logs", "figures", "specs"}

def get_staged_files():
    """
    Retrieve the list of files staged for commit using git.
    Returns a list of relative paths.
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        if not result.stdout:
            return []
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except subprocess.CalledProcessError as e:
        print(f"Error running git diff: {e.stderr}", file=sys.stderr)
        return []
    except FileNotFoundError:
        print("Git command not found. Skipping timestamp update.", file=sys.stderr)
        return []

def is_artifact_changed(staged_files):
    """
    Check if any of the staged files are in the monitored directories.
    """
    for file_path in staged_files:
        # Check if the file path starts with any of the trigger directories
        for dir_name in TRIGGERED_DIRS:
            if file_path.startswith(f"{dir_name}/"):
                return True
    return False

def update_state_timestamp():
    """
    Update the 'updated_at' field in the state file to the current UTC timestamp.
    """
    if not STATE_FILE_PATH.exists():
        print(f"State file not found: {STATE_FILE_PATH}", file=sys.stderr)
        print("Skipping timestamp update.", file=sys.stderr)
        return False

    try:
        with open(STATE_FILE_PATH, 'r', encoding='utf-8') as f:
            state_data = yaml.safe_load(f) or {}

        # Update the timestamp
        state_data['updated_at'] = datetime.now(timezone.utc).isoformat()

        with open(STATE_FILE_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(state_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        print(f"Updated state file timestamp: {STATE_FILE_PATH}")
        return True

    except yaml.YAMLError as e:
        print(f"Error parsing state YAML: {e}", file=sys.stderr)
        return False
    except IOError as e:
        print(f"Error writing state file: {e}", file=sys.stderr)
        return False

def main():
    """
    Main entry point for the pre-commit hook.
    """
    staged_files = get_staged_files()
    
    if not staged_files:
        print("No staged files found.")
        return 0

    if not is_artifact_changed(staged_files):
        print("No changes in monitored artifact directories.")
        return 0

    print("Artifact changes detected. Updating state file timestamp...")
    success = update_state_timestamp()
    
    if not success:
        print("Failed to update state file timestamp.", file=sys.stderr)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())