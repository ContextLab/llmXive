"""
Checkpoint utility module.

Provides simple functions to save and load JSON checkpoint files,
and to obtain a standard checkpoint file path.

The API matches the contract required by task T015a and the unit tests:
  - save_checkpoint(state: dict, path: str) -> None
  - load_checkpoint(path: str) -> dict
  - get_checkpoint_path(name: str) -> pathlib.Path
  - ensure_checkpoint_dir() -> pathlib.Path

All paths are resolved relative to the project root and are stored under
the ``data/checkpoints`` directory, which is the only project‑owned
location for checkpoint files.
"""

import json
from pathlib import Path
from typing import Dict

# Default directory for all checkpoints
_DEFAULT_CHECKPOINT_DIR = Path("data/checkpoints")


def ensure_checkpoint_dir() -> Path:
    """
    Ensure that the default checkpoint directory exists.

    Returns
    -------
    pathlib.Path
        The path to the checkpoint directory.
    """
    _DEFAULT_CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    return _DEFAULT_CHECKPOINT_DIR


def _resolve_path(path: str) -> Path:
    """
    Resolve a user‑provided path to an absolute ``Path`` object.

    If the path is relative, it is interpreted relative to the default
    checkpoint directory.

    Parameters
    ----------
    path : str
        The path supplied by the caller.

    Returns
    -------
    pathlib.Path
        The resolved path.
    """
    p = Path(path)
    if not p.is_absolute():
        p = ensure_checkpoint_dir() / p
    return p


def save_checkpoint(state: Dict, path: str) -> None:
    """
    Save a checkpoint dictionary to ``path`` as JSON.

    The function overwrites any existing file.

    Parameters
    ----------
    state : dict
        The checkpoint state to serialise.
    path : str
        Destination file path (relative to the project root or absolute).
    """
    p = _resolve_path(path)
    # Ensure parent directory exists
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def load_checkpoint(path: str) -> Dict:
    """
    Load a checkpoint JSON file.

    If the file does not exist, an empty dictionary is returned.

    Parameters
    ----------
    path : str
        Path to the checkpoint file.

    Returns
    -------
    dict
        The checkpoint contents, or an empty dict if the file is missing.
    """
    p = _resolve_path(path)
    if not p.is_file():
        return {}
    with p.open("r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            # Guard against malformed content
            return {}
        except json.JSONDecodeError:
            # Corrupt checkpoint – treat as empty
            return {}


def get_checkpoint_path(name: str) -> Path:
    """
    Return the canonical checkpoint file path for a given ``name``.

    The convention is ``data/checkpoints/<name>_checkpoint.json``.

    Parameters
    ----------
    name : str
        Logical name of the checkpoint (e.g., ``'fetch'`` or ``'preprocess'``).

    Returns
    -------
    pathlib.Path
        Full path to the checkpoint file.
    """
    ensure_checkpoint_dir()
    filename = f"{name}_checkpoint.json"
    return _DEFAULT_CHECKPOINT_DIR / filename
