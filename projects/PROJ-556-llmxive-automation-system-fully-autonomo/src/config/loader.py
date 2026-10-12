"""
Loader utilities for ArchConfig definitions.

This module provides two public functions:
- `load_arch_configs`: Load and validate all ArchConfig entries from the YAML file.
- `get_arch_config`: Retrieve a single ArchConfig by its `config_id`.

The configuration file is expected to be located at the same directory as this
module and named ``arch_configs.yaml``. The YAML schema follows the example
provided in the project documentation and includes ``defaults`` and a list of
``configs``. Each config must contain the required keys listed in
``REQUIRED_KEYS``; otherwise a ``ValueError`` is raised.

The functions raise:
- ``FileNotFoundError`` if the configuration file does not exist.
- ``ValueError`` for structural validation errors.
- ``KeyError`` when a requested ``config_id`` is not present.
"""

from __future__ import annotations

import pathlib
from typing import Any, Dict, List

import yaml

from llmxive_toolkit import get_logger

log = get_logger(__name__)

# Path to the YAML configuration file (same directory as this loader)
CONFIG_PATH = pathlib.Path(__file__).with_name("arch_configs.yaml")

# Keys that must be present in each individual config entry
REQUIRED_KEYS = {
    "config_id",
    "model_name",
    "model_size_params",
    "context_window_tokens",
    "retrieval_augmented",
    "temperature",
    "top_p",
}

def _validate_config_entry(entry: Dict[str, Any]) -> None:
    """Validate a single config dictionary.

    Args:
        entry: The dictionary representing one ArchConfig.

    Raises:
        ValueError: If any required key is missing.
    """
    missing = REQUIRED_KEYS - entry.keys()
    if missing:
        raise ValueError(
            f"ArchConfig entry missing required keys: {sorted(missing)}. "
            f"Entry: {entry}"
        )
    # Additional optional validation can be added here (e.g., type checks).

def load_arch_configs(path: pathlib.Path | str = CONFIG_PATH) -> List[Dict[str, Any]]:
    """Load and validate all ArchConfig definitions from the YAML file.

    Args:
        path: Path to the ``arch_configs.yaml`` file. Defaults to the module‑level
              ``CONFIG_PATH`` which points to the bundled configuration.

    Returns:
        A list of dictionaries, each representing a validated ArchConfig.

    Raises:
        FileNotFoundError: If the config file does not exist.
        ValueError: If the file cannot be parsed, lacks the ``configs`` section,
                    or any entry fails validation.
    """
    cfg_path = pathlib.Path(path)
    log.debug("Loading ArchConfig definitions from %s", cfg_path)

    if not cfg_path.is_file():
        raise FileNotFoundError(f"ArchConfig file not found at {cfg_path}")

    with cfg_path.open("r", encoding="utf-8") as f:
        try:
            raw_cfg = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            raise ValueError(f"Failed to parse YAML config at {cfg_path}: {exc}") from exc

    if not isinstance(raw_cfg, dict):
        raise ValueError(f"Expected top‑level mapping in {cfg_path}, got {type(raw_cfg)}")

    configs = raw_cfg.get("configs")
    if configs is None:
        raise ValueError(f"'configs' section missing in {cfg_path}")
    if not isinstance(configs, list):
        raise ValueError(f"'configs' must be a list in {cfg_path}")

    validated: List[Dict[str, Any]] = []
    for entry in configs:
        if not isinstance(entry, dict):
            raise ValueError(f"Each config entry must be a mapping, got {type(entry)}")
        _validate_config_entry(entry)
        validated.append(entry)

    log.info("Loaded %d ArchConfig entries from %s", len(validated), cfg_path)
    return validated

def get_arch_config(
    config_id: str,
    path: pathlib.Path | str = CONFIG_PATH,
) -> Dict[str, Any]:
    """Return a single ArchConfig by its ``config_id``.

    Args:
        config_id: Identifier of the desired configuration.
        path: Optional custom path to the YAML file (defaults to the bundled file).

    Returns:
        The configuration dictionary matching ``config_id``.

    Raises:
        KeyError: If ``config_id`` is not defined in the configuration file.
    """
    configs = load_arch_configs(path)
    for cfg in configs:
        if cfg.get("config_id") == config_id:
            log.debug("Found ArchConfig for id=%s", config_id)
            return cfg
    raise KeyError(f"ArchConfig with config_id '{config_id}' not found.")