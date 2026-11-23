"""
scripts/update_state_hashes.py

Compute SHA‑256 hashes for every file under ``data/``, ``src/`` and
``outputs/`` and write a summary YAML file to
``state/projects/PROJ-260-investigating-the-influence-of-network-s.yaml``.

The script is deliberately lightweight and has no external side‑effects
beyond writing the state file.  It is intended to be invoked as part of the
project's quick‑start or CI pipeline.
"""

import hashlib
import pathlib
import sys
from typing import Dict

import yaml

# Import the helper that already implements SHA‑256 for a single file.
# The wrapper in ``src.lib.utils`` forwards to the real implementation.
try:
    from src.lib.utils import compute_sha256
except Exception as exc:
    sys.stderr.write(f"Failed to import compute_sha256: {exc}\\n")
    raise


def _hash_file(path: pathlib.Path) -> str:
    """
    Return the SHA‑256 hex digest of *path*.

    Parameters
    ----------
    path: pathlib.Path
        Path to the file to be hashed.

    Returns
    -------
    str
        64‑character hexadecimal digest.
    """
    return compute_sha256(path)


def _gather_files(root: pathlib.Path) -> Dict[str, str]:
    """
    Recursively walk *root* and return a mapping from relative POSIX paths
    to their SHA‑256 hashes.
    """
    hashes: Dict[str, str] = {}
    for file_path in root.rglob("*"):
        if file_path.is_file():
            # Store paths relative to the project root (one level above the
            # top‑level ``data``, ``src`` or ``outputs`` directories).
            rel_path = file_path.relative_to(root.parent).as_posix()
            hashes[rel_path] = _hash_file(file_path)
    return hashes


def main() -> int:
    """
    Entry point for the script.

    Returns
    -------
    int
        Exit status (0 on success, non‑zero on error).
    """
    # ``scripts`` lives inside the top‑level ``code`` directory.  The project
    # root is therefore two levels up from this file.
    project_root = pathlib.Path(__file__).resolve().parents[1]  # ``code/scripts/..`` → project root

    # Directories to hash
    data_dir = project_root / "data"
    src_dir = project_root / "src"
    outputs_dir = project_root / "outputs"

    # Verify that the directories exist; if any are missing we treat that as an error
    for d in (data_dir, src_dir, outputs_dir):
        if not d.is_dir():
            sys.stderr.write(f"Required directory missing: {d}\\n")
            return 1

    # Collect hashes
    all_hashes: Dict[str, str] = {}
    for base_dir in (data_dir, src_dir, outputs_dir):
        all_hashes.update(_gather_files(base_dir))

    if not all_hashes:
        sys.stderr.write("No files found to hash.\\n")
        return 1

    # Prepare the output YAML structure
    state = {
        "project": "PROJ-260-investigating-the-influence-of-network-s",
        "hashes": all_hashes,
    }

    # Ensure the output directory exists
    state_dir = project_root / "state" / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)

    output_path = state_dir / "PROJ-260-investigating-the-influence-of-network-s.yaml"
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(state, f, sort_keys=False)
    except Exception as exc:
        sys.stderr.write(f"Failed to write state file: {exc}\\n")
        return 1

    print(f"State file written to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())