"""
code/utils/config.py
--------------------

Minimal configuration helper used by the data‑fetching utilities.
The project does not currently expose a user‑editable configuration
file, so the implementation simply returns an empty dictionary.
This satisfies the import contract required by ``code/data/fetch_heas.py``
while remaining extensible for future settings.
"""
from pathlib import Path
import yaml

_CONFIG_CACHE = None

def get_config() -> dict:
    """
    Load a YAML configuration file if it exists.

    The function looks for ``config.yaml`` in the project root.
    If the file is not present, an empty dictionary is returned.
    The result is cached for subsequent calls.

    Returns
    -------
    dict
        Configuration mapping (may be empty).
    """
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE

    config_path = Path.cwd() / "config.yaml"
    if config_path.is_file():
        with config_path.open("r", encoding="utf-8") as f:
            _CONFIG_CACHE = yaml.safe_load(f) or {}
    else:
        _CONFIG_CACHE = {}
    return _CONFIG_CACHE
