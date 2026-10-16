"""Create required top‑level directory layout and record it.

This script creates the nine directories required by task T001:
  - code/
  - code/simulation/
  - code/analysis/
  - code/utils/
  - tests/unit/
  - tests/integration/
  - data/raw/
  - data/processed/
  - state/

After creation it writes a ``tree``‑like listing (depth 2) to
``state/dir_structure.txt``.  The file is used by CI to verify that all
directories exist.

The script is safe to run multiple times; existing directories are left
untouched and the listing file is overwritten.
"""

import os
from pathlib import Path
from llmxive_toolkit import paths

def _ensure_directories(root: Path, dirs: list[Path]) -> None:
    """Create each directory in ``dirs`` under ``root`` if it does not exist."""
    for d in dirs:
        (root / d).mkdir(parents=True, exist_ok=True)

def _tree_listing(root: Path, max_depth: int = 2) -> str:
    """Return a ``tree -L <max_depth>``‑style string for ``root``."""
    # Helper to compute prefix strings for tree drawing
    def _prefix(parts, is_last):
        """Build a prefix for a given depth."""
        prefix = ""
        for i, last in enumerate(parts):
            prefix += "    " if i == 0 else ("│   " if not last else "    ")
        prefix += "└── " if is_last else "├── "
        return prefix

    lines = ["."]
    # Walk the directory tree up to ``max_depth`` levels
    for current_root, dirs, _ in os.walk(root):
        # Depth relative to root (0 for root itself)
        rel_path = Path(current_root).relative_to(root)
        depth = len(rel_path.parts)
        if depth > max_depth:
            # Prune deeper traversal
            dirs[:] = []
            continue
        # Sort for deterministic output
        dirs.sort()
        # Compute prefix parts for current level (excluding root)
        parent_parts = [True] * (depth - 1)  # placeholder, will be replaced below
        for i, d in enumerate(dirs):
            is_last = i == len(dirs) - 1
            # Build prefix based on current depth
            prefix = "│   " * (depth - 1) if depth > 0 else ""
            connector = "└── " if is_last else "├── "
            line = f"{prefix}{connector}{d}"
            lines.append(line)
            # Recurse into sub‑directory (handled by os.walk)
    return "\n".join(lines)

def main() -> None:
    root = paths.root  # project root as a pathlib.Path
    # Define required directories relative to the project root
    required_dirs = [
        Path("code"),
        Path("code/simulation"),
        Path("code/analysis"),
        Path("code/utils"),
        Path("tests/unit"),
        Path("tests/integration"),
        Path("data/raw"),
        Path("data/processed"),
        Path("state"),
    ]

    # Create directories
    _ensure_directories(root, required_dirs)

    # Generate tree listing (depth 2) and write it
    listing = _tree_listing(root, max_depth=2)
    out_path = paths.state("dir_structure.txt")
    out_path.write_text(listing + "\n", encoding="utf-8")
    print(f"Directory structure written to {out_path}")

if __name__ == "__main__":
    main()
