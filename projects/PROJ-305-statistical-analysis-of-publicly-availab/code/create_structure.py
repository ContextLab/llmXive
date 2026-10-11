"""
Script to create the required project directory tree and capture a
filesystem snapshot (up to depth 3) in logs/structure.txt.
"""
import sys
from pathlib import Path

# List of directories that must exist for the project
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

def _create_directories(root: Path) -> None:
    """
    Create all directories listed in REQUIRED_DIRS under the given root.
    """
    for rel_dir in REQUIRED_DIRS:
        dir_path = root / rel_dir
        dir_path.mkdir(parents=True, exist_ok=True)

def _write_snapshot(root: Path, output_file: Path, max_depth: int = 3) -> None:
    """
    Write a simple tree‑like snapshot of the directory hierarchy up to
    ``max_depth``. The format is lightweight – each line contains the
    relative path of a file or directory (directories end with a slash).
    """
    lines = []

    root = root.resolve()

    def walk(current: Path, depth: int) -> None:
        if depth > max_depth:
            return
        for entry in sorted(current.iterdir()):
            rel = entry.relative_to(root)
            line = str(rel) + ("/" if entry.is_dir() else "")
            lines.append(line)
            if entry.is_dir():
                walk(entry, depth + 1)

    walk(root, 0)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("\n".join(lines), encoding="utf-8")

def main() -> None:
    """
    Main entry point:
    1. Create the required directory tree.
    2. Write the snapshot to logs/structure.txt.
    """
    root = Path.cwd()
    _create_directories(root)
    snapshot_path = root / "logs" / "structure.txt"
    _write_snapshot(root, snapshot_path, max_depth=3)
    print(f"Directory snapshot written to {snapshot_path}")
    sys.exit(0)

if __name__ == "__main__":
    main()
