"""
Verification script for T004: Configuration Management.
Loads projects/PROJ-227-assessing-the-trade-offs-between-static-/code/config.yaml
and asserts types for all required keys.
"""
import sys
import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.yaml"

REQUIRED_SCHEMA = {
    "human_eval_url": str,
    "codeql_path": str,
    "sonar_path": str,
    "max_cpu": int,
    "max_ram_gb": int,
}

def main():
    if not CONFIG_PATH.exists():
        print(f"ERROR: Configuration file not found at {CONFIG_PATH}")
        sys.exit(1)

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"ERROR: Failed to parse YAML: {e}")
        sys.exit(1)

    if not isinstance(config, dict):
        print("ERROR: Config root must be a mapping (dict).")
        sys.exit(1)

    errors = []
    for key, expected_type in REQUIRED_SCHEMA.items():
        if key not in config:
            errors.append(f"Missing required key: '{key}'")
            continue

        value = config[key]
        if not isinstance(value, expected_type):
            # Special case for int: yaml might load bool as int subclass, but we want strict int
            if expected_type == int and isinstance(value, bool):
                errors.append(f"Key '{key}' is bool, expected int.")
            elif not isinstance(value, expected_type):
                errors.append(f"Key '{key}' is {type(value).__name__}, expected {expected_type.__name__}.")

    if errors:
        print("CONFIGURATION VALIDATION FAILED:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    print("CONFIGURATION VALIDATION SUCCESSFUL:")
    for key, value in config.items():
        print(f"  {key}: {value} ({type(value).__name__})")
    sys.exit(0)

if __name__ == "__main__":
    main()
