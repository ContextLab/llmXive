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

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Project root is three levels up from this file:
#   <project>/code/utils/artifact.py
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# State file location (as defined in the task description)
STATE_FILE = PROJECT_ROOT / "state" / "projects" / "PROJ-001-predict-plant-metabolite-pr.yaml"

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
    # Guard against malformed content
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
    # Read in chunks to avoid loading huge files into memory
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
_PENDING_PATHS: List[Path] = []  # paths that will be recorded on interpreter shutdown


def track_path(path: Path) -> None:
    """
    Register *path* to be recorded in the state file when the interpreter exits.

    This is convenient for scripts that write many artifacts – they can simply
    call ``track_path`` after the write operation without worrying about when
    the state file is updated.
    """
    _PENDING_PATHS.append(Path(path).resolve())


def record_artifacts(paths: Iterable[Path]) -> None:
    """
    Compute SHA‑256 hashes for all *paths* and store them in the state file.

    Existing entries are overwritten with the latest hash.
    The function is idempotent – calling it repeatedly with the same files
    yields the same state.
    """
    state = _load_state()
    for p in paths:
        p_resolved = Path(p).resolve()
        if not p_resolved.is_file():
            raise FileNotFoundError(f"Artifact not found: {p_resolved}")
        rel_path = p_resolved.relative_to(PROJECT_ROOT)
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
        except Exception as exc:  # pragma: no cover – best‑effort logging
            # Import lazily to avoid circular imports
            from utils.logging import get_logger

            log = get_logger(__name__)
            log.error("Failed to record artifact hashes on shutdown: %s", exc)

atexit.register(_flush_pending)