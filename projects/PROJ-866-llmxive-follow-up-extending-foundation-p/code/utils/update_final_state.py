"""
Script to finalize the project state after the full pipeline has run.

It computes a reproducibility SHA‑256 hash of the entire ``data/`` directory
(using the existing ``checksum_utils`` module) and records this hash together
with a timestamp in the project's state YAML file.

The script is idempotent: running it multiple times overwrites the same
fields with fresh values.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

from llmxive_toolkit import paths
from utils.checksum_utils import compute_directory_hash


def _state_file_path() -> Path:
    """Return the absolute path to the project's state YAML file."""
    # The state file lives under ``state/projects/`` with a fixed name.
    return Path("state/projects/PROJ-866-llmxive-follow-up-extending-foundation-p.yaml")


def _load_state(state_path: Path) -> dict:
    """Load the YAML state file; exit with an error if it cannot be read."""
    import yaml

    if not state_path.is_file():
        sys.stderr.write(f"State file not found: {state_path}\\n")
        sys.exit(1)
    with state_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _save_state(state_path: Path, state: dict) -> None:
    """Write the updated state back to ``state_path``."""
    import yaml

    state_path.parent.mkdir(parents=True, exist_ok=True)
    with state_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(state, f, sort_keys=False)


def main() -> None:
    # Compute the reproducibility hash of the whole ``data`` directory.
    data_dir = paths.data()
    reproducibility_hash = compute_directory_hash(str(data_dir))

    # Load, modify, and save the state file.
    state_path = _state_file_path()
    state = _load_state(state_path)

    state["reproducibility_hash"] = reproducibility_hash
    state["final_verification_timestamp"] = datetime.now(timezone.utc).isoformat()

    _save_state(state_path, state)

    print(f"Updated {state_path} with reproducibility_hash={reproducibility_hash}")


if __name__ == "__main__":
    main()