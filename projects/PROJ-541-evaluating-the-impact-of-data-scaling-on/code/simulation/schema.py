import json
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import jsonschema
from jsonschema import validate, ValidationError


def load_seed_schema() -> Dict[str, Any]:
    """Load the seed schema from data/config/seed_schema.json."""
    schema_path = Path("data/config/seed_schema.json")
    if not schema_path.exists():
        raise FileNotFoundError(f"Seed schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return json.load(f)


def validate_seed_config(config: Dict[str, Any]) -> bool:
    """
    Validate the seed configuration against the schema defined in T005d.
    
    Requirement: Use jsonschema library to validate against data/config/seed_schema.json.
    Error Handling: Must raise ValidationError with a clear message if the config is invalid.
    
    Returns: True if valid (raises on invalid).
    """
    schema = load_seed_schema()
    try:
        validate(instance=config, schema=schema)
        return True
    except ValidationError as e:
        raise ValidationError(f"Seed config validation failed: {e.message}")


def load_seed_config() -> Dict[str, Any]:
    """Load the seed config from data/config/seed_config.json."""
    config_path = Path("data/config/seed_config.json")
    if not config_path.exists():
        return {}
    
    with open(config_path, 'r') as f:
        return json.load(f)


def save_seed_config_entry(batch_id: str, seed: int, config_hash: str) -> Dict[str, Any]:
    """
    Save a single seed config entry. 
    Note: This is a legacy helper. The main logic is now in logger.py save_seed_config.
    """
    # Delegate to the main implementation in logger.py if needed, 
    # but for schema.py we keep validation/loading logic here.
    # This function is kept for backward compatibility if called elsewhere.
    from code.simulation.logger import save_seed_config
    return save_seed_config(batch_id, seed, config_hash)


def get_seed_for_batch(batch_id: str) -> Optional[int]:
    """Retrieve the seed for a specific batch_id."""
    config = load_seed_config()
    if batch_id in config:
        return config[batch_id].get("seed")
    return None


def compute_config_hash(config: Dict[str, Any]) -> str:
    """Compute a hash of the configuration for reproducibility tracking."""
    config_str = json.dumps(config, sort_keys=True)
    return hashlib.sha256(config_str.encode()).hexdigest()
