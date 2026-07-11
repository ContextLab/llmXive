"""
Configuration management for the llmXive project.
"""
import json
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, List

import yaml

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "state" / "config.yaml"
SEED = 42

# Global state
_config: Optional[Dict[str, Any]] = None
_seed: int = SEED


def load_config() -> Dict[str, Any]:
    """
    Load configuration from state/config.yaml or return defaults.
    """
    global _config
    if _config is not None:
        return _config

    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r') as f:
            _config = yaml.safe_load(f)
    else:
        _config = {
            "seed": SEED,
            "paths": {
                "raw_data": "data/raw",
                "processed_data": "data/processed",
                "models": "artifacts/models",
                "metrics": "artifacts/metrics"
            }
        }
    return _config


def set_seed(seed: int) -> None:
    """
    Set the global random seed.
    """
    global _seed
    _seed = seed
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)


def get_seed() -> int:
    """
    Get the current global random seed.
    """
    global _seed
    return _seed


def load_schema(schema_name: str) -> Dict[str, Any]:
    """
    Load a schema definition from the contracts directory.
    """
    schema_path = PROJECT_ROOT / "contracts" / f"{schema_name}.json"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return json.load(f)


def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate data against a schema (simple implementation).
    """
    # Basic check for required keys
    if "required" in schema:
        for key in schema["required"]:
            if key not in data:
                return False
    return True


def get_contract_paths() -> List[str]:
    """
    Get list of contract file paths.
    """
    contracts_dir = PROJECT_ROOT / "contracts"
    if not contracts_dir.exists():
        return []
    return [str(p) for p in contracts_dir.glob("*.json")]


def save_config(config: Dict[str, Any]) -> None:
    """
    Save configuration to state/config.yaml.
    """
    ensure_dir(CONFIG_PATH.parent)
    with open(CONFIG_PATH, 'w') as f:
        yaml.dump(config, f)


def reset_config() -> None:
    """
    Reset configuration to defaults.
    """
    global _config, _seed
    _config = None
    _seed = SEED


def ensure_dir(path: Path) -> None:
    """
    Ensure directory exists.
    """
    path.mkdir(parents=True, exist_ok=True)


def main():
    """
    Main entry point for config module.
    """
    config = load_config()
    print(f"Loaded config: {config}")
    print(f"Current seed: {get_seed()}")


if __name__ == "__main__":
    main()
