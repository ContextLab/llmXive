"""Create the project skeleton directories and regenerate docs/structure.txt.

Ensures data/raw/, data/processed/, logs/, docs/, results/ exist (each with a
.gitkeep so empty directories are tracked), then writes a directory-tree
listing to docs/structure.txt (T001/T017).
"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "logs",
    "docs",
    "results",
]

EXCLUDED_DIRS = {".venv", "__pycache__", ".git", ".pytest_cache", "node_modules"}


def ensure_directories() -> None:
    """Create every required skeleton directory with a .gitkeep file."""
    for rel in REQUIRED_DIRS:
        d = PROJECT_ROOT / rel
        d.mkdir(parents=True, exist_ok=True)
        keep = d / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")
        print(f"ensured: {rel}/")


def build_tree(root: Path, prefix: str = "") -> list:
    """Return a list of tree-formatted lines for the directory at root."""
    entries = sorted(
        [e for e in root.iterdir() if e.name not in EXCLUDED_DIRS],
        key=lambda p: (p.is_file(), p.name.lower()),
    )
    lines = []
    for i, entry in enumerate(entries):
        connector = "└── " if i == len(entries) - 1 else "├── "
        lines.append(f"{prefix}{connector}{entry.name}")
        if entry.is_dir():
            extension = "    " if i == len(entries) - 1 else "│   "
            lines.extend(build_tree(entry, prefix + extension))
    return lines


def write_structure_file() -> Path:
    """Write the directory-tree listing to docs/structure.txt."""
    out_path = PROJECT_ROOT / "docs" / "structure.txt"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["."] + build_tree(PROJECT_ROOT)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote: docs/structure.txt ({len(lines)} lines)")
    return out_path


def main() -> int:
    """Entry point: create skeleton and regenerate the structure listing."""
    ensure_directories()
    write_structure_file()
    # Sanity checks required by T001 verification.
    for rel in REQUIRED_DIRS:
        if not (PROJECT_ROOT / rel).is_dir():
            print(f"ERROR: missing directory {rel}", file=sys.stderr)
            return 1
    structure = PROJECT_ROOT / "docs" / "structure.txt"
    if not structure.exists() or structure.stat().st_size == 0:
        print("ERROR: docs/structure.txt missing or empty", file=sys.stderr)
        return 1
    if "logs" not in structure.read_text(encoding="utf-8"):
        print("ERROR: logs/ not listed in docs/structure.txt", file=sys.stderr)
        return 1
    print("skeleton OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())