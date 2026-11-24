"""Configuration loader for ArchConfig definitions.

This module provides two public functions:
  - ``load_arch_configs``: Load and validate all ArchConfig entries from the
    YAML file.
  - ``get_arch_config``: Retrieve a single ArchConfig by its ``config_id``.

The implementation is deliberately lightweight and uses only the standard
library plus ``pyyaml`` (already available via the project's ``requirements.txt``).
"""

from __future__ import annotations

import pathlib
from typing import Any, Dict, List

import yaml

from llmxive_toolkit import get_logger

log = get_logger(__name__)

# Path to the default configuration file bundled with the package.
CONFIG_PATH = pathlib.Path(__file__).with_name("arch_configs.yaml")

# --------------------------------------------------------------------------- #
# Helper validation utilities
# --------------------------------------------------------------------------- #

_REQUIRED_KEYS = {
    "config_id",
    "model_name",
    "model_size_params",
    "context_window_tokens",
    "retrieval_augmented",
    "temperature",
    "top_p",
}


def _validate_config_entry(entry: Dict[str, Any]) -> None:
    """Validate a single ArchConfig dictionary.

    Args:
        entry: The dictionary representing one ArchConfig.

    Raises:
        ValueError: If any required key is missing.
    """
    missing = _REQUIRED_KEYS - entry.keys()
    if missing:
        raise ValueError(
            f"ArchConfig entry missing required keys: {sorted(missing)}"
        )
    # Additional type/value checks can be added here if desired.
    log.debug("Validated ArchConfig entry %s", entry.get("config_id"))


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def load_arch_configs(
    path: pathlib.Path | str = CONFIG_PATH,
) -> List[Dict[str, Any]]:
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
    if not cfg_path.is_file():
        raise FileNotFoundError(f"ArchConfig file not found: {cfg_path}")

    with cfg_path.open("r", encoding="utf-8") as f:
        try:
            raw_cfg = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            raise ValueError(f"Failed to parse YAML config: {exc}") from exc

    if not isinstance(raw_cfg, dict) or "configs" not in raw_cfg:
        raise ValueError("Config file must contain a top‑level 'configs' key.")

    configs = raw_cfg["configs"]
    if not isinstance(configs, list):
        raise ValueError("'configs' must be a list of configuration dictionaries.")

    for entry in configs:
        if not isinstance(entry, dict):
            raise ValueError("Each config entry must be a dictionary.")
        _validate_config_entry(entry)

    log.info("Loaded %d ArchConfig entries from %s", len(configs), cfg_path)
    return configs


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
            log.debug("Found ArchConfig for id %s", config_id)
            return cfg
    raise KeyError(f"ArchConfig with id '{config_id}' not found.")
