#!/usr/bin/env python3
"""
Script to create the required project directory tree and capture a simple
filesystem snapshot.

Directories created:
  src/
  src/data/
  src/analysis/
  src/utils/
  src/validation/
  tests/
  data/
  data/raw/
  data/processed/
  output/
  output/figures/
  output/temporal_profiles/
  contracts/
  logs/

After creation, a snapshot limited to depth 3 is written to
logs/structure.txt. The snapshot contains at least one line that includes
each of the directory names, satisfying the verification step:
  grep -E "src|data|output|contracts|logs" logs/structure.txt
"""
import logging
from pathlib import Path
import sys

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
REQUIRED_DIRS = [
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

SNAPSHOT_MAX_DEPTH = 3  # Mirrors `tree -a -L 3` depth limit


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _create_directories(root: Path) -> None:
    """Create all directories listed in ``REQUIRED_DIRS``."""
    for rel_path in REQUIRED_DIRS:
        dir_path = root / rel_path
        dir_path.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created directory: {dir_path}")


def _write_snapshot(root: Path, output_file: Path, max_depth: int = SNAPSHOT_MAX_DEPTH) -> None:
    """
    Write a simple tree‑like snapshot of the directory hierarchy up to
    ``max_depth``. The output format is deliberately lightweight – it only
    needs to contain the directory names so that the verification ``grep``
    command finds a match for each required top‑level folder.
    """
    def _walk(current: Path, depth: int, prefix: str, lines: list):
        if depth > max_depth:
            return
        children = sorted(current.iterdir())
        for idx, child in enumerate(children):
            connector = "└── " if idx == len(children) - 1 else "├── "
            line = f"{prefix}{connector}{child.name}"
            lines.append(line)
            if child.is_dir():
                new_prefix = prefix + ("    " if idx == len(children) - 1 else "│   ")
                _walk(child, depth + 1, new_prefix, lines)

    lines: list[str] = []
    _walk(root, 0, "", lines)

    # Ensure the parent directory for the snapshot exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    logging.info(f"Filesystem snapshot written to {output_file}")


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
    root = Path.cwd()
    logging.info(f"Project root resolved as: {root}")

    # Step 1: create the required directory tree
    _create_directories(root)

    # Step 2: capture a tree snapshot (depth‑limited) into logs/structure.txt
    snapshot_path = root / "logs" / "structure.txt"
    _write_snapshot(root, snapshot_path, max_depth=SNAPSHOT_MAX_DEPTH)

    logging.info("Directory scaffolding completed successfully.")


if __name__ == "__main__":
    main()