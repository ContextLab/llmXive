"""
Verification script for T004: Configuration Management.
Loads code/config.yaml and asserts types against the required schema.
"""
import sys
import yaml
from pathlib import Path

def main():
    project_root = Path(__file__).parent.parent
    config_path = project_root / "code" / "config.yaml"

    if not config_path.exists():
        print(f"ERROR: Config file not found at {config_path}")
        sys.exit(1)

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"ERROR: Failed to parse YAML: {e}")
        sys.exit(1)

    if not isinstance(config, dict):
        print("ERROR: Config root must be a dictionary")
        sys.exit(1)

    # Define schema expectations
    required_keys = {
        "human_eval_url": str,
        "codeql_path": str,
        "sonar_path": str,
        "max_cpu": int,
        "max_ram_gb": int
    }

    errors = []
    for key, expected_type in required_keys.items():
        if key not in config:
            errors.append(f"Missing required key: {key}")
            continue

        value = config[key]
        # Handle bool subclass of int in Python
        if expected_type == int and isinstance(value, bool):
            errors.append(f"Key '{key}' must be int, got bool")
        elif not isinstance(value, expected_type):
            errors.append(f"Key '{key}' must be {expected_type.__name__}, got {type(value).__name__}")

    if errors:
        print("VERIFICATION FAILED:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    print("VERIFICATION PASSED:")
    print(f"  human_eval_url: {config['human_eval_url']} (str)")
    print(f"  codeql_path: {config['codeql_path']} (str)")
    print(f"  sonar_path: {config['sonar_path']} (str)")
    print(f"  max_cpu: {config['max_cpu']} (int)")
    print(f"  max_ram_gb: {config['max_ram_gb']} (int)")
    sys.exit(0)

if __name__ == "__main__":
    main()
