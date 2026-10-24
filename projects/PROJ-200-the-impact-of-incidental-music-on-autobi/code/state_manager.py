"""
State manager for tracking artifact checksums and metadata.

Provides utilities to compute SHA-256 checksums, load and save a YAML
state file, register new artifacts, verify integrity, and clean up
stale entries.

The implementation follows the expectations of
`tests/unit/test_state_manager.py`.
"""

import hashlib
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

from config import get_project_root

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _compute_file_checksum(file_path: Path) -> str:
    """
    Compute the SHA-256 checksum of a file.

    Parameters
    ----------
    file_path: Path
        Absolute path to the file.

    Returns
    -------
    str
        Hexadecimal SHA-256 digest (64 characters).
    """
    if not file_path.is_file():
        raise FileNotFoundError(f"File not found for checksum: {file_path}")

    hasher = hashlib.sha256()
    # Read in chunks to avoid loading huge files into memory
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


# ----------------------------------------------------------------------
# Core state handling
# ----------------------------------------------------------------------


def _default_state() -> Dict[str, Any]:
    """
    Create a brand‑new state dictionary with required top‑level keys.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    return {
        "metadata": {
            "version": "1.0",
            "created_at": now_iso,
            "last_updated": now_iso,
        },
        "files": {},  # mapping of relative_path -> info dict
    }


def _state_file_path() -> Path:
    """
    Resolve the absolute path to ``state.yaml`` in the project root.
    """
    root = get_project_root()
    return root / "state.yaml"


def load_state() -> Dict[str, Any]:
    """
    Load the state file if it exists; otherwise return a fresh state.

    Returns
    -------
    dict
        The parsed state dictionary.
    """
    state_path = _state_file_path()
    if state_path.is_file():
        with state_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        # Ensure required top‑level structure even if the file is malformed
        if not isinstance(data, dict):
            data = {}
        data.setdefault("metadata", {})
        data["metadata"].setdefault("version", "1.0")
        data["metadata"].setdefault(
            "created_at", datetime.now(timezone.utc).isoformat()
        )
        data["metadata"].setdefault(
            "last_updated", datetime.now(timezone.utc).isoformat()
        )
        data.setdefault("files", {})
        return data
    else:
        return _default_state()


def save_state(state: Optional[Dict[str, Any]] = None) -> None:
    """
    Write the provided state dictionary to ``state.yaml``.
    If ``state`` is ``None`` the current state on disk is loaded,
    refreshed (updates ``last_updated``) and written back.
    """
    if state is None:
        state = load_state()
    # Update the ``last_updated`` timestamp
    state.setdefault("metadata", {})
    state["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()

    state_path = _state_file_path()
    # Ensure the parent directory exists (project root always exists)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with state_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(state, f, sort_keys=False)


# ----------------------------------------------------------------------
# Public API used by the test suite
# ----------------------------------------------------------------------


def register_file(
    file_path: str,
    state: Optional[Dict[str, Any]] = None,
    checksum: Optional[str] = None,
    description: str = "",
) -> Dict[str, Any]:
    """
    Register a file in the state tracking system.

    Parameters
    ----------
    file_path: str
        Relative path (from the project root) of the file to register.
    state: dict | None
        Existing state dictionary; if ``None`` the state is loaded from
        disk.
    checksum: str | None
        Pre‑computed checksum; if omitted the checksum is calculated.
    description: str
        Optional human‑readable description of the artifact.

    Returns
    -------
    dict
        Updated state dictionary (also persisted to disk).
    """
    root = get_project_root()
    abs_path = root / file_path

    if not abs_path.is_file():
        raise FileNotFoundError(f"Cannot register non‑existent file: {file_path}")

    if state is None:
        state = load_state()

    if checksum is None:
        checksum = _compute_file_checksum(abs_path)

    file_info = {
        "path": file_path,
        "checksum": checksum,
        "size_bytes": abs_path.stat().st_size,
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "description": description,
    }

    state.setdefault("files", {})
    state["files"][file_path] = file_info

    save_state(state)
    return state


def verify_file(file_path: str) -> bool:
    """
    Verify that a registered file's checksum matches the current file
    on disk.

    Parameters
    ----------
    file_path: str
        Relative path (from the project root) of the file to verify.

    Returns
    -------
    bool
        ``True`` if the checksum matches, ``False`` otherwise.
    """
    root = get_project_root()
    abs_path = root / file_path
    state = load_state()
    info = state.get("files", {}).get(file_path)

    if info is None:
        # Not registered – treat as invalid
        return False

    try:
        current_checksum = _compute_file_checksum(abs_path)
    except FileNotFoundError:
        return False

    return current_checksum == info.get("checksum")


def verify_all() -> Dict[str, bool]:
    """
    Verify every file recorded in the state.

    Returns
    -------
    dict
        Mapping of relative file path -> verification result (True/False).
    """
    state = load_state()
    results: Dict[str, bool] = {}
    for rel_path in state.get("files", {}):
        results[rel_path] = verify_file(rel_path)
    return results


def get_file_info(file_path: str, state: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieve the stored metadata for a given file.

    Parameters
    ----------
    file_path: str
        Relative path (from the project root) of the file.
    state: dict | None
        Optional pre‑loaded state dictionary.

    Returns
    -------
    dict | None
        The file's metadata dictionary if present, else ``None``.
    """
    if state is None:
        state = load_state()
    return state.get("files", {}).get(file_path)


def clear_stale_entries() -> Dict[str, Any]:
    """
    Remove entries for files that no longer exist on disk.

    Returns
    -------
    dict
        The cleaned state dictionary (also persisted to disk).
    """
    root = get_project_root()
    state = load_state()
    files_dict = state.get("files", {})
    stale_keys = [p for p in files_dict if not (root / p).is_file()]

    for key in stale_keys:
        del files_dict[key]

    state["files"] = files_dict
    save_state(state)
    return state