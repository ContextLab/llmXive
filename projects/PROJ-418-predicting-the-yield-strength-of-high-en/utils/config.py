"""
utils/config.py
----------------

Minimal configuration helper for the project. In production this could
read a YAML/JSON configuration file or environment variables. For the
purposes of the current tasks we only need a callable ``get_config``
that returns a dictionary (possibly empty) so that modules such as
``data.fetch_heas`` can retrieve optional configuration values without
raising import errors.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any

import yaml


def _default_config_path() -> Path:
    """
    Return the default path where a configuration file would be located.
    The project does not ship a config file, so this simply points to a
    conventional location under the project root.
    """
    # ``utils`` lives at <project_root>/utils; the root is its parent.
    return Path(__file__).resolve().parents[1] / "config.yaml"


def get_config() -> Dict[str, Any]:
    """
    Load a YAML configuration file if it exists, otherwise return an
    empty dictionary.

    Returns
    -------
    dict
        Configuration mapping. Currently only the key
        ``hea_dataset_url`` is consulted by ``data.fetch_heas``.
    """
    config_path = _default_config_path()
    if config_path.is_file():
        try:
            with config_path.open("r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as exc:
            # If parsing fails we fall back to an empty config – the
            # calling code will treat the absence of a value as “use the
            # default/fallback” behaviour.
            import logging

            logging.getLogger(__name__).warning(
                "Failed to parse config file %s: %s – using empty config",
                config_path,
                exc,
            )
            return {}
    # No config file – return empty dict.
    return {}
