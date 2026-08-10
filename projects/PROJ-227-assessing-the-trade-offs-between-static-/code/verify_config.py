"""
Verification script for T004: Configuration Management.
Loads code/config.yaml and asserts schema types.
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

    if not isinstance(config, dict):
        print("ERROR: Config root must be a dictionary")
        sys.exit(1)

    # Define schema requirements
    required_keys = {
        'human_eval_url': str,
        'codeql_path': str,
        'sonar_path': str,
        'max_cpu': int,
        'max_ram_gb': int
    }

    errors = []
    for key, expected_type in required_keys.items():
        if key not in config:
            errors.append(f"Missing required key: {key}")
            continue
        
        value = config[key]
        if not isinstance(value, expected_type):
            errors.append(f"Type mismatch for {key}: expected {expected_type.__name__}, got {type(value).__name__}")

    if errors:
        print("VALIDATION FAILED:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    print("Configuration validation successful.")
    print(f"  human_eval_url: {config['human_eval_url']}")
    print(f"  codeql_path: {config['codeql_path']}")
    print(f"  sonar_path: {config['sonar_path']}")
    print(f"  max_cpu: {config['max_cpu']}")
    print(f"  max_ram_gb: {config['max_ram_gb']}")

if __name__ == "__main__":
    main()
