#!/usr/bin/env python
"""
Record a SHA-256 hash snapshot of all project artifacts.

This script walks the entire project directory (excluding the ``state`` folder
itself and any ``__pycache__`` directories), computes SHA-256 hashes for every
file, and writes a JSON snapshot into ``state/snapshot.json``.  The snapshot
can later be used to verify that artifacts have not changed.

Usage:
    python code/record_state_snapshot.py
"""
import sys
from pathlib import Path
from typing import List

# Import the state manager utilities that provide the hashing and snapshot logic.
from state_manager import record_state_snapshot

def collect_artifact_paths(root: Path) -> List[Path]:
    """
    Recursively collect all file paths under ``root`` that should be versioned.

    Files inside the ``state`` directory and any ``__pycache__`` directories are
    excluded because they contain generated metadata or compiled byte‑code that
    should not be part of the reproducibility snapshot.

    Parameters
    ----------
    root: Path
        The absolute path to the project root.

    Returns
    -------
    List[Path]
        A list of absolute file paths to be hashed.
    """
    exclude_dirs = {"state", "__pycache__"}
    artifact_paths: List[Path] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        # Skip files that reside in any excluded directory.
        if any(part in exclude_dirs for part in path.parts):
            continue
        artifact_paths.append(path)

    return artifact_paths

def main() -> None:
    # The script lives in ``code/``; the project root is its parent directory.
    project_root = Path(__file__).resolve().parents[1]

    # Ensure the ``state`` directory exists.
    state_dir = project_root / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    # Gather all artifact file paths that we want to version.
    artifacts = collect_artifact_paths(project_root)

    # Write the snapshot JSON file.  ``record_state_snapshot`` returns the path
    # it wrote, which we report for user feedback.
    snapshot_path = state_dir / "snapshot.json"
    written_path = record_state_snapshot(artifacts, output_file=snapshot_path)

    print(f"✅ Snapshot written to {written_path}")

if __name__ == "__main__":
    # ``sys.argv`` is not used because the script has no CLI options;
    # it simply records the current state.
    main()
