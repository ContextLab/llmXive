"""
Initialization script for the project state file (state.yaml).

This script creates ``state.yaml`` at the project root with the required
top‑level keys:

- ``artifact_hashes``: a mapping from relative artifact paths to their SHA‑256
  checksum.
- ``updated_at``: ISO‑8601 timestamp of the last update.
- ``config``: a copy of the configuration dictionary returned by
  ``config.get_config_dict()`` (useful for reproducibility).

The script is idempotent – if ``state.yaml`` already exists it will be
overwritten with a fresh skeleton.
"""
import hashlib
import yaml
from datetime import datetime, timezone
from pathlib import Path

from config import get_config_dict, get_project_root
from utils import get_logger

log = get_logger(__name__)

STATE_FILE = get_project_root() / "state.yaml"


def _compute_sha256(file_path: Path) -> str:
    """Compute the SHA‑256 checksum of ``file_path``."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def initialize_state():
    """Write a fresh ``state.yaml`` with the required skeleton."""
    log.info(f"Initializing state file at {STATE_FILE}")

    # Build the initial structure
    state = {
        "artifact_hashes": {},          # will be populated by other scripts
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "config": get_config_dict(),
    }

    # Write YAML (ensuring the parent directory exists)
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with STATE_FILE.open("w") as f:
        yaml.safe_dump(state, f, sort_keys=False)

    log.info("state.yaml created successfully.")


if __name__ == "__main__":
    initialize_state()
