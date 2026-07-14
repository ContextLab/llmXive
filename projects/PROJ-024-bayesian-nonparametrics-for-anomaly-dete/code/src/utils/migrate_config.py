"""
Utility to migrate derived statistics from config.yaml to the state file.

This script performs the following steps:
1. Loads the project's config.yaml (located at projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/config.yaml).
2. Identifies derived statistic keys: 'dataset_stats', 'inference_results', 'simulation_metrics'.
3. Removes these keys from the config (if present).
4. Loads the target state file (state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml).
5. Merges the removed keys into the state file under a 'derived_statistics' section.
6. Saves the updated config and state files.
7. Verifies the config file size is < 2048 bytes.
"""
import os
import sys
import yaml
from pathlib import Path
from datetime import datetime

# Determine the project root.
# The script is at: projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/utils/migrate_config.py
# Project root is: projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/
SCRIPT_DIR = Path(__file__).resolve().parent
CODE_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = CODE_DIR.parent

CONFIG_PATH = PROJECT_ROOT / "code" / "config.yaml"
STATE_PATH = PROJECT_ROOT / "state" / "projects" / "PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml"

# Keys to migrate
DERIVED_KEYS = ['dataset_stats', 'inference_results', 'simulation_metrics']

def load_yaml(path: Path) -> dict:
    if not path.exists():
        print(f"Error: File not found: {path}")
        sys.exit(1)
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}

def save_yaml(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    print(f"Saved: {path}")

def main():
    print(f"Starting config migration at {datetime.now().isoformat()}")
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Config path: {CONFIG_PATH}")
    print(f"State path: {STATE_PATH}")

    # 1. Load config
    if not CONFIG_PATH.exists():
        print(f"Error: Config file not found at {CONFIG_PATH}")
        sys.exit(1)
    
    config = load_yaml(CONFIG_PATH)
    
    # 2. Extract derived statistics
    migrated_data = {}
    missing_keys = []
    for key in DERIVED_KEYS:
        if key in config:
            migrated_data[key] = config.pop(key)
        else:
            missing_keys.append(key)
    
    if missing_keys:
        print(f"Note: Keys not found in config (already migrated?): {missing_keys}")
    
    if not migrated_data:
        print("No derived statistics found to migrate (keys were empty or missing).")
    else:
        print(f"Migrating keys: {list(migrated_data.keys())}")

    # 3. Load or initialize state file
    if STATE_PATH.exists():
        state = load_yaml(STATE_PATH)
    else:
        state = {
            "project_id": "PROJ-024-bayesian-nonparametrics-for-anomaly-dete",
            "created_at": datetime.now().isoformat(),
            "derived_statistics": {}
        }
        print(f"Created new state file: {STATE_PATH}")

    # 4. Merge into state file
    if "derived_statistics" not in state:
        state["derived_statistics"] = {}
    
    state["derived_statistics"].update(migrated_data)
    state["last_updated"] = datetime.now().isoformat()

    # 5. Save updated files
    save_yaml(CONFIG_PATH, config)
    save_yaml(STATE_PATH, state)

    # 6. Verify config size
    config_size = os.path.getsize(CONFIG_PATH)
    limit = 2048
    print(f"Config file size: {config_size} bytes (limit: {limit} bytes)")
    
    if config_size > limit:
        print(f"ERROR: Config file size {config_size} exceeds limit {limit}.")
        sys.exit(1)
    else:
        print("SUCCESS: Config file size is within limits.")

    return 0

if __name__ == "__main__":
    sys.exit(main())