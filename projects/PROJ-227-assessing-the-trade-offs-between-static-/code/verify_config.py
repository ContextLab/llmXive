"""
Verification script for T004: Configuration Management.
Loads config.yaml and asserts types for all required fields.
"""
import sys
import yaml
from pathlib import Path

def main():
    config_path = Path(__file__).parent / "config.yaml"
    
    if not config_path.exists():
        print(f"ERROR: Config file not found at {config_path}")
        sys.exit(1)

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"ERROR: Failed to parse YAML: {e}")
        sys.exit(1)

    # Define expected schema and types
    expected_fields = {
        'human_eval_url': str,
        'codeql_path': str,
        'sonar_path': str,
        'max_cpu': int,
        'max_ram_gb': int
    }

    errors = []

    for field, expected_type in expected_fields.items():
        if field not in config:
            errors.append(f"Missing field: {field}")
            continue

        value = config[field]
        if not isinstance(value, expected_type):
            errors.append(
                f"Type mismatch for '{field}': expected {expected_type.__name__}, "
                f"got {type(value).__name__} (value: {value})"
            )

    if errors:
        print("Configuration validation FAILED:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    print("Configuration validation PASSED.")
    print(f"Loaded config: {config}")
    sys.exit(0)

if __name__ == "__main__":
    main()
