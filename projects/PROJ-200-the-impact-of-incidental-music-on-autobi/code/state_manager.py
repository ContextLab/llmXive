"""
State manager for the project.

Provides utilities to compute file checksums, load and save a central
``state.yaml`` file, register new artifacts, verify integrity, and clean
stale entries.

The ``state.yaml`` file lives at the project root (``paths.root``) and
contains three top‑level keys required by the specification:

- ``artifact_hashes`` – a mapping from relative file paths to metadata
  (checksum, size, registration timestamp, optional description).
- ``updated_at`` – ISO‑8601 timestamp of the last modification of the
  state file.
- ``config`` – a placeholder for any future configuration values.

All helper functions operate on relative POSIX paths (e.g. ``data/processed/file.parquet``)
and raise clear errors when expectations are not met.
"""

import hashlib
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Internal helpers
# ----------------------------------------------------------------------


def _state_path() -> Path:
    """Return the absolute Path to ``state.yaml`` at the project root."""
    return paths.root / "state.yaml"


def _compute_file_checksum(file_path: Path) -> str:
    """
    Compute the SHA‑256 checksum of the file at ``file_path``.

    Parameters
    ----------
    file_path: Path
        Path to the file whose checksum should be calculated.

    Returns
    -------
    str
        64‑character hexadecimal SHA‑256 digest.
    """
    if not file_path.is_file():
        raise FileNotFoundError(f"Cannot compute checksum – file does not exist: {file_path}")

    sha256 = hashlib.sha256()
    # Read in chunks to avoid loading huge files into memory
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------


def load_state() -> Dict[str, Any]:
    """
    Load the ``state.yaml`` file.

    If the file does not exist, a default state with the required top‑level
    keys is returned.

    Returns
    -------
    dict
        The parsed YAML content.
    """
    state_file = _state_path()
    if not state_file.exists():
        log.info("State file not found – creating a default empty state.")
        return {
            "artifact_hashes": {},
            "updated_at": datetime.utcnow().isoformat(),
            "config": {}
        }

    with state_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    # Ensure the required top‑level keys exist (backwards compatibility)
    for key in ("artifact_hashes", "updated_at", "config"):
        if key not in data:
            if key == "artifact_hashes":
                data[key] = {}
            elif key == "updated_at":
                data[key] = datetime.utcnow().isoformat()
            else:  # config
                data[key] = {}
    return data


def save_state(state: Optional[Dict[str, Any]] = None) -> None:
    """
    Persist the current state to ``state.yaml``.

    Parameters
    ----------
    state: dict | None
        If provided, this dictionary is written; otherwise the current
        state on disk is re‑loaded, updated with a fresh ``updated_at``
        timestamp and written back.
    """
    if state is None:
        state = load_state()
    state["updated_at"] = datetime.utcnow().isoformat()
    state_file = _state_path()
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with state_file.open("w", encoding="utf-8") as f:
        yaml.dump(state, f, sort_keys=False)
    log.info(f"State saved to {state_file}")


def register_file(
    file_path: str,
    state: Optional[Dict[str, Any]] = None,
    checksum: Optional[str] = None,
    description: str = ""
) -> Dict[str, Any]:
    """
    Register a file in the state manifest.

    Parameters
    ----------
    file_path: str
        Relative POSIX path (e.g. ``data/processed/file.parquet``).
    state: dict | None
        Existing state dictionary to update; if ``None`` the state is
        loaded from disk.
    checksum: str | None
        If supplied, the checksum is used directly; otherwise it is
        computed from the file contents.
    description: str
        Optional free‑form description stored alongside the entry.

    Returns
    -------
    dict
        The updated state dictionary.
    """
    if state is None:
        state = load_state()

    rel_path = Path(file_path).as_posix()
    abs_path = paths.root / rel_path

    if not abs_path.is_file():
        raise FileNotFoundError(f"Cannot register non‑existent file: {abs_path}")

    if checksum is None:
        checksum = _compute_file_checksum(abs_path)

    size_bytes = abs_path.stat().st_size
    entry = {
        "checksum": checksum,
        "size_bytes": size_bytes,
        "registered_at": datetime.utcnow().isoformat(),
        "description": description,
    }

    state.setdefault("artifact_hashes", {})[rel_path] = entry
    log.debug(f"Registered file {rel_path} with checksum {checksum[:8]}...")
    return state


def get_file_info(file_path: str, state: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieve the stored metadata for ``file_path`` from the state.

    Returns ``None`` if the file has not been registered.
    """
    if state is None:
        state = load_state()
    return state.get("artifact_hashes", {}).get(Path(file_path).as_posix())


def verify_file(file_path: str, state: Optional[Dict[str, Any]] = None) -> bool:
    """
    Verify that the stored checksum matches the current file contents.

    Returns ``True`` if the file exists and the checksum matches,
    otherwise ``False``.
    """
    if state is None:
        state = load_state()
    info = get_file_info(file_path, state)
    if info is None:
        log.warning(f"No state entry for {file_path}; cannot verify.")
        return False

    abs_path = paths.root / Path(file_path).as_posix()
    if not abs_path.is_file():
        log.warning(f"File missing on disk: {abs_path}")
        return False

    current_checksum = _compute_file_checksum(abs_path)
    match = current_checksum == info["checksum"]
    if not match:
        log.warning(f"Checksum mismatch for {file_path}: expected {info['checksum']}, got {current_checksum}")
    return match


def verify_all() -> Dict[str, bool]:
    """
    Verify every registered artifact.

    Returns
    -------
    dict
        Mapping from relative file path to boolean indicating verification
        success.
    """
    state = load_state()
    results = {}
    for rel_path in state.get("artifact_hashes", {}):
        results[rel_path] = verify_file(rel_path, state)
    return results


def clear_stale_entries(state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Remove entries for files that no longer exist on disk.

    Returns the cleaned state dictionary.
    """
    if state is None:
        state = load_state()
    artifact_hashes = state.get("artifact_hashes", {})
    to_remove = [p for p in artifact_hashes if not (paths.root / p).exists()]
    for p in to_remove:
        log.info(f"Removing stale state entry for missing file: {p}")
        del artifact_hashes[p]
    state["artifact_hashes"] = artifact_hashes
    return state


# Backwards‑compatible alias used by existing tests (they import the
# private helper directly).  The leading underscore is retained to avoid
# breaking import statements.
_compute_file_checksum = _compute_file_checksum