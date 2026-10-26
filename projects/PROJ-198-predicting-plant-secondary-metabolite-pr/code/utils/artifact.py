"""
Utility functions for artifact hygiene:
- SHA‑256 checksum computation
- State‑file (YAML) handling
- Simple API to record one or many artifact hashes
"""

from __future__ import annotations

import hashlib
import yaml
import atexit
from pathlib import Path
from typing import Iterable, List, Mapping, MutableMapping

from llmxive_toolkit import paths

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# State file location: placed under `data/state/` to avoid shadowing 
# the platform-owned `state/` directory.
STATE_FILE = paths.data("state", "artifact_hashes.yaml")

# Ensure the state directory exists
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# Internal helpers
# ----------------------------------------------------------------------
def _load_state() -> MutableMapping[str, str]:
    """Load the YAML state file, returning an empty dict if the file does not exist."""
    if not STATE_FILE.is_file():
        return {}
    with STATE_FILE.open("rt", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        return {}
    return data

def _save_state(state: Mapping[str, str]) -> None:
    """Write the state mapping to the YAML file (sorted for reproducibility)."""
    with STATE_FILE.open("wt", encoding="utf-8") as f:
        yaml.safe_dump(dict(sorted(state.items())), f, sort_keys=False)

def _compute_sha256(file_path: Path) -> str:
    """Return the hex SHA‑256 digest of *file_path*."""
    if not file_path.is_file():
        raise FileNotFoundError(f"Cannot compute checksum – file not found: {file_path}")
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
_PENDING_PATHS: List[Path] = []

def track_path(path: Path | str) -> None:
    """
    Register *path* to be recorded in the state file when the interpreter exits.
    """
    _PENDING_PATHS.append(Path(path).resolve())

def record_artifacts(paths_to_record: Iterable[Path | str]) -> None:
    """
    Compute SHA‑256 hashes for all *paths* and store them in the state file.
    """
    state = _load_state()
    root = paths.root
    for p in paths_to_record:
        p_resolved = Path(p).resolve()
        if not p_resolved.is_file():
            raise FileNotFoundError(f"Artifact not found: {p_resolved}")
        
        try:
            rel_path = p_resolved.relative_to(root)
        except ValueError:
            # Fallback if for some reason the path is outside root
            rel_path = p_resolved.name

        checksum = _compute_sha256(p_resolved)
        state[str(rel_path)] = checksum
    _save_state(state)

# ----------------------------------------------------------------------
# Automatic flushing on interpreter shutdown
# ----------------------------------------------------------------------
def _flush_pending() -> None:
    """Write any paths registered via :func:`track_path` to the state file."""
    if _PENDING_PATHS:
        try:
            record_artifacts(_PENDING_PATHS)
        except Exception as exc:
            try:
                from code.utils.logging import get_logger
                log = get_logger(__name__)
                log.error("Failed to record artifact hashes on shutdown: %s", exc)
            except ImportError:
                pass

atexit.register(_flush_pending)
