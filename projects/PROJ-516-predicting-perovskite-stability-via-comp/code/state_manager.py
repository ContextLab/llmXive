"""
State Manager Module for the perovskite stability pipeline.

This module provides two simple utility functions:
  * ``compute_hash(path)`` – returns the SHA‑256 hash of the file at ``path``.
  * ``update_state(path)`` – records the hash together with an ISO‑8601
    timestamp in ``state/project_state.yaml`` (creating the file if it does not
    exist).

The module also exposes a CLI entry point that matches the verification
expectation:

    python -m code.state_manager data/raw/dummy.csv

Running the command updates (or creates) ``state/project_state.yaml`` with an
entry for the supplied file.
"""

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import yaml

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _ensure_state_file(state_path: Path) -> Dict[str, Any]:
    """
    Load the YAML state file if it exists; otherwise return a fresh structure.

    The state file has the shape:
        {
            "artifacts": {
                "<relative/path>": {
                    "hash": "<sha256>",
                    "timestamp": "<ISO‑8601 UTC>"
                },
                ...
            }
        }
    """
    if not state_path.exists():
        # Ensure the parent directory exists
        state_path.parent.mkdir(parents=True, exist_ok=True)
        return {"artifacts": {}}

    try:
        with state_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            if not isinstance(data, dict):
                raise ValueError("State file must contain a top‑level mapping.")
            # Normalise missing top‑level keys
            data.setdefault("artifacts", {})
            return data
    except yaml.YAMLError as exc:
        raise RuntimeError(f"Failed to parse state file {state_path}: {exc}")

def _write_state(state_path: Path, state: Dict[str, Any]) -> None:
    """Serialise ``state`` to ``state_path`` using safe YAML."""
    with state_path.open("w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_hash(path: str) -> str:
    """
    Compute the SHA‑256 hash of the file at ``path``.

    Parameters
    ----------
    path: str
        Path to the file whose hash should be computed.

    Returns
    -------
    str
        Hexadecimal SHA‑256 digest.

    Raises
    ------
    FileNotFoundError
        If ``path`` does not exist.
    IOError
        If the file cannot be read.
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    hasher = hashlib.sha256()
    # Read in 4 KB blocks to avoid loading huge files into memory
    with file_path.open("rb") as fh:
        for block in iter(lambda: fh.read(4096), b""):
            hasher.update(block)
    return hasher.hexdigest()


def update_state(path: str, state_file: str = "state/project_state.yaml") -> None:
    """
    Record the hash of ``path`` together with a timestamp in the state file.

    If the state file does not exist it will be created. The entry key is the
    *relative* path (as supplied to the function) so that verification scripts
    can look it up directly.

    Parameters
    ----------
    path: str
        Path to the artifact whose hash should be recorded.
    state_file: str, optional
        Destination YAML file (default ``state/project_state.yaml``).
    """
    state_path = Path(state_file)
    state = _ensure_state_file(state_path)

    # Compute hash; this will raise if the file is missing – the caller wants to
    # fail loudly.
    file_hash = compute_hash(path)

    # Record the hash with an ISO‑8601 UTC timestamp
    timestamp = datetime.now(timezone.utc).isoformat()
    state["artifacts"][path] = {"hash": file_hash, "timestamp": timestamp}

    _write_state(state_path, state)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _print_usage_and_exit(code: int = 1) -> None:
    prog = Path(sys.argv[0]).name
    sys.stderr.write(f"Usage: python -m {prog} <file_path>\n")
    sys.exit(code)


def main() -> None:
    """
    Minimal CLI that matches the verification step:

        python -m code.state_manager data/raw/dummy.csv

    The command updates the state file for the supplied artifact.
    """
    if len(sys.argv) != 2:
        _print_usage_and_exit()

    file_path = sys.argv[1]
    try:
        update_state(file_path)
        print(f"State updated for {file_path}")
    except Exception as exc:
        sys.stderr.write(f"Error updating state: {exc}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
