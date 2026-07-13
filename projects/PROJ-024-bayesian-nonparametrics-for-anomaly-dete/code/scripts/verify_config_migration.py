"""
Verify that T060 migration was successful.

Checks:
1. config.yaml is under 2KB
2. State file contains migrated keys
3. Config file no longer contains migrated keys
"""
import os
import sys
import yaml
from pathlib import Path

def get_project_root():
    """Get the project root directory."""
    current = Path(__file__).resolve()
    # Navigate up: scripts -> code -> project root
    project_root = current.parent.parent
    return project_root

def load_yaml(path):
    """Load a YAML file."""
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def main():
    project_root = get_project_root()
    config_path = project_root / "code" / "config.yaml"
    state_path = project_root / "state" / "projects" / "PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml"

    print("=== Config Migration Verification ===\n")

    # Check config size
    config_size = os.path.getsize(config_path)
    max_size = 2048
    print(f"Config file size: {config_size} bytes")
    print(f"Max allowed size: {max_size} bytes")
    
    if config_size > max_size:
        print("❌ FAILED: Config file exceeds 2KB limit")
        return 1
    else:
        print("✅ PASSED: Config file is under 2KB limit")

    # Load config and check for migrated keys
    config = load_yaml(config_path)
    migrated_keys = ['dataset_stats', 'inference_results', 'simulation_metrics']
    found_in_config = [k for k in migrated_keys if k in config]
    
    if found_in_config:
        print(f"❌ FAILED: Config still contains migrated keys: {found_in_config}")
        return 1
    else:
        print("✅ PASSED: Config does not contain migrated keys")

    # Load state and check for migrated data
    state = load_yaml(state_path)
    if 'migrated_data' not in state:
        print("❌ FAILED: State file does not contain 'migrated_data' section")
        return 1

    migrated_data = state['migrated_data']
    missing_in_state = [k for k in migrated_keys if k not in migrated_data]
    
    if missing_in_state:
        print(f"❌ FAILED: State file missing migrated keys: {missing_in_state}")
        return 1
    else:
        print("✅ PASSED: State file contains all migrated keys")

    # Check migration metadata
    if 'migration_timestamp' not in migrated_data:
        print("⚠️ WARNING: Migration timestamp not found in state file")
    else:
        print(f"✅ Migration timestamp: {migrated_data['migration_timestamp']}")

    if 'migration_task' not in migrated_data:
        print("⚠️ WARNING: Migration task ID not found in state file")
    else:
        print(f"✅ Migration task: {migrated_data['migration_task']}")

    print("\n=== All Checks Passed ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())