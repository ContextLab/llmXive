#!/usr/bin/env python
"""
T001 – Project scaffolding

This script creates the required directory tree for the project and captures a
filesystem snapshot using the `tree` command. The snapshot is written to
`logs/structure.txt`. The script is intended to be run as:

    python -m code.create_structure

The script exits with an exception if the `tree` command fails, ensuring that
the pipeline halts loudly on any problem.
"""

import subprocess
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _create_directories() -> None:
    """Create all directories required by the scaffolding task."""
    # List of directories relative to the project root
    dirs = [
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

    for rel_dir in dirs:
        dir_path: Path = paths.root / rel_dir
        dir_path.mkdir(parents=True, exist_ok=True)
        log.info(f"Created directory: {dir_path}")

def _capture_tree_snapshot() -> None:
    """Run `tree -a -L 3` on the project root and write the output."""
    try:
        result = subprocess.run(
            ["tree", "-a", "-L", "3", str(paths.root)],
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError as exc:
        # `tree` utility is not installed – fail loudly as required.
        log.error("The `tree` command is not available on this system.")
        raise exc
    except subprocess.CalledProcessError as exc:
        log.error(f"`tree` command failed with return code {exc.returncode}")
        raise exc

    output_path = paths.logs("structure.txt")
    output_path.write_text(result.stdout)
    log.info(f"Filesystem snapshot written to {output_path}")

    # Verify the snapshot is non-empty and contains every required directory.
    text = output_path.read_text()
    if not text.strip():
        raise RuntimeError("logs/structure.txt is empty; snapshot capture failed.")
    required = [
        "src", "src/data", "src/analysis", "src/utils", "src/validation",
        "tests", "data", "data/raw", "data/processed",
        "output", "output/figures", "output/temporal_profiles",
        "contracts", "logs",
    ]
    lines = {line.strip("├─│└ ─") for line in text.splitlines()}
    missing = [d for d in required if not any(d.split("/")[-1] in l for l in lines)]
    if missing:
        raise RuntimeError(
            f"Snapshot missing entries for directories: {missing}"
        )
    log.info("Snapshot verified: non-empty and contains all required directories.")

def main() -> None:
    """Entry point for the scaffolding script."""
    _create_directories()
    _capture_tree_snapshot()

if __name__ == "__main__":
    main()
