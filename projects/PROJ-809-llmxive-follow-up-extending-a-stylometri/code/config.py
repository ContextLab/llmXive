import json
import os
import random
import re
from pathlib import Path
from typing import Any, Dict, Optional, List

import yaml

# Global configuration state
_config: Dict[str, Any] = {
    "seed": 42,
    "contracts_dir": "contracts",
    "data_dir": "data",
    "artifacts_dir": "artifacts",
    "state_file": "state/PROJ-809-llmxive-followup.yaml",
    "strict_mode": True,
    "allowed_categories": ["cs.CL", "physics.gen-ph", "q-bio.QM"],
    "min_abstract_length": 6,
    "target_authors": 20,
    "min_abstracts_per_author": 10,
    "collision_warning_threshold": 50,
    "ngram_orders": [4, 5, 6],
    "train_test_split": 0.2,
}

def ensure_dir(path: str) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file if provided, otherwise return defaults.
    If the file exists but is invalid, raises ValueError.
    """
    global _config
    if config_path and os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            try:
                custom_config = yaml.safe_load(f)
                if isinstance(custom_config, dict):
                    _config.update(custom_config)
                else:
                    raise ValueError(f"Config file {config_path} must contain a YAML mapping.")
            except yaml.YAMLError as e:
                raise ValueError(f"Failed to parse config file {config_path}: {e}")
    return _config.copy()

def save_config(config: Dict[str, Any], config_path: str) -> None:
    """Save the current configuration to a YAML file."""
    ensure_dir(os.path.dirname(config_path))
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

def set_seed(seed: int) -> None:
    """Set the global random seed for reproducibility."""
    _config["seed"] = seed
    random.seed(seed)
    # Note: numpy and torch seeds would be set here if those were dependencies,
    # but per constraints we stick to stdlib and declared deps.

def get_seed() -> int:
    """Get the current global random seed."""
    return _config["seed"]

def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a JSON schema from the contracts directory.
    Raises FileNotFoundError if the schema does not exist.
    """
    full_path = Path(schema_path)
    if not full_path.is_absolute():
        contracts_dir = Path(_config["contracts_dir"])
        full_path = contracts_dir / schema_path

    if not full_path.exists():
        raise FileNotFoundError(f"Schema file not found: {full_path}")

    with open(full_path, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_against_schema(data: Any, schema: Dict[str, Any]) -> List[str]:
    """
    Validate data against a JSON schema.
    Returns a list of error messages. If empty, validation passed.
    Note: This is a basic implementation assuming 'type' and 'properties' checks.
    For full JSON Schema validation, a library like 'jsonschema' would be needed.
    Given constraints, we implement a minimal validator for common patterns.
    """
    errors = []
    schema_type = schema.get("type")

    if schema_type == "object":
        if not isinstance(data, dict):
            errors.append(f"Expected object, got {type(data).__name__}")
            return errors
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        for key in required:
            if key not in data:
                errors.append(f"Missing required property: {key}")
        for key, value_schema in properties.items():
            if key in data:
                sub_errors = validate_against_schema(data[key], value_schema)
                errors.extend([f"{key}: {err}" for err in sub_errors])
    elif schema_type == "array":
        if not isinstance(data, list):
            errors.append(f"Expected array, got {type(data).__name__}")
            return errors
        items_schema = schema.get("items")
        if items_schema:
            for i, item in enumerate(data):
                sub_errors = validate_against_schema(item, items_schema)
                errors.extend([f"[{i}]: {err}" for err in sub_errors])
    elif schema_type == "string":
        if not isinstance(data, str):
            errors.append(f"Expected string, got {type(data).__name__}")
    elif schema_type == "integer":
        if not isinstance(data, int):
            errors.append(f"Expected integer, got {type(data).__name__}")
    elif schema_type == "number":
        if not isinstance(data, (int, float)):
            errors.append(f"Expected number, got {type(data).__name__}")
    elif schema_type == "boolean":
        if not isinstance(data, bool):
            errors.append(f"Expected boolean, got {type(data).__name__}")

    return errors

def get_contract_paths() -> List[str]:
    """
    Return a list of paths to all JSON schema files in the contracts directory.
    """
    contracts_dir = Path(_config["contracts_dir"])
    if not contracts_dir.exists():
        return []
    return [str(p) for p in contracts_dir.glob("*.json")]

def reset_config() -> None:
    """Reset configuration to defaults."""
    global _config
    _config = {
        "seed": 42,
        "contracts_dir": "contracts",
        "data_dir": "data",
        "artifacts_dir": "artifacts",
        "state_file": "state/PROJ-809-llmxive-followup.yaml",
        "strict_mode": True,
        "allowed_categories": ["cs.CL", "physics.gen-ph", "q-bio.QM"],
        "min_abstract_length": 6,
        "target_authors": 20,
        "min_abstracts_per_author": 10,
        "collision_warning_threshold": 50,
        "ngram_orders": [4, 5, 6],
        "train_test_split": 0.2,
    }

def main():
    """
    Command-line entry point for configuration management.
    Usage:
      python code/config.py --init <path>   # Initialize a new config file
      python code/config.py --show          # Show current config
      python code/config.py --seed <int>    # Set seed
    """
    import argparse

    parser = argparse.ArgumentParser(description="llmXive Configuration Manager")
    parser.add_argument("--init", type=str, help="Path to initialize a new config file")
    parser.add_argument("--show", action="store_true", help="Display current configuration")
    parser.add_argument("--seed", type=int, help="Set the random seed")
    parser.add_argument("--load", type=str, help="Load configuration from a file")

    args = parser.parse_args()

    if args.init:
        ensure_dir(os.path.dirname(args.init))
        save_config(_config, args.init)
        print(f"Configuration initialized at {args.init}")
    elif args.show:
        print(json.dumps(_config, indent=2))
    elif args.seed is not None:
        set_seed(args.seed)
        print(f"Seed set to {get_seed()}")
    elif args.load:
        load_config(args.load)
        print(f"Configuration loaded from {args.load}")
        print(json.dumps(_config, indent=2))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()