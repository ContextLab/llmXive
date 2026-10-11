"""
Script to create the required project directory tree and capture a filesystem snapshot.

This fulfills task T001 by:
1. Creating the directories listed in the task description.
2. Writing a tree‑like snapshot (up to depth 3) to `logs/structure.txt`.

The script is intended to be run as:
    python code/setup_structure.py

It uses only the Python standard library and the `llmxive_toolkit` helpers for
path handling, ensuring compatibility with the existing project environment.
"""

import os
import sys
from pathlib import Path
from llmxive_toolkit import paths, get_logger

# Initialise logger (writes to stdout; the script itself does not create a log file)
log = get_logger(__name__)

# ----------------------------------------------------------------------
# 1. Directory creation
# ----------------------------------------------------------------------
DIRS_TO_CREATE = [
    "src",
    "src/data",
    "src/analysis",
    "src/utils",
    "src/validation",
    "tests",
    "data",
    "data/raw",
    "data/processed",
    "output",
    "output/figures",
    "output/temporal_profiles",
    "contracts",
    "logs",
]


def create_directories(base: Path = Path.cwd()) -> None:
    """Create all required directories under the given base path."""
    for rel_dir in DIRS_TO_CREATE:
        dir_path = base / rel_dir
        dir_path.mkdir(parents=True, exist_ok=True)
        log.info(f"Created directory: {dir_path}")


# ----------------------------------------------------------------------
# 2. Snapshot generation (tree‑like output, depth limited to 3)
# ----------------------------------------------------------------------
def write_tree_snapshot(root: Path, max_depth: int = 3, output_file: Path = None) -> None:
    """
    Write a simple tree representation of the directory hierarchy.

    The format mimics `tree -a -L <max_depth>` but is implemented in pure Python
    to avoid external dependencies.

    Parameters
    ----------
    root: Path
        The directory from which the snapshot starts.
    max_depth: int
        Maximum depth to traverse (root is depth 0).
    output_file: Path
        Destination file. If None, defaults to ``logs/structure.txt``.
    """
    if output_file is None:
        output_file = paths.logs("structure.txt")
    
    # Ensure the logs directory exists (the create_directories step already does this)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", encoding="utf-8") as f:
        for dirpath, dirnames, filenames in os.walk(root):
            # Compute depth relative to the root
            rel_path = Path(dirpath).relative_to(root)
            depth = len(rel_path.parts)
            if depth > max_depth:
                # Prune deeper branches
                dirnames[:] = []  # prevents walk from recursing further
                continue

            indent = "│   " * depth
            line = f"{indent}{Path(dirpath).name}/\n"
            f.write(line)

            # List files (sorted for deterministic output)
            for fname in sorted(filenames):
                file_indent = "│   " * (depth + 1)
                f.write(f"{file_indent}{fname}\n")

    log.info(f"Filesystem snapshot written to: {output_file}")


# ----------------------------------------------------------------------
# 3. Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Execute the directory‑creation and snapshot steps.

    The function is deliberately lightweight: it performs the actions
    synchronously and exits with status 0 on success. Any unexpected
    exception will propagate, causing a non‑zero exit code, which is
    appropriate for CI verification.
    """
    base_path = Path.cwd()
    create_directories(base_path)
    write_tree_snapshot(base_path, max_depth=3)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.error(f"Unexpected error: {exc}")
        sys.exit(1)