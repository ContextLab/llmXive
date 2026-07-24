"""Schema validation and seed configuration management."""
import json
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Path to the seed configuration file
SEED_CONFIG_PATH = Path(__file__).parent / "seed_config.json"

# JSON Schema definition for seed_config
SEED_SCHEMA = {
    "type": "object",
    "additionalProperties": {
        "type": "object",
        "properties": {
            "seed": {"type": "integer"},
            "timestamp": {"type": "string"},
            "config_hash": {"type": "string"}
        },
        "required": ["seed", "timestamp", "config_hash"]
    }
}


def validate_seed_config(config: Dict[str, Any]) -> bool:
    """
    Validate a seed configuration dictionary against the schema.

    Args:
        config: Dictionary to validate

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(config, dict):
        return False

    for batch_id, entry in config.items():
        if not isinstance(entry, dict):
            return False
        if not isinstance(entry.get("seed"), int):
            return False
        if not isinstance(entry.get("timestamp"), str):
            return False
        if not isinstance(entry.get("config_hash"), str):
            return False

    return True


def load_seed_config() -> Dict[str, Any]:
    """
    Load the seed configuration from the JSON file.

    Returns:
        Dictionary containing the seed configuration, or empty dict if file doesn't exist.
    """
    if not SEED_CONFIG_PATH.exists():
        return {}

    try:
        with open(SEED_CONFIG_PATH, 'r') as f:
            config = json.load(f)
            if validate_seed_config(config):
                return config
            else:
                # If validation fails, return empty config to avoid corruption
                return {}
    except (json.JSONDecodeError, IOError):
        return {}


def save_seed_config(batch_id: str, seed: int, config: Dict[str, Any]) -> None:
    """
    Append a new batch's seed configuration to the seed_config.json file.
    This function is append-only; existing entries are never overwritten.

    Args:
        batch_id: Unique identifier for the batch
        seed: Random seed used for this batch
        config: Simulation configuration dictionary to hash
    """
    # Load existing config
    existing_config = load_seed_config()

    # Generate config hash
    config_str = json.dumps(config, sort_keys=True)
    config_hash = hashlib.sha256(config_str.encode()).hexdigest()

    # Create new entry
    timestamp = datetime.utcnow().isoformat()
    new_entry = {
        "seed": seed,
        "timestamp": timestamp,
        "config_hash": config_hash
    }

    # Append to existing config (batch_id is the key)
    existing_config[batch_id] = new_entry

    # Validate before writing
    if not validate_seed_config(existing_config):
        raise ValueError("Generated seed config failed validation")

    # Ensure directory exists
    SEED_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Write to file
    with open(SEED_CONFIG_PATH, 'w') as f:
        json.dump(existing_config, f, indent=2)


def get_seed_for_batch(batch_id: str) -> Optional[int]:
    """
    Retrieve the seed for a specific batch.

    Args:
        batch_id: The batch identifier

    Returns:
        The seed integer if found, None otherwise
    """
    config = load_seed_config()
    if batch_id in config:
        return config[batch_id].get("seed")
    return None
