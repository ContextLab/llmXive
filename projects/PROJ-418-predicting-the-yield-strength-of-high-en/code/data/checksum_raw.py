"""
Utility functions for computing and recording SHA‑256 checksums of raw data files.
"""

import hashlib
from pathlib import Path
import yaml
from llmxive_toolkit import paths

DEFAULT_STATE_PATH = paths.root / "state.yaml"

def compute_sha256(file_path: str) -> str:
    """Compute the SHA‑256 checksum of *file_path*."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def load_state(state_path: Path = DEFAULT_STATE_PATH) -> dict:
    """Load the YAML state file; return empty dict if missing."""
    if not state_path.is_file():
        return {}
    with state_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def save_state(state: dict, state_path: Path = DEFAULT_STATE_PATH) -> None:
    """Write *state* back to *state_path*."""
    with state_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(state, f)

def record_checksum(
    descriptor_path: str, state_path: Path = DEFAULT_STATE_PATH
) -> str:
    """
    Compute the checksum of *descriptor_path* and store it under the key
    ``raw_dataset_sha256`` in the state file.
    """
    checksum = compute_sha256(descriptor_path)
    state = load_state(state_path)
    state["raw_dataset_sha256"] = checksum
    save_state(state, state_path)
    return checksum

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python -m code.data.checksum_raw <path-to-raw-file>")
        sys.exit(1)
    path = sys.argv[1]
    print(record_checksum(path))