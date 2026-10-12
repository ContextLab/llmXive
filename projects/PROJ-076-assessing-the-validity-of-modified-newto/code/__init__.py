"""
Project‑level utilities.

Currently provides a simple loader for the ``data/metadata.yaml`` configuration
file used throughout the pipeline.
"""

import yaml
from pathlib import Path
from typing import Any, Dict

__all__ = ["load_metadata"]


def load_metadata(metadata_path: str = "data/metadata.yaml") -> Dict[str, Any]:
    """
    Load the project's ``metadata.yaml`` file.

    Parameters
    ----------
    metadata_path : str, optional
        Path to the metadata YAML file. Defaults to ``data/metadata.yaml``.

    Returns
    -------
    dict
        Parsed metadata dictionary. Returns an empty dict if the file does not
        exist or cannot be parsed.
    """
    path = Path(metadata_path)
    if not path.is_file():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        # In a research pipeline we prefer a hard failure; however, for
        # robustness during testing we return an empty dict.
        return {}
