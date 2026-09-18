"""
Script to remove Artificial Drift Injection Config.

This script scans the `config/` directory for YAML files containing
keys associated with artificial drift injection (e.g., 'drift_probability',
'error_injection_rules', 'random_noise_seed'). It deletes any files
containing these keys, while preserving valid configuration files
such as those containing the 'correction_token' mechanism.

It ensures the project adheres to the principle of not simulating
artificial drift in the data generation process.
"""
import os
import sys
import yaml
from pathlib import Path
from typing import Set, List, Dict, Any

# Keys that indicate artificial drift injection
DRIFT_INJECTION_KEYS: Set[str] = {
    "drift_probability",
    "error_injection_rules",
    "random_noise_generators",
    "drift_noise_seed",
    "artificial_drift",
    "simulate_drift",
    "noise_injection_rate",
    "drift_factor",
    "fake_drift_params"
}

# Keys that are VALID interventions (must be preserved)
VALID_INTERVENTION_KEYS: Set[str] = {
    "correction_token",
    "correction_tokens",
    "dynamic_prompt_reconditioning",
    "symbolic_correction"
}

def contains_drift_injection_keys(file_path: Path) -> bool:
    """
    Check if a YAML file contains any keys associated with artificial drift injection.
    
    Args:
        file_path: Path to the YAML file.
        
    Returns:
        True if the file contains drift injection keys, False otherwise.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"Warning: Could not parse YAML in {file_path}: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)
        return False

    if data is None:
        return False

    # Flatten all keys in the YAML structure (including nested ones)
    all_keys: Set[str] = set()
    def extract_keys(d: Any):
        if isinstance(d, dict):
            for k, v in d.items():
                all_keys.add(str(k).lower())
                extract_keys(v)
        elif isinstance(d, list):
            for item in d:
                extract_keys(item)

    extract_keys(data)

    # Check for intersection with drift injection keys
    found_drift_keys = all_keys.intersection(DRIFT_INJECTION_KEYS)
    if found_drift_keys:
        print(f"  -> Found drift injection keys: {found_drift_keys}")
        return True

    return False

def main():
    """
    Main entry point for the drift config removal script.
    """
    # Determine project root (assuming script is in code/scripts/)
    # We look for the 'config' directory relative to the project root.
    # The project root is typically 2 levels up from code/scripts/
    script_dir = Path(__file__).resolve().parent
    code_dir = script_dir.parent
    project_root = code_dir.parent

    config_dir = project_root / "config"

    if not config_dir.exists():
        print(f"Config directory not found at {config_dir}. Exiting.")
        return 0

    print(f"Scanning config directory: {config_dir}")
    files_to_delete: List[Path] = []
    files_preserved: List[Path] = []

    # Iterate over all YAML files in the config directory
    yaml_files = list(config_dir.glob("*.yaml")) + list(config_dir.glob("*.yml"))

    if not yaml_files:
        print("No YAML files found in config directory.")
        return 0

    for file_path in yaml_files:
        print(f"Checking: {file_path.name}")
        if contains_drift_injection_keys(file_path):
            files_to_delete.append(file_path)
        else:
            # Double check: if it has valid intervention keys, ensure it's definitely not drift
            # Our logic above only flags drift if drift keys are present.
            # If no drift keys are present, we preserve it.
            files_preserved.append(file_path)
            print(f"  -> Preserved (no drift injection keys found).")

    if not files_to_delete:
        print("\nNo files containing artificial drift injection keys were found.")
        print("Configuration is clean.")
        return 0

    # Perform deletion
    print(f"\nDeleting {len(files_to_delete)} file(s) containing artificial drift injection:")
    for file_path in files_to_delete:
        try:
            file_path.unlink()
            print(f"  Deleted: {file_path.name}")
        except Exception as e:
            print(f"  ERROR: Failed to delete {file_path.name}: {e}", file=sys.stderr)
            return 1

    print("\nCleanup complete.")
    print(f"Preserved {len(files_preserved)} configuration file(s).")
    return 0

if __name__ == "__main__":
    sys.exit(main())
