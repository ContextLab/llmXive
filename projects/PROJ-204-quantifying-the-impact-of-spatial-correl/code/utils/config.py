"""
code/utils/config.py
--------------------

Minimal configuration helper used by the ingestion pipeline and other
stages.  The function looks for a YAML file; if the path is ``None`` it
falls back to the default configuration file ``code/config.yaml`` (which
is created by task T106a).  When the file does not exist a sensible
default configuration dictionary is returned.
"""

import yaml
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_CONFIG = {
    "base_dir": ".",
    "log_dir": "logs",
}

def get_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load a YAML configuration file.

    Parameters
    ----------
    config_path: str | None
        Path to a YAML file.  If ``None`` the function searches for
        ``code/config.yaml`` relative to the project root.

    Returns
    -------
    dict
        Configuration dictionary.  Missing keys are filled with defaults.
    """
    if config_path is None:
        # Look for the default config file next to this module
        default_path = Path(__file__).parent / "config.yaml"
        if default_path.is_file():
            config_path = str(default_path)
    if config_path is None:
        # No configuration file – return the defaults
        return DEFAULT_CONFIG.copy()

    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f) or {}

    # Merge with defaults
    merged = DEFAULT_CONFIG.copy()
    merged.update(cfg)
    return merged
