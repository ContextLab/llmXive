"""Schema definitions and validation for seed configuration."""
import json
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Path to the seed configuration file
SEED_CONFIG_PATH = Path("code/simulation/seed_config.json")

# JSON Schema definition for seed_config.json
SEED_CONFIG_SCHEMA = {
    "type": "object",
    "patternProperties": {
        "^batch_[0-9]+$": {  # Keys must look like batch_N
            "type": "object",
            "properties": {
                "seed": {"type": "integer"},
                "timestamp": {"type": "string", "format": "date-time"},
                "config_hash": {"type": "string", "minLength": 64, "maxLength": 64}
            },
            "required": ["seed", "timestamp", "config_hash"]
        }
    },
    "additionalProperties": False
}

def validate_seed_config(config: Dict[str, Any]) -> bool:
    """
    Validate a seed configuration dictionary against the schema.
    Returns True if valid, False otherwise.
    """
    # Basic type check
    if not isinstance(config, dict):
        return False

    # Check that all keys follow the batch_N pattern
    import re
    batch_pattern = re.compile(r'^batch_[0-9]+$')
    for key in config.keys():
        if not batch_pattern.match(key):
            return False

    # Check each batch entry
    for batch_id, entry in config.items():
        if not isinstance(entry, dict):
            return False

        # Check required fields
        required_fields = ["seed", "timestamp", "config_hash"]
        for field in required_fields:
            if field not in entry:
                return False

        # Type checks
        if not isinstance(entry["seed"], int):
            return False
        if not isinstance(entry["timestamp"], str):
            return False
        if not isinstance(entry["config_hash"], str):
            return False

        # Config hash should be a valid SHA256 hex string (64 chars)
        if len(entry["config_hash"]) != 64:
            return False
        try:
            int(entry["config_hash"], 16)
        except ValueError:
            return False

    return True

def load_seed_config() -> Dict[str, Any]:
    """
    Load the seed configuration from disk.
    Returns an empty dict if the file doesn't exist.
    """
    if not SEED_CONFIG_PATH.exists():
        return {}

    try:
        with open(SEED_CONFIG_PATH, 'r') as f:
            config = json.load(f)
        if not validate_seed_config(config):
            # If validation fails, return empty config to avoid corruption
            return {}
        return config
    except (json.JSONDecodeError, IOError):
        return {}

def save_seed_config(batch_id: str, seed: int, config_hash: str) -> None:
    """
    Append a new batch's seed configuration to the seed_config.json file.
    The file is append-only: existing keys are never overwritten.
    
    Args:
        batch_id: The batch identifier (e.g., 'batch_1')
        seed: The random seed for this batch
        config_hash: SHA256 hash of the configuration
    """
    # Load existing config
    config = load_seed_config()

    # Check if batch_id already exists (should not happen in normal operation)
    if batch_id in config:
        # Skip to avoid overwriting (append-only policy)
        return

    # Create new entry
    new_entry = {
        "seed": seed,
        "timestamp": datetime.utcnow().isoformat(),
        "config_hash": config_hash
    }

    # Add to config
    config[batch_id] = new_entry

    # Validate before writing
    if not validate_seed_config(config):
        raise ValueError(f"Invalid seed configuration after adding {batch_id}")

    # Ensure directory exists
    SEED_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Write to file
    with open(SEED_CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)

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

def compute_config_hash(config_dict: Dict[str, Any]) -> str:
    """
    Compute a SHA256 hash of a configuration dictionary.
    
    Args:
        config_dict: The configuration dictionary to hash
        
    Returns:
        Hexadecimal string of the SHA256 hash
    """
    # Serialize with sorted keys for consistency
    config_str = json.dumps(config_dict, sort_keys=True)
    return hashlib.sha256(config_str.encode()).hexdigest()
