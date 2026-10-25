"""Setup project directory layout and capture a filesystem snapshot.

This script creates all required directories for the VAERS analysis pipeline
and writes a three‑level directory tree to ``logs/structure.txt``.  It first
tries to use the system ``tree`` command; if unavailable it falls back to a
pure‑Python implementation that mimics ``tree -a -L 3``.

Required directories (created if missing):
  - src/data/
  - src/analysis/
  - src/utils/
  - src/validation/
  - tests/unit/
  - tests/integration/
  - data/raw/
  - data/processed/
  - output/
  - logs/

The ``quickstart.md`` already documents the runnable command
``python -m src.main``; this script satisfies the verification steps:
  * ``test -s logs/structure.txt`` – the file is non‑empty.
  * ``grep -c src logs/structure.txt`` – at least one line contains ``src``.
"""

import subprocess
from pathlib import Path

from llmxive_toolkit import paths

def _create_required_directories() -> None:
    """Create the directory tree required by the project."""
    required_dirs = [
        Path("src/data"),
        Path("src/analysis"),
        Path("src/utils"),
        Path("src/validation"),
        Path("tests/unit"),
        Path("tests/integration"),
        Path("data/raw"),
        Path("data/processed"),
        Path("output"),
        Path("logs"),
    ]
    for d in required_dirs:
        d.mkdir(parents=True, exist_ok=True)

def _write_structure_snapshot() -> None:
    """Write a three‑level directory listing to ``logs/structure.txt``."""
    logs_dir = paths.logs()
    logs_dir.mkdir(parents=True, exist_ok=True)
    output_path = logs_dir / "structure.txt"

    # Prefer the real ``tree`` utility for exact formatting.
    try:
        result = subprocess.run(
            ["tree", "-a", "-L", "3"],
            capture_output=True,
            text=True,
            check=True,
        )
        output_path.write_text(result.stdout, encoding="utf-8")
        return
    except Exception:
        # ``tree`` not available – fall back to a simple pathlib walk.
        max_depth = 3
        lines = []

        def _add_path(p: Path, depth: int) -> None:
            indent = "│   " * (depth - 1)
            prefix = "├── " if depth > 0 else ""
            lines.append(f"{indent}{prefix}{p.name}")

        root = Path(".")
        for path in sorted(root.rglob("*")):
            relative = path.relative_to(root)
            depth = len(relative.parts)
            if depth <= max_depth:
                _add_path(path, depth)

        output_path.write_text("\n".join(lines), encoding="utf-8")

def main() -> None:
    """Entry point for the setup script."""
    _create_required_directories()
    _write_structure_snapshot()

if __name__ == "__main__":
    main()