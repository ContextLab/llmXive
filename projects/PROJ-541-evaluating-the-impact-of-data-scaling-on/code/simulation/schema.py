"""
Simulation seed‑configuration schema handling.

This module provides utilities for:
* Computing a deterministic hash of a SimulationConfig.
* Persisting a per‑batch seed configuration to ``data/config/seed_config.json``.
* Loading and validating the persisted seed configuration.
"""

from __future__ import annotations

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from llmxive_toolkit import paths, get_logger
from jsonschema import validate, ValidationError

log = get_logger(__name__)

# Path to the JSON file that stores seed configurations.
SEED_CONFIG_PATH: Path = paths.data("config", "seed_config.json")

# Load the JSON schema used for validation.
_SCHEMA_PATH: Path = paths.data("config", "seed_schema.json")
with _SCHEMA_PATH.open("r", encoding="utf-8") as f:
    _SEED_SCHEMA: Dict[str, Any] = json.load(f)


def compute_config_hash(config: Any) -> str:
    """
    Compute a SHA‑256 hash that uniquely identifies a SimulationConfig.

    The function serialises the config (using ``json.dumps`` with sorted keys)
    and hashes the resulting string.

    Parameters
    ----------
    config: Any
        A dataclass, dictionary or any JSON‑serialisable object representing the
        simulation configuration.

    Returns
    -------
    str
        64‑character hexadecimal SHA‑256 digest.
    """
    # Ensure a deterministic representation.
    config_json = json.dumps(config, sort_keys=True, default=str)
    return hashlib.sha256(config_json.encode("utf-8")).hexdigest()


def _ensure_file_exists() -> None:
    """Create an empty JSON object at ``SEED_CONFIG_PATH`` if the file does not exist."""
    if not SEED_CONFIG_PATH.parent.exists():
        SEED_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not SEED_CONFIG_PATH.exists():
        SEED_CONFIG_PATH.write_text("{}", encoding="utf-8")


def load_seed_config() -> Dict[str, Any]:
    """
    Load the seed‑configuration JSON file.

    Returns
    -------
    dict
        Mapping from ``batch_id`` to a dictionary containing ``seed``, ``timestamp`` and
        ``config_hash``.
    """
    _ensure_file_exists()
    with SEED_CONFIG_PATH.open("r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("Seed config file must contain a JSON object.")
            return data
        except json.JSONDecodeError as exc:
            log.error(f"Failed to parse seed config: {exc}")
            raise


def save_seed_config(batch_id: str, seed: int, config_hash: str) -> None:
    """
    Append a new batch entry to ``seed_config.json``.

    The function is **append‑only**: if ``batch_id`` already exists the call is a no‑op.

    Parameters
    ----------
    batch_id: str
        Identifier for the batch (e.g. ``simulation_2024_09_13_001``).
    seed: int
        Random seed used for the batch.
    config_hash: str
        SHA‑256 hash of the configuration used in the batch.
    """
    if not isinstance(batch_id, str) or not batch_id:
        raise ValueError("batch_id must be a non‑empty string")
    if not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    if not isinstance(config_hash, str) or len(config_hash) != 64:
        raise ValueError("config_hash must be a 64‑character SHA‑256 hex string")

    _ensure_file_exists()
    data = load_seed_config()

    if batch_id in data:
        # Append‑only semantics – do not overwrite existing entry.
        log.debug(f"Batch '{batch_id}' already present in seed config; skipping write.")
        return

    data[batch_id] = {
        "seed": seed,
        "timestamp": datetime.utcnow().isoformat(),
        "config_hash": config_hash,
    }

    # Validate before persisting.
    if not validate_seed_config(data):
        raise ValueError("Resulting seed config does not conform to schema.")

    with SEED_CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    log.info(f"Saved seed config for batch '{batch_id}'.")


def validate_seed_config(config: Dict[str, Any]) -> bool:
    """
    Validate a seed‑configuration dictionary against the JSON schema.

    Parameters
    ----------
    config: dict
        The loaded JSON object to validate.

    Returns
    -------
    bool
        ``True`` if the config conforms to the schema, ``False`` otherwise.
    """
    try:
        validate(instance=config, schema=_SEED_SCHEMA)
        return True
    except ValidationError as exc:
        log.error(f"Seed config validation error: {exc.message}")
        return False


def get_seed_for_batch(batch_id: str) -> Optional[int]:
    """
    Retrieve the stored seed for a given ``batch_id``.

    Parameters
    ----------
    batch_id: str

    Returns
    -------
    Optional[int]
        The seed if the batch exists, otherwise ``None``.
    """
    config = load_seed_config()
    entry = config.get(batch_id)
    if entry:
        return entry.get("seed")
    return None
