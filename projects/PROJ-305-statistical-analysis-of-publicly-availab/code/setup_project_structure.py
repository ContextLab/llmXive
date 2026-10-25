"""
Project setup script for T001.

This script creates the required project directory layout and writes a
filesystem snapshot to `logs/structure.txt` using the `tree` command when
available, otherwise falling back to a simple Python implementation.
"""

import subprocess
from pathlib import Path
import sys

# List of directories required by the specification
REQUIRED_DIRS = [
    "src/data",
    "src/analysis",
    "src/utils",
    "src/validation",
    "tests/unit",
    "tests/integration",
    "data/raw",
    "data/processed",
    "output",
    "logs",
]


def create_directories() -> None:
    """Create all required directories (idempotent)."""
    for d in REQUIRED_DIRS:
        Path(d).mkdir(parents=True, exist_ok=True)


def _run_tree_command(output_path: Path) -> bool:
    """Run `tree -a -L 3` and write its output to `output_path`.

    Returns True if the command succeeded, False otherwise.
    """
    try:
        # The command may not exist on minimal CI images; capture stderr to avoid noise
        result = subprocess.run(
            ["tree", "-a", "-L", "3"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True,
            text=True,
        )
        output_path.write_text(result.stdout, encoding="utf-8")
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def _fallback_tree(output_path: Path, max_depth: int = 3) -> None:
    """Simple fallback that mimics `tree -a -L <max_depth>` using pathlib."""
    root = Path(".").resolve()

    def _walk(current: Path, prefix: str, depth: int) -> None:
        if depth > max_depth:
            return
        entries = sorted([e for e in current.iterdir()], key=lambda p: p.name.lower())
        for i, entry in enumerate(entries):
            connector = "├── " if i < len(entries) - 1 else "└── "
            line = f"{prefix}{connector}{entry.name}"
            output_path.write_text(line + "\n", encoding="utf-8", append=True)
            if entry.is_dir():
                extension = "│   " if i < len(entries) - 1 else "    "
                _walk(entry, prefix + extension, depth + 1)

    # Ensure the file starts empty
    output_path.write_text("", encoding="utf-8")
    _walk(root, "", 0)


def write_structure_snapshot() -> None:
    """Capture a three‑level directory listing into `logs/structure.txt`."""
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    output_file = logs_dir / "structure.txt"

    if not _run_tree_command(output_file):
        # Fallback implementation
        _fallback_tree(output_file, max_depth=3)


def main() -> None:
    """Entry point for the setup script."""
    create_directories()
    write_structure_snapshot()
    print("Project layout created and logged to logs/structure.txt", file=sys.stderr)


if __name__ == "__main__":
    main()
