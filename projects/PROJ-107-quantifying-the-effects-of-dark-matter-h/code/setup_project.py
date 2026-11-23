"""T001: Create the full project directory hierarchy and verify its existence.

Creates every directory listed in tasks.md T001, then captures a
directory-tree listing to ``data_dir_tree.txt`` (data hierarchy) and
``output_dir_tree.txt`` (output/docs hierarchy) at the project root for
later audit. Exits non-zero if any required directory is missing.
"""
import sys
from pathlib import Path

from llmxive_toolkit import paths

PROJECT_ROOT = paths.root

REQUIRED_DIRS = [
    "code/ingestion",
    "code/processing",
    "code/analysis",
    "code/utils",
    "code/tests",
    "data/raw/tng100",
    "data/raw/millennium",
    "data/processed",
    "outputs/figures",
    "outputs/reports",
]

REQUIRED_FILES = [
    "docs/quickstart.md",
    "docs/README.md",
]

DATA_TREE_ROOTS = ["data"]
OUTPUT_TREE_ROOTS = ["outputs", "docs", "code"]


def create_hierarchy() -> None:
    for rel in REQUIRED_DIRS:
        (PROJECT_ROOT / rel).mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "docs").mkdir(parents=True, exist_ok=True)
    for rel in REQUIRED_FILES:
        path = PROJECT_ROOT / rel
        if not path.exists():
            path.touch()


def build_tree(root: Path, prefix: str = "", max_depth: int = 2, depth: int = 0) -> list:
    """Return a list of text lines for a directory tree (like `tree -L 2`)."""
    lines = []
    if depth >= max_depth:
        return lines
    try:
        entries = sorted(
            [p for p in root.iterdir() if p.is_dir()],
            key=lambda p: p.name,
        )
    except OSError:
        return lines
    for i, entry in enumerate(entries):
        connector = "└── " if i == len(entries) - 1 else "├── "
        lines.append(f"{prefix}{connector}{entry.name}/")
        extension = "    " if i == len(entries) - 1 else "│   "
        lines.extend(
            build_tree(entry, prefix + extension, max_depth, depth + 1)
        )
    return lines


def write_tree_file(out_path: Path, tree_roots: list) -> None:
    lines = []
    for i, rel in enumerate(tree_roots):
        root = PROJECT_ROOT / rel
        lines.append(f"{rel}/")
        lines.extend(build_tree(root))
        if i < len(tree_roots) - 1:
            lines.append("")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def verify() -> bool:
    missing = [rel for rel in REQUIRED_DIRS if not (PROJECT_ROOT / rel).is_dir()]
    missing_files = [rel for rel in REQUIRED_FILES if not (PROJECT_ROOT / rel).is_file()]
    if missing:
        print(f"MISSING DIRECTORIES: {missing}", file=sys.stderr)
    if missing_files:
        print(f"MISSING FILES: {missing_files}", file=sys.stderr)
    return not missing and not missing_files


def main() -> int:
    create_hierarchy()
    write_tree_file(PROJECT_ROOT / "data_dir_tree.txt", DATA_TREE_ROOTS)
    write_tree_file(PROJECT_ROOT / "output_dir_tree.txt", OUTPUT_TREE_ROOTS)
    ok = verify()
    if ok:
        print("All required directories and files present.")
        print("Wrote data_dir_tree.txt and output_dir_tree.txt")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
