"""
Checkpoint utility for resuming long-running scripts on CI timeout.

Provides functions to save and load intermediate state as JSON files.
State includes progress markers (e.g., last processed game ID) and
partial results to allow resumption without reprocessing completed items.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Default locations – can be monkey‑patched in tests
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CHECKPOINT_DIR = BASE_DIR / "data" / "checkpoints"


def ensure_checkpoint_dir(dir_path: Optional[Union[str, Path]] = None) -> Path:
    """
    Ensure a checkpoint directory exists.

    If ``dir_path`` is provided it is created (if necessary) and returned.
    Otherwise the module‑level ``CHECKPOINT_DIR`` is used.

    Returns:
        pathlib.Path: The directory that now exists.
    """
    target = Path(dir_path) if dir_path is not None else CHECKPOINT_DIR
    target.mkdir(parents=True, exist_ok=True)
    return target


def _resolve_path(
    location: Union[str, Path],
    filename: Optional[str] = None,
    default_dir: Optional[Path] = None,
) -> Path:
    """
    Helper to turn a flexible ``location``/``filename`` pair into a concrete Path.

    - If ``location`` is a Path and ``filename`` is ``None`` → treat it as the full file path.
    - If ``location`` is a Path or str and ``filename`` is supplied → join them.
    - If only ``location`` (a string) is supplied → interpret it as a filename
      and place it inside ``default_dir`` (or the module‑level ``CHECKPOINT_DIR``).

    This mirrors the historic API used throughout the project where some
    callers passed ``(dir, filename)`` and others passed just ``filename``.
    """
    if filename is None:
        # ``location`` is the full path (could be str or Path)
        return Path(location)
    # ``location`` is a directory, ``filename`` is the file name
    return Path(location) / filename


def save_checkpoint(
    location: Union[str, Path],
    state: Dict[str, Any],
    *,
    filename: Optional[str] = None,
) -> None:
    """
    Save ``state`` to a JSON checkpoint file.

    The function is deliberately tolerant of the two calling conventions
    used in the code base:

    1. ``save_checkpoint('my_checkpoint.json', state)`` – ``location`` is the
       filename and the default checkpoint directory is used.
    2. ``save_checkpoint(dir_path, state, filename='my_checkpoint.json')`` – a
       custom directory is supplied.

    Args:
        location: Either the full path to the checkpoint file or the directory
                  where the checkpoint should be stored.
        state:    The dictionary to serialise.
        filename: Optional filename when ``location`` is a directory.
    """
    # Resolve the final file path
    path = _resolve_path(location, filename, default_dir=CHECKPOINT_DIR)

    # Ensure the parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, default=str)
        print(f"Checkpoint saved: {path}")
    except Exception as e:
        raise RuntimeError(f"Failed to save checkpoint to {path}: {e}")


def load_checkpoint(
    location: Union[str, Path],
    *,
    filename: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Load a checkpoint JSON file if it exists.

    Mirrors the flexible calling patterns of :func:`save_checkpoint`.

    Args:
        location: Either the full path to the checkpoint file or the directory
                  containing the checkpoint.
        filename: Optional filename when ``location`` is a directory.

    Returns:
        The deserialized state dictionary, or ``None`` if the file does not exist.
    """
    path = _resolve_path(location, filename, default_dir=CHECKPOINT_DIR)

    if not path.exists():
        return None

    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Warning: Checkpoint file {path} is corrupted. Ignoring.")
        return None
    except Exception as e:
        raise RuntimeError(f"Failed to load checkpoint from {path}: {e}")


def delete_checkpoint(
    location: Union[str, Path],
    *,
    filename: Optional[str] = None,
) -> bool:
    """
    Delete a checkpoint file after successful completion.

    Args:
        location: Either the full path to the checkpoint file or the directory
                  containing the checkpoint.
        filename: Optional filename when ``location`` is a directory.

    Returns:
        ``True`` if the file was deleted, ``False`` if it did not exist.
    """
    path = _resolve_path(location, filename, default_dir=CHECKPOINT_DIR)

    if path.exists():
        try:
            path.unlink()
            print(f"Checkpoint deleted: {path}")
            return True
        except Exception as e:
            print(f"Warning: Failed to delete checkpoint {path}: {e}")
            return False
    return False


def get_checkpoint_path(
    location: Union[str, Path],
    *,
    filename: Optional[str] = None,
) -> Path:
    """
    Return the full path to a checkpoint file.

    This helper is used by scripts that build the path themselves
    (e.g., ``get_checkpoint_path('fetch_data')``) as well as those that
    supply a custom directory (e.g., ``get_checkpoint_path(dir, filename='x.json')``).

    Args:
        location: Either a directory or the full file path.
        filename: Optional filename when ``location`` is a directory.

    Returns:
        pathlib.Path pointing at the checkpoint file.
    """
    return _resolve_path(location, filename, default_dir=CHECKPOINT_DIR)


# Backwards‑compatible aliases (the original code imported these names)
__all__ = [
    "ensure_checkpoint_dir",
    "save_checkpoint",
    "load_checkpoint",
    "delete_checkpoint",
    "get_checkpoint_path",
    "BASE_DIR",
    "CHECKPOINT_DIR",
]
