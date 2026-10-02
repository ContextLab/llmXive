"""T061_compute_checksum.py

Compute SHA256 checksum for the processed descriptor file
``data/processed/hea_descriptors.csv`` and record it in the project
state file ``state/projects/PROJ-418-predicting-the-yield-strength-of-high-en.yaml``.

This script is intended to be run after the descriptor generation step
(T015). It can be invoked directly from the command line or imported by
other pipeline modules.

The script is deliberately lightweight and has no external side‑effects
other than updating the state file.
"""

import argparse
import hashlib
import os
from pathlib import Path
import sys
import yaml

# Default locations – relative to the repository root
DEFAULT_DESCRIPTOR_PATH = Path("data/processed/hea_descriptors.csv")
DEFAULT_STATE_PATH = Path(
    "state/projects/PROJ-418-predicting-the-yield-strength-of-high-en.yaml"
)


def compute_sha256(file_path: Path) -> str:
    """Return the hex SHA256 checksum of *file_path*."""
    if not file_path.is_file():
        raise FileNotFoundError(f"Descriptor file not found: {file_path}")
    sha256 = hashlib.sha256()
    # Read in chunks to handle large files without exhausting memory
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_state(state_path: Path) -> dict:
    """Load the YAML state file; create a minimal structure if missing."""
    if state_path.is_file():
        with state_path.open("r", encoding="utf-8") as f:
            try:
                state = yaml.safe_load(f) or {}
            except yaml.YAMLError as exc:
                raise ValueError(f"Failed to parse state YAML: {exc}") from exc
    else:
        state = {}
    # Ensure the top‑level ``artifact_hashes`` map exists
    state.setdefault("artifact_hashes", {})
    return state


def save_state(state: dict, state_path: Path) -> None:
    """Write *state* back to *state_path* using safe YAML dumping."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with state_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(state, f, sort_keys=False)


def record_checksum(
    descriptor_path: Path = DEFAULT_DESCRIPTOR_PATH,
    state_path: Path = DEFAULT_STATE_PATH,
) -> str:
    """Compute the checksum of *descriptor_path* and store it in *state_path*.

    Returns the computed checksum string.
    """
    checksum = compute_sha256(descriptor_path)
    state = load_state(state_path)
    # Store using the relative path string as the key, matching other tasks
    rel_path = str(descriptor_path.as_posix())
    state["artifact_hashes"][rel_path] = checksum
    save_state(state, state_path)
    return checksum


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Compute SHA256 checksum for the processed descriptor CSV "
        "and record it in the project state file."
    )
    parser.add_argument(
        "--descriptor-path",
        type=Path,
        default=DEFAULT_DESCRIPTOR_PATH,
        help=f"Path to the descriptor CSV (default: {DEFAULT_DESCRIPTOR_PATH})",
    )
    parser.add_argument(
        "--state-path",
        type=Path,
        default=DEFAULT_STATE_PATH,
        help=f"Path to the YAML state file (default: {DEFAULT_STATE_PATH})",
    )
    return parser.parse_args(argv)


def main(argv=None):
    """Entry point for ``python -m code.T061_compute_checksum``."""
    args = _parse_args(argv or sys.argv[1:])
    checksum = record_checksum(args.descriptor_path, args.state_path)
    print(f"Recorded checksum for {args.descriptor_path}: {checksum}")


if __name__ == "__main__":
    main()
