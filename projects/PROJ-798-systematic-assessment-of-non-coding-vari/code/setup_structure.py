"""
setup_structure.py

Utility script to create the required project directory layout and
generate a manifest file listing all directories under `code/`, `data/`,
and `tests/`. This satisfies task T001 which verifies that at least
11 directories exist.

The script is deliberately simple and has no external dependencies
beyond the Python standard library.
"""

import sys
from pathlib import Path

# List of directories required by the project specification.
REQUIRED_DIRS = [
    Path("code"),
    Path("code/data_ingestion"),
    Path("code/scoring"),
    Path("code/analysis"),
    Path("code/visualization"),
    Path("code/utils"),
    Path("data/raw"),
    Path("data/derived"),
    Path("data/results"),
    Path("tests/unit"),
    Path("tests/integration"),
    Path("tests/contract"),
]

def _ensure_directories():
    """Create all required directories (including parents)."""
    for d in REQUIRED_DIRS:
        d.mkdir(parents=True, exist_ok=True)

def _write_manifest():
    """
    Write a sorted list of all directories under `code`, `data`,
    and `tests` to ``data/results/structure_manifest.txt``.
    """
    manifest_path = Path("data/results/structure_manifest.txt")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    # Gather directories recursively.
    dirs = set()
    for base in ("code", "data", "tests"):
        for p in Path(base).rglob("*"):
            if p.is_dir():
                # Store the path relative to the project root.
                dirs.add(str(p))

    # Write sorted list.
    with manifest_path.open("w") as f:
        for d in sorted(dirs):
            f.write(f"{d}\n")

def main():
    """Create directories and write the manifest."""
    _ensure_directories()
    _write_manifest()
    # Simple verification: ensure at least 11 lines.
    manifest_path = Path("data/results/structure_manifest.txt")
    line_count = sum(1 for _ in manifest_path.open())
    if line_count < 11:
        sys.stderr.write(
            f"ERROR: Manifest contains only {line_count} lines; expected >= 11.\\n"
        )
        sys.exit(1)

if __name__ == "__main__":
    main()
