"""
Configuration loader for ArchConfig definitions.

This module provides functions to load and validate architectural configurations
from the arch_configs.yaml file. Each ArchConfig defines structural parameters
(context window, model size, retrieval toggle) and sampling parameters
(temperature, top_p) for hypothesis generation.
"""

from __future__ import annotations

import pathlib
from typing import Any, Dict, List

import yaml

from llmxive_toolkit import get_logger

log = get_logger(__name__)

# Default path to the configuration file relative to the project root.
CONFIG_PATH = pathlib.Path(__file__).parent / "arch_configs.yaml"


def _validate_config_entry(entry: Dict[str, Any]) -> None:
    """
    Validate a single config dictionary.

    Args:
        entry: The dictionary representing one ArchConfig.

    Raises:
        ValueError: If any required key is missing.
    """
    required_keys = {
        "config_id",
        "model_name",
        "model_size_params",
        "context_window_tokens",
        "retrieval_augmented",
        "temperature",
        "top_p",
    }
    missing = required_keys - set(entry.keys())
    if missing:
        raise ValueError(
            f"Config entry missing required keys: {missing}. "
            f"Entry: {entry}"
        )

    # Validate types and ranges.
    if not isinstance(entry["config_id"], str):
        raise ValueError(f"config_id must be a string, got {type(entry['config_id'])}")
    if not isinstance(entry["model_size_params"], int):
        raise ValueError(
            f"model_size_params must be an int, got {type(entry['model_size_params'])}"
        )
    if not isinstance(entry["context_window_tokens"], int):
        raise ValueError(
            f"context_window_tokens must be an int, got {type(entry['context_window_tokens'])}"
        )
    if not isinstance(entry["retrieval_augmented"], bool):
        raise ValueError(
            f"retrieval_augmented must be a bool, got {type(entry['retrieval_augmented'])}"
        )
    if not isinstance(entry["temperature"], (int, float)):
        raise ValueError(
            f"temperature must be numeric, got {type(entry['temperature'])}"
        )
    if not isinstance(entry["top_p"], (int, float)):
        raise ValueError(f"top_p must be numeric, got {type(entry['top_p'])}")

    # Validate ranges.
    if entry["temperature"] < 0 or entry["temperature"] > 2:
        raise ValueError(
            f"temperature must be in [0, 2], got {entry['temperature']}"
        )
    if entry["top_p"] < 0 or entry["top_p"] > 1:
        raise ValueError(f"top_p must be in [0, 1], got {entry['top_p']}")
    if entry["model_size_params"] <= 0:
        raise ValueError(
            f"model_size_params must be positive, got {entry['model_size_params']}"
        )
    if entry["context_window_tokens"] <= 0:
        raise ValueError(
            f"context_window_tokens must be positive, got {entry['context_window_tokens']}"
        )


def load_arch_configs(path: pathlib.Path | str = CONFIG_PATH) -> List[Dict[str, Any]]:
    """
    Load and validate all ArchConfig definitions from the YAML file.

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
    path = pathlib.Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse YAML configuration file: {e}")

    if data is None:
        raise ValueError("Configuration file is empty")

    if "configs" not in data:
        raise ValueError(
            "Configuration file must contain a 'configs' section with a list of configurations"
        )

    configs = data["configs"]
    if not isinstance(configs, list):
        raise ValueError(
            f"'configs' section must be a list, got {type(configs)}"
        )

    if len(configs) == 0:
        raise ValueError("'configs' section must contain at least one configuration")

    # Validate each configuration entry.
    for i, entry in enumerate(configs):
        try:
            _validate_config_entry(entry)
        except ValueError as e:
            raise ValueError(f"Validation failed for config entry {i}: {e}")

    log.info(f"Loaded {len(configs)} ArchConfig(s) from {path}")
    return configs


def get_arch_config(
    config_id: str, path: pathlib.Path | str = CONFIG_PATH
) -> Dict[str, Any]:
    """
    Return a single ArchConfig by its ``config_id``.

    Args:
        config_id: Identifier of the desired configuration.
        path: Optional custom path to the YAML file (defaults to the bundled file).

    Returns:
        The configuration dictionary matching ``config_id``.

    Raises:
        KeyError: If ``config_id`` is not defined in the configuration file.
    """
    configs = load_arch_configs(path)
    for config in configs:
        if config["config_id"] == config_id:
            return config
    raise KeyError(
        f"ArchConfig '{config_id}' not found. Available configs: "
        f"{[c['config_id'] for c in configs]}"
    )