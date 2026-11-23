"""
Utility module to update the project's state registry with hashes of raw data files.

This module is used by the T051 task to record a reproducibility hash of the
``data/`` directory. It provides a small helper that scans a directory,
computes SHA‑256 hashes for each file, and writes the result back into the
project's state YAML file.

The public API matches what the unit tests expect:

* ``compute_sha256`` – compute the SHA‑256 hash of a file (returns ``None`` if the
  file does not exist).
* ``STATE_FILE`` – path to the state YAML file.
* ``DATA_RAW_DIR`` – path to the directory whose files should be hashed.
* ``PROJECT_ID`` – identifier of the current project.
* ``update_state_registry`` – load the state file, update the ``artifact_hashes``
  mapping with the current file hashes, add ``updated_at`` and ``last_operation``
  metadata, and write the file back to disk.

The implementation deliberately avoids any silent fall‑backs: if the state file
is missing a ``SystemExit`` is raised (as required by the tests). All paths are
handled relative to the current working directory, which the test suite sets
to a temporary project root.
"""

import hashlib
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Default locations – the test suite monkey‑patches these to point at temporary
# files/directories.
STATE_FILE: Path = Path("state/projects/PROJ-866-llmxive-follow-up-extending-foundation-p.yaml")
DATA_RAW_DIR: Path = Path("data/raw")
PROJECT_ID: str = "PROJ-866-llmxive-follow-up-extending-foundation-p"


def compute_sha256(file_path: Path) -> Optional[str]:
    """
    Compute the SHA‑256 hash of a file.

    Parameters
    ----------
    file_path: Path
        Path to the file whose hash should be calculated.

    Returns
    -------
    Optional[str]
        Hexadecimal SHA‑256 digest, or ``None`` if the file does not exist.
    """
    if not file_path.is_file():
        return None
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def _load_state() -> dict:
    """Load the YAML state file; raise ``SystemExit`` if it cannot be read."""
    if not STATE_FILE.is_file():
        raise SystemExit(f"State file not found: {STATE_FILE}")
    with STATE_FILE.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


def _save_state(state: dict) -> None:
    """Write the updated state back to ``STATE_FILE``."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with STATE_FILE.open("w", encoding="utf-8") as f:
        yaml.safe_dump(state, f, sort_keys=False)


def update_state_registry() -> None:
    """
    Update the project's state registry.

    The function:
    1. Loads the existing state YAML.
    2. Scans ``DATA_RAW_DIR`` for files (recursively) and computes a SHA‑256 hash
       for each file.
    3. Stores the hashes in ``state['artifact_hashes']`` using a path that is
       relative to the current working directory (e.g. ``data/raw/foo.json``).
    4. Adds ``updated_at`` (ISO‑8601 UTC) and ``last_operation`` metadata.
    5. Writes the updated state back to disk.
    """
    state = _load_state()

    # Ensure the required top‑level keys exist.
    state.setdefault("artifact_hashes", {})
    artifact_hashes: dict = {}

    raw_dir = Path(DATA_RAW_DIR)
    if raw_dir.is_dir():
        for file_path in sorted(raw_dir.rglob("*")):
            if file_path.is_file():
                rel_path = file_path.relative_to(Path.cwd()).as_posix()
                file_hash = compute_sha256(file_path)
                if file_hash is not None:
                    artifact_hashes[rel_path] = file_hash
    # If the directory does not exist or contains no files, we keep an empty dict.

    state["artifact_hashes"] = artifact_hashes
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    state["last_operation"] = "update_state_registry"

    _save_state(state)
