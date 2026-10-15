"""
Helper utilities for managing ``state.yaml`` – the central registry that
tracks artifact checksums and timestamps.

The module provides a minimal API that is used throughout the codebase:

* ``load_state()`` – read and return the current state dictionary.
* ``save_state(state)`` – write the provided state back to ``state.yaml``.
* ``register_file(file_path, checksum=None, description="")`` – add or
  update an entry for ``file_path`` in ``artifact_hashes``.  If ``checksum``
  is ``None`` the SHA‑256 hash is computed automatically.
"""
import hashlib
from pathlib import Path
from datetime import datetime, timezone
import yaml

from config import get_project_root
from utils import get_logger

log = get_logger(__name__)

STATE_PATH = get_project_root() / "state.yaml"


def _ensure_state_file():
    """Make sure ``state.yaml`` exists; create a minimal one if missing."""
    if not STATE_PATH.exists():
        log.warning("state.yaml not found – creating a fresh skeleton.")
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with STATE_PATH.open("w") as f:
            yaml.safe_dump(
                {"artifact_hashes": {}, "updated_at": "", "config": {}},
                f,
            )


def load_state() -> dict:
    """Load and return the full state dictionary."""
    _ensure_state_file()
    with STATE_PATH.open("r") as f:
        return yaml.safe_load(f) or {}


def save_state(state: dict | None = None) -> None:
    """
    Persist ``state`` to ``state.yaml``.  If ``state`` is ``None`` the current
    state is re‑loaded, its ``updated_at`` timestamp refreshed and then saved.
    """
    if state is None:
        state = load_state()
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    with STATE_PATH.open("w") as f:
        yaml.safe_dump(state, f, sort_keys=False)
    log.info("state.yaml updated.")


def _compute_sha256(file_path: Path) -> str:
    """Return the SHA‑256 checksum of ``file_path``."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def register_file(
    file_path: str | Path,
    checksum: str | None = None,
    description: str = "",
) -> None:
    """
    Register (or update) an artifact in ``state.yaml``.

    Parameters
    ----------
    file_path: str or Path
        Path to the artifact relative to the project root.
    checksum: str, optional
        Pre‑computed SHA‑256 checksum.  If omitted the checksum is
        calculated automatically.
    description: str, optional
        Human‑readable description stored alongside the checksum.
    """
    _ensure_state_file()
    state = load_state()

    path_obj = Path(file_path)
    rel_path = str(path_obj.relative_to(get_project_root()))

    if checksum is None:
        checksum = _compute_sha256(get_project_root() / rel_path)

    entry = {"checksum": checksum, "description": description}
    state.setdefault("artifact_hashes", {})[rel_path] = entry
    save_state(state)
    log.debug(f"Registered {rel_path} with checksum {checksum}")
