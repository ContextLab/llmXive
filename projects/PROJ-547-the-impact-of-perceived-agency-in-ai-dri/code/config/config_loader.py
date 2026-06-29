"""
Configuration Loader Module
----------------------------

Provides a simple utility to load YAML configuration files from the
``configs/`` directory (or any explicit path). The loader returns the
parsed content as a Python dictionary.

The implementation is deliberately lightweight: it relies on PyYAML's
``safe_load`` to avoid executing arbitrary code and uses :class:`pathlib.Path`
for robust path handling.
"""

from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any, Dict, Union

__all__ = ["load_config", "ConfigLoader"]


def _resolve_path(config_path: Union[str, Path]) -> Path:
    """
    Resolve the provided ``config_path`` to an absolute :class:`Path`.

    If ``config_path`` is a relative path, it is interpreted as relative to the
    project's ``configs/`` directory.
    """
    path = Path(config_path)
    if not path.is_absolute():
        # Assume relative to the top‑level ``configs`` directory
        path = Path(__file__).resolve().parents[2] / "configs" / path
    return path


def load_config(config_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a YAML configuration file and return its contents as a dictionary.

    Parameters
    ----------
    config_path:
        Path to the YAML file.  Can be absolute or relative to the ``configs/``
        directory.

    Returns
    -------
    dict
        Parsed YAML content.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    yaml.YAMLError
        If the file cannot be parsed as valid YAML.
    """
    path = _resolve_path(config_path)
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError("Top‑level YAML content must be a mapping (dictionary).")
    return data


class ConfigLoader:
    """
    Object‑oriented wrapper around :func:`load_config`.

    Example
    -------
    >>> loader = ConfigLoader()
    >>> cfg = loader.load("example.yaml")
    >>> cfg["some_key"]
    """

    def __init__(self, base_dir: Union[str, Path] | None = None) -> None:
        """
        Parameters
        ----------
        base_dir:
            Optional base directory to resolve relative config paths.
            If ``None`` (default), the project's top‑level ``configs/`` directory
            is used.
        """
        if base_dir is None:
            self.base_dir = Path(__file__).resolve().parents[2] / "configs"
        else:
            self.base_dir = Path(base_dir).expanduser().resolve()

    def load(self, config_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load a YAML file using the loader's ``base_dir`` as the reference point
        for relative paths.
        """
        path = Path(config_path)
        if not path.is_absolute():
            path = self.base_dir / path
        return load_config(path)
