"""Loader for ArchConfig definitions in src/config/arch_configs.yaml."""

from __future__ import annotations

import pathlib
from typing import Any, Dict, List

import yaml

CONFIG_PATH = pathlib.Path(__file__).resolve().parent / "arch_configs.yaml"

_REQUIRED_KEYS = (
    "config_id",
    "model_name",
    "model_size_params",
    "context_window_tokens",
    "retrieval_augmented",
    "temperature",
)


def load_arch_configs(path: pathlib.Path | str = CONFIG_PATH) -> List[Dict[str, Any]]:
    """Load and validate all ArchConfig definitions from the YAML file.

    Raises:
        FileNotFoundError: if the config file does not exist.
        ValueError: if any config entry is missing required keys or the
            file contains no configs.
    """
    path = pathlib.Path(path)
    if not path.exists():
        raise FileNotFoundError(f"ArchConfig file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    configs = data.get("configs")
    if not configs:
        raise ValueError(f"No 'configs' entries found in {path}")

    for cfg in configs:
        missing = [key for key in _REQUIRED_KEYS if key not in cfg]
        if missing:
            raise ValueError(
                f"Config '{cfg.get('config_id', '<unknown>')}' missing keys: {missing}"
            )
    return configs


def get_arch_config(config_id: str, path: pathlib.Path | str = CONFIG_PATH) -> Dict[str, Any]:
    """Return a single ArchConfig by its config_id.

    Raises:
        KeyError: if the config_id is not defined.
    """
    for cfg in load_arch_configs(path):
        if cfg["config_id"] == config_id:
            return cfg
    raise KeyError(f"Unknown ArchConfig id: {config_id}")
