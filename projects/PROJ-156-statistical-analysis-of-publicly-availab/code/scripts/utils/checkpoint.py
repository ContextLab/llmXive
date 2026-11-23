"""
Utility functions for saving, loading, and deleting JSON checkpoint files.
Provides a simple API used throughout the pipeline and unit tests.
"""
import json
from pathlib import Path
from typing import Any, Dict, Union

# Default directory for checkpoints (project-owned location)
# Exposed as CHECKPOINT_DIR for tests that monkey-patch it.
CHECKPOINT_DIR: Path = Path("data") / "checkpoints"

def ensure_checkpoint_dir(base_dir: Union[str, Path] = None) -> Path:
    """
    Ensure that the checkpoint directory exists.

    Parameters
    ----------
    base_dir : str | Path, optional
        If provided, the directory is created relative to this path.
        Otherwise ``CHECKPOINT_DIR`` is used.

    Returns
    -------
    pathlib.Path
        The path to the directory that now exists.
    """
    dir_path = Path(base_dir) if base_dir is not None else CHECKPOINT_DIR
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path

def get_checkpoint_path(*args: Any) -> Path:
    """
    Resolve a checkpoint file path.

    Two calling styles are supported:
    1. ``get_checkpoint_path("fetch_checkpoint.json")`` – returns
       ``<CHECKPOINT_DIR>/fetch_checkpoint.json``.
    2. ``get_checkpoint_path(custom_dir, "fetch_data")`` – returns
       ``<custom_dir>/fetch_data`` (the name can include an extension).

    Parameters
    ----------
    *args : Any
        Either a single filename (or relative path) or a base directory
        followed by a filename.

    Returns
    -------
    pathlib.Path
        The resolved absolute path.
    """
    if len(args) == 1:
        # Only a filename – use default checkpoint directory
        filename = args[0]
        base_dir = CHECKPOINT_DIR
    elif len(args) == 2:
        base_dir, filename = args
    else:
        raise ValueError("get_checkpoint_path expects 1 or 2 arguments")
    return Path(base_dir) / filename

def _resolve_path(path: Union[str, Path]) -> Path:
    """
    Resolve a possibly-relative checkpoint path. If ``path`` is just a 
    filename (no directory components), it is interpreted relative to 
    ``CHECKPOINT_DIR``.
    """
    p = Path(path)
    # If the path is just a filename, p.name will equal the string representation of p.
    if p.name == str(p):
        return CHECKPOINT_DIR / p
    return p

def save_checkpoint(state_or_path: Union[Dict, str, Path],
                    path_or_state: Union[Dict, str, Path, None] = None) -> None:
    """
    Persist a checkpoint dictionary to a JSON file.

    The function is flexible and accepts arguments in either order:
    ``save_checkpoint(state, path)`` or ``save_checkpoint(path, state)``.

    Parameters
    ----------
    state_or_path : dict | str | pathlib.Path
        Either the checkpoint data (if ``path_or_state`` is a path) or the
        destination path (if ``path_or_state`` is a dict).
    path_or_state : dict | str | pathlib.Path, optional
        The complementary argument.
    """
    # Resolve arguments
    if isinstance(state_or_path, dict) and path_or_state is not None:
        state = state_or_path
        path = _resolve_path(path_or_state)
    elif isinstance(path_or_state, dict) and state_or_path is not None:
        state = path_or_state
        path = _resolve_path(state_or_path)
    else:
        raise ValueError("save_checkpoint requires one dict and one path argument")

    # Ensure the parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)

def load_checkpoint(path: Union[str, Path]) -> Union[Dict, None]:
    """
    Load a checkpoint JSON file.

    Returns ``None`` if the file does not exist.

    Parameters
    ----------
    path : str | pathlib.Path
        The path to the checkpoint file.

    Returns
    -------
    dict | None
        The checkpoint contents, or ``None`` if the file does not exist.
    """
    p = _resolve_path(path)
    if not p.is_file():
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def delete_checkpoint(path: Union[str, Path]) -> bool:
    """
    Delete a checkpoint file if it exists.

    Parameters
    ----------
    path : str | pathlib.Path
        The path to the checkpoint file.

    Returns
    -------
    bool
        ``True`` if the file was removed, ``False`` otherwise.
    """
    p = _resolve_path(path)
    try:
        p.unlink()
        return True
    except FileNotFoundError:
        return False
    except Exception:
        return False
