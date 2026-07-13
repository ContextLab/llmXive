"""
Migrate derived statistics from config.yaml to state file.

This script moves keys 'dataset_stats', 'inference_results', and 'simulation_metrics'
from code/config.yaml to state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml.
It then verifies that code/config.yaml is under 2048 bytes.
"""
import os
import sys
import yaml
from pathlib import Path
from datetime import datetime

def get_project_root():
    """Get the project root directory."""
    current = Path(__file__).resolve()
    # Script is at code/src/utils/migrate_config.py
    # Navigate up 4 levels: utils -> src -> code -> project_root
    # Wait, the structure is:
    # projects/PROJ-024.../
    #   code/
    #     src/
    #       utils/
    #         migrate_config.py
    #   state/
    #     projects/
    #
    # So from migrate_config.py:
    # parent: utils
    # parent: src
    # parent: code
    # parent: project_root
    return current.parent.parent.parent.parent

def load_yaml(path):
    """Load a YAML file."""
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def save_yaml(path, data):
    """Save data to a YAML file."""
    with open(path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

def main():
    project_root = get_project_root()
    config_path = project_root / "code" / "config.yaml"
    state_path = project_root / "state" / "projects" / "PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml"

    print(f"Project root: {project_root}")
    print(f"Config path: {config_path}")
    print(f"State path: {state_path}")

    if not config_path.exists():
        print(f"ERROR: Config file not found at {config_path}")
        sys.exit(1)

    if not state_path.exists():
        print(f"ERROR: State file not found at {state_path}")
        sys.exit(1)

    # Load config
    config = load_yaml(config_path)
    print(f"Loaded config with {len(config)} keys")

    # Keys to migrate
    keys_to_migrate = ['dataset_stats', 'inference_results', 'simulation_metrics']
    migrated_data = {}
    remaining_keys = []

    for key in list(config.keys()):
        if key in keys_to_migrate:
            migrated_data[key] = config.pop(key)
            print(f"Migrated key: {key}")
        else:
            remaining_keys.append(key)

    print(f"Remaining keys in config: {remaining_keys}")

    # Load state file
    state = load_yaml(state_path)
    print(f"Loaded state file with keys: {list(state.keys())}")

    # Ensure 'migrated_data' section exists in state
    if 'migrated_data' not in state:
        state['migrated_data'] = {}
    
    # Add migration timestamp
    state['migrated_data']['migration_timestamp'] = datetime.now().isoformat()
    state['migrated_data']['migration_task'] = 'T060'

    # Add the migrated data
    for key, value in migrated_data.items():
        state['migrated_data'][key] = value
        print(f"Added {key} to state file")

    # Save updated state file
    save_yaml(state_path, state)
    print(f"Updated state file saved to {state_path}")

    # Save updated config file
    save_yaml(config_path, config)
    print(f"Updated config file saved to {config_path}")

    # Verify config size
    config_size = os.path.getsize(config_path)
    max_size = 2048  # 2KB

    print(f"\nConfig file size: {config_size} bytes")
    print(f"Max allowed size: {max_size} bytes")

    if config_size > max_size:
        print(f"ERROR: Config file exceeds 2KB limit by {config_size - max_size} bytes")
        sys.exit(1)
    else:
        print("SUCCESS: Config file is under 2KB limit")
        return 0

if __name__ == "__main__":
    sys.exit(main())
