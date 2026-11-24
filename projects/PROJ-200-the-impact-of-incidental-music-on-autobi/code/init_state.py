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
import logging
import yaml
from datetime import datetime, timezone
from pathlib import Path

# Import configuration utilities directly (avoid importing utils which pulls in
# heavy optional dependencies like pyarrow that may not be available in the
# execution environment).
from config import get_config_dict, get_project_root

# Set up a minimal logger that writes to stdout; this avoids the circular
# import issue that previously arose from importing ``utils.get_logger``.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
log = logging.getLogger(__name__)

# Path to the state file at the project root.
STATE_FILE = get_project_root() / "state.yaml"


def _compute_sha256(file_path: Path) -> str:
    """Compute the SHA‑256 checksum of ``file_path``."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def initialize_state() -> None:
    """Write a fresh ``state.yaml`` with the required skeleton."""
    log.info(f"Initializing state file at {STATE_FILE}")

    # Build the initial structure
    state = {
        "artifact_hashes": {},          # will be populated by other scripts
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "config": get_config_dict(),
    }

    # Ensure the parent directory exists and write the YAML file.
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with STATE_FILE.open("w") as f:
        yaml.safe_dump(state, f, sort_keys=False)

    log.info("state.yaml created successfully.")


if __name__ == "__main__":
    initialize_state()